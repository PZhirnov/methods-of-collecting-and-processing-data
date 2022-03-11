# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


# Item по постам
class InstaparserItem(scrapy.Item):
    # define the fields for your item here like:
    user_id = scrapy.Field()
    photo = scrapy.Field()
    likes = scrapy.Field()
    post_data = scrapy.Field()


# Item по подписчикам / подпискам
class InstaUserItem(scrapy.Item):
    current_user = scrapy.Field()
    current_user_name = scrapy.Field()
    user_group = scrapy.Field()
    user_id = scrapy.Field()
    user_name = scrapy.Field()
    user_full_name = scrapy.Field()
    profile_pic_url = scrapy.Field()
    image_paths = scrapy.Field()
