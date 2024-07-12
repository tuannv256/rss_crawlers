import scrapy
from scrapy.http.response.html import HtmlResponse

from web_crawlers.items import RSSNewsItem


class YahooNewsSpider(scrapy.Spider):
    name = "yahoo_news"
    allowed_domains = ["news.yahoo.co.jp"]

    def parse(self, response: HtmlResponse):
        # parse article link
        body = response.xpath('//*[@id="uamods"]')
        header = body.xpath("header/h1/text()").get()
        article_body = body.css("div.article_body")
        thumbnail_div = article_body.css("div.thumbnail")
        image_url = thumbnail_div.css("img::attr(src)").get()
        content_divs = article_body.xpath("div")
        content = ""
        paragraphs = []
        for content_div in content_divs:
            h2 = content_div.xpath("h2/text()").get()
            if h2:
                content += h2
            p_div = content_div.xpath("p")
            paragraphs = "".join(p_div.xpath(".//text()").getall())
            content += paragraphs
        yield RSSNewsItem(
            source_id=self.source_id,
            batch_id=self.batch_id,
            article_link=response.url,
            rss_link=self.rss_link,
            header=header,
            image_url=self.image_url or image_url,
            content=content,
        )

    def parse_expert_article(self, response: HtmlResponse):
        # parse expert article link
        body = response.xpath('//*[@id="uamods-article"]')
        divs = body.xpath("div")
        content_div = divs[0]
        header = content_div.xpath("header/h1/text()").get()
        section = content_div.xpath("section")
        content = "".join(section.xpath(".//text()").getall())
        yield RSSNewsItem(
            source_id=self.source_id,
            batch_id=self.batch_id,
            article_link=response.url,
            rss_link=self.rss_link,
            header=header,
            content=content,
        )
