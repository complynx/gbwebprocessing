import scrapy
from scrapy.http import HtmlResponse
from jobparser.items import JobparserItem


class SJruSpider(scrapy.Spider):
    name = 'superjob.ru'
    allowed_domains = ['superjob.ru']
    start_urls = ['https://www.superjob.ru/vacancy/search/?keywords=python&geo%5Bt%5D%5B0%5D=4']

    def parse(self, response: HtmlResponse, **kwargs):
        vacancies = response.css(".f-test-vacancy-item a[href^='/vakansii']::attr(href)").extract()
        for vacancy in vacancies:
            yield response.follow(vacancy, callback=self.vacancy_parse)

        next_page = response.css(".f-test-link-Dalshe::attr(href)").extract_first()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def vacancy_parse(self, response: HtmlResponse):
        name = response.css(".f-test-vacancy-base-info h1::text").extract_first()
        salary = response.css(".f-test-vacancy-base-info h1").xpath("../span").css("*::text").extract()

        yield JobparserItem(
            name=name,
            salary=salary,
            url=response.url,
            site=self.name)
