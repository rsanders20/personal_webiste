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


def auto_portfolio_1(now_time, best_num, best_dur_yrs, opt_dur_yrs, eval_dur_yrs):
    # Find 10 best (best_num) simple ROI's over the last year (best_dur)
    base_time = now_time-datetime.timedelta(days=365*best_dur_yrs)
    next_time = now_time+datetime.timedelta(days=365*eval_dur_yrs)
    data_dir = r'./assets/opt/'
    default_file = os.path.join(data_dir, "default-2017-20yrs")
    rules_list, buy_threshold, sell_threshold, ti, bt, nt, bo, go = create_starting_values()

    default_df = pd.read_csv(default_file, index_col=0)
    default_array = default_df.to_numpy()

    results_list = []
    random_list = np.random.randint(low=0, high=len(default_array), size=10)
    print(random_list)
    # for factors in default_array[random_list]:
    #     # if float(factors[7]) < -0.85:
    #     ticker = factors[4]
    #     values_df = get_roi(ticker, base_time, now_time, rules_list, buy_threshold, sell_threshold)
    #     roi = values_df['simple_values'][-1] / values_df['simple_values'][0]
    #     if not np.isnan(roi):
    #         results_list.append([roi, ticker, *factors[0:4], factors[7]])
    #     print(ticker)
    #
    # best_num = len(results_list)
    # results_array = np.array(results_list)
    # roi_array = results_array[:, 0].astype(float)
    # ind = np.argpartition(roi_array, -best_num)[-best_num:]
    # sorted_ind = ind[np.argsort(-1 * roi_array[ind])]
    #
    # best_df = pd.DataFrame.from_records(results_array[sorted_ind, :])
    # print(best_df)

    # Build optimized factors over the last 20 yrs. (opt_dur for the 10 chosen).
        # Is there a shortcut to this?  perhaps check 5-10 "standard" rules packages?
        # 2.0, 1.1, 0.93, 0.51
        # 3.0, 1.5  1.4, 0.9
        # 4.0, 2.2, 1.86, 1.0
        # 5.0, 3.3, 2.2, 1.2
    # Using existing factors

    best_array = default_array[random_list]

    # For each of the best, check if the optimimized solution did better than the simple solution over the last year (best_dur)
    # If the optmized solution was better, add to final portfolio.
    # perhaps add a check on the total buy and sell numbers...good solutions don't trade all the time

    # best_array = best_df.to_numpy()
    print(best_array)
    roi_list = []
    for row in best_array:
        for i, rule in enumerate(rules_list):
            rules_list[i]['Percentage'] = float(row[i])
            # rules_list[i]['Percentage'] = opt_r5[i]*2
        ticker = row[4]

        check_values_df = get_roi(ticker, base_time, now_time, rules_list, buy_threshold, sell_threshold)
        check_strat_roi = check_values_df['strategic_values'][-1] / check_values_df['strategic_values'][0]
        check_simp_roi = check_values_df['simple_values'][-1] / check_values_df['simple_values'][0]

        if check_strat_roi > check_simp_roi*0.95:
            values_df = get_roi(ticker, now_time, next_time, rules_list, buy_threshold, sell_threshold)
            strat_roi = values_df['strategic_values'][-1] / check_values_df['strategic_values'][0]
            simp_roi = values_df['simple_values'][-1] / check_values_df['simple_values'][0]
            if not np.isnan(strat_roi):
                roi_list.append([strat_roi, simp_roi, ticker, *row[0:4]])

    roi_df = pd.DataFrame.from_records(roi_list)
    roi_df.columns = ['strat_roi', 'simp_roi', 'ticker', 'w1', 'w2', 'w3', 'w4']
    print(roi_df)
    roi_df.to_csv(os.path.join(data_dir, "auto_portfolio_1.csv"))
    auto_portfolio_roi = (roi_df['strat_roi'].sum()/len(roi_df['strat_roi']))

    # compare to just SPY and "optimized" SPY (OPT-R5)
    opt_r5 = [1.95, 1.14, 0.93, 0.51]
    for i, rule in enumerate(rules_list):
        rules_list[i]['Percentage'] = opt_r5[i]
    spy_values_df = get_roi("SPY", now_time, next_time, rules_list, buy_threshold, sell_threshold)
    spy_strat_roi = spy_values_df['strategic_values'][-1] / spy_values_df['strategic_values'][0]
    spy_simp_roi = spy_values_df['simple_values'][-1] / spy_values_df['simple_values'][0]

    ap = [auto_portfolio_roi, spy_strat_roi, spy_simp_roi]

    return ap


def auto_portfolio_2(eval_start_time, eval_end_time, opt_start_time, opt_end_time):
    # Get 10 random stocks from the sp500
    data_dir = r'./assets/opt/'
    default_file = os.path.join(data_dir, "default-2017-20yrs")
    rules_list, buy_threshold, sell_threshold, ti, bt, nt, bo, go = create_starting_values()

    default_df = pd.read_csv(default_file, index_col=0)
    default_array = default_df.to_numpy()

    random_list = np.random.randint(low=0, high=len(default_array), size=1)
    # random_array = default_array[random_list]
    random_array = default_array
    print(random_array)

    # Optimize the factors:
        # Based on roi, not number of realizations
        # Uses -5, -1, -2, 3 timing
        # Uses the OPT-R5 initial guess with associated bounds
        # Starts in 2005 and goes to 2010.
    now_time = datetime.datetime.strptime(opt_end_time, '%Y-%m-%d')
    base_time = datetime.datetime.strptime(opt_start_time, '%Y-%m-%d')
    # bounds = []
    # opt_r5 = [4.0, 2.0, 2.0, 1.0]
    # for i, rule in enumerate(rules_list):
    #     lower_bound = opt_r5[i]
    #     upper_bound = opt_r5[i] * 3.0
    #     bounds.append((lower_bound, upper_bound))
    bounds = [(0.0, 20.0), (0.0, 20.0), (0.0, 20.0), (0.0, 20.0)]

    durations = [[-5, 0], [0, -1], [0, -2], [0, -3]]
    for i, dur in enumerate(durations):
        rules_list[i]['Larger: When?'] = dur[0]
        rules_list[i]['Smaller: When?'] = dur[1]

    goal = "roi"

    results_list = []
    for chosen in random_array:
        ticker = chosen[4]
        print(base_time, now_time)
        try:
            results, performance = create_single_solutions(
                rules_list, buy_threshold, sell_threshold, ticker,
                base_time, now_time, bounds, goal)
            print(results, performance)

            # Update the rules list
            for i, result in enumerate(results):
                rules_list[i]['Percentage'] = result

            # Evaluate the performance over the chosen duration
            start_time = datetime.datetime.strptime(eval_start_time, '%Y-%m-%d')
            end_time = datetime.datetime.strptime(eval_end_time, '%Y-%m-%d')
            values_df = get_roi(ticker, start_time, end_time, rules_list, buy_threshold, sell_threshold)
            strat_roi = values_df['strategic_values'][-1] / values_df['strategic_values'][0]
            simp_roi = values_df['simple_values'][-1] / values_df['simple_values'][0]

            results_list.append([*results, ticker, start_time, end_time, performance, strat_roi, simp_roi])
            print(results_list)
            results_df = pd.DataFrame.from_records(results_list)
            results_df.to_csv(os.path.join(data_dir, "default3-2010-5yrs.csv"))
        except:
            print("Error Downloading Data")


def auto_portfolio_3(eval_start_time, eval_end_time, opt_start_time, opt_end_time, threshold):
    # Get 10 random stocks from the sp500
    data_dir = r'./assets/opt/'
    default_file = os.path.join(data_dir, "default-2017-20yrs")
    rules_list, buy_threshold, sell_threshold, ti, bt, nt, bo, go = create_starting_values()

    default_df = pd.read_csv(default_file, index_col=0)
    default_array = default_df.to_numpy()

    random_list = np.random.randint(low=0, high=len(default_array), size=20)
    random_array = default_array[random_list]
    # random_array = default_array
    print(random_array)

    opt_r5 = [2.0, 1.0, 1.0, 0.5]

    # Update the rules list
    for i, result in enumerate(opt_r5):
        rules_list[i]['Percentage'] = result

    print(rules_list)
    results_list = []
    for chosen in random_array:
        try:
            ticker = chosen[4]
            print(ticker)
            # Evaluate the performance over the chosen duration
            start_time = datetime.datetime.strptime(opt_start_time, '%Y-%m-%d')
            end_time = datetime.datetime.strptime(opt_end_time, '%Y-%m-%d')
            values_df = get_roi(ticker, start_time, end_time, rules_list, buy_threshold, sell_threshold)
            strat_roi = values_df['strategic_values'][-1] / values_df['strategic_values'][0]
            simp_roi = values_df['simple_values'][-1] / values_df['simple_values'][0]
            if (strat_roi > simp_roi*threshold):
                start_time = datetime.datetime.strptime(eval_start_time, '%Y-%m-%d')
                end_time = datetime.datetime.strptime(eval_end_time, '%Y-%m-%d')
                values_df = get_roi(ticker, start_time, end_time, rules_list, buy_threshold, sell_threshold)
                strat_roi = values_df['strategic_values'][-1] / values_df['strategic_values'][0]
                simp_roi = values_df['simple_values'][-1] / values_df['simple_values'][0]

                results_list.append([ticker, start_time, end_time, strat_roi, simp_roi])
        except:
            print("Problem Downloading Data")

    start_time = datetime.datetime.strptime(eval_start_time, '%Y-%m-%d')
    end_time = datetime.datetime.strptime(eval_end_time, '%Y-%m-%d')
    spy_df = get_roi("SPY", start_time, end_time, rules_list, buy_threshold, sell_threshold)
    spy_roi = spy_df['simple_values'][-1] / spy_df['simple_values'][0]

    print(results_list)
    strat_sum = 0
    simp_sum = 0
    for result in results_list:
        print(result[3], result[4])
        if not np.isnan(result[3]) and not np.isnan(result[4]):
            strat_sum+=result[3]
            simp_sum+=result[4]

    print(strat_sum/len(results_list), simp_sum/len(results_list), spy_roi)
    rois = [strat_sum/len(results_list), simp_sum/len(results_list), spy_roi]

    return rois


def run_ap_3():
    roi_list = []
    num_checks = 10
    for i in range(num_checks):
        # Note:  This worked, but only by picking stocks that did poorly in the recession, that then outperformed over the next 5 yrs.
        # The strategic portfolio was also better than the simple portfolio.
        # rois = auto_portfolio_3('2010-01-01', '2015-01-01', '2005-01-01', '2010-01-01', 1.5)
        # Note:  This does not work.  Those same stocks do not perform better over the next 5 yrs.
        rois = auto_portfolio_3('2015-01-01', '2020-01-01', '2005-01-01', '2015-01-01', 1.5)

        # New Plan:  Look for 2005 like shapes.
        # Long slow build up (stock that doubled (or more) over n-6 to n-5
        # Stock that lost > 30% of value in the last year
        # Use OPT-R5 for the next year.

        roi_list.append(rois)
    print(roi_list)
    improved = 0
    for roi in roi_list:
        if roi[0] > roi[2]:
            improved += 1.0
    print(improved / num_checks)
    roi_df = pd.DataFrame.from_records(roi_list)
    print(roi_df)


def run_ap_2():
    data_dir = r'./assets/opt/'
    file = os.path.join(data_dir, "default3-2010-5yrs.csv")

    default_df = pd.read_csv(file, index_col=0)
    default_array = default_df.to_numpy()
    strat_return = 0
    simp_return = 0
    for row in default_array:
        strat_roi = row[8]
        simp_roi = row[9]
        if not np.isnan(strat_roi) and not np.isnan(simp_roi):
            strat_return += strat_roi
            simp_return += simp_roi
            if simp_roi>strat_roi*1.2:
                print(row)
    print(strat_return, simp_return)


def run_ap_1():
    #Note:  Auto PF1 was a failure.  The opt. factors did not help, and the chosen stocks were average
    #AP2 will focus on random stocks, and then work on the optimization of which stocks to pick
    tic = time.time()
    now_time = datetime.datetime.strptime("2018-01-01", '%Y-%m-%d')
    ap = auto_portfolio_1(now_time, 10, 1, 20, 1)
    toc = time.time()
    print(toc-tic)
    print(ap)


if __name__ == "__main__":
    # build_portfolio()
    # run_auto_portfolio()
    # improve_default()
    # run_ap_1()
    # auto_portfolio_2('2010-01-01', '2015-01-01', '2005-01-01', '2010-01-01')
    # run_ap_2()
    # auto_portfolio_3('2010-01-01', '2015-01-01', '2005-01-01', '2010-01-01')
    run_ap_3()

