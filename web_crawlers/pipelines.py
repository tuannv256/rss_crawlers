# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface


from biz.images import download_resize_and_upload_image, get_default_image_url
from services.scylladb.mm_scylla_db import MMScyllaDB
from shared_components.domains.music_monster.models.cql.crawled_rss_news import CrawledRSSNews
from shared_components.utilities.design_patterns.singleton_registry import Si
from web_crawlers.items import RSSNewsItem


class WebCrawlersPipeline:
    async def process_item(self, item, spider):
        if type(item) is RSSNewsItem:
            mobile_resized_image_url = None
            image_url = item.get("image_url")
            if image_url:
                mobile_resized_image_url = await download_resize_and_upload_image(image_url)
            if not mobile_resized_image_url:
                mobile_resized_image_url = get_default_image_url(item.get("source_id"))
            await Si(MMScyllaDB).update(
                CrawledRSSNews,
                [
                    (CrawledRSSNews.header, item.get("header")),
                    (CrawledRSSNews.image_url, image_url),
                    (CrawledRSSNews.mobile_resized_image_url, mobile_resized_image_url),
                    (CrawledRSSNews.article_link, item.get("article_link")),
                    (CrawledRSSNews.content, item.get("content")),
                    (CrawledRSSNews.is_crawled, True),
                ],
                where_clauses=[
                    (CrawledRSSNews.rss_link, item.get("rss_link")),
                    (CrawledRSSNews.batch_id, item.get("batch_id")),
                ],
            )
        return item
