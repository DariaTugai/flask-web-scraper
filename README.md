# ETF Flow Scraper

## Description

ETF Flow Scraper is a Python web application built with Flask that automatically collects cryptocurrency ETF flow data from CoinGlass and displays it in a user-friendly web interface.

The application uses Selenium to access dynamic web content, extracts ETF flow information for selected cryptocurrencies, processes the data, and presents it on a local website.

Currently supported assets include:

* Bitcoin (BTC)
* Ethereum (ETH)
* Solana (SOL)
* XRP
* HYPE

## Features

* Automatic ETF flow data collection
* Web scraping using Selenium and BeautifulSoup
* Flask-based web interface
* Support for dynamic website content
* Display of daily ETF inflows and outflows
* Trading day verification using NYSE calendar

## Technologies Used

* Python
* Flask
* Selenium
* BeautifulSoup4
* webdriver-manager
* selenium-stealth
* pandas-market-calendars
* holidays

## Installation

### 1. Clone the repository

git clone <repository-url>
cd flask-web-scraper


### 2. Install dependencies

pip install -r requirements.txt


### 3. Run the application

python app.py


### 4. Open the application

Open your browser and go to:

http://127.0.0.1:5000

## Project Structure

├── app.py
├── scraper.py
├── templates/
│   └── index.html
├── static/
│   └── index.css
└── requirements.txt
