import requests
import json
import os
from pprint import pprint
from dotenv import load_dotenv
from datetime import datetime

load_dotenv('./.env')
ow_token = os.getenv('TOKEN_OW', None)


def geocoding(city_name):
    """
    Функция выполняет геокодирование местоположение по наименованию
    :param city_name:
    :return: список объектов с соотвествующим наименованием местоположения
    http://api.openweathermap.org/geo/1.0/direct?q={city name},
    {state code},{country code}&limit={limit}&appid={API key}
    """
    url_api = 'http://api.openweathermap.org/geo/1.0/direct'
    geo_api_request = requests.get(url_api, params={'q': city_name, 'limit': 5, 'appid': ow_token})
    # Сделаем словарик из результатов запроса - Наименование города и координаты
    objects_geo_api = [{'num': num + 1,
                        'name': i['name'],
                        'lat': i['lat'],
                        'lon': i['lon'],
                        'country': i['country'],
                        'state': i['state']} for num, i in enumerate(geo_api_request.json())]
    return objects_geo_api


def weather(city):
    """
    Функция делает запрос по полученным геоданным и возвращает информацию о погоде в выбранном месте
    :param city:
    :return: json файл с данными о погоде в выбранном местоположении
    """
    objects_geo_api = geocoding(city)
    len_objects = len(objects_geo_api)
    if len_objects == 0:
        return False
    if len_objects > 1:
        print('Найдено несколько местоположений с указанным наименованием. Выберите нужный код положения.')
        print(*objects_geo_api, sep='\n')
        while True:
            num = input("Введите условный номер нужного местоположения:")
            if num.isdigit():
                if int(num) - 1 in range(len_objects):
                    break
                else:
                    print(f'Необходимо ввести значение от 1 до {len_objects}!')
            else:
                print(f'Вы должны ввести число от 1 до {len_objects}!')
        select_location = objects_geo_api[int(num) - 1]
    else:
        select_location = objects_geo_api[0]
    # Делаем запрос
    url_api = 'http://api.openweathermap.org/data/2.5/weather'
    weather_requests = requests.get(url_api, params={'lat': select_location.get('lat'),
                                                     'lon': select_location.get('lon'),
                                                     'appid': ow_token})
    result = weather_requests.json()
    return result


# Проверка результата


while True:
    city = input('Введите наименование города или q для выхода:')
    if city == 'q':
        break
    # выведем результат на экран
    result = weather(city)
    if result:
        pprint(result)
        # сохраним в файл
        with open(f'{city}-{datetime.date(datetime.now())}.json', 'w', encoding='utf8') as f:
            json.dump(result, f, indent=2)
    else:
        print(f'Указанное наименование города {city} не найдено. Повторите ввод.')
