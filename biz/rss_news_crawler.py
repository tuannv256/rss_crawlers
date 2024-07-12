import datetime
import logging
import uuid
from typing import Dict, List, Tuple

import feedparser
from pydantic import BaseModel
from scrapy.crawler import CrawlerRunner
from scrapy.utils.project import get_project_settings

from services.scylladb.mm_scylla_db import MMScyllaDB
from shared_components.domains.music_monster.biz.shared_logic.system_configs import get_system_configs_by_name
from shared_components.domains.music_monster.models.cql.crawled_rss_news import CrawledRSSNews
from shared_components.domains.music_monster.models.cql.rss_source import RSSSource
from shared_components.domains.music_monster.models.enum.rss_news import RSSNewsSource
from shared_components.domains.music_monster.models.schemas.rss_news import (
    CrawlRSSSourcesData,
    CrawlRSSSourcesRequest,
    CrawlRSSSourcesResponse,
    RSSSourceRequest,
)
from shared_components.domains.music_monster.models.schemas.system_configs import CrawlerConfig, SystemConfigName
from shared_components.models.schemas.api.common_result import has_common_result
from shared_components.utilities.design_patterns.singleton_registry import Si
from web_crawlers.spiders.bbc_news import BBCNewsSpider
from web_crawlers.spiders.yahoo_news import YahooNewsSpider

RSS_DATETIME_FORMAT = "%a, %d %b %Y %H:%M:%S %Z"


class RSSItem(BaseModel):
    source_id: int
    category: str
    language: str
    rss_link: str
    description: str | None
    image_url: str | None
    publish_time: datetime.datetime | None
    title: str


spider_settings = get_project_settings()
runner = CrawlerRunner(spider_settings)


def run_spiders(batch_id: uuid.UUID, rss_news: List[CrawledRSSNews]):
    for news in rss_news:
        kwargs = {
            "start_urls": [news.rss_link],
            "source_id": news.source_id,
            "rss_link": news.rss_link,
            "batch_id": batch_id,
            "image_url": news.image_url,
        }
        if news.source_id == RSSNewsSource.YAHOO:
            runner.crawl(YahooNewsSpider, **kwargs)
        elif news.source_id == RSSNewsSource.BBC:
            runner.crawl(BBCNewsSpider, **kwargs)
        else:
            logging.info(f"Unsupported RSS source: {news.source_id}")


async def get_rss_news_to_crawl(
    batch_id: uuid.UUID, sources: List[RSSSourceRequest]
) -> Tuple[int, List[CrawledRSSNews]]:
    """
    Get RSS news from RSS sources to crawl
    :param body: CrawlRSSSourceRequest
    :return: total rss links were scanned and list of new rss news
    """
    rss_sources: List[RSSSource] = []
    for rss_source_request in sources:
        rss_source = await Si(MMScyllaDB).get_one(
            RSSSource,
            where_clauses=[
                (RSSSource.source_id, rss_source_request.source_id),
                (RSSSource.category, rss_source_request.category),
            ],
        )
        rss_sources.append(rss_source)
    rss_link_item_map: Dict[str, RSSItem] = {}
    # get all rss info from rss sources
    for rss_source in rss_sources:
        data = feedparser.parse(rss_source.link)
        for entry in data.get("entries", []):
            rss_link = entry.get("link")
            if rss_source.source_id == RSSNewsSource.BBC and (
                "/videos/" in rss_link or "/sounds/" in rss_link or "/iplayer/" in rss_link
            ):
                continue
            image_url = None
            thumbnails = entry.get("media_thumbnail", [])
            if thumbnails:
                image_url = thumbnails[0].get("url")
            publish_time_str = entry.get("published")
            publish_time = datetime.datetime.strptime(publish_time_str, RSS_DATETIME_FORMAT)
            rss_link_item_map[rss_link] = RSSItem(
                source_id=rss_source.source_id,
                category=rss_source.category,
                language=rss_source.language,
                rss_link=rss_link,
                description=entry.get("summary"),
                image_url=image_url,
                publish_time=publish_time,
                title=entry.get("title"),
            )
    # get all rss news by rss_links
    rss_news = await Si(MMScyllaDB).get_multi_with_in_operator(
        CrawledRSSNews, CrawledRSSNews.rss_link, list(rss_link_item_map.keys())
    )
    rss_link_existed_map = {rss.rss_link: True for rss in rss_news}
    # remove existed rss news
    yahoo_news = []
    bbc_news = []
    rss_news: List[CrawledRSSNews] = []
    for rss_link, rss_item in rss_link_item_map.items():
        if rss_link_existed_map.get(rss_link):
            continue
        if rss_item.source_id == RSSNewsSource.BBC:
            bbc_news.append(
                CrawledRSSNews(
                    rss_link=rss_link,
                    batch_id=batch_id,
                    category=rss_item.category,
                    description=rss_item.description,
                    image_url=rss_item.image_url,
                    language=rss_item.language,
                    publish_time=rss_item.publish_time,
                    source_id=rss_item.source_id,
                )
            )
        elif rss_item.source_id == RSSNewsSource.YAHOO:
            yahoo_news.append(
                CrawledRSSNews(
                    rss_link=rss_link,
                    batch_id=batch_id,
                    category=rss_item.category,
                    description=rss_item.description,
                    image_url=rss_item.image_url,
                    language=rss_item.language,
                    publish_time=rss_item.publish_time,
                    source_id=rss_item.source_id,
                )
            )
    # apply limit random max 5 links per source per times
    filtered_news = []
    crawler_config = await get_system_configs_by_name(SystemConfigName.CRAWLER, CrawlerConfig)
    max_article_per_source_per_times = crawler_config.max_articles_per_source_per_times
    if len(yahoo_news) > max_article_per_source_per_times:
        filtered_news.extend(yahoo_news[0 - max_article_per_source_per_times :])
    if len(bbc_news) > max_article_per_source_per_times:
        filtered_news.extend(bbc_news[0 - max_article_per_source_per_times :])
    if filtered_news:
        await Si(MMScyllaDB).insert_multi(filtered_news)
    logging.info(f"Get {len(filtered_news)} new rss news")
    return len(rss_link_item_map.keys()), filtered_news


@has_common_result
async def crawl_rss_news_from_sources(body: CrawlRSSSourcesRequest) -> CrawlRSSSourcesResponse:
    batch_id = uuid.UUID(body.batch_id)
    logging.info("Start crawling RSS news")
    total_links_scanned, rss_news = await get_rss_news_to_crawl(batch_id, body.sources)
    if not rss_news:
        logging.info("No new news to push")
    else:
        run_spiders(batch_id, rss_news)
    return CrawlRSSSourcesResponse(
        data=CrawlRSSSourcesData(total_links_scanned=total_links_scanned, total_new_links=len(rss_news))
    )
