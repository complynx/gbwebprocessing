import json
import urllib.request
import urllib.parse
import sys
from lxml import html,etree
import re
import time

parser = etree.HTMLParser(encoding="utf-8")
ya_date_re = re.compile("//")


def ya_date_parser(raw_date):
    try:
        import dateparser
        return dateparser.parse(raw_date).isoformat()
    except:
        return raw_date


sites = {
    "news.mail.ru": {
        "URL": 'https://news.mail.ru/',
        "elements": "//*[@class='daynews__inner']//td/div/a | //*[@class='daynews__inner']/../../ul//a",
        "link": "./@href",
        "title": ".//text()",
        "date": "$follow$//div[@class='article js-article js-module']//span[@class='note']//@datetime | //div[@class='article js-article']//span[@class='note']//@datetime",
        "source": "$follow$//div[@class='article js-article js-module']//span[@class='note']//*[@class='link__text']/text()|//div[@class='article js-article']//span[@class='note']//*[@class='link__text']/text()",
        "source_url": "$follow$//div[@class='article js-article js-module']//span[@class='note']//*[@class='link__text']/../@href | //div[@class='article js-article']//span[@class='note']//*[@class='link__text']/../@href"
    },
    "lenta.ru": {
        "URL": 'https://lenta.ru/',
        "elements": "//section//section//h2/a/../../../../div/div/a[@href!='/parts/news/']",
        "link": "./@href",
        "title": "../h2/a/text()|./text()",
        "date": "../h2/a/time/@datetime|./time/@datetime",
        "source": "$static$lenta.ru",
        "source_url": "$static$lenta.ru",
        "parse_date": ya_date_parser
    },
    "Яндекс-Новости": {
        "URL": 'https://yandex.ru/news/?utm_source=main_stripe_big',
        "elements": "//a[@class='news-card__link']/../../../article | //a[@class='news-card__link']/../../article | //a[@class='news-card__link']/../../../../article",
        "link": ".//a[@class='news-card__link']/@href",
        "title": ".//a[@class='news-card__link']/h2/text()",
        "date": ".//*[@class='mg-card-source__time']/text()",
        "source": ".//*[@class='mg-card-source__source']//a/text()",
        "parse_date": ya_date_parser
    }
}


class NewsPiece(object):
    def __init__(self, site, url, xpath):
        self.site = site
        self.xpath = xpath
        self.follow = None
        self.dict = {
            "URL": url
        }

    def fetch_from_root(self, xpath):
        ret = self.xpath.xpath(xpath)
        return ret[0] if len(ret) > 0 else None

    def fetch_from_follow(self, xpath):
        time.sleep(.4)
        if self.follow is None:
            req = urllib.request.Request(self.dict["URL"], headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Upgrade-Insecure-Requests": "1",
                "Cache-Control": "max-age=0"
            })
            with urllib.request.urlopen(req) as res:
                self.follow = html.parse(res, parser=parser)
        ret = self.follow.xpath(xpath)
        return ret[0] if len(ret) > 0 else None

    def fetch_from_static(self, text):
        return text

    def parse(self, fetched, data_name):
        data_parser = self.site["parse_"+data_name]
        return data_parser(fetched)

    def fetch_data_one(self, data_name):
        if data_name not in self.site:
            return None
        data_path = self.site[data_name]
        if data_path.startswith("$"):
            data_path_split = data_path.split("$", 2)
            data_source = data_path_split[1]
            data_path = data_path_split[2]
        else:
            data_source = "root"
        fetched = getattr(self, "fetch_from_" + data_source)(data_path)
        if "parse_" + data_name in self.site:
            fetched = self.parse(fetched, data_name)
        return fetched

    def fetch_data(self):
        for item_name in ["title", "date", "source", "source_url"]:
            self.dict[item_name] = self.fetch_data_one(item_name)

    def to_dict(self):
        return self.dict


def fetch_news_piece(site, url, news_piece_xpath):
    news_piece = NewsPiece(site, url, news_piece_xpath)
    news_piece.fetch_data()
    return news_piece.to_dict()


def get_news(site):
    req = urllib.request.Request(site["URL"], headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0"
    })
    recent_news_parsed = dict()
    with urllib.request.urlopen(req) as res:
        doc = html.parse(res, parser=parser)
        recent_news = doc.xpath(site["elements"])
        for news_piece in recent_news:
            rel_url = news_piece.xpath(site["link"])[0]
            url = urllib.parse.urljoin(site["URL"], rel_url)

            if url not in recent_news_parsed:
                news_piece_dict = fetch_news_piece(site, url, news_piece)
                recent_news_parsed[url] = news_piece_dict

    return list(recent_news_parsed.values())


if __name__ == "__main__":
    if len(sys.argv) < 1:
        print(f"Usage: {sys.argv[0]} [output.json]")
        exit(1)

    file = sys.stdout
    if len(sys.argv) > 1:
        file = open(sys.argv[1], "w+")

    news = []
    for site_name, site_settings in sites.items():
        news_part = get_news(site_settings)
        print(f"got {len(news_part)} news of site {site_name}")
        news += news_part

    json.dump(news, file, indent=4, ensure_ascii=False)
