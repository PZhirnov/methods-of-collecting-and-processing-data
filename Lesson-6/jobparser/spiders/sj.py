import scrapy
from scrapy.http import TextResponse
from jobparser.items import JobParserItem
from bs4 import BeautifulSoup

SJ_URL_TEMPLATE = (
    "https://www.superjob.ru/vacancy/search/?keywords="
)
GEO = (
    "&geoMoscow=4"
)


class SuperJobSpider(scrapy.Spider):
    name = "superjob"
    allowed_domains = ["superjob.ru"]
    start_urls = ["http://superjob.ru/"]
    main_urls = "http://superjob.ru"
    # XPath для полей в блоках items
    field_to_xpath_for_parse = {
        'url': './/a/@href',
        'title': './/a/text()',
    }

    def __init__(self, query_text: str, **kwargs):
        super().__init__(**kwargs)
        start_url = SJ_URL_TEMPLATE + query_text + GEO
        self.start_urls = [start_url]
        print('init_сработал')

    def parse_item(self, response: TextResponse):
        item = JobParserItem()
        item["url"] = response.url
        item["source_name"] = self.name
        item['title'] = response.xpath('.//div[contains(@class, "f-test-vacancy-base-info")][1]//h1/text()').get()
        salary_preprocessing = response.xpath('.//div[contains(@class, "f-test-vacancy-base-info")]'
                                              '//span[contains(text(), "месяц")]/preceding::span[1]')
        item['salary'] = BeautifulSoup(salary_preprocessing.get(), "lxml").text
        print('сработал')
        yield item

    def parse(self, response: TextResponse):
        # Получили блоки с вакансиями на странице
        items = response.xpath(
            './/div[contains(@class, "f-test-vacancy-item")]'
        )
        # print(items)
        for item in items:
            url = self.main_urls + item.xpath(self.field_to_xpath_for_parse["url"]).get()
            print('url get()', url)
            yield response.follow(url, callback=self.parse_item)

        # Пагинация по странице
        next_url = self.main_urls + response.xpath('.//a[@rel="next"]/@href').get()
        if next_url:
            yield response.follow(next_url, callback=self.parse)
        pass
