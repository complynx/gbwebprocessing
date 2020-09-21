# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader.processors import MapCompose, TakeFirst, Compose
from parsel.selector import SelectorList
from lxml import html
import logging
log = logging.getLogger(__name__)


def price_to_int(price):
    if price:
        return float(price)  # Better to use Decimal, but whatever
    return price


def leroy_characteristic_dict(char_str: SelectorList):
    try:
        char = html.fromstring(char_str)
        if char is not None:
            val_str = char.find_class("def-list__definition")[0].text.strip()
            try:
                val = float(val_str)
            except ValueError:
                val = val_str
            return {
                'property': char.find_class("def-list__term")[0].text,
                'value': val
            }
    except Exception as e:
        log.error(e)
    return None


class AvitoparserItem(scrapy.Item):
    # define the fields for your item here like:
    name = scrapy.Field(output_processor=TakeFirst())
    price = scrapy.Field(input_processor=MapCompose(price_to_int), output_processor=TakeFirst())
    photo = scrapy.Field()
    _id = scrapy.Field()


class LeroyParserItem(scrapy.Item):
    # define the fields for your item here like:
    name = scrapy.Field(output_processor=TakeFirst())
    price = scrapy.Field(input_processor=MapCompose(price_to_int), output_processor=TakeFirst())
    currency = scrapy.Field(output_processor=TakeFirst())
    availability = scrapy.Field(output_processor=TakeFirst())
    unit = scrapy.Field(output_processor=TakeFirst())
    characteristics = scrapy.Field(input_processor=MapCompose(leroy_characteristic_dict))
    photo = scrapy.Field()
    url = scrapy.Field(output_processor=TakeFirst())
    _id = scrapy.Field()


