from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from requests import Session
from bs4 import BeautifulSoup
import datetime
import psycopg2
import asyncio
import json
from selenium_stealth import stealth
import holidays
import time
import pandas_market_calendars as mcal

class updateStockData():
    def __init__(self, driver):
        self.etf_price_update_frequency_minutes = 24 * 60
        self.etf_flows_update_frequency_minutes = 24 * 60
        self.etf_price_last_update_date = 0
        self.etf_flows_last_update_date = 0
        self.driver = driver
        self.supported_cryptocurrencies = ['ethereum', 'bitcoin', 'solana', 'xrp', 'hype']
        self.accepted_terms = False
        self.etf_flow_table_suffix = '_etf_flows'
        self.tracked_crypto_file_name = "tracked_etf.json"
        self.tracked_etf_dict = json.load(open(self.tracked_crypto_file_name, 'r'))
        self.etf_price_table_suffix = '_etf_price_record'
        self.testing = False
        self.etf_price_endpoint = f'https://api.twelvedata.com/price'
        self.twelwedata_apikey = 'YOUR_API_KEY'
        self.twelwedata_minute_limit = 8
        self.session = Session()
        twelwe_data_headers = {'apikey': self.twelwedata_apikey}
        self.session.headers.update(twelwe_data_headers)
        self.delay_after_error_sec = 2
        self.us_holidays_dates = [str(date) for date, holiday in holidays.US(years=int(datetime.datetime.today().strftime('%Y'))).items()]
        self.us_holidays_dates.append("2026-04-03")

    def market_is_open(self, date):
        result = mcal.get_calendar("NYSE").schedule(start_date=date, end_date=date)
        return result.empty == False

    def update_crypto_ETF_flows(self):
        def table_loader(driver):
            try:
                table = driver.find_element(By.CLASS_NAME, "ant-table-container")
                rows = table.find_elements(By.CLASS_NAME, "ant-table-row")
                return len(rows) > 10
            except:
                False
        full_etf_list_to_return = []
        rendered_etf_tables = {}
        t = time.time()
        todays_date = datetime.datetime.today()
        # update_date = (datetime.datetime.strptime(todays_date.strftime('%Y-%m-%d'), '%Y-%m-%d') + datetime.timedelta(days=-3)).strftime('%Y-%m-%d')
        # update_date_lst = [update_date]
        update_date_lst = [(datetime.datetime.strptime(todays_date.strftime('%Y-%m-%d'), '%Y-%m-%d') + datetime.timedelta(days=-3-x)).strftime('%Y-%m-%d') for x in range(10)]
        print(update_date_lst)
        for update_date in update_date_lst:
            same_date_etf_flows_dict  = {}

            yesterday_date = (datetime.datetime.strptime(update_date, '%Y-%m-%d') + datetime.timedelta(days=-1)).strftime('%Y-%m-%d')

            if self.market_is_open(update_date) == False:
                continue

            while self.market_is_open(yesterday_date) == False:
                yesterday_date = (datetime.datetime.strptime(yesterday_date, '%Y-%m-%d') + datetime.timedelta(days=-1)).strftime('%Y-%m-%d')

            # if t - self.etf_flows_last_update_date >= self.etf_flows_update_frequency_minutes * 60:
            for cryptocurrency in self.supported_cryptocurrencies:
                succesfully_updated_ETF = False
                sub_header_exist = True
                coin_glass_btc_etf_url = f'https://www.coinglass.com/etf/{cryptocurrency}'

                if cryptocurrency == 'bitcoin':
                    sub_header_exist = False

                while succesfully_updated_ETF == False:
                    try:
                        timeout = 10
                        if cryptocurrency not in rendered_etf_tables.keys():

                            self.driver.get(coin_glass_btc_etf_url)
                            WebDriverWait(driver=self.driver, timeout=timeout).until(method=table_loader)
                            page = self.driver.page_source
                            soup = BeautifulSoup(page, 'html.parser')
                            all_tables = soup.find_all('div', {"class": 'ant-table-container'})
                            # etf_table = all_tables[0]
                            rendered_etf_tables[cryptocurrency] =  all_tables[0]
                        etf_table = rendered_etf_tables[cryptocurrency]
                        first_table_headers = [header for header in etf_table.find_all('th', {'class': 'ant-table-cell'})]
                        table_header_lst = [str(th_el) for th_el in first_table_headers]
                        joined_table_headers = ''.join(table_header_lst)
                        inflows_headers = joined_table_headers.split('Time(UTC)')[1].split('Total')[0]

                        parsed_inflows_headers = BeautifulSoup(inflows_headers, 'html.parser').find_all('th')[:-1]
                        all_table_cells = [str(cell) for cell in etf_table.find_all('td', {"class": "ant-table-cell"})]
                        joined_table_cells = ''.join(all_table_cells)

                        todays_inflows_row = joined_table_cells.split(yesterday_date)[0].split(update_date)[1]
                        parsed_todays_inflows_row = BeautifulSoup(todays_inflows_row, 'html.parser').find_all('td')
                        parsed_todays_inflows_row = parsed_todays_inflows_row[:-2]

                        if sub_header_exist:
                            separator_text_inside_tag = '\n'
                            strip_text_inside_tag = True
                            inflows_ETF_dict = {parsed_inflows_headers[inflow_indx].get_text(separator_text_inside_tag, strip_text_inside_tag).split('\n')[0]
                                                : parsed_todays_inflows_row[inflow_indx].get_text(separator_text_inside_tag, strip_text_inside_tag)
                                                for inflow_indx in range(len(parsed_inflows_headers))}
                        else:
                            separator_text_inside_tag = ''
                            strip_text_inside_tag = True
                            inflows_ETF_dict = {parsed_inflows_headers[inflow_indx].get_text(separator_text_inside_tag, strip_text_inside_tag)
                                                : parsed_todays_inflows_row[inflow_indx].get_text(separator_text_inside_tag, strip_text_inside_tag)
                                                for inflow_indx in range(len(parsed_todays_inflows_row))}

                        succesfully_updated_ETF = True
                        self.etf_flows_last_update_date = t

                    except Exception as e:
                        print(e)
                        print('error')
                        # await asyncio.sleep(self.delay_after_error_sec)

                format_num_dict = {'K': 10**3, 'M': 10**6, 'B': 10**9}
                for etf_name, etf_flow_value in inflows_ETF_dict.items():
                    if etf_name not in self.tracked_etf_dict[cryptocurrency]:
                        self.add_new_etf(cryptocurrency,etf_name)
                    if etf_flow_value == '-':
                        inflows_ETF_dict[etf_name] = 0
                    if str(etf_flow_value)[-1] in format_num_dict.keys():
                        inflows_ETF_dict[etf_name] = float(etf_flow_value[:-1]) * format_num_dict[etf_flow_value[-1]]
                    else:
                        if etf_flow_value == '-':
                            inflows_ETF_dict[etf_name] = 0
                        else:
                            inflows_ETF_dict[etf_name] = float(etf_flow_value)
                # print(inflows_ETF_dict)
                same_date_etf_flows_dict[cryptocurrency] = inflows_ETF_dict
            same_date_etf_flows_dict['date'] = update_date
            full_etf_list_to_return.append(same_date_etf_flows_dict)
        return full_etf_list_to_return
                    # self.write_to_database(cryptocurrency + self.etf_flow_table_suffix, inflows_ETF_dict, update_date, crypto_name=cryptocurrency)

    def add_new_etf(self, crypto_name, new_etf):
        self.tracked_etf_dict[crypto_name].append(new_etf)
        json.dump(self.tracked_etf_dict,open(self.tracked_crypto_file_name,'w'),indent=4)

if __name__ =="__main__":
    pass