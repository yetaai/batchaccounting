from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.common.exceptions import TimeoutException

import traceback as tb
import re
import time

user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox'
drivers = {}
re1 = re.compile(r'\s+\(')
re2 = re.compile('\-')
pagerefresh = {}
def makeChromeDriver(headless=True, port=9222):
    chrome_options = ChromeOptions()
    chrome_options.add_argument(f'user-agent={user_agent}')
    driver = None
    if headless:
        chrome_options.add_argument("--headless")
        # chrome_options.add_argument('--remote-debugging-port=' + str(port))
    while 1:
        try:
            driver = webdriver.Chrome(chrome_options=chrome_options, service_log_path="chromedriver001.log")
            return driver
        except Exception as e:
            print('==========12345====================Failed to get driver, sleep half second then try again')
            time.sleep(0.5)
            break

def makeDriver(headless=True, port=4444):
    chrome_options = ChromeOptions()
    capability = webdriver.DesiredCapabilities.CHROME
    if headless:
        chrome_options.add_argument("--headless")
    while 1:
        try:
            # run chromedriver --url-base=/wd/hub
            driver = webdriver.Remote(command_executor='http://127.0.0.1:' + str(port) + '/wd/hub', desired_capabilities=capability, options=chrome_options)
            return driver
        except Exception as e:
            print('Failed to get remote connection, error: ', e)
            time.sleep(0.5)
def makeFirefoxDriver(headless=True, port=9222):
    firefoxoptions = Options()
    # chrome_options.add_argument(f'user-agent={user_agent}')
    profile = webdriver.FirefoxProfile()
    profile.set_preference("general.useragent.override", user_agent)
    profile.set_preference("plugin.disable_full_page_plugin_for_types",
                                 "application/pdf,application/vnd.adobe.xfdf,application/vnd.fdf,application/vnd.adobe.xdp+xml");
    driver = None
    if headless:
        firefoxoptions.headless = True
    while 1:
        try:
            driver = webdriver.Firefox(options=firefoxoptions, service_log_path="firefoxdriver001.log", firefox_profile=profile)
            print('============================67890==Success get firefox driver')
            return driver
        except Exception as e:
            print(e)
            print('==========12345====================Failed to get firefox driver, sleep half second then try again')
            time.sleep(0.5)
