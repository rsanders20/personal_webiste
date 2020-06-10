import os
from datetime import datetime
from datetime import timedelta

import numpy as np
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objs as go

from trades.strategy import strategy_calculations
from trades.strategy.strategy_calculations import signal_to_dict


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


def trade_to_dict(trade):
    trade_dict = {'Name': trade.security,
                  'Value': trade.purchase_value,
                  'Strategy': trade.strategy,
                  'Start Date': datetime.strftime(trade.purchase_date, '%Y-%m-%d'),
                  'purchase_internal': trade.purchase_internal}
    return trade_dict


def get_auto_data(user, trades):
    data = []
    for trade in trades:
        data.append(trade_to_dict(trade))

    df_strat_dict = {}
    for i,row in enumerate(data):
        if not row['purchase_internal']:
            df_strat = pd.DataFrame()
            value_df = strategy_calculations.get_values_df(row, user)
            ticker = row['Name']
            df_strat['strategic'] = value_df['strategic_values']
            df_strat_dict[ticker+f'-{i}'] = df_strat

    full_strat_df = pd.concat(df_strat_dict, axis=1)
    full_strat_df['sum'] = full_strat_df[list(full_strat_df.columns)].sum(axis=1)

    return full_strat_df


def plot_stocks(user, all_trades):
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

    if len(ticker_list) == 1 or ticker_list.count(ticker_list[0]) == len(ticker_list):
        print('Modifying yahoo data')
        new_df = pd.concat({ticker_list[0]: full_df}, axis=1)
        full_df = new_df

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

    full_strat_df = get_auto_data(user, all_trades)

    if not df.empty:
        i_graph = go.Figure()
        for i, ticker in enumerate(ticker_list):
            i_graph.add_trace(go.Scatter(x=df.index, y=df[ticker+f'-{i}'], name=ticker+f'-{i}'))
        i_graph.add_trace(go.Scatter(x=df.index, y=df['cash'], name='Cash'))
        i_graph.update_layout(legend_orientation='h')

        t_graph = go.Figure()
        t_graph.add_trace(go.Scatter(x=df.index, y=df['total'], name='Simple'))
        t_graph.add_trace(go.Scatter(x=full_strat_df.index, y=full_strat_df['sum'], name='Strategic'))
        t_graph.add_trace(go.Scatter(x=df.index, y=df['invested'], name='Invested'))
        t_graph.update_layout(xaxis_title='Date', legend_orientation='h')

        r_graph = go.Figure()
        r_graph.add_trace(go.Scatter(x=df.index, y=df['roi'], name='Simple ROI'))
        r_graph.add_trace(go.Scatter(x=full_strat_df.index, y=full_strat_df['sum']/df['invested'], name='Strategic ROI'))
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
