# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class WebCrawlersItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class RSSNewsItem(scrapy.Item):
    source_id = scrapy.Field()
    batch_id = scrapy.Field()
    article_link = scrapy.Field()
    rss_link = scrapy.Field()
    header = scrapy.Field()
    image_url = scrapy.Field()
    content = scrapy.Field()
