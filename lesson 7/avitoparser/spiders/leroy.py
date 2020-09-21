import scrapy
from scrapy.http import HtmlResponse
from avitoparser.items import LeroyParserItem
from scrapy.loader import ItemLoader
import urllib.parse


class LeroySpider(scrapy.Spider):
    name = 'leroy'
    allowed_domains = ['leroymerlin.ru']

    def __init__(self, search, **kwargs):
        super().__init__(**kwargs)
        self.start_urls = [f'https://leroymerlin.ru/search/?q={urllib.parse.quote(search)}']

    def parse(self, response: HtmlResponse, **kwargs):
        ads_links = response.css(".plp-item__info__title")
        for link in ads_links:
            yield response.follow(link, callback=self.parse_products)

    def parse_products(self, response: HtmlResponse, **kwargs):
        loader = ItemLoader(item=LeroyParserItem(),response=response)
        loader.add_value('url', response.url)
        loader.add_xpath('name', "//h1/text()")
        loader.add_css('price', 'uc-pdp-price-view [itemprop=price]::attr(content)')
        loader.add_css('currency', 'uc-pdp-price-view [itemprop=priceCurrency]::attr(content)')
        loader.add_css('availability', 'uc-pdp-price-view [itemprop=availability]::attr(content)')
        loader.add_css('unit', 'uc-pdp-price-view [slot=unit]::text')
        loader.add_css('characteristics', '#nav-characteristics .def-list__group')
        loader.add_xpath('photo', "//uc-pdp-media-carousel//picture//img/@src")
        yield loader.load_item()
