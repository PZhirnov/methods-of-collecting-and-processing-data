# import response as response
import scrapy
from scrapy.http import TextResponse
from scrapy.loader import ItemLoader

from leroy.items import LeroyItem


class LeroySpider(scrapy.Spider):
    name = "leroymerlin"
    allowed_domains = ["leroymerlin.ru"]
    start_urls = [
        "https://leroymerlin.ru/search/?q=плитка",
    ]

    def __init__(self, query):
        super().__init__()
        self.start_urls = [
            f"https://leroymerlin.ru/search/?q={query}",
        ]

    def parse_item(self, response: TextResponse):
        print("PARSE_ITEM")
        article_xpath = '//span[@slot="article"]/@content'
        title_xpath = './/h1[@slot="title"]/text()'
        price_xpath = './/*[@class="primary-price"]/span[@slot="price"]/text()'
        small_images_xpath = './/picture//source//@data-origin'
        def_list_xpath = './/dl[@class="def-list"]//div[@class="def-list__group"]'

        # print(len(response.xpath(small_images_xpath)))
        loader = ItemLoader(item=LeroyItem(), response=response)

        loader.add_xpath("article_number", article_xpath)
        loader.add_value("url", response.url)
        loader.add_xpath("title", title_xpath)
        loader.add_xpath("price", price_xpath)
        loader.add_xpath("img_urls", small_images_xpath)
        loader.add_xpath("def_list", def_list_xpath)
        print('Loader: ', loader.load_item())
        yield loader.load_item()

    def parse(self, response: TextResponse, **kwargs):
        items_xpath = './/section[contains(@class, "_plp")]/div/div[contains(@class, "largeCard")]//a'
        print(items_xpath)
        item_urls = response.xpath(items_xpath)
        print(item_urls)
        for item_url in item_urls:
            href = item_url.xpath('./@href').get()
            url = response.urljoin(href)
            print(url)
            yield response.follow(url, callback=self.parse_item)
        # pagination
        next_url = response.xpath('.//a[@data-qa-pagination-item="right"]/@href').get()
        if next_url:
            yield response.follow(next_url, callback=self.parse)
