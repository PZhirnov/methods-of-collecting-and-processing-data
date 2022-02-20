from pprint import pprint
import requests
from lxml.html import fromstring
import re
from pymongo import MongoClient
from datetime import datetime


# -- Параметры БД ----
MONGO_HOST = "localhost"
MONGO_PORT = 27017
MONGO_DB = "news_feed"
MONGO_COLLECTION = "news"
MONGO_ARCHIVE = "archive"


# -- Функции для работы с БД

def get_from_cursor(cursor, all_data=False):
    """
    Получает список словарей из курсора, если all_data=True.
    Если all = Flase, то возвращаем только первый словарь
    """
    rows_data = []
    for i in cursor:
        rows_data.append(i)
    return rows_data if all_data else rows_data[0]


def add_last_modified(dict_in):
    """
    Функция доавляет в словарь поле с датой последней модификации
    """
    dict_in['last_modified'] = datetime.utcnow()
    return dict_in


def insert_only_new(list_dict):
    """
    Функция принимает список словарей, но может принять и один словарь, если нужно.
    Возвращает 1, если запись новая и была добавлена в базу
    """
    with MongoClient(MONGO_HOST, MONGO_PORT) as client:
        db = client[MONGO_DB]
        collection = db[MONGO_COLLECTION]
        i = 0
        for cur_dict in list_dict:
            cur_dict = add_last_modified(cur_dict)
            find_one = collection.find({'href': cur_dict.get('href')})
            old_data = get_from_cursor(find_one, True)
            if not len(old_data):
                collection.insert_one(cur_dict)
                i += 1
    return [len(list_dict), i]

# --- Общие параметры


HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
           }

# ---------------------- ПАРАМЕТРЫ XPATH ДЛЯ РЕСУРСОВ ------------------------------------

# -------- LENTA ---------
NAME_SOURCE_LENTA = 'Lenta'
URL_SOURCE_LENTA = 'https://lenta.ru/'
DATE_NEWS_LENTA = './/time[contains(@class, "topic-header__item topic-header__time")]/text()'
HREF_DATA_LENTA = {
    'main_url_source': None,
    'name_source': None,
    'date': './/time[contains(@class, "topic-header__item topic-header__time")]/text()',
}
PARAMS_BLOCK_LENTA = {
    'last24': {
        'ITEM_XPATH': '//div[contains(@class, "last24")]//a',  # список новостей
        'HREF_FROM_LINK': './@href',
        'NEWS_HEADLINE': './div[@class="card-mini__text"]/span/text()',
        'HREF_DATA': HREF_DATA_LENTA
    },
    'top_news': {
        'ITEM_XPATH': '//div[@class="topnews"]//a[@class="card-mini _topnews"]',  # список новостей
        'HREF_FROM_LINK': './@href',
        'NEWS_HEADLINE': './div[@class="card-mini__text"]/span/text()',
        'HREF_DATA': HREF_DATA_LENTA
    },
    'first_top_news': {
        'ITEM_XPATH': '//div[@class="topnews__first-topic"]//a[@class="card-big _topnews _news"]',  # список новостей
        'HREF_FROM_LINK': './@href',
        'NEWS_HEADLINE': '//h3[@class="card-big__title"]/text()',
        'HREF_DATA': HREF_DATA_LENTA
    },
    'long_grid_card_mini': {
        'ITEM_XPATH': '//a[@class="card-mini _longgrid"]',  # список новостей
        'HREF_FROM_LINK': './@href',
        'NEWS_HEADLINE': './div[@class="card-mini__text"]/span/text()',
        'HREF_DATA': HREF_DATA_LENTA
    },
    'long_grid_card_big': {
        'ITEM_XPATH': '//a[@class="card-big _longgrid"]',  # список новостей
        'HREF_FROM_LINK': './@href',
        'NEWS_HEADLINE': './/h3[@class="card-big__title"]/text()',
        'HREF_DATA': HREF_DATA_LENTA
    }
}

# MAIL RU
# DATE_NEWS_MAIL = './/span[@datetime]/@datetime'
URL_SOURCE_MAIL = 'https://news.mail.ru/'
HREF_DATA_MAIL = {
    'main_url_source': './/div[@data-logger="Breadcrumbs"]//'
                       'span[contains(@class, "breadcrumbs__item")]//a[1]/@href',
    'name_source': './/div[@data-logger="Breadcrumbs"]//'
                   'span[contains(@class, "breadcrumbs__item")]//a[1]/span/text()',
    'date': './/span[@datetime]/@datetime',
}
PARAMS_BLOCK_MAIL = {
    'daynews__main': {
        'ITEM_XPATH': './/div[@data-module="TrackBlocks"]//td[@class="daynews__main"]//a',  # список новостей
        'HREF_FROM_LINK': './@href',
        'NEWS_HEADLINE': './/span[contains(@class, "photo__subtitle")]/text()',
        'HREF_DATA': HREF_DATA_MAIL
    },
    'daynews__items': {
        'ITEM_XPATH': './/div[@data-module="TrackBlocks"]//td[@class="daynews__items"]//'
                      'div[contains(@class, "daynews__item")]//a',  # список новостей
        'HREF_FROM_LINK': './@href',
        'NEWS_HEADLINE': './/span[contains(@class, "photo__title")]/text()',
        'HREF_DATA': HREF_DATA_MAIL
    },
    'track_blocks': {
        'ITEM_XPATH': './/ul[@data-module="TrackBlocks"]//li[contains(@class, "list__item")]//a',  # список новостей
        'HREF_FROM_LINK': './@href',
        'NEWS_HEADLINE': './text()',
        'HREF_DATA': HREF_DATA_MAIL
    },
}

# YANDEX
URL_SOURCE_YANDEX = 'https://yandex.ru/news/'
HREF_DATA_YANDEX = {}
DATA_ON_PAGE = {
    'main_url_source': './/a[@class="mg-card__source-link"][1]/@href',
    'name_source': './/a[@class="mg-card__source-link"][1]/text()',
    'date': './/span[@class="mg-card-source__time"]/text()',
}
PARAMS_BLOCK_YANDEX = {
    'top-heading': {
        'ITEM_XPATH': './/section[@aria-labelledby="top-heading"]//'
                      'div[contains(@class, "mg-grid__col")]',  # список новостей
        'HREF_FROM_LINK': './/a[@class="mg-card__link"]/@href',
        'NEWS_HEADLINE': './/a[@class="mg-card__link"]/text()',
        'DATA_ON_PAGE': DATA_ON_PAGE,
    },
}

# ----- РАБОТА С ЗАПРОСОМ ------------


def get_dom_from_response(url):
    """
    Отправляет сформированный запрос
    """
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        result_dom = fromstring(response.text)
        return result_dom
    return None


def get_data_from_link(url, dict_xpath_selectors: {}):
    """
    Функция получает словарь с выражениями XPATH и возвращает значения.
    Используется при необходимости получения данных после перехода по внешней ссылке.
    """
    try:
        domain = re.findall(r'(\w+\.\w+)', url)
        dom = get_dom_from_response(url)
        result_dict = {}
        for key, val in dict_xpath_selectors.items():
            result_dict[key] = dom.xpath(val)[0] if val else None
        # Если это первоисточник или данных нет на странице, то ипользуем домен
        if result_dict.get('main_url_source') is None:
            result_dict['main_url_source'] = domain[0]
            result_dict['name_source'] = domain[0].split('.')[0]
        return result_dict
    except IndexError as exc:
        # print(exc, url)   # отладочаная информация
        result_dict['main_url_source'] = domain[0]
        result_dict['name_source'] = domain[0].split('.')[0]
    return result_dict


def get_news(url, name_block, params):
    """
    Функция возвращает новости с ресурса
    :param url: url главной страницы источника
    :param name_block: имя обрабатываемого блока
    :param params: словарь с параметрами блока
    :return: список с словарей
    """
    dom = get_dom_from_response(url)
    items_news = dom.xpath(params.get(name_block).get('ITEM_XPATH'))
    dict_block = params.get(name_block)
    news_data = []
    for item in items_news:
        item_data = {}
        item_data['name_block'] = name_block
        href = item.xpath(dict_block.get('HREF_FROM_LINK'))[0]
        item_data['headline'] = item.xpath(dict_block.get('NEWS_HEADLINE'))[0]
        href = href if 'http' in href else url + href
        item_data['href'] = href  # сразу сделаем полную ссылку
        # Получим данные об источнике и дате публикации из ссылки
        href_data = dict_block.get('HREF_DATA')
        if href_data:
            data_from_link = get_data_from_link(item_data.get('href'), href_data)
            for key, val in data_from_link.items():
                item_data[key] = val
        data_on_page = dict_block.get('DATA_ON_PAGE')
        if data_on_page:
            for key, val in data_on_page.items():
                item_data[key] = item.xpath(val)[0]
        news_data.append(item_data)
    return news_data

# ----------- Start parsing ------------------


def start():
    # Запуск сбора новостей
    while True:
        answ = input('Укажите код сайта, с котрого надо получить последние новости '
                     '(l - Lenta, m - Mail, y - Yandex, all - со всех) или q для выхода:').lower()[:1]
        # LENTA

        if answ in ['l', 'a']:
            print(f'Источник данных: ', URL_SOURCE_LENTA)
            for key, val in PARAMS_BLOCK_LENTA.items():
                news_block = get_news(URL_SOURCE_LENTA, key, PARAMS_BLOCK_LENTA)
                report = insert_only_new(news_block)
                print(f'Блок: {key} Всего: {report[0]} Новых: {report[1]}')
        # MAIL
        if answ in ['m', 'a']:
            print(f'Источник данных: ', URL_SOURCE_MAIL)
            for key, val in PARAMS_BLOCK_MAIL.items():
                news_block = get_news(URL_SOURCE_MAIL, key, PARAMS_BLOCK_MAIL)
                report = insert_only_new(news_block)
                print(f'Блок: {key} Всего: {report[0]} Новых: {report[1]}')
        # YANDEX.RU
        if answ in ['y', 'a']:
            print(f'Источник данных: ', URL_SOURCE_YANDEX)
            for key, val in PARAMS_BLOCK_YANDEX.items():
                news_block = get_news(URL_SOURCE_YANDEX, key, PARAMS_BLOCK_YANDEX)
                report = insert_only_new(news_block)
                print(f'Блок: {key} Всего: {report[0]} Новых: {report[1]}')
        if answ == 'q':
            print('Спасибо за использование приложения!')
            break


start()

# news_last24 = get_news(URL_SOURCE_LENTA, 'last24', PARAMS_BLOCK_LENTA)
# pprint(news_last24)
# insert_only_new(news_last24)
# pprint(get_news(URL_SOURCE_YANDEX, 'top-heading', PARAMS_BLOCK_YANDEX))
