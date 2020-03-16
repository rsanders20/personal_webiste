import os
import pandas as pd
import yfinance as yf
import plotly.express as px


def get_securities_list():
    dirpath = os.getcwd()
    file_path = os.path.join(dirpath, "assets","sp500.csv")
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


def flatten_df(df, ticker_symbol, value_list):
    if len(ticker_symbol) == 0:
        return df

    if len(ticker_symbol) == 1:
        df['ticker'] = ticker_symbol[0]
        value_factor = float(value_list[0])/df['Close'][0]
        df['Close'] = df['Close']*value_factor
        return df

    df_list = []
    for ticker in ticker_symbol:
        # TODO:  Add in value list
        individual_df = df[ticker]
        individual_df['ticker'] = ticker
        df_list.append(individual_df)
    pxdf = pd.concat(df_list)
    return pxdf


def plot_stocks(ticker_symbol, value_list, start_time, end_time):
    # df = get_alpha_stock_data(ticker_symbol)
    df = get_yahoo_stock_data(ticker_symbol, start_time, end_time)
    pxdf = flatten_df(df, ticker_symbol, value_list)
    if not pxdf.empty:
        pxdf.reset_index(level=0, inplace=True)
        graph = px.line(pxdf, x='Date', y='Close', color='ticker')

        return graph
    else:
        return px.line()