from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import argparse
import urllib.parse
import sys
import time
import json

if __name__ == "__main__":
    # screw it, too many arguments, time for argparse
    parser = argparse.ArgumentParser(description='Get top sales')
    parser.add_argument('-d', '--webdriver', help="selenium driver", default=".")
    parser.add_argument('-B', '--break-from-loops', help="break from long loops for debug", default=".", dest='break_loops', action='store_true')
    parser.add_argument('-D', '--save_to_db', help="save to database instead of dumping JSON")
    parser.add_argument('-c', '--collection', help="Mongo collection (used with -D)", default="mail")
    parser.add_argument('-M', '--mongo_address', help="Mongo address (used with -D)", default="mongodb://localhost:27017/")
    parser.add_argument("-o", '--output', help="output file, if not present, outputs to stdout (unused if -D is present)")
    args = parser.parse_args()

    driver = webdriver.Firefox(args.webdriver)
    driver.set_window_position(0,0)
    driver.set_window_size(1240, 800)

    driver.get("https://www.mvideo.ru/")
    WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".sel-hits-block")))
    carousels = driver.find_elements_by_css_selector(".section")
    tops = None
    for carousel in carousels:
        try:
            title = carousel.find_element_by_css_selector(".gallery-title-wrapper").get_attribute("innerText")
            if title == "Хиты продаж":
                tops = carousel
                break
        except NoSuchElementException:
            pass
    got_items = {}
    cur_url = driver.current_url

    while True:
        items = tops.find_elements_by_css_selector(".accessories-product-list li")
        for item in items:
            title = item.find_element_by_css_selector("a.sel-product-tile-title")
            url = title.get_attribute("href")

            if url not in got_items:
                got_items[url] = {
                    "url": urllib.parse.urljoin(cur_url, url),
                    "title": title.get_attribute("innerText")
                    # I could get other info, you know it, but it's unnecessary for the task
                }

        driver.execute_script("arguments[0].scrollIntoView(true);", tops)
        ActionChains(driver).move_to_element(items[0])
        try:
            next = tops.find_element_by_css_selector(".sel-hits-button-next:not(.disabled)")
            next.click()
        except NoSuchElementException:
            break

        if args.break_loops:
            break

        # TODO: copy and paste proper observer from the first HW
        time.sleep(1)

    if args.save_to_db is not None:
        from pymongo import MongoClient

        client = MongoClient(args.mongo_address)
        db = client[args.save_to_db]
        collection = db[args.collection]

        collection.insert_many(got_items.values())
    else:
        import json
        out_file = sys.stdout
        if args.output is not None:
            out_file = open(args.output, "w+")

        json.dump(got_items, out_file, indent=4)
