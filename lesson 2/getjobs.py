import json
import urllib.request
import urllib.parse
import sys
from bs4 import BeautifulSoup
import re
import time

sites = {
    "HeadHunter": {
        "URL": 'https://hh.ru/search/vacancy?L_save_area=true&clusters=true&enable_snippets=true&page={page_num}'
               '&search_field=name&text={job_name}&showClusters=true',
        "offset": 0,
        "elements": ".vacancy-serp-item",
        "job_title": ".resume-search-item__name",
        "link": ".resume-search-item__name a",
        "link_prefix":"",
        "salary": ".vacancy-serp-item__sidebar",
        "salary_regexp": re.compile("((?P<both>(?P<from>[1-9][0-9\s]*)-(?P<to>[1-9][0-9\s]*))|(до\s+(?P<upper>[1-9][0-9\s]*))|(от\s+(?P<lower>[1-9][0-9\s]*)))\s+(?P<currency>.*)")
    },
    "SuperJob": {
        "URL": 'https://russia.superjob.ru/vacancy/search/?keywords={job_name}&page={page_num}',
        "offset": 1,
        "elements": ".f-test-vacancy-item",
        "job_title": "a",
        "link": "a",
        "link_prefix":"https://russia.superjob.ru",
        "salary": ".f-test-text-company-item-salary",
        "salary_regexp": re.compile("((?P<both>(?P<from>[1-9][0-9\s]*)\s+—\s+(?P<to>[1-9][0-9\s]*))|(до\s+(?P<upper>[1-9][0-9\s]*))|(от\s+(?P<lower>[1-9][0-9\s]*)))\s+(?P<currency>.*)/(?P<period>.*)")
    }
}


def filter_digits(_str):
    return ''.join(i for i in _str if i in "0123456789")


def first_of(_dict, *matches, default=None):
    for match in matches:
        if match in _dict and _dict[match] is not None:
            return _dict[match]
    return default

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} job-name [output.json]")
        exit(1)

    job_name = sys.argv[1]
    job_name_quoted = urllib.parse.quote(job_name)

    file = sys.stdout
    if len(sys.argv) > 2:
        file = open(sys.argv[2], "w+")

    jobs = []
    for sitename, site in sites.items():
        page = 0
        while True:
            req = urllib.request.Request(site["URL"].format(
                job_name=job_name_quoted,
                page_num=page+site["offset"]))
            req.add_header('User_Agent', 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36'
                                         '(KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36')
            with urllib.request.urlopen(req) as res:
                soup = BeautifulSoup(res)
                elements = soup.select(site["elements"])
                if len(elements) == 0:
                    break

                for element in elements:
                    job = {
                        "site_name": sitename
                    }
                    job_title = element.select(site["job_title"])
                    job["title"] = job_title[0].text if len(job_title) >= 1 else None

                    link = element.select(site["link"])
                    job["url"] = (site["link_prefix"] + link[0]["href"]) if len(link) >= 1 else None

                    salary_el = element.select(site["salary"])
                    salary_text = salary_el[0].text if len(salary_el) >= 1 else None
                    if salary_text is None:
                        salary_text = ""
                    salary_match = site["salary_regexp"].match(salary_text)
                    if salary_match is not None:
                        groups = salary_match.groupdict()
                        lower = first_of(groups, "lower", "from")
                        upper = first_of(groups, "upper", "to")
                        if lower is not None:
                            job["salary_lower"] = int(filter_digits(lower))
                        if upper is not None:
                            job["salary_upper"] = int(filter_digits(upper))
                        job["salary_currency"] = first_of(groups, "currency")
                        job["salary_period"] = first_of(groups, "period", default="месяц")
                    jobs.append(job)

            time.sleep(1)
            page += 1
            print(f"Got {page} page(s) of {sitename}")

    json.dump(jobs, file, indent=4)