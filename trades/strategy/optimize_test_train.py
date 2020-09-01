import datetime
import os
import time

import numpy
import pandas
from skopt import gp_minimize

from trades.strategy.strategy_calculations import get_historic_roi, get_roi


def optimize_roi_and_realizations(opt_function, bounds):
    res = gp_minimize(opt_function,  # the function to minimize
                      bounds,  # the bounds on each dimension of x
                      acq_func="EI",  # the acquisition function
                      n_calls=40,  # the number of evaluations of f
                      n_random_starts=20,  # the number of random initialization points
                      random_state=1234)  # the random seed
    print('completed optimization')
    return res.x, res.fun


def create_weighted_solution(start_train, train_dur, rules_dict_list, target, chosen_rule):
    if target=='percentage':
        opt_function = create_weighted_function(rules_dict_list[chosen_rule]['rules_list'],
                                                rules_dict_list[chosen_rule]['buy_threshold'],
                                                rules_dict_list[chosen_rule]['sell_threshold'],
                                                rules_dict_list[chosen_rule]['ticker'],
                                                start_train,
                                                start_train+train_dur,
                                                target)
        train_results, train_performance = optimize_roi_and_realizations(opt_function, rules_dict_list[chosen_rule]['bounds'])
        return train_results, chosen_rule
    elif target=='timing':
        opt_function = create_weighted_function(rules_dict_list[chosen_rule]['rules_list'],
                                                rules_dict_list[chosen_rule]['buy_threshold'],
                                                rules_dict_list[chosen_rule]['sell_threshold'],
                                                rules_dict_list[chosen_rule]['ticker'],
                                                start_train,
                                                start_train+train_dur,
                                                target)
        train_results, train_performance = optimize_roi_and_realizations(opt_function, rules_dict_list[chosen_rule]['timing_bounds'])
        return train_results, chosen_rule


def test_weighted_solution(start_test, test_dur, rules_dict_list, train_results, chosen_rule, target):
    starting_value = 1000

    # if train_results[4] > 1.4:
    #     print("using alternate strategy")
    #     chosen_rule = 3
    #     train_results = [rule['Percentage'] for rule in rules_dict_list[chosen_rule]['rules_list']]
        # opt_function = create_weighted_function(rules_dict_list[chosen_rule]['rules_list'],
        #                                         rules_dict_list[chosen_rule]['buy_threshold'],
        #                                         rules_dict_list[chosen_rule]['sell_threshold'],
        #                                         rules_dict_list[chosen_rule]['ticker'],
        #                                         start_train,
        #                                         start_train + train_dur)
        # train_results, train_performance = optimize_roi_and_realizations(opt_function, rules_dict_list[1]['bounds'])
        # print(train_results)

    if target=='percentage':
        for i, weight in enumerate(train_results):
            rules_dict_list[chosen_rule]['rules_list'][i]["Percentage"] = weight
    else:
        for i, timing in enumerate(train_results):
            if i <= 3:
                rules_dict_list[chosen_rule]['rules_list'][i]["Larger: When?"] = timing
            elif i<=7:
                rules_dict_list[chosen_rule]['rules_list'][i-4]["Smaller: When?"] = timing
            else:
                rules_dict_list[chosen_rule]['rules_list'][i-8]['Percentage'] = timing

    values_df = get_roi(rules_dict_list[chosen_rule]['ticker'], start_test, start_test+test_dur,
                        rules_dict_list[chosen_rule]['rules_list'],
                        rules_dict_list[chosen_rule]['buy_threshold'],
                        rules_dict_list[chosen_rule]['sell_threshold'],
                        starting_value)

    strat_roi = -1 * values_df['strategic_values'][-1] / values_df['strategic_values'][0]
    simple_roi = -1 * values_df['simple_values'][-1] / values_df['simple_values'][0]

    return simple_roi, strat_roi


def create_weighted_function(rules_list, buy_threshold, sell_threshold, ticker, base_time, now_time, target):
    if target == 'percentage':
        def optimize_weights(weight_list):
            for i, weight in enumerate(weight_list):
                rules_list[i]["Percentage"] = weight

            values_df = get_roi(
                ticker, base_time, now_time, rules_list, buy_threshold, sell_threshold, 1000)
            strat_roi = -1 * values_df['strategic_values'][-1] / values_df['strategic_values'][0]
            return strat_roi
    elif target == 'timing':
        def optimize_weights(time_list):
            for i, timing in enumerate(time_list):
                if i<=3:
                    rules_list[i]["Larger: When?"] = timing
                elif i<=7:
                    rules_list[i-4]["Smaller: When?"] = timing
                else:
                    rules_list[i-8]['Percentage'] = timing
            values_df = get_roi(
                ticker, base_time, now_time, rules_list, buy_threshold, sell_threshold, 1000)
            strat_roi = -1 * values_df['strategic_values'][-1] / values_df['strategic_values'][0]
            return strat_roi

    return optimize_weights


def get_volatility(test_start, test_dur, train_dur, rules_dict_list, chosen_rule):
    # Calculate volatility for every 50 day period, and save start and end times (100)
    values_df = get_roi(
        rules_dict_list[chosen_rule]['ticker'],
        test_start-train_dur, test_start-test_dur*2,
        rules_dict_list[chosen_rule]['rules_list'],
        rules_dict_list[chosen_rule]['buy_threshold'],
        rules_dict_list[chosen_rule]['sell_threshold'],
        1000)

    volatility_list = []
    last_day = test_start-train_dur
    for day in values_df.index:
        if (day-last_day).days > test_dur.days:
            start_time = day - test_dur
            end_time = day
            if values_df.index[-1] > end_time:
                interval_df = values_df.iloc[(values_df.index >= start_time) & (values_df.index <= end_time)]
                volatility = interval_df.Dif.std()
                volatility_list.append({'start_time': start_time,
                                        'end_time': end_time,
                                        'volatility': volatility})
                last_day = day

    volatility_df = pandas.DataFrame.from_records(volatility_list)

    # Calculate the volatility of the last 50 days
    recent_values_df = get_roi(
        rules_dict_list[chosen_rule]['ticker'],
        test_start-test_dur, test_start,
        rules_dict_list[chosen_rule]['rules_list'],
        rules_dict_list[chosen_rule]['buy_threshold'],
        rules_dict_list[chosen_rule]['sell_threshold'],
        1000)
    recent_volatility = recent_values_df.Dif.std()
    # Compare volatility, and select the 10 closest to the current volatility
    df_sort = volatility_df.iloc[(volatility_df['volatility']-recent_volatility).abs().argsort()[:1]]
    array_sort = df_sort.to_numpy()
    chosen_end_time = array_sort[0][1]
    # Take the 50 days after each time identified, and concatenate them together
        # shortcut:  only take the closest one
    print(chosen_end_time, chosen_end_time+test_dur)
    if chosen_end_time+test_dur >= test_start:
        print("Invalid data selected")
        return [], 0
    train_results, chosen_rule = create_weighted_solution(chosen_end_time-test_dur, test_dur, rules_dict_list, 'timing', chosen_rule)

    # Fit the chosen model to the time selected
    # return the fitted parameters
    return train_results, chosen_rule


def run_training_testing():

    rules_dict_list = [
        {
            'name': 'Strategy 1',
            'rules_list':
                [
                    {'Larger: When?': -10, 'Larger: What?': 'Close', 'Smaller: When?': 0, 'Smaller: What?': 'Close',
                     'Percentage': 1.0, "Weight": -2.0},
                    {'Larger: When?': 0, 'Larger: What?': 'Close', 'Smaller: When?': -1, 'Smaller: What?': 'Close',
                     'Percentage': 1.0, "Weight": -1.0},
                    {'Larger: When?': 0, 'Larger: What?': 'Close', 'Smaller: When?': -3, 'Smaller: What?': 'Close',
                     'Percentage': 1.0, "Weight": -1.0},
                    {'Larger: When?': 0, 'Larger: What?': 'Close', 'Smaller: When?': -5, 'Smaller: What?': 'Close',
                     'Percentage': 1.0, "Weight": -1.0},
                ],
            'timing_bounds':
                [
                    (-15, -14, -13, -12, -11, -10),
                    # (-1, 0),
                    # (-2, -1, 0),
                    (-4, -3, -2, -1, 0),
                    (-1, 0),
                    (-1, 0),

                    (-1, 0),
                    (-2, -1, 0),
                    (-4, -3),
                    (-7, -6, -5),

                    (1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0),
                    (1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0),
                    (1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0),
                    (1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0),
                ],
            'bounds':
                [
                    (1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 4.0, 5.0, 6.0, 7.0),
                    (1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 4.0, 5.0, 6.0, 7.0),
                    (1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 4.0, 5.0, 6.0, 7.0),
                    (1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 4.0, 5.0, 6.0, 7.0),
                ],
            'buy_threshold': -2.5,
            'sell_threshold': -2.5,
            'ticker': ''
        },
        {
            'name': 'Strategy 2',
            'rules_list':
                [

                    {'Larger: When?': -10, 'Larger: What?': 'Close', 'Smaller: When?': 0, 'Smaller: What?': 'Close',
                     'Percentage': 2.0, "Weight": -2.0},
                    {'Larger: When?': 0, 'Larger: What?': 'Close', 'Smaller: When?': -1, 'Smaller: What?': 'Close',
                     'Percentage': 2.0, "Weight": -1.0},
                    {'Larger: When?': 0, 'Larger: What?': 'Close', 'Smaller: When?': -5, 'Smaller: What?': 'Close',
                     'Percentage': 1.0, "Weight": -1.0},
                ],
            'bounds':
                [
                    (0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0),
                    (0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0),
                    (0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0)

                ],
            'buy_threshold': -2.5,
            'sell_threshold': -2.5,
            'ticker': 'BA'
        },
        {
            'name': 'Strategy 3',
            'rules_list':
                [
                    {'Larger: When?': -1, 'Larger: What?': 'Close', 'Smaller: When?': 0, 'Smaller: What?': 'Close',
                     'Percentage': 3.0, "Weight": -1.0},
                    {'Larger: When?': 0, 'Larger: What?': 'Close', 'Smaller: When?': -1, 'Smaller: What?': 'Close',
                     'Percentage': 0.25, "Weight": 1.0},
                ],
            'bounds':
                [
                    (0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0),
                    (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
                ],
            'buy_threshold': 0.5,
            'sell_threshold': -0.5,
            'ticker': 'BA'
        },
        {
            'name': 'Strategy 4',
            'rules_list':
                [
                    {'Larger: When?': -10, 'Larger: What?': 'Close', 'Smaller: When?': 0, 'Smaller: What?': 'Close',
                     'Percentage': 5.0, "Weight": -3.0},
                ],
            'bounds':
                [
                    (0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0),
                ],
            'buy_threshold': -2.5,
            'sell_threshold': -2.5,
            'ticker': 'BA'
        },
        {
            'name': 'Strategy 5',
            'rules_list':
                [
                    {'Larger: When?': -10, 'Larger: What?': 'Close', 'Smaller: When?': 0, 'Smaller: What?': 'Close',
                     'Percentage': 1.0, "Weight": -2.0},
                    {'Larger: When?': 0, 'Larger: What?': 'Close', 'Smaller: When?': -1, 'Smaller: What?': 'Close',
                     'Percentage': 1.0, "Weight": -1.0},
                    {'Larger: When?': 0, 'Larger: What?': 'Close', 'Smaller: When?': -3, 'Smaller: What?': 'Close',
                     'Percentage': 1.0, "Weight": -1.0},
                    {'Larger: When?': 0, 'Larger: What?': 'Close', 'Smaller: When?': -5, 'Smaller: What?': 'Close',
                     'Percentage': 1.0, "Weight": -1.0},
                    {'Larger: When?': -10, 'Larger: What?': 'Close', 'Smaller: When?': -5, 'Smaller: What?': 'Close',
                     'Percentage': 1.0, "Weight": -1.0},

                ],
            'bounds':
                [
                    (1.75, 2.0, 2.25, 2.5, 2.75, 3.0),
                    (1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0),
                    (1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0),
                    (1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0),
                    (1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0)
                ],
            'buy_threshold': -3.5,
            'sell_threshold': -3.5,
            'ticker': 'MSFT'
        },
        {
            'name': 'Strategy 6',
            'rules_list':
                [
                    {'Larger: When?': -10, 'Larger: What?': 'Close', 'Smaller: When?': 0, 'Smaller: What?': 'Close',
                     'Percentage': 1.25, "Weight": -2.0},
                    {'Larger: When?': 0, 'Larger: What?': 'Close', 'Smaller: When?': -1, 'Smaller: What?': 'Close',
                     'Percentage': 1.25, "Weight": -1.0},
                    {'Larger: When?': 0, 'Larger: What?': 'Close', 'Smaller: When?': -3, 'Smaller: What?': 'Close',
                     'Percentage': 1.25, "Weight": -1.0},
                    {'Larger: When?': 0, 'Larger: What?': 'Close', 'Smaller: When?': -5, 'Smaller: What?': 'Close',
                     'Percentage': 1.25, "Weight": -1.0},
                    {'Larger: When?': -10, 'Larger: What?': 'Close', 'Smaller: When?': -5, 'Smaller: What?': 'Close',
                     'Percentage': 3.0, "Weight": -1.0},
                    {'Larger: When?': -15, 'Larger: What?': 'Close', 'Smaller: When?': -10, 'Smaller: What?': 'Close',
                     'Percentage': 3.0, "Weight": -1.0},

                ],
            'timing_bounds':
                [
                    (-35, -30, -25, -20, -15, -14, -13, -12, -11, -10),
                    (-1, 0),
                    (-1, 0),
                    (-1, 0),
                    (-15, -14, -13, -12, -11, -10),
                    (-35, -30, -25, -20, -19, -18, -17, -16, -15),

                    (-1, 0),
                    (-2, -1),
                    (-4, -3),
                    (-7, -6, -5),
                    (-9, -8, -7, -6, -5, -4, -3, -2, -1, 0),
                    (-14, -13, -12, -11, -10, -8, -7, -6, -5, -4, -3, -2, -1, 0),

                    (1.0, 1.5, 2.0, 2.5, 3.0),
                    (1.0, 1.5, 2.0, 2.5, 3.0),
                    (1.0, 1.5, 2.0, 2.5, 3.0),
                    (1.0, 1.5, 2.0, 2.5, 3.0),
                    (1.0, 1.5, 2.0, 2.5, 3.0),
                    (1.0, 1.5, 2.0, 2.5, 3.0),
                ],
            'bounds':
                [
                    (1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0),
                    (1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0),
                    (1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0),
                    (1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0),
                    (1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0),
                    (1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0),
                ],
            'buy_threshold': -3.5,
            'sell_threshold': -3.5,
            'ticker': ''
        },
        {
            'name': 'Strategy 7',
            'rules_list':
                [
                    {'Larger: When?': -10, 'Larger: What?': 'Close', 'Smaller: When?': 0, 'Smaller: What?': 'Close',
                     'Percentage': 1.25, "Weight": -1.0},
                    {'Larger: When?': 0, 'Larger: What?': 'Close', 'Smaller: When?': -1, 'Smaller: What?': 'Close',
                     'Percentage': 1.25, "Weight": -1.0},
                    {'Larger: When?': 0, 'Larger: What?': 'Close', 'Smaller: When?': -3, 'Smaller: What?': 'Close',
                     'Percentage': 1.25, "Weight": -1.0},
                    {'Larger: When?': 0, 'Larger: What?': 'Close', 'Smaller: When?': -5, 'Smaller: What?': 'Close',
                     'Percentage': 1.25, "Weight": -1.0},
                    {'Larger: When?': -10, 'Larger: What?': 'Close', 'Smaller: When?': -5, 'Smaller: What?': 'Close',
                     'Percentage': 3.0, "Weight": -1.0},
                    {'Larger: When?': -15, 'Larger: What?': 'Close', 'Smaller: When?': -10, 'Smaller: What?': 'Close',
                     'Percentage': 3.0, "Weight": -1.0},

                ],
            'timing_bounds':
                [
                    (-15, -14, -13, -12, -11, -10),
                    (-1, 0),
                    (-1, 0),
                    (-1, 0),
                    (-15, -14, -13, -12, -11, -10),
                    (-20, -19, -18, -17, -16, -15),

                    (-1, 0),
                    (-2, -1),
                    (-4, -3),
                    (-7, -6, -5),
                    (-5, -4, -3, -2, -1, 0),
                    (-10, -8, -7, -6, -5, -4, -3, -2, -1, 0),

                    # (-1, 0),
                    # (-2, -1),
                    # (-4, -3),
                    # (-6, -5),
                    # (-5, -4, -3),
                    # (-10, -9, -8),


                    (1.0, 1.5, 2.0, 2.5, 3.0),
                    (1.0, 1.5, 2.0, 2.5, 3.0),
                    (1.0, 1.5, 2.0, 2.5, 3.0),
                    (1.0, 1.5, 2.0, 2.5, 3.0),
                    (1.0, 1.5, 2.0, 2.5, 3.0),
                    (1.0, 1.5, 2.0, 2.5, 3.0),
                ],
            'bounds':
                [
                    (1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0),
                    (1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0),
                    (1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0),
                    (1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0),
                    (1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0),
                    (1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0),
                ],
            'buy_threshold': -3.5,
            'sell_threshold': -3.5,
            'ticker': ''
        },
    ]

    chosen_rule = 0
    results = []
    for ticker in ['BA', 'CVX', 'PFE', 'MCD', 'DIS', 'MSFT', 'SPY', 'GOOG', 'AMZN', 'TSLA']:
        rules_dict_list[chosen_rule]['ticker'] = ticker

        start_train = datetime.datetime.strptime('1994-01-01', '%Y-%m-%d')
        train_dur = datetime.timedelta(days=365*26.5)
        end_train = start_train+train_dur

        start_test = start_train+train_dur
        end_test = datetime.datetime.now()
        test_dur = end_test-start_test

        print(start_train)
        train_results, chosen_rule = create_weighted_solution(start_train, train_dur, rules_dict_list, 'timing', chosen_rule)
        # train_results, chosen_rule = create_weighted_solution(start_train, datetime.datetime.now()-start_train, rules_dict_list, 'timing', chosen_rule)
        print(train_results)
        for i, timing in enumerate(train_results):
            if i <= 3:
                rules_dict_list[chosen_rule]['rules_list'][i]["Larger: When?"] = timing
            elif i <= 7:
                rules_dict_list[chosen_rule]['rules_list'][i - 4]["Smaller: When?"] = timing
            else:
                rules_dict_list[chosen_rule]['rules_list'][i - 8]['Percentage'] = timing

        simple_roi, strat_roi = test_weighted_solution(start_test, test_dur, rules_dict_list, train_results, chosen_rule, 'timing')
        # simple_roi, strat_roi = test_weighted_solution(datetime.datetime.now()-datetime.timedelta(days=365),
        #                                                datetime.timedelta(days=365),
        #                                                rules_dict_list, train_results, chosen_rule, 'timing')

        print(train_results)
        print(start_test, simple_roi, strat_roi)
        results.append({
            'ticker': ticker,
            'start_train': start_train,
            'end_train': end_train,
            'start_test': start_test,
            'end_test': end_test,
            'training': train_results,
            'simple_roi': simple_roi,
            'strat_roi': strat_roi,
        })

    results_df = pandas.DataFrame.from_records(results)
    print(results_df)
    results_df.to_csv("testing-07-02-2020-10.csv")
    kddk
    # ticker = 'BA'
    # # test_start = datetime.datetime.strptime(f'{2014}-01-01', '%Y-%m-%d')
    # test_start = datetime.datetime.strptime("2020-04-25", '%Y-%m-%d')
    # test_dur = datetime.timedelta(days=50)
    # train_dur = datetime.timedelta(days=365*20)
    # initial_rule = 6
    # for j, rule_dict in enumerate(rules_dict_list):
    #     rules_dict_list[j]['ticker'] = ticker
    # train_results, chosen_rule = get_volatility(test_start, test_dur, train_dur, rules_dict_list, initial_rule)
    # print(test_start, test_start+test_dur)
    # print(train_results, chosen_rule)

    for ticker in ['BA', 'CVX', 'PFE', 'MCD', 'DIS', 'MSFT']:
        results = []
        for i in range(100):
            try:
                # ticker = 'MCD'
                first_test_start = datetime.datetime.strptime(f'{2014}-01-01', '%Y-%m-%d')
                test_dur = datetime.timedelta(days=60)
                test_start = first_test_start + test_dur*i
                train_dur = datetime.timedelta(days=365 * 20)
                initial_rule = 0

                for j, rule_dict in enumerate(rules_dict_list):
                    rules_dict_list[j]['ticker'] = ticker

                train_results, chosen_rule = get_volatility(test_start, test_dur, train_dur, rules_dict_list, initial_rule)
                # train_results, chosen_rule = create_weighted_solution(start_train, train_dur, rules_dict_list, 'timing')

                if test_start+test_dur > datetime.datetime.now():
                    break

                simple_roi, strat_roi = test_weighted_solution(
                    test_start, test_dur, rules_dict_list, train_results, chosen_rule, 'timing')

                print(test_start, train_results, simple_roi, strat_roi)

                results.append({
                    'start': test_start,
                    'end': test_start+test_dur,
                    'factors': train_results,
                    'simple_roi': simple_roi,
                    'strat_roi': strat_roi,
                })
                time.sleep(1)
            except:
                print("Nan Detected")

        results_df = pandas.DataFrame.from_records(results)
        print(results_df)
        results_df.to_csv(f"ott_S{chosen_rule}_{ticker}_{test_start.year}.csv")
        time.sleep(1)


if __name__ == "__main__":
    run_training_testing()
