import os
from datetime import datetime
from datetime import timedelta

import numpy as np
import pandas as pd
import yfinance as yf
import plotly.express as px


def get_securities_list():
    dirpath = os.getcwd()
    file_path = os.path.join(dirpath, "assets", "sp500.csv")
    ticker_df = pd.read_csv(file_path)
    ticker_df.columns = ['value', 'label']
    return ticker_df.to_dict("rows")


def get_yahoo_stock_data(ticker_symbol, start_time, end_time):
    if not ticker_symbol:
        return pd.DataFrame()
    ticker_symbol_string = make_ticker_string(ticker_symbol)
    df = pd.DataFrame()

    try:
        df = yf.download(ticker_symbol_string, start=start_time, end=end_time, group_by="ticker")
    except KeyError:
        print("Key Error Caught")
    return df


def make_ticker_string(ticker_symbol):
    if len(ticker_symbol) == 0:
        return ''

    if len(ticker_symbol) == 1:
        return ticker_symbol[0]

    ticker_symbol_str = ''
    for ticker in ticker_symbol:
        ticker_symbol_str += ticker
        ticker_symbol_str += ' '

    return ticker_symbol_str


def make_np_date(date_str):
    np_date = np.array(pd.to_datetime(date_str, format='%Y-%m-%d'), dtype=np.datetime64)
    return np_date


def flatten_df(df, ticker_symbol, value_list, start_time_list):
    if len(ticker_symbol) == 0:
        return df

    if len(ticker_symbol) == 1:
        df['ticker'] = ticker_symbol[0]
        np_date = make_np_date(start_time_list[0])
        df = df.loc[df.index.values >= np_date]
        value_factor = float(value_list[0])/df['Close'][0]
        df['Close'] = df['Close']*value_factor
        return df

    df_list = []
    for ticker, value, start_time in zip(ticker_symbol, value_list, start_time_list):
        individual_df = df[ticker].copy()
        individual_df['ticker'] = ticker
        np_date = make_np_date(start_time)
        individual_df = individual_df.loc[individual_df.index.values >= np_date]
        value_factor = float(value)/individual_df['Close'][0]
        individual_df['Close'] = individual_df['Close']*value_factor
        df_list.append(individual_df)
        if start_time == min(start_time_list):
            total_time_list = individual_df.index.values
    pxdf = pd.concat(df_list)

    total_list = []
    for total_time in total_time_list:
        total_sum = pxdf.loc[pxdf.index.values == total_time, 'Close'].sum()
        s = pd.Series(dict(zip(pxdf.columns, [0, total_sum, 0, 0, 0, 0, 'Total']))).rename(total_time)
        total_list.append(s)

    total = pd.DataFrame(total_list)
    total.index.name = 'Date'
    return pd.concat([pxdf, total])


def plot_stocks(ticker_symbol, value_list, start_time_list, end_time):
    start_time = min([datetime.strptime(sti, '%Y-%m-%d') for sti in start_time_list])
    print(ticker_symbol, value_list, start_time, end_time)
    df = get_yahoo_stock_data(ticker_symbol, start_time, end_time)
    print(df)

    pxdf = flatten_df(df, ticker_symbol, value_list, start_time_list)
    if not pxdf.empty:
        pxdf.reset_index(level=0, inplace=True)
        graph = px.line(pxdf, x='Date', y='Close', color='ticker')

        return graph
    else:
        return px.line()
