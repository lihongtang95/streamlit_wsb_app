import streamlit as st

from selenium import webdriver
import os
from collections import Counter
from datetime import date,timedelta
from dateutil.parser import parse 
import requests

import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from PIL import Image



def grab_html():
    
    #If today is MON or SUN then we get data from a weekend discussion thread. Else, daily.

    if date.today().weekday() in (1,2,3,4,5):
        url = 'https://www.reddit.com/r/wallstreetbets/search/?q=flair%3A%22Daily%20Discussion%22&restrict_sr=1&sort=new%27'
        
    else:
        url = 'https://www.reddit.com/r/wallstreetbets/search/?q=flair%3A%22Weekend%20Discussion%22&restrict_sr=1&sort=new%27'
    
   
    CHROMEDRIVER_PATH = "/app/.chromedriver/bin/chromedriver"
    chrome_bin = os.environ.get('GOOGLE_CHROME_BIN', 'chromedriver')
    options = webdriver.ChromeOptions()
    options.binary_location = chrome_bin
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--headless')
    browser = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH, chrome_options=options)

    browser.get(url)

    return browser

    

def grab_link(driver):
    yesterday = date.today() - timedelta(days=1)
    links = driver.find_elements_by_xpath('//*[@class="_eYtD2XCVieq6emjKBH3m"]')
    
    for a in links:
        if a.text.startswith('Daily Discussion Thread'):
            DATE = ''.join(a.text.split(' ')[-3:])
            #print(f'DATE: {DATE}')
            parsed = parse(DATE) 
            if parse(str(yesterday)) == parsed:
                link = a.find_element_by_xpath('../..').get_attribute('href')
                stock_link = link.split('/')[-3]
                driver.close() 
                return stock_link, link
    
        if a.text.startswith('Weekend'):
            if date.today().weekday() == 0:
                friday = date.today() - timedelta(days=3)
            # elif date.today().weekday() == 5:
            #     friday = date.today() - timedelta(days=1)
            elif date.today().weekday() == 6:
                friday = date.today() - timedelta(days=2)
            DATE = ''.join(a.text.split(' ')[-3:])
            parsed = parse(DATE)
            if parse(str(friday)) == parsed:
                link = a.find_element_by_xpath('../..').get_attribute('href')
                stock_link = link.split('/')[-3]
                driver.close() 
                return stock_link, link
    

def grab_commentid_list(stock_link):
    html = requests.get(f'https://api.pushshift.io/reddit/submission/comment_ids/{stock_link}')
    raw_comment_list = html.json()
    return raw_comment_list

def grab_stocklist():
    stocklist = []
    with open('REDDIT_STOCK_LIST.txt', 'r') as w:
        stocks = w.readlines()
        for a in stocks:
            a = a.replace('\n','').replace('\t','')
            stocklist.append(a)
    #stocks_list = ['BABA','MSFT','SOFI','MVST','AMC','GME','AMZN','CLOV','BB','SPY','MRNA','QQQ']

    # Remove common words from list of tickers

    blacklist = ['I', 'A','DD','PT','MY','FOR','EOD','GO','TA','USA','AI','ALL','ARE','ON','IT','F','SO','NOW']
    #greylist = []

    for stock in blacklist:
        stocklist.remove(stock)
    # for stock in greylist:
    #     stocklist.remove(stock)

    return stocklist


def get_comments(comment_list):

    comment_list = comment_list['data']
    
    l = comment_list.copy()
    string = ''
    #string_list = []
    html_list = []
    for i in range(1,len(comment_list)+1):

        string += l.pop() + ','
        if i % 600 == 0:
            html = requests.get(f'https://api.pushshift.io/reddit/comment/search?ids={string}&fields=body&limit=1000')
            html_list.append(html.json())
    
            string = ''
            
    #Getting last chunk leftover, not divisible by 600

    if string:
        html = requests.get(f'https://api.pushshift.io/reddit/comment/search?ids={string}&fields=body&limit=1000')
        html_list.append(html.json())
            
    return html_list
        


def get_stock_list(newcomments,stocks_list):
    stock_dict = Counter()
    for chunk in newcomments:
        for a in chunk['data']:
            for ticker in stocks_list:
                
                parsedTicker1 = '$' + ticker + ' '
                parsedTicker2 = ' ' + ticker + ' '
                #parsedTicker3 = ' ' + ticker.lower().capitalize() + ' '

                if parsedTicker1 in a['body'] or parsedTicker2 in a['body']: #or parsedTicker3 in a['body']:
                    stock_dict[ticker]+=1

    return stock_dict


if __name__ == "__main__":
    driver = grab_html()
    stock_link, link = grab_link(driver)
    comment_list = grab_commentid_list(stock_link)

    stocks_list = grab_stocklist()
    new_comments = get_comments(comment_list)
  
    stock_dict = get_stock_list(new_comments,stocks_list)
    #stock_dict = {'HOOD': 62, 'NVDA': 59, 'TSLA': 58, 'PFE': 52, 'TLRY': 33, 'AMD': 32, 'BABA': 11}

    df = pd.DataFrame()
    df['ticker'] = stock_dict.keys()
    df['mentions'] = stock_dict.values()
    df = df.sort_values(by=['mentions'], ascending=False, ignore_index=True)
    df = df.head(10)

    image = Image.open('wsb.jpeg')
    

    col1, col2, col3 = st.columns([1.5,6,1])

    with col1:
        pass

    with col2:
        st.image(image)

    with col3:
        pass
    st.write("###")

    st.title(f'WSB daily trending stocks for {date.today().strftime("%m/%d")}')
    st.write("#")
    

    url= link
    st.markdown(url, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([2.5,6,1])

    with col1:
        pass

    with col2:
        st.write(df)

    with col3:
        pass

    
    st.write("#")
    

    df = df.head(5)

    for index, row in df.iterrows():
        
        ticker = row['ticker']
        
        st.write(f"""
        # ${ticker}
        """)

        # https://towardsdatascience.com/how-to-get-stock-data-using-python-c0de1df17e75
        #define the ticker symbol
        tickerSymbol = ticker
        #print(tickerSymbol)
        #get data on this ticker
        tickerData = yf.Ticker(tickerSymbol)
        #get the historical prices for this ticker
        tickerDf = tickerData.history( start=date.today() - timedelta(days=30), end=date.today())


        tickerDf = tickerDf.reset_index()
        for i in ['Open', 'High', 'Close', 'Low']: 
            tickerDf[i]  =  tickerDf[i].astype('float64')

        fig = go.Figure(data=[go.Candlestick(x=tickerDf['Date'],
                                   open=tickerDf['Open'],
                                high=tickerDf['High'],
                                low=tickerDf['Low'],
                                close=tickerDf['Close'])])
        fig.update_layout(height=650,width=900)
        st.plotly_chart(fig, use_container_width=True)


        col1, col2, col3 = st.columns([1,6,1])

        with col1:
            pass

        with col2:
            st.line_chart(tickerDf.Volume, use_container_width=True)

        with col3:
            pass

 
        st.write("##")
