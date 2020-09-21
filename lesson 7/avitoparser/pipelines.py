# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from builtins import super
import os
import urllib.parse
import scrapy
from pymongo import MongoClient
from scrapy.pipelines.images import ImagesPipeline


class AvitoparserPipeline:
    def __init__(self):
        client = MongoClient('localhost', 27017)
        self.mongo_base = client.avito_photo_kittens

    def process_item(self, item, spider):
        collection = self.mongo_base[spider.name]
        collection.update_one({"url": item["url"]}, [{"$replaceWith": item}], upsert=True)
        return item


class AvitoPhotosPipeline(ImagesPipeline):
    current = dict()

    def get_media_requests(self, item, info):
        if item['photo']:
            for img in item['photo']:
                try:
                    self.current[img] = item
                    yield scrapy.Request(img)
                except Exception as e:
                    import traceback
                    traceback.print_exc(e)

    def file_path(self, request, response=None, info=None):
        path = super(AvitoPhotosPipeline, self).file_path(request, response, info)
        item = self.current[request.url]
        item_url = item['url']
        url_path = urllib.parse.urlsplit(item_url).path
        url_file_name = os.path.basename(url_path[:-1] if url_path.endswith("/") else url_path)
        dir_name, file_name = os.path.split(path)
        return os.path.join(dir_name, url_file_name, file_name)

    def item_completed(self, results, item, info):
        if results:
            for img in results:
                img_url = img[1]['url']
                if img[0] and self.current[img_url] == item:
                    del self.current[img_url]
            item['photo'] = [itm[1] for itm in results if itm[0]]
        return item
