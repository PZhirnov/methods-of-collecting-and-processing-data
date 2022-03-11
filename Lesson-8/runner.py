from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from instaparser import settings
from instaparser.spiders.instagram import InstagramSpider
from pymongo import MongoClient

if __name__ == "__main__":

    crawler_settings = Settings()
    crawler_settings.setmodule(settings)

    mongo_host = settings.MONGO_HOST
    mongo_port = settings.MONGO_PORT
    mongo_db = settings.MONGO_DB
    collection_users_for_parse = settings.MONGO_COLLECTION_USERS
    collection_users = settings.MONGO_COLLECTION

# -------- Решение по п.4-5

    def bd_mongo(collections, query_find=None, query_insert=None):
        """
        Функция выполняем запрос в БД на получение данных и добавление новых
        :param collections: наименование коллекции, которая используется в процессе диалога
        :param query_find: содержание запроса на поиск данных
        :param query_insert: содержание запроса на добавление данных
        :return: возвращает имена пользователей при старте, по которым ранее проводился парсинг подписчиков / подписок
        """
        with MongoClient(mongo_host, mongo_port) as client:
            db = client[mongo_db]
            collection = db[collections]
            # Выведем всех пользователей, которые обработаны в базе данных
            if query_find == 'all':
                return [d['current_user_name'] for d in collection.find()]
            elif query_find:
                query_result = collection.find(query_find)
                # выведем данные
                for user in query_result:
                    print(f'id: {user["user_id"]} group: {user["user_group"]} '
                          f'name: {user["user_name"]} fullname: {user["user_full_name"]}')
            if query_insert:
                collection.update_one(query_insert, {"$set": query_insert}, upsert=True)

    # Получим имена пользователей, которые ранее обрабатывались
    # Если нет, то сразу переходим к диалога по парсингу
    users_ready = bd_mongo(collection_users_for_parse, query_find='all')
    if users_ready:
        print('В базе данных имеется информация по пользователям:')
        users_for_parse = []
        for num, i in enumerate(users_ready, start=1):
            current_user_name = i
            users_for_parse.append(current_user_name)
            print(f"\t{num}. {current_user_name}")
        print('-'*35)
        while True:
            answ = input('Введите условный номер или имя пользователя для выполнения запроса, или q для продолжения:')
            if answ == 'q':
                break
            data_user_show = None
            if answ.isdigit():
                if len(users_for_parse) >= int(answ) > 0:
                    data_user_show = users_for_parse[int(answ)-1]
                else:
                    print(f'Вы должны ввести значение от 1 до {len(users_for_parse)}!')
            elif answ in users_for_parse:
                data_user_show = answ
            else:
                print('Введено значение, отсуствующее в базе данных.')
            if data_user_show:
                print(f'Данные в БД по пользователю {data_user_show}:')
                bd_mongo(collection_users, query_find={"current_user_name": data_user_show,
                                                       "user_group": "followers"})
                bd_mongo(collection_users, query_find={"current_user_name": data_user_show,
                                                       "user_group": "following"})
                print('-'*150)

    else:
        print('В базе данных отсуствуют данные по пользователям.')

# -------- Решение по п.1-3

    # В парсинг передедим список с именами интересующих нас пользователей - т.е. список.
    # Пример: users_to_parse = ['python_for_begginer', 'machine.learning.memes']
    print('-' * 150)
    print('Тестовый пример для ввода:\npython_for_begginer machine.learning.memes')
    users_to_parse = input('Введите имена пользователей через пробел, по которым нужно собрать данные:').split(' ')
    users_to_parse = list(map(lambda x: x.strip(), users_to_parse))
    # Перед отправкой сохраняем именя пользователей в отдельной таблице, по которым собираем данные.
    for user in users_to_parse:
        bd_mongo(collection_users_for_parse, query_insert={"current_user_name": user})

    # Запускаем паука
    process = CrawlerProcess(settings=crawler_settings)
    process.crawl(InstagramSpider, users_to_parse=users_to_parse)
    process.start()

"""
1. Пример стартового диалога (решение по п.4-5):

    В базе данных имеется информация по пользователям:
        1. machine.learning.memes
        2. python_for_begginer
    -----------------------------------
    Введите условный номер или имя пользователя для выполнения запроса, или q для продолжения:2
    Данные в БД по пользователю python_for_begginer:
    id: 51535019799 group: followers name: khushdil.mirov fullname: Khushdil Mirov
    id: 8699215656 group: followers name: deepvdk fullname: Николай
    id: 31121908408 group: followers name: lev.shtykov fullname: Лев Штыков
    ....
    id: 3222792076 group: following name: programminghub_app_official fullname: Programming Hub™ | Coding👨‍💻
    id: 18554294555 group: following name: codehub.py fullname: python
    id: 48004788903 group: following name: thatcodingvibe fullname: WEB DEVELOPMENT | PROGRAMMING
    id: 35187596062 group: following name: pythonpro_ fullname: Code💻 | Learn🚀 | Grow💯


2. Пример запуска паука на сбор информации (решени по п.1-3):
    Введите условный номер или имя пользователя для выполнения запроса, или q для продолжения:q
    ------------------------------------------------------------------------------------------------------------------------------------------------------
    Тестовый пример для ввода:
    python_for_begginer machine.learning.memes
    Введите имена пользователей через пробел, по которым нужно собрать данные:python_for_begginer machine.learning.memes

    ... 
    Далее работает Scrapy!
"""
