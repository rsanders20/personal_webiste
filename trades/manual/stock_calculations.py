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


def flatten_df(df, ticker_symbol, value_list, start_time_list, end_time_list, all_cash):
    if len(ticker_symbol) == 0:
        return df

    # if len(ticker_symbol) == 1:
    #     df['ticker'] = ticker_symbol[0]
    #     np_start_date = make_np_date(start_time_list[0])
    #     np_end_date = make_np_date(end_time_list[0])
    #     df = df.loc[(df.index.values <= np_end_date) & (df.index.values >= np_start_date)]
    #     value_factor = float(value_list[0])/df['Close'][0]
    #     df['Close'] = df['Close']*value_factor
    #     return df

    ticker_dict_list = []
    for ticker, value, start_time, end_time in zip(ticker_symbol, value_list, start_time_list, end_time_list):
        if ticker_dict_list:
            is_duplicate = False
            for i, ticker_dict in enumerate(ticker_dict_list):
                if ticker == ticker_dict['ticker']:
                    ticker_dict_list[i]['values'].append(value)
                    ticker_dict_list[i]['start_times'].append(start_time)
                    ticker_dict_list[i]['end_times'].append(end_time)
                    is_duplicate = True
                    break
            if is_duplicate is False:
                ticker_dict_list.append({'ticker': ticker,
                                         'values': [value],
                                         'start_times':[start_time],
                                         'end_times':[end_time]})
        else:
            ticker_dict_list.append({'ticker': ticker,
                                     'values': [value],
                                     'start_times':[start_time],
                                     'end_times':[end_time]})

    df_list = []
    for ticker_dict in ticker_dict_list:
        index = 0
        for value, start_time, end_time in zip(ticker_dict['values'], ticker_dict['start_times'], ticker_dict['end_times']):
            if ticker_dict['ticker'] in df:
                individual_df = df[ticker_dict['ticker']].copy()
            else:
                individual_df = df.copy()
            individual_df['ticker'] = ticker_dict['ticker'] + "-" + str(index)
            if start_time == min(start_time_list):
                total_time_list = individual_df.index.values

            index = index + 1
            np_start_date = make_np_date(start_time)
            np_end_date = make_np_date(end_time)
            individual_df = individual_df.loc[(individual_df.index.values <= np_end_date) & (individual_df.index.values>=np_start_date)]
            value_factor = float(value) / individual_df['Close'][0]
            individual_df['Close'] = individual_df['Close'] * value_factor
            df_list.append(individual_df)
        pxdf = pd.concat(df_list)

    total_cash_list = []
    invested_cash_list = []
    for total_time in total_time_list:
        cash_value = 0
        invested_value = 0
        for row in all_cash:
            if np.datetime64(row.purchase_date) <= total_time:
                if row.added:
                    cash_value = cash_value + row.value
                    invested_value = invested_value + row.value
                elif row.invested:
                    cash_value = cash_value - row.value
                elif row.de_invested:
                    cash_value = cash_value + row.value
        tcl = pd.Series(dict(zip(pxdf.columns, [0, 0, 0, cash_value, 0, 0, 'Cash']))).rename(total_time)
        icl = pd.Series(dict(zip(pxdf.columns, [0, 0, 0, invested_value, 0, 0, 'Invested']))).rename(total_time)
        invested_cash_list.append(icl)
        total_cash_list.append(tcl)
    cash = pd.DataFrame(total_cash_list)
    invested = pd.DataFrame(invested_cash_list)

    cash.index.name = 'Date'
    invested.index.name = 'Date'

    pxdf = pd.concat(([pxdf, cash]))

    total_list = []
    roi_list = []
    for total_time in total_time_list:
        total_sum = pxdf.loc[pxdf.index.values == total_time, 'Close'].sum()
        invested_sum = invested.loc[invested.index.values == total_time, 'Close'].sum()
        s = pd.Series(dict(zip(pxdf.columns, [0, 0, 0, total_sum, 0, 0, 'Total']))).rename(total_time)
        roi = pd.Series(dict(zip(pxdf.columns, [0, 0, 0, total_sum/invested_sum, 0, 0, 'ROI']))).rename(total_time)
        total_list.append(s)
        roi_list.append(roi)

    total = pd.DataFrame(total_list)
    total.index.name = 'Date'

    roi = pd.DataFrame(roi_list)
    roi.index.name = 'Date'

    ti_df = pd.concat([total, invested])
    ti_df.index.name='Date'

    return pxdf, ti_df, roi


def plot_stocks(ticker_symbol, value_list, start_time_list, end_time_list, all_cash):
    start_time = min([sti for sti in start_time_list])
    end_time = max([eti for eti in end_time_list])
    df = get_yahoo_stock_data(ticker_symbol, start_time, end_time)
    pxdf, total, roi = flatten_df(df, ticker_symbol, value_list, start_time_list, end_time_list, all_cash)
    if not pxdf.empty:
        pxdf.reset_index(level=0, inplace=True)
        i_graph = px.line(pxdf, x='Date', y='Close', color='ticker')
        i_graph.update_layout(title="Individual Closing Values")

        t_graph = px.line(total, x=total.index, y='Close', color='ticker')
        t_graph.update_layout(title="Total Portfolio Value", xaxis_title='Date')

        r_graph = px.line(roi, x=roi.index, y='Close', color='ticker')
        r_graph.update_layout(title="Return on Investment", xaxis_title='Date')

        return i_graph, t_graph, r_graph
    else:
        return px.line(), px.line(), px.line()


def plot_individual_stocks(ticker_symbol, value_list, start_time_list, end_time_list, all_cash):
    start_time = min([datetime.strptime(sti, '%Y-%m-%d') for sti in start_time_list])
    end_time = max([datetime.strptime(sti, '%Y-%m-%d') for sti in end_time_list])
    df = get_yahoo_stock_data(ticker_symbol, start_time, end_time)
    if not df.empty:
        graph = px.line(df, x=df.index, y='Close')
        graph.update_layout(title=ticker_symbol[0])
        return graph
    else:
        return px.line()
