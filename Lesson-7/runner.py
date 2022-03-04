from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from leroy import settings
from leroy.spiders.leroymerlin import LeroySpider


if __name__ == "__main__":
    crawler_settings = Settings()
    crawler_settings.setmodule(settings)

    # TODO: customize it
    search = input('Введите товар (если не введете, то выполнится поиск плитки):')
    if not search:
        search = 'плитка'
    process = CrawlerProcess(settings=crawler_settings)
    process.crawl(LeroySpider, query=search)
    process.start()
