# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import re
from pprint import pprint
import unicodedata

# useful for handling different item types with a single interface
# from itemadapter import ItemAdapter
from pymongo import MongoClient

MONGO_PORT = 27017
MONGO_HOST = "localhost"


class JobParserPipeline:
    def __init__(self):
        # TODO: где закрывается соединение?
        self.client = MongoClient(MONGO_HOST, MONGO_PORT)

    def salary_range_and_currency(self, text):
        clear_text = text.replace(' ', '').replace('\u202f', '')
        result_re = list(map(int, re.findall(r'\d+', clear_text)))
        if len(result_re) == 0:
            result_re = [None, None]
        text_split = list(map(lambda x: x.lower(), text.split(' ')))
        if 'от' in text_split and len(result_re) == 1:
            result_re = [result_re[0], None]
        if 'до' in text_split and len(result_re) == 1:
            result_re = [None, result_re[0]]
        result_re.append(None)
        for i in ['руб.', 'usd', 'eur']:
            if i in text_split:
                result_re[2] = i
                break
        return result_re

    def convert_string_list_to_string(self, string_list):
        return unicodedata.normalize("NFKD", "".join(string_list))

    def process_item(self, item, spider):
        # print("PIPELINE")
        for field in ["salary", "title", "source_name"]:
            item[field] = self.convert_string_list_to_string(item[field])
        # как удалять ненужные поля
        # del item["field_name"]
        # item.pop("field_name")

        # PREPROCESSING ITEM FOR ... (WRITING TO MONGO etc)

        # pprint(item)

        # self-handling _id
        item["_id"] = re.findall(r'(\d+\d)', item["url"])[0]
        item["salary_min"], item["salary_max"], item["salary_currency"] = self.salary_range_and_currency(item["salary"])
        pprint(item)
        # если abc существует в классе Item-а, то все хорошо
        # item['abc'] = 42
        # print()
        db = self.client["vacancies"]
        collection = db[spider.name]
        # UPSERT
        collection.update_one(
            {"_id": item["_id"]},
            {"$set": item},
            upsert=True,
        )
        with MongoClient(MONGO_HOST, MONGO_PORT) as client:
            db = client['vacancies']
            collection = db[spider.name]
            # collection.insert_one(item)
            # UPSERT
            collection.update_one(
                {"_id": item['_id']},
                {"$set": item},
                upsert=True,
            )
        return item
