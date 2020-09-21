# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import re

from pymongo import MongoClient
from pymongo.collection import Collection

digits = re.compile("\\D")


class JobparserPipeline:
    def __init__(self):
        client = MongoClient('localhost', 27017)
        self.mongo_base = client.lesson6

    def process_item(self, item, spider):
        salary = item['salary']
        item["salary"] = None

        if len(salary)>2 and salary[2] == '—':
            item['min_salary'] = int(digits.sub("", salary[0]))
            item['max_salary'] = int(digits.sub("", salary[4]))
            item['curency'] = salary[-3].strip()
        else:
            if salary[0].strip() == "от" and salary[1] != "\xa0":
                item['min_salary'] = int(digits.sub("",salary[1]))
                item['curency'] = salary[-2].strip()
                item['salary'] = salary[-1].strip()
                salary = salary[2:]
            elif salary[0].strip() == "от":
                salary_split = salary[2].split("\xa0")
                item["curency"] = salary_split[-1]
                salary_split = salary_split[:-1]
                item["min_salary"] = int(''.join(salary_split))
            if salary[0].strip() == "до" and salary[1] != "\xa0":
                item['max_salary'] = int(digits.sub("",salary[1]))
                item['curency'] = salary[-2].strip()
                item['salary'] = salary[-1].strip()
            elif salary[0].strip() == "до":
                salary_split = salary[2].split("\xa0")
                item["curency"] = salary_split[-1]
                salary_split = salary_split[:-1]
                item["max_salary"] = int(''.join(salary_split))

        collection = self.mongo_base[spider.name]  # type: Collection
        collection.update_one({"url": item["url"]}, [{"$replaceWith": item}], upsert=True)

        return item
