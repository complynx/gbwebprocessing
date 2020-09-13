from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
import argparse
import sys
import time


def ya_date_parser(raw_date):
    try:
        import dateparser
        return dateparser.parse(raw_date).isoformat()
    except:
        return raw_date


class JsCondition(object):
    def __init__(self, script, *args):
        self.script = script
        self.args = args

    def __call__(self, driver):
        return driver.execute_script(self.script, *self.args)


if __name__ == "__main__":
    # screw it, too many arguments, time for argparse
    parser = argparse.ArgumentParser(description='Get all mail')
    parser.add_argument('-l', '--login', help="your login")
    parser.add_argument('-p', '--password', help="your password")
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

    driver.get('https://mail.ru')

    login = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, "mailbox:login-input")))
    login.send_keys(args.login)
    login.send_keys(Keys.RETURN)
    time.sleep(0.1)

    passwd = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, "mailbox:password-input")))
    passwd.send_keys(args.password)
    passwd.send_keys(Keys.RETURN)

    WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.llc.js-letter-list-item")))
    current_url = driver.current_url
    fetched_letters = dict()
    container = driver.find_elements_by_css_selector(".letter-list .scrollable")[0]

    driver.execute_script("""
        let container = arguments[0];
        if(!window.clx) window.clx = {};
        
        clx.observer = new MutationObserver(()=>clx.observed=true);
        let target = container.querySelector(".dataset__items");
        
        clx.observer.observe(target, {childList:true});
    """, container)

    got_new = True
    while got_new:
        got_new = False

        letters = driver.find_elements_by_css_selector("a.llc.js-letter-list-item")
        for letter in letters:
            id = letter.get_attribute("data-id")
            if id not in fetched_letters:
                fetched_letters[id] = {
                    "url": letter.get_attribute("href")
                }
                got_new = True

        driver.execute_script("""
            clx.observed = false;
            arguments[0].scrollTop += arguments[0].clientHeight - 10;
        """, container)
        try:
            WebDriverWait(driver, 3).until(JsCondition("""
                return clx.observed; 
            """))
        except TimeoutException:
            pass
        if args.break_loops:
            break

    count = 0
    for lid, letter in fetched_letters.items():
        driver.get(letter["url"])
        from_addr = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".letter .letter-contact")))

        letter["from"] = from_addr.get_attribute("innerText") + " <" + from_addr.get_attribute("title") + ">"
        letter["date"] = ya_date_parser(driver.find_element_by_css_selector(".letter .letter__date").get_attribute("innerText"))
        letter["text"] = driver.find_element_by_css_selector(".letter .letter-body__body-content").get_attribute("innerHTML")
        count += 1
        if args.break_loops and count > 1:
            break

    driver.close()

    if args.save_to_db is not None:
        from pymongo import MongoClient

        client = MongoClient(args.mongo_address)
        db = client[args.save_to_db]
        collection = db[args.collection]

        collection.insert_many(fetched_letters.values())
    else:
        import json
        out_file = sys.stdout
        if args.output is not None:
            out_file = open(args.output, "w+")

        json.dump(fetched_letters, out_file, indent=4)

