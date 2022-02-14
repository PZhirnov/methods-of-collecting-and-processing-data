import requests
from bs4 import BeautifulSoup
import re
import time
import pandas as pd
from random import randint


URL_MAIN = 'https://hh.ru'


def clear(text):
    text = text.replace(' ', '').replace('\u202f', '')
    result = re.findall(r'\d+', text)
    return result


def compensation(compensation_val):
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
        print(compensation_val)
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
    print(result_html.status_code)
    print(result_html.text)
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

    def get_item(self, vacancy):
        # Получаем все данные по вакансии
        item = vacancy
        # 1. Наименование вакансии и ссылка
        vacancy_title = item.a.string
        vacancy_href = item.a.attrs.get('href')
        # 2. Условия оплаты - диапазон от и до, валюта.
        vacancy_compensation = item.find('span', attrs={'data-qa': 'vacancy-serp__vacancy-compensation'})
        if vacancy_compensation:
            salary_from, salary_to, salary_currency = compensation(vacancy_compensation.text)
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
        return [vacancy_title,
                vacancy_href,
                salary_from,
                salary_to,
                salary_currency,
                employer_name,
                employer_href,
                status_link,
                status_class,
                address_employer,
                responsibility,
                requirements
                ]

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


def get_hh(url_start, page_num=None):
    data_all_pages = []
    page_html = request_page(url_start)
    time.sleep(5)
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


START_URL = 'https://hh.ru/search/vacancy?area=1&fromSearchLine=true&text=Python'

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
