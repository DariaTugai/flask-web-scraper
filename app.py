
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions

from webdriver_manager.chrome import ChromeDriverManager

from bs4 import BeautifulSoup

import datetime

import psycopg2

import asyncio

from selenium_stealth import stealth

import holidays

from scraper import updateStockData

import uvicorn

from flask import Flask, render_template
app = Flask(__name__)

chrome_driver_path = ChromeDriverManager().install()
service = Service(chrome_driver_path)
options = Options()
options.add_argument('--disable-images')
options.add_argument('--blink-settings=imagesEnabled=false')
options.add_argument('--headless=new')
# options.add_argument("--headless") 
driver = webdriver.Chrome(service=service,options =options)
us_holidays = holidays.US(years=int(datetime.datetime.today().strftime('%Y')))
stealth(
#ant-table-container
driver,

    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",

    languages=["en-US", "en"],

    vendor="Google Inc.",

    platform="Win32",

    webgl_vendor="Intel Inc.",  

    renderer="Intel Iris OpenGL Engine",

    fix_hairline=True,

)


update_stock_data_obj = updateStockData(driver=driver)
print(100*'*')
# print(update_stock_data_obj.update_crypto_ETF_flows())

CRYPTO_KEYS = ['bitcoin', 'ethereum', 'solana', 'xrp', 'hype']
etf_data = update_stock_data_obj.update_crypto_ETF_flows()
 
def fmt_flow(value: float) -> str:
    sign = '+' if value > 0 else ''
    if abs(value) >= 1_000_000:
        return f"{sign}{value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"{sign}{value / 1_000:.1f}K"
    return f"{sign}{value:,.2f}".rstrip('0').rstrip('.')
 
 
app.jinja_env.globals['fmt_flow'] = fmt_flow
 
 
@app.route('/')
def index():
    return render_template('index.html', etf_data=etf_data, crypto_keys=CRYPTO_KEYS)
 
 
if __name__ == '__main__':
    app.run()