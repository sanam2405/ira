import scrapy
from scrapy import Request
from scrapy.http import TextResponse


class GitabitanSpider(scrapy.Spider):
    name = "gitabitan"
    allowed_domains = ["gitabitan.net"]
    start_urls = ["http://gitabitan.net"]

    def start_requests(self):
        yield scrapy.Request(
            url="http://gitabitan.net/top.asp?songid=2300", callback=self.parse
        )

    def parse(self, response):
        print("Response: ", response.text)
        pass
