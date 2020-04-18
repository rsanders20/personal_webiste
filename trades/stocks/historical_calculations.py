import datetime
from trades.stocks import stock_calculations
import matplotlib.pyplot as plt
import pandas as pd
from trades.models import Portfolio
from trades.stocks.stock_calculations import flatten_df
import scipy


def make_portfolio(purchase_date, sell_date):
    spy_trade = {
        'ticker_sybmol': 'SPY',
        'value': 100.00,
        'purchase_date': purchase_date,
        'sell_date': sell_date,
    }

    return spy_trade


def get_total_value(pf):
    df = stock_calculations.get_yahoo_stock_data([pf['ticker_symbol']], pf['purchase_date'], pf['sell_date'])

    pxdf, total, roi = flatten_df(df,
                                  [pf['ticker_symbol']],
                                  [pf['value']],
                                  [pf['purchase_date']],
                                  [pf['sell_date']],
                                  [])

    return pxdf, total, roi


def get_historic_data():
    base_time = datetime.datetime.strptime("2000-01-01", "%Y-%m-%d")
    all_times = [base_time+datetime.timedelta(days=x) for x in range(5)]

    interval = 1
    spy_statistics = []
    for time in all_times:
        pf = make_portfolio(time, time+datetime.timedelta(days=interval))
        pxdf, total, roi = get_total_value(pf)
        statistics_dict = {
            'interval': interval,
            'roi': roi[-1],
        }
        spy_statistics.append(statistics_dict)


    #         day_change_1 = 100*(row[3] - df_array[i-1][3])/df_array[i-1][3]
    #         day_change_5 = 100*(row[3] - df_array[i-5][3])/df_array[i-5][3]
    #         day_change_10 = 100*(row[3] - df_array[i-10][3])/df_array[i-10][3]
    #         day_change_20 = 100*(row[3] - df_array[i-20][3])/df_array[i-20][3]
    #         day_change_50 = 100*(row[3] - df_array[i-50][3])/df_array[i-50][3]
    #         day_change_100 = 100*(row[3] - df_array[i-100][3])/df_array[i-100][3]
    #         day_change_200 = 100*(row[3] - df_array[i-200][3])/df_array[i-200][3]
    #
    #         year_change_1 = 100*(row[3] - df_array[i-260][3])/df_array[i-260][3]
    #         year_change_2 = 100*(row[3] - df_array[i-520][3])/df_array[i-520][3]
    #         year_change_5 = 100*(row[3] - df_array[i-2600][3])/df_array[i-2600][3]
    #         year_change_10 = 100*(row[3] - df_array[i-5200][3])/df_array[i-5200][3]
    #
    #
    #         dict = {'Ticker': 'SPY',
    #                 'Dates': row[6],
    #                 'Close': row[3],
    #                 'Day-Change-1': day_change_1,
    #                 'Day-Change-5': day_change_5,
    #                 'Day-Change-10': day_change_10,
    #                 'Day-Change-20': day_change_20,
    #                 'Day-Change-50': day_change_50,
    #                 'Day-Change-100': day_change_100,
    #                 'Day-Change-200': day_change_200,
    #                 'Year-Change-1': year_change_1,
    #                 'Year-Change-2': year_change_2,
    #                 'Year-Change-5': year_change_5,
    #                 'Year-Change-10': year_change_10}
    #         spy_performance.append(dict)

    spy_df = pd.DataFrame.from_records(spy_performance)

    # spy_df.plot(kind="line", use_index=True, y=['Day-Change-100'])
    # ax1 = spy_df.plot.kde(y=['Year-Change-5'])
    # spy_df.plot.hist(bins=20, y=['Year-Change-1', 'Year-Change-2', 'Year-Change-5'], alpha=0.5, density=True, ax=ax1)
    spy_df.plot.hist(bins=20, y=['Year-Change-1', 'Year-Change-2', 'Year-Change-5'], alpha=0.5, density=True)

    # Stocks purchased in 1990, held for 1-day to 10-years.
    # Save histograms, mean, max, min, std
    plt.savefig('mygraph.png')


if __name__ == "__main__":
    get_historic_data()