from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from jobparser import settings
from jobparser.spiders.hh import HhSpider
from jobparser.spiders.sj import SuperJobSpider

if __name__ == "__main__":
    crawler_settings = Settings()
    crawler_settings.setmodule(settings)

    # TODO: customize it
    while True:
        answ = input("Введите условный код паука (hh, sj) и через пробел ключевое слово для поиска :")
        answ = answ.split()
        if 'hh' in answ or 'sj' in answ:
            source_code = answ[0]
            query_keyword = answ[1]
        else:
            source_code = 'all'
            query_keyword = answ[0]

        spider_hh_init_kwargs = {"query_text": query_keyword}
        spider_sj_init_kwargs = {"query_text": query_keyword}

        process = CrawlerProcess(settings=crawler_settings)
        if source_code == 'hh' or source_code == 'all':
            process.crawl(HhSpider, **spider_hh_init_kwargs)
        if source_code == 'sj' or source_code == 'all':
            process.crawl(SuperJobSpider, **spider_sj_init_kwargs)

        process.start()
