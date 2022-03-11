import json
import re
from copy import deepcopy
from pprint import pprint
from urllib.parse import quote

import scrapy
from scrapy.http import HtmlResponse

from instaparser.items import InstaparserItem, InstaUserItem


# https://www.instagram.com/graphql/query/
# ?query_hash=8c2a529969ee035a5063f2fc8602a0fd
# &variables=%7B%22id%22%3A%2227790688603%22%2C%22first%22%3A12%2C%22after%22%3A%22QVFBUS1lVHhvSHBZenR2S3c1ZGFzV2tPazVPTTY1Y0JLekdnSHdKbkZUN3FzbzRMMkZKMi1lRnlEczdFRFJYSXUwWk1fMWNRdHc4Mll1M1pQT0FZQXFkOA%3D%3D%22%7D


class InstagramSpider(scrapy.Spider):
    name = "instagram"
    max_page_number = 3
    allowed_domains = ["instagram.com"]
    start_urls = ["https://www.instagram.com/"]
    login_url = "https://www.instagram.com/accounts/login/ajax/"
    username = "zhirnov.pzhirnov"
    enc_pass = (
        "#PWD_INSTAGRAM_BROWSER:10:1646990056:"
        "Aa1QAHkmmnrHbkh46aQJrHvJzHs9c9PSc4LBHz"
        "fwCHlLyG5rykWhkiil7soPv+Og0CNpPpPX99op8Z"
        "udtgVzOqGZvQUFHqhmYHU8nb/A4ioC0qFOUhLaJ/fmx0rwtuYvfMttOrwoBi1iAeDi+g=="
    )
    user_to_parse_url_template = "/%s"
    # user_to_parse = "machinelearning"
    # posts_hash = "32b14723a678bd4628d70c1f877b94c9"
    # graphql_url = "https://www.instagram.com/graphql/query/?"

    def __init__(self, users_to_parse):
        super(InstagramSpider, self).__init__()
        self.users_to_parse = users_to_parse

# --- 1
    def parse(self, response: HtmlResponse, **kwargs):
        if response.status != 200:
            print(f"Запрос вернул статус = {response.status}")
            return

        print()
        csrf_token = self.fetch_csrf_token(response.text)
        instagram_ajax = self.fetch_instagram_ajax(response.text)
        cookie_string = response.headers["Set-Cookie"].decode()
        cookie_dict = dict(
            map(lambda x: x.strip().split("="), cookie_string.split(";")[:-1])
        )
        headers = {
            "x-instagram-ajax": instagram_ajax,
            "x-ig-app-id": "936619743392459",
            "x-ig-www-claim": "hmac.AR1TmS_I7mxuJ9XyC_Ay6M5-oVmyK-6gm1JiTE8V-XjMLEg1",
            "x-csrftoken": csrf_token,
        }
        form_data = {"username": self.username, "enc_password": self.enc_pass}
        yield scrapy.FormRequest(
            self.login_url,
            method="POST",
            callback=self.user_login,
            formdata=form_data,
            headers=headers,
            cookies=cookie_dict,
        )

    # Получаем токен для авторизации
    def fetch_csrf_token(self, text: str):
        matched = re.search('"csrf_token":"\\w+"', text).group()
        return matched.split(":").pop().replace(r'"', "")

    # Получаем instagram ajax заголовок
    def fetch_instagram_ajax(self, text: str):
        matched = re.search('"rollout_hash":"\\S+"', text).group()
        matched = matched.split(',')[0]
        return matched.split(":").pop().replace(r'"', "")

# -- 2. Логинимся
    def user_login(self, response: HtmlResponse):
        if response.status != 200:
            print(f"Запрос вернул статус = {response.status}")
            return

        data = response.json()
        print()
        if data["status"] != "ok":
            print("Произошла ошибка при логине")
            pprint(data)
            return

        if data["authenticated"]:

            for current_user in self.users_to_parse:
                #current_user = self.users_to_parse
                yield response.follow(
                    self.user_to_parse_url_template % current_user,
                    # callback=self.user_data_parse,
                    callback=self.current_user_page,
                    cb_kwargs={
                        "username": current_user,
                        "next_max_id": 0,  # при первом запуске передадим 0
                        "user_group": "all",  # при первом запуске отправляем обе задачи
                    },
                )

# -- Базовая реализация
    def make_str_variables(self, variables: dict):
        str_variables = str(variables).replace(" ", "").replace("'", '"')
        return quote(str_variables)

    def fetch_user_id(self, text: str, username: str):
        print()
        regexp = '{"id":"\\d+","username":"%s"}' % username
        # regexp = '"userId":"\\d+"' # если не работает первый, то попробовать это
        matched = re.search(regexp, text).group()
        return json.loads(matched).get("id")
        # return matched.replace('"', '').split(':')[1]

# ****
    def current_user_page(self, response: HtmlResponse, username: str, next_max_id=None, user_group=None):
        print()
        # id пользователя с которым работаем
        user_id = self.fetch_user_id(response.text, username)

        # -- Общие параметры для подписчиков / подписок
        csrf_token = self.fetch_csrf_token(response.text)
        cookie_string = response.headers["Set-Cookie"].decode()
        cookie_dict = dict(
            map(lambda x: x.strip().split("="), cookie_string.split(";")[:-1])
        )
        headers = {
            "x-ig-app-id": "936619743392459",
            "x-ig-www-claim": "hmac.AR1TmS_I7mxuJ9XyC_Ay6M5-oVmyK-6gm1JiTE8V-XjMLEg1",
            "x-csrftoken": csrf_token,
        }

        # --- Url Подписки и отправка запроса
        # https://i.instagram.com/api/v1/friendships/501615099/following/?count=12
        # https://i.instagram.com/api/v1/friendships/501615099/following/?count=12&max_id=60
        if (next_max_id or next_max_id == 0) and (user_group == 'all' or user_group == 'following'):
            subsc_url = (
                f"https://i.instagram.com/api/v1/friendships/{user_id}/following/?count=12"
            )
            if next_max_id and next_max_id != 0:
                subsc_url += f"&max_id={next_max_id}"

            print()

            # --- Подписки
            yield response.follow(
                subsc_url,
                callback=self.parse_response,
                cb_kwargs={
                    "username": username,
                    "user_id": user_id,
                    "subsc_url": subsc_url,
                    "user_group": "following",
                },
                cookies=cookie_dict,
                headers=headers,
            )

        # --- Url Подписчики (followers)
        # https://i.instagram.com/api/v1/friendships/501615099/followers/?count=12&search_surface=follow_list_page
        # https://i.instagram.com/api/v1/friendships/501615099/followers/?count=12&max_id=36&search_surface=follow_list_page
        if (next_max_id or next_max_id == 0) and (user_group == 'all' or user_group == 'followers'):
            followers_url = (
                f"https://i.instagram.com/api/v1/friendships/{user_id}/followers/?count=12&search_surface=follow_list_page"
            )
            if next_max_id and next_max_id != 0:
                followers_url = followers_url.replace('&search_surface', f"&max_id={next_max_id}&search_surface")

            yield response.follow(
                    followers_url,
                    callback=self.parse_response,
                    cb_kwargs={
                        "username": username,
                        "user_id": user_id,
                        "subsc_url": followers_url,
                        "user_group": "followers",
                    },
                    cookies=cookie_dict,
                    headers=headers,
                )

    # Парсинг подписчиков и подписок сделан в одной функции
    def parse_response(
            self,
            response: HtmlResponse,
            username: str,
            user_id: str,
            subsc_url: str,
            user_group: str=None,
    ):
        print()
        # csrf_token = self.fetch_csrf_token(response.text)
        data = response.json()
        next_max_id = data.get('next_max_id')
        users = data['users']
        for user in users:
            item = InstaUserItem()
            item['current_user'] = int(user_id)
            item['current_user_name'] = username
            item['user_group'] = user_group
            item['user_id'] = user['pk']
            item['user_name'] = user['username']
            item['user_full_name'] = user['full_name']
            item['profile_pic_url'] = user['profile_pic_url']
            yield item
        if next_max_id:
            yield response.follow(
                self.user_to_parse_url_template % username,
                callback=self.current_user_page,
                cb_kwargs={
                    "username": username,
                    "next_max_id": next_max_id,  # при первом запуске передадим 0
                    "user_group": user_group,
                },
                dont_filter=True,
            )

# ****




