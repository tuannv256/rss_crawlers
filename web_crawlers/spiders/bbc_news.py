import scrapy
from scrapy.http.response.html import HtmlResponse

from web_crawlers.items import RSSNewsItem


class BBCNewsSpider(scrapy.Spider):
    name = "bbc_news"
    allowed_domains = ["bbc.com", "bbc.co.uk"]

    def parse(self, response: HtmlResponse):
        article = response.xpath('//*[@id="main-content"]/article')
        header_div = article.xpath("header")
        header = "".join(header_div.xpath(".//text()").getall())
        article_divs = article.xpath("div")
        content = ""
        for div in article_divs:
            component = div.xpath("@data-component").get()
            if component == "headline-block":
                header = div.xpath("h1/text()").get()
            elif component == "text-block":
                content += "".join(div.xpath(".//text()").getall())
        if header and content:
            yield RSSNewsItem(
                source_id=self.source_id,
                batch_id=self.batch_id,
                article_link=response.url,
                rss_link=self.rss_link,
                header=header,
                image_url=self.image_url,
                content=content,
            )
