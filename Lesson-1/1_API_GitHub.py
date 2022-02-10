"""
Задание №1

Посмотреть документацию к API GitHub, разобраться как вывести список репозиториев для конкретного пользователя,
сохранить JSON-вывод в файле *.json; написать функцию, возвращающую(return) список репозиториев.
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv('./.env')


class GitUser:
    info_user_json = None
    repo_list_json = None
    repos_on_all_pages = []

    def __init__(self, user_name, token=None):
        self.username = user_name
        self.token = token

    def request_data(self, url, param=None):
        """Возвращает результат запроса по сформированному url"""

        if self.token:
            info_request = requests.get(url[0], auth=(self.username, self.token), params=param)
        else:
            info_request = requests.get(url[1], params=param)
        if info_request.status_code == 200:
            result_json = info_request.json()
        else:
            result_json = None
        return result_json

    def info_user(self):
        """Возвращает информацию о пользователе"""

        return self.request_data(['https://api.github.com/user',
                                  f'https://api.github.com/users/{self.username}'])

    def repos_list(self):
        """Возвращает перечень репозиториев"""
        # Реализована возможность пагинации, чтобы забрать все репозитории
        page = 1
        self.repos_on_all_pages = []
        while True:
            repos_on_page = self.request_data(['https://api.github.com/user/repos',
                                               f'https://api.github.com/users/{self.username}/repos'],
                                              {'page': page, 'per_page': 50})
            page += 1
            # если вернулось 0 записей на странице, то можно завершать сбор данных
            if len(repos_on_page) == 0:
                break
            self.repos_on_all_pages.extend(repos_on_page)
        return self.repos_on_all_pages

    def save_json(self, file_name=None, type_data='info'):
        """Сохраняет результаты в файл"""
        if file_name is None:
            return None
        if type_data == 'repos':
            all_repos = self.repos_list() if not len(self.repos_on_all_pages) else self.repos_on_all_pages
            if all_repos is None:
                return 'Запрос завершен с ошибкой'
            result = {}
            # В файл сохраняем только те поля, которые были по условию
            for repo in all_repos:
                result[repo['name']] = repo['html_url']
        else:
            result = self.info_user()
            if result is None:
                return 'Запрос завершен с ошибкой'
        try:
            with open(file_name, 'w', encoding='utf8') as f:
                json.dump(result, f, indent=2)
        except FileNotFoundError:
            return 'Файл не был записан'
        else:
            return f'Файл {file_name} создан успешно!'


# Функция для вызова
def user_repos(user_name):
    user_git_object = GitUser(user_name)
    return user_git_object.save_json(f'{user_name}_repos.json', 'repos')

# Проверка работы функции


while True:
    input_user_git = input('Введите имя пользователя или q для выхода:')
    if input_user_git == 'q':
        break
    print(user_repos(input_user_git))


# Примеры расширенного использования:

# ----- Проверка работоспособности -------:

# Получим пользователя и токен из
# username = os.getenv('USER_GIT', None)
# git_token = os.getenv('TOKEN_GIT', None)

# Если нужно получить данные по пользователю, для которого известен токен - публичные и приватные
# f = GitUser(username, git_token)
# print(f.save_json(f'{username} with token_repos.json', 'repos'))
# print(f.save_json(f'{username} with token_info.json', 'info'))

# Если нужно получить данные по пользователю без токена - только публичные репозитории
# f = GitUser(username)
# print(f.save_json(f'{username} no token_repos.json', 'repos'))
# print(f.save_json(f'{username} no token_info.json', 'info'))

# Пример получения репозиториев Microsoft - 608 ссылок - см. результат выгрузки в отд.
# f = GitUser('MicrosoftLearning')
# print(f.save_json(r'MicrosoftLearning_repos.json', 'repos'))
# print(f.save_json(r'MicrosoftLearning_info.json', 'info'))
