import datetime
import os
import time

from trades.manual import stock_calculations
from trades.manual.stock_calculations import get_securities_list
from trades.strategy.optimize import create_starting_values, create_single_solutions
import pandas as pd

import numpy as np

from trades.strategy.strategy_calculations import get_roi


def make_default_factors(start_time, training_yrs, tickers):
    rules_list, buy_threshold, sell_threshold,\
    ticker, base_time, now_time, bounds, goal = create_starting_values()
    data_dir = r'./assets/opt/'
    file = os.path.join(data_dir, "default.csv")

    results_list = []
    now_time = start_time
    base_time = start_time-datetime.timedelta(days=365*training_yrs)
    for ticker in tickers:
        try:
            results, performance = create_single_solutions(
                rules_list, buy_threshold, sell_threshold, ticker, base_time, now_time, bounds, goal)
            results.append(ticker)
            results.append(base_time)
            results.append(now_time)
            results.append(performance)
            results_list.append(results)

            results_df = pd.DataFrame.from_records(results_list)
            print(results_df)
            results_df.to_csv(file)
        except:
            print("Failed to Download")

    print(results_list)


def run_20_yr_opt():
    start_time = datetime.datetime.strptime("2017-01-01", '%Y-%m-%d')
    training_yrs = 20
    tickers = get_securities_list()
    ticker_list = []
    new_ticker = False
    for i, ticker in enumerate(tickers):
        if ticker['value'] == 'ARNC':
            new_ticker = True

        if new_ticker:
            ticker_list.append(ticker['value'])

    print(tickers)
    make_default_factors(start_time, training_yrs, ticker_list)


def build_portfolio():
    #1  top 10 roi (simple or strategic?) from 2016 to 2017
    #2  most improved over the 20 yr. training period
    #3  most improved from 2016 to 2017
    data_dir = r'./assets/opt/'
    file = os.path.join(data_dir, "default-2017-20yrs")
    best_roi_file = os.path.join(data_dir, "best_roi-2017-20yrs")
    rules_list, buy_threshold, sell_threshold, ti, bt, nt, bounds, goal = create_starting_values()

    percentage_df = pd.read_csv(file, index_col=0)
    percentage_array = percentage_df.to_numpy()

    results_list = []
    for factors in percentage_array[0:100]:
        ticker = factors[4]
        base_time = datetime.datetime.strptime("2016-01-01", '%Y-%m-%d')
        now_time = base_time+datetime.timedelta(days=365)
        for i, rule in enumerate(rules_list):
            rules_list[i]['Percentage'] = factors[i]

        values_df = get_roi(ticker, base_time, now_time, rules_list, buy_threshold, sell_threshold)
        roi = -1 * values_df['strategic_values'][-1] / values_df['strategic_values'][0]
        if not np.isnan(roi):
            results_list.append([-1*roi, ticker, *factors[0:4]])
        print(ticker)

    toc = time.time()

    results_array = np.array(results_list)
    roi_array = results_array[:, 0].astype(float)
    ind = np.argpartition(roi_array, -10)[-10:]
    sorted_ind = ind[np.argsort(-1*roi_array[ind])]
    print(roi_array[sorted_ind])
    print(results_array[sorted_ind, :])

    best_10_df = pd.DataFrame.from_records(results_array[sorted_ind, :])
    print(best_10_df)
    best_10_df.to_csv(best_roi_file)


def run_auto_portfolio():
    data_dir = r'./assets/opt/'
    best_roi_file = os.path.join(data_dir, "best_roi-2017-20yrs")
    # improved_percentages = os.path.join(data_dir, "default2-2017-20yrs")
    rules_list, buy_threshold, sell_threshold, ti, bt, nt, bo, goal = create_starting_values()

    df = pd.read_csv(best_roi_file)
    # df2 = pd.read_csv(improved_percentages)
    auto_array = df.to_numpy()
    # improved_array = df2.to_numpy()

    check_base_time = datetime.datetime.strptime("2016-01-01", '%Y-%m-%d')
    check_now_time = check_base_time + datetime.timedelta(days=365)

    base_time = datetime.datetime.strptime("2017-01-01", '%Y-%m-%d')
    now_time = base_time + datetime.timedelta(days=365)

    roi_list = []
    # for improved_row, auto_row in zip(improved_array, auto_array):
    for row in auto_array:
        for i, rule in enumerate(rules_list):
            rules_list[i]['Percentage'] = row[i+3]

        ticker = row[2]

        check_values_df = get_roi(ticker, check_base_time, check_now_time, rules_list, buy_threshold, sell_threshold)
        check_strat_roi = check_values_df['strategic_values'][-1] / check_values_df['strategic_values'][0]
        check_simp_roi = check_values_df['simple_values'][-1] / check_values_df['simple_values'][0]

        if check_strat_roi > check_simp_roi*0.95:
            values_df = get_roi(ticker, base_time, now_time, rules_list, buy_threshold, sell_threshold)
            strat_roi = values_df['strategic_values'][-1] / check_values_df['strategic_values'][0]
            simp_roi = values_df['simple_values'][-1] / check_values_df['simple_values'][0]

            roi_list.append([strat_roi, simp_roi, ticker])

    roi_df = pd.DataFrame.from_records(roi_list)
    roi_df.columns = ['strat_roi', 'simp_roi', 'ticker']
    print(roi_df)
    total_roi = (roi_df['strat_roi'].sum()/len(roi_df['strat_roi']))
    print(total_roi)


def improve_default():
    #Note:  This did not improve the results.
    data_dir = r'./assets/opt/'
    best_roi_file = os.path.join(data_dir, "best_roi-2017-20yrs")
    default2 = os.path.join(data_dir, "default2-2017-20yrs")
    rules_list, buy_threshold, sell_threshold, ti, bt, nt, bo, goal = create_starting_values()

    df = pd.read_csv(best_roi_file)
    auto_array = df.to_numpy()

    base_time = datetime.datetime.strptime("1997-01-01", '%Y-%m-%d')
    now_time = datetime.datetime.strptime("2017-01-01", '%Y-%m-%d')

    results_list = []
    for row in auto_array:
        for i, rule in enumerate(rules_list):
            rules_list[i]['Percentage'] = row[i + 3]

        bounds = []
        for rule in rules_list:
            lower_bound = rule['Percentage'] * 0.5
            upper_bound = rule['Percentage'] * 3.0
            bounds.append((lower_bound, upper_bound))

        ticker = row[2]

        try:
            results, performance = create_single_solutions(
                rules_list, buy_threshold, sell_threshold, ticker, base_time, now_time, bounds, goal)
            results.append(ticker)
            results.append(base_time)
            results.append(now_time)
            results.append(performance)
            results_list.append(results)

            results_df = pd.DataFrame.from_records(results_list)
            print(results_df)
            results_df.to_csv(default2)
        except:
            print("Failed to Download")


if __name__ == "__main__":
    # build_portfolio()
    run_auto_portfolio()
    # improve_default()
