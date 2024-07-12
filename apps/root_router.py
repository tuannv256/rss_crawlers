import crochet
from biz.rss_news_crawler import crawl_rss_news_from_sources
from fastapi import APIRouter
from shared_components.domains.music_monster.models.schemas.rss_news import (
    CrawlRSSSourcesRequest,
    CrawlRSSSourcesResponse,
)

router = APIRouter()


@crochet.run_in_reactor
@router.post("/crawl_rss_sources", response_model=CrawlRSSSourcesResponse)
async def crawl_rss_sources(body: CrawlRSSSourcesRequest):
    return CrawlRSSSourcesResponse.from_common_result(await crawl_rss_news_from_sources(body))
