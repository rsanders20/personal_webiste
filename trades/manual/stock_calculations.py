import os
from datetime import datetime
from datetime import timedelta

import numpy as np
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objs as go


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


def plot_stocks(all_trades):
    #TODO:  Handle the one or no-stock case
    now_time = datetime.now()
    ticker_list = []
    purchase_dates = []
    purchase_values = []
    purchase_internals = []
    sell_dates = []
    sell_values = []
    for trade in all_trades:
        ticker_list.append(trade.security)
        purchase_dates.append(trade.purchase_date)
        purchase_values.append(trade.purchase_value)
        purchase_internals.append(trade.purchase_internal)
        if trade.sell_date:
            sell_dates.append(trade.sell_date)
            sell_values.append(trade.sell_value)
        else:
            sell_dates.append(now_time)
            sell_values.append(None)

    start_time = min([sti for sti in purchase_dates])
    end_time = max([eti for eti in sell_dates])
    full_df = get_yahoo_stock_data(ticker_list, start_time, end_time)

    df_list = []
    for i, ticker in enumerate(ticker_list):
        individual_df = pd.DataFrame()
        purchase_date = make_np_date(purchase_dates[i])
        sell_date = make_np_date(sell_dates[i])

        individual_df[ticker+f'-{i}'] = full_df.loc[(full_df.index.values >= purchase_date) & (full_df.index.values < sell_date), ticker]['Close'].copy(deep=True)
        shares = purchase_values[i]/individual_df[ticker+f'-{i}'][0]
        individual_df[ticker+f'-{i}'] = individual_df[ticker+f'-{i}']*shares

        df_list.append(individual_df)

    df1 = pd.DataFrame()
    #This is only in place to keep the dataframe from losing rows.
    df1['remove'] = full_df[ticker_list[0]]['Close'].copy(deep=True)
    df = pd.concat([df1, *df_list], axis=1)

    cash_list = []
    invested_list = []
    for date in df.index.values:
        pd_date = pd.to_datetime(date)
        cash = 0
        invested = 0
        for trade in all_trades:
            if trade.sell_date:
                # print(trade.sell_date, type(trade.sell_date))
                # print(pd.to_datetime(date), type(pd.to_datetime(date)))
                if trade.sell_date <= pd_date:
                    cash += trade.sell_value
            if trade.purchase_date <= pd_date:
                if trade.purchase_internal:
                    cash += -1 * trade.purchase_value
                else:
                    invested += trade.purchase_value

        cash_list.append(cash)
        invested_list.append(invested)

    df['cash'] = cash_list
    del df['remove']
    df['total'] = df.sum(axis=1)
    df['invested'] = invested_list
    df['roi'] = df['total']/df['invested']

    # with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
    #     print(df)

    if not df.empty:
        i_graph = go.Figure()
        for i, ticker in enumerate(ticker_list):
            i_graph.add_trace(go.Scatter(x=df.index, y=df[ticker+f'-{i}'], name=ticker+f'-{i}'))
        i_graph.add_trace(go.Scatter(x=df.index, y=df['cash'], name='Cash'))
        i_graph.update_layout(legend_orientation='h')

        t_graph = go.Figure()
        t_graph.add_trace(go.Scatter(x=df.index, y=df['total'], name='Total'))
        t_graph.add_trace(go.Scatter(x=df.index, y=df['invested'], name='Invested'))
        t_graph.update_layout(xaxis_title='Date', legend_orientation='h')

        r_graph = go.Figure()
        r_graph.add_trace(go.Scatter(x=df.index, y=df['roi'], name='ROI'))
        r_graph.update_layout(xaxis_title='Date', legend_orientation='h')

        return i_graph, t_graph, r_graph
    else:
        return px.line(), px.line(), px.line()


def plot_individual_stocks(ticker_symbol, start_time_list, end_time_list):
    if not start_time_list:
        return px.line()
    start_time = min([datetime.strptime(sti, '%Y-%m-%d') for sti in start_time_list])
    end_time = max([datetime.strptime(sti, '%Y-%m-%d') for sti in end_time_list])
    df = get_yahoo_stock_data(ticker_symbol, start_time, end_time)
    if not df.empty:
        graph = px.line(df, x=df.index, y='Close')
        graph.update_layout(title=ticker_symbol[0],
                            margin={'l': 0, 'r': 0, 't': 0, 'b': 0})
        return graph
    else:
        return px.line()
