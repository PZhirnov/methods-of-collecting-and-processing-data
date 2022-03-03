# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import hashlib

import scrapy
import pymongo
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from scrapy.pipelines.images import ImagesPipeline


class LeroyImagesPipeline(ImagesPipeline):

    def file_path(self, request, response=None, info=None, *, item=None, article_num=None):
        # для каждого продукта создается папка с номером артикула и туда сохраняются фотографии
        image_name = request.url.split('/')[-1]
        folder_name = image_name.split('.')[0].split('_')[0]
        return f'full/{folder_name}/{image_name}'

    def get_media_requests(self, item, info):
        if item["img_urls"]:
            for img_url in item["img_urls"]:
                try:
                    yield scrapy.Request(img_url)
                except Exception as e:
                    print(e)

    def item_completed(self, results, item, info):
        image_paths = [x['path'] for ok, x in results if ok]
        if not image_paths:
            raise DropItem("Item contains no images")
        adapter = ItemAdapter(item)
        adapter['image_paths'] = image_paths
        return item


class LeroyParserPipeline:

    def __init__(self, mongo_host, mongo_port, mongo_collection, mongo_db):
        self.mongo_host = mongo_host
        self.mongo_db = mongo_db
        self.mongo_port = mongo_port
        self.mongo_collection = mongo_collection

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_host=crawler.settings.get('MONGO_HOST'),
            mongo_port=crawler.settings.get('MONGO_PORT'),
            mongo_db=crawler.settings.get('MONGO_DB'),
            mongo_collection=crawler.settings.get('MONGO_COLLECTION'),
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_host, self.mongo_port)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        print("PROCESS_ITEM")
        print(item)
        # TODO: write code for MongoDB
        item_dict = ItemAdapter(item).asdict()
        # self.db[self.mongo_collection].insert_one(item_dict)
        self.db[self.mongo_collection].update_one(
            {"article_number": item_dict["article_number"]},
            {"$set": item_dict},
            upsert=True
        )
        return item
