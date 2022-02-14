import requests
from bs4 import BeautifulSoup
import re
import time


URL_MAIN = 'https://hh.ru'


def clear(text):
    text = text.replace(' ', '')
    result = re.findall(r'\d+', text)
    return result[0]


def compensation(compensation_val):
    new_list = []
    if 'до' in compensation_val:
        new_list = [0, clear(compensation_val)]

    if 'от' in compensation_val:
        new_list = [clear(compensation_val), None]

    if '-' in compensation_val:
        new_list = compensation_val.split('-')
        new_list = list(map(lambda x: clear(x), new_list))
    # Получим валюту
    currency = compensation_val.split(' ')[-1]
    new_list.append(currency)
    return new_list


def request_page(url_page):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36"
    }
    result_html = requests.get(url_page, headers=headers).text
    return result_html


class DataFromPage:
    num_vacancies_on_page = 0
    page_next_href = None

    def __init__(self, html_page):
        self.html_page = html_page
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

    def get_item(self, index_vacancy):
        # Получаем все данные по вакансии
        item = self.vacancy_items[index_vacancy]
        # 1. Наименование вакансии и ссылка
        vacancy_title = item.a.string
        vacancy_href = item.a.attrs.get('href')
        # 2. Условия оплаты
        vacancy_compensation = item.find('span', attrs={'data-qa': 'vacancy-serp__vacancy-compensation'})
        if vacancy_compensation:
            compensation_range = vacancy_compensation.get_text()  # диапазон от и до
        else:
            compensation_range = "n/a"
        # 3. Работодатель и ссылка на него
        vacancy_employer = item.find('div', attrs={'class': 'vacancy-serp-item__info'})
        company_employer = vacancy_employer.next
        company_employer_a = company_employer.find_all('a')
        # вывод для 3
        if company_employer_a:
            name_employer_name = company_employer_a[0].text.replace('\xa0', ' ')
            name_employer_href = URL_MAIN + company_employer_a[0].attrs.get('href')
        else:
            name_employer_name = 'n/a'
            name_employer_href = 'n/a'

        # 4. Статус работодателя
        if company_employer_a:
            status_link = company_employer_a[1].attrs.get('href')
            status_class = company_employer_a[1].next.get('class')[0]
        else:
            status_link = None
            status_class = None
        # 5. Адрес
        address_employer_html = item.find('div', attrs={'data-qa': 'vacancy-serp__vacancy-address'})
        address_employer = ' '.join(address_employer_html.text.split(','))  # вывод Москва - Шаболовка

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
                compensation_range,
                name_employer_name,
                status_link,
                status_class,
                address_employer,
                responsibility,
                requirements
                ]

    def start_parsing(self, page_num=None):
        """
        Запуск процедуры сбора данных
        :param num_pages:
        :return: список списков со всеми вакансиями страницы
        """
        result_list = []
        i = 0
        for vacancy in self.vacancy_items:
            vacancy_data = self.get_item(i)
            result_list.append(vacancy_data)
            i += 1
            print(f'{page_num} - {str(i)}:', vacancy_data)
        return result_list


def get_hh(url_start, page_num=None):
    data_all_pages = {}
    page_html = request_page(url_start)
    i = 0
    while True:
        vac_on_page = DataFromPage(page_html)
        data_from_page = vac_on_page.start_parsing(i+1)
        data_all_pages[i] = data_from_page
        print(f'Page: {i+1} {vac_on_page.num_vacancies_on_page}')
        i += 1
        if page_num == i:
            break
        if vac_on_page.page_next_href:
            page_html = request_page(vac_on_page.page_next_href)
        else:
            break
        time.sleep(2)
    return data_all_pages


START_URL = 'https://hh.ru/search/vacancy?area=1&fromSearchLine=true&text=Python'

print(get_hh(START_URL, 2))
