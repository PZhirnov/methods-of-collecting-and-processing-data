import requests
from bs4 import BeautifulSoup
import re
import time
import pandas as pd
from random import randint
from pprint import pprint
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING, MongoClient
from datetime import datetime
from random import randint
from pprint import pprint


URL_MAIN = 'https://hh.ru'
START_URL = 'https://hh.ru/search/vacancy?area=1&fromSearchLine=true&text=Python'


def clear(text):
    text = text.replace(' ', '').replace('\u202f', '')
    result = list(map(int, re.findall(r'\d+', text)))
    return result


def parse_compensation(compensation_val):
    """
    Обработка данных о заработной плате
    :param compensation_val:
    :return: список - [ от, до, валюта ]
    """
    val_from = None
    val_to = None
    currency = None
    new_list = [val_from, val_to, currency]
    try:
        val_range = clear(compensation_val)
        if 'до' in compensation_val:
            val_to = val_range[0]
        if 'от' in compensation_val:
            val_from = val_range[0]
        if len(val_range) == 2:
            val_from, val_to = val_range
        # Получим валюту
        currency = compensation_val.split(' ')[-1]
        new_list = [val_from, val_to, currency]
    except ValueError:
        pass
    return new_list


def request_page(url_page):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36"
    }
    result_html = requests.get(url_page, headers=headers)
    return result_html.text


class DataFromPage:
    num_vacancies_on_page = 0
    page_next_href = None
    soup_page_full = None

    def __init__(self, html_page):
        self.soup_page_full = BeautifulSoup(html_page, "lxml")
        # Получим полный перечень вакансий на странице
        self.vacancy_items = self.soup_page_full.find_all('div',
                                                          attrs={
                                                              'class': 'vacancy-serp-item vacancy-serp-item_redesigned'
                                                          })
        self.num_vacancies_on_page = len(self.vacancy_items)

        # Сразу проверим возможность перехода на следующую страницу
        page_next_find = self.soup_page_full.find('a', attrs={'data-qa': 'pager-next'})
        if page_next_find:
            self.page_next_href = URL_MAIN + page_next_find.attrs['href']
        else:
            self.page_next_href = None

    def get_item(self, item):
        # Получаем все данные по вакансии - item
        # 1. Наименование вакансии и ссылка
        vacancy_title = item.a.string
        vacancy_href = item.a.attrs.get('href')
        # 2. Условия оплаты - диапазон от и до, валюта.
        vacancy_compensation = item.find('span', attrs={'data-qa': 'vacancy-serp__vacancy-compensation'})
        if vacancy_compensation:
            salary_from, salary_to, salary_currency = parse_compensation(vacancy_compensation.text)
        else:
            salary_from, salary_to, salary_currency = [None, None, None]
        # 3. Работодатель и ссылка на него
        vacancy_employer = item.find('div', attrs={'class': 'vacancy-serp-item__info'})
        company_employer = vacancy_employer.next
        company_employer_a = company_employer.find_all('a')
        # вывод для 3
        if company_employer_a:
            employer_name = company_employer_a[0].text.replace('\xa0', ' ')
            employer_href = URL_MAIN + company_employer_a[0].attrs.get('href')
        else:
            employer_name = None
            employer_href = None

        # 4. Статус работодателя
        try:
            status_link = company_employer_a[1].attrs.get('href')
            status_class = company_employer_a[1].next.get('class')[0]
        except IndexError:
            status_link = None
            status_class = None
        # 5. Адрес
        address_employer_html = item.find('div', attrs={'data-qa': 'vacancy-serp__vacancy-address'})
        address_employer = ', '.join(address_employer_html.text.split(','))  # вывод Москва - Шаболовка

        # 6. Получаем описание вакансии
        g_user_content = item.find('div', attrs={'class': 'g-user-content'})
        description = g_user_content.find_all('div')
        if len(description) == 2:
            responsibility, requirements = [i.text for i in description]
        elif len(description) == 1:
            responsibility, requirements = [description[0].text, None]
        else:
            responsibility, requirements = [None, None]
        return {'vacancy_title': vacancy_title,
                'vacancy_href': vacancy_href,
                'salary_from': salary_from,
                'salary_to': salary_to,
                'salary_currency': salary_currency,
                'employer_name': employer_name,
                'employer_href': employer_href,
                'status_link': status_link,
                'status_class': status_class,
                'address_employer': address_employer,
                'responsibility': responsibility,
                'requirements': requirements,
                }

    def start_parsing(self, page_num=None):
        """
        Запуск процедуры сбора данных
        :param page_num: обозначение страницы - для вывода
        :return: список списков со всеми вакансиями страницы
        """
        result_list = []
        i = 0
        for vacancy in self.vacancy_items:
            vacancy_data = self.get_item(vacancy)
            result_list.append(vacancy_data)
            i += 1
            print(f'{page_num} - {str(i)}:', vacancy_data)
        return result_list


# ------- Основаня функция к 2-му уроку --------
def get_hh(url_start, page_num=None):
    """
    Получаем данные с HH
    """
    data_all_pages = []
    page_html = request_page(url_start)
    i = 0
    while True:
        vac_on_page = DataFromPage(page_html)
        data_from_page = vac_on_page.start_parsing(i+1)
        data_all_pages.extend(data_from_page)
        print(f'Page: {i+1} {vac_on_page.num_vacancies_on_page}')
        i += 1
        if page_num == i:
            break
        if vac_on_page.page_next_href:
            page_html = request_page(vac_on_page.page_next_href)
        else:
            break
        time.sleep(randint(3, 10))
    return data_all_pages


'''
data = get_hh(START_URL, 1)  # если добавить параметр, то можно установить количество выгружаемых страниц
data_frame = pd.DataFrame(data, columns=['Наименование вакансии',
                                         'Ссылка на вакансию',
                                         'ЗП от',
                                         'ЗП до',
                                         'Валюта ЗП',
                                         'Работодатель',
                                         'Ссылка на работодателя',
                                         'Описание статуса',
                                         'Статус проверки работодателя',
                                         'Адрес',
                                         'Обзанности',
                                         'Требования',
                                         ])
data_frame.to_excel("output.xlsx")
'''


# -------- Решения к 3-му уроку --------

# -- Параметры БД ----
MONGO_HOST = "localhost"
MONGO_PORT = 27017
MONGO_DB = "vacancies_from_websites"
MONGO_COLLECTION = "vacancies"
MONGO_ARCHIVE = "archive"


# -- Вспомогательные функции ----

def add_last_modified(dict_in):
    """
    Функция доавляет в словарь поле с датой последней модификации
    """
    dict_in['last_modified'] = datetime.utcnow()
    return dict_in


def get_from_cursor(cursor, all_data=False):
    """
    Получает список словарей из курсора, если all_data=True.
    Если all = Flase, то возвращаем только первый словарь
    """
    rows_data = []
    for i in cursor:
        rows_data.append(i)
    return rows_data if all_data else rows_data[0]


def compare_dicts(dict1: {}, dict2: {}):
    """
    Сравнивает два словаря, предварительно исключив поле 'last_modified' и '_id'
    """
    dict1 = dict1.copy()
    dict2 = dict2.copy()
    for i in ['_id', 'last_modified']:
        if dict1.get(i):
            dict1.pop(i)
        if dict2.get(i):
            dict2.pop(i)
    compare_result = dict1 == dict2
    return compare_result


# РЕШЕНИЯ ПО УСЛОВИЯМ


"""
    1. Развернуть у себя на компьютере/виртуальной машине/хостинге 
    MongoDB и реализовать функцию, записывающую собранные вакансии в созданную БД.
"""


def insert_data_many(list_dict):
    with MongoClient(MONGO_HOST, MONGO_PORT) as client:
        db = client[MONGO_DB]
        collection = db[MONGO_COLLECTION]
        # Добавим даты в словари
        list_dict = list(map(lambda x: add_last_modified(x), list_dict))
        collection.insert_many(list_dict)


# -- Проверка :
def get_and_insert_many_in_mongo(url_start, page_num=None):
    """
    1. Получаем данные с HH.
    2. Обрабатываем все ссылке на странице и сохраняем в БД.
    3. Переходим на следуюущую страницу и повторяем п.1-2 пока есть данные
    """
    page_html = request_page(url_start)
    i = 0
    rows_count = 0
    while True:
        vac_on_page = DataFromPage(page_html)
        data_from_page = vac_on_page.start_parsing(i+1)
        insert_data_many(data_from_page)
        i += 1
        rows_count += len(data_from_page)
        if i == page_num:
            break
        if vac_on_page.page_next_href:
            page_html = request_page(vac_on_page.page_next_href)
        else:
            break
        time.sleep(randint(3, 10))
    return f'Обработано и добавлено {rows_count} записей.'

# Раскомментировать строку для проверки задания - добавит вакансии со всех страниц
# print(get_and_insert_many_in_mongo(START_URL))


"""
    2. Написать функцию, которая производит поиск и выводит 
    на экран вакансии с заработной платой больше введённой суммы.
"""


def get_salary_more_than(salary, currency):
    search_result = []
    with MongoClient(MONGO_HOST, MONGO_PORT) as client:
        db = client[MONGO_DB]
        collection = db[MONGO_COLLECTION]
        cursor = collection.find({'$and': [
            {'$or': [{'$and': [{'salary_from': {'$gte': salary}},
                               {'salary_to': {'$lte': salary}}]},
                     {'salary_to': {'$gte': salary}}]}, {'salary_currency': currency}
        ]})
        for i in cursor:
            search_result.append(i)
    return search_result

# Проверка решения по условию задачи:

# while True:
#     min_wage = int(input('Введите манимальную заработную плату или 0 для выхода: '))
#     if min_wage == 0:
#         break
#     result = get_salary_more_than(min_wage, 'руб.')  # вы выборке есть и доллары, поэтому тут можно доработку сделать
#     pprint(result)
#     print(f'Найдено {len(result)} записей.')


"""
    3. Написать функцию, которая будет добавлять в вашу базу данные только новые вакансии с сайта.
"""


def insert_only_new(list_dict):
    """
        Функция принимает список словарей, но может принять и один словарь, если нужно.
    """
    with MongoClient(MONGO_HOST, MONGO_PORT) as client:
        db = client[MONGO_DB]
        collection = db[MONGO_COLLECTION]
        archive = db[MONGO_ARCHIVE]
        for cur_dict in list_dict:
            cur_dict = add_last_modified(cur_dict)

            # Вариант 1. С find_one_and_update, но без сохранения архива
            # collection.find_one_and_update({'vacancy_href': cur_dict.get('vacancy_href')},
            #                                {'$set': cur_dict}, upsert=True)

            # Вариант 2. C возможностью сохранения данных в архив
            find_one = collection.find({'vacancy_href': cur_dict.get('vacancy_href')})
            old_data = get_from_cursor(find_one, False)
            # если найдена запись, то проверим ее и при необходимости обновим, сохранив в архиве историю изменений
            if len(old_data):
                # сравним переданные данные с имеющимися
                if not compare_dicts(old_data, cur_dict):
                    # сохраним id документа в коллекции для архива перед обновлением
                    id_in_collection = old_data.pop("_id")
                    old_data['id_in_collection'] = id_in_collection
                    archive.insert_one(old_data)
                    collection.update_one({'_id': id_in_collection}, {'$set': add_last_modified(list_dict[0])})
            else:
                collection.insert_one(cur_dict)

# -- Проверка решения по условию задачи №3:


# Еще раз используем ранее созданную функцию, но уже с insert_only_new
def get_insert_only_new(url_start, page_num=None):
    """
    Отличается от get_and_insert_many_in_mongo только одной функцией

    1. Получаем данные с HH.
    2. Обрабатываем все ссылке на странице и сохраняем в БД.
    3. Переходим на следуюущую страницу и повторяем п.1-2 пока есть данные
    """
    page_html = request_page(url_start)
    i = 0
    rows_count = 0
    while True:
        vac_on_page = DataFromPage(page_html)
        data_from_page = vac_on_page.start_parsing(i+1)
        insert_only_new(data_from_page)  # - тут использовали
        i += 1
        rows_count += len(data_from_page)
        if i == page_num:
            break
        if vac_on_page.page_next_href:
            page_html = request_page(vac_on_page.page_next_href)
        else:
            break
        time.sleep(randint(3, 10))
    return f'Обработано {rows_count} записей.'


# При вызове функции не будут добавлены имеющиеся вакансии в БД
# Если вакансия была найдена и данные в ней оличаются от имеющихся,
# то данные отправляются в архив
print(get_insert_only_new(START_URL, page_num=1))
