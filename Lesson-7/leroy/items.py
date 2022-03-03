# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader.processors import Compose, MapCompose, TakeFirst
from lxml import html
import json


def clean_string(s):
    return s.strip()


def clean_strings(string_array):
    return [s.strip() for s in string_array]


def def_dict_json(def_list):
    # print(def_list)
    try:
        def_result_dict = {}
        for element in def_list:
            row = html.fromstring(element)
            def_result_dict[row[0].text.strip()] = row[1].text.strip()
        result_json = json.dumps(def_result_dict, ensure_ascii=False)
        return result_json
    except Exception as err:
        return None


def href_images(img_list):
    # Оставляем только уникальные изображения размером 800 х 800
    start_href = 'https://res.cloudinary.com/lmru/image/upload/f_auto,q_auto,' \
                 'w_800,h_800,c_pad,b_white,d_photoiscoming.png/LMCode/'
    imgs = set([i.split('/')[-1] for i in img_list])
    imgs = list(map(lambda x: start_href + x, list(imgs)))
    return imgs


def int_val(string):
    try:
        return int(string[0].strip().replace(' ', ''))
    except Exception as exc:
        return None


# Леруа
class LeroyItem(scrapy.Item):
    article_number = scrapy.Field(output_processor=TakeFirst())
    url = scrapy.Field(output_processor=TakeFirst())
    price = scrapy.Field(
        input_processor=Compose(int_val),
        output_processor=TakeFirst()
    )
    title = scrapy.Field(
        input_processor=Compose(clean_strings),
        output_processor=TakeFirst(),
    )
    img_urls = scrapy.Field(input_processor=Compose(href_images))
    def_list = scrapy.Field(input_processor=Compose(def_dict_json))
    image_paths = scrapy.Field()
