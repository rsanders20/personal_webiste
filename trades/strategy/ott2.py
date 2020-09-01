import datetime
import os
import time

import numpy
import pandas
from skopt import gp_minimize

from trades.strategy.strategy_calculations import get_historic_roi, get_roi


def make_rule_dict_list():

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
            'bounds':
                [
                    (1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0),
                    (1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0),
                    (1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0),
                    (1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0),
                ],
            'buy_threshold': -2.5,
            'sell_threshold': -2.5,
        },
        {
            'name': 'Strategy 2',
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
            'bounds':
                [
                    (2.0, 2.25, 2.5, 2.75, 3.0, 4.0, 5.0, 6.0, 7.0),
                    (2.0, 2.25, 2.5, 2.75, 3.0, 4.0, 5.0, 6.0, 7.0),
                    (2.0, 2.25, 2.5, 2.75, 3.0, 4.0, 5.0, 6.0, 7.0),
                    (2.0, 2.25, 2.5, 2.75, 3.0, 4.0, 5.0, 6.0, 7.0),
                ],
            'buy_threshold': -2.5,
            'sell_threshold': -2.5,
        },
        {
            'name': 'Strategy 3',
            'rules_list':
                [
                    {'Larger: When?': -10, 'Larger: What?': 'Close', 'Smaller: When?': 0, 'Smaller: What?': 'Close',
                     'Percentage': 1.0, "Weight": -2.0},
                    {'Larger: When?': -2, 'Larger: What?': 'Close', 'Smaller: When?': 0, 'Smaller: What?': 'Close',
                     'Percentage': 1.0, "Weight": -1.0},
                    {'Larger: When?': 0, 'Larger: What?': 'Close', 'Smaller: When?': -3, 'Smaller: What?': 'Close',
                     'Percentage': 1.0, "Weight": -1.0},
                    {'Larger: When?': 0, 'Larger: What?': 'Close', 'Smaller: When?': -5, 'Smaller: What?': 'Close',
                     'Percentage': 1.0, "Weight": -1.0},
                ],
            'bounds':
                [
                    (1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 4.0, 5.0, 6.0, 7.0),
                    (1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 4.0, 5.0, 6.0, 7.0),
                    (1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 4.0, 5.0, 6.0, 7.0),
                    (1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 4.0, 5.0, 6.0, 7.0),
                ],
            'buy_threshold': -2.5,
            'sell_threshold': -2.5,
        },
    ]

    return rules_dict_list


def optimize_roi_and_realizations(opt_function, bounds):
    res = gp_minimize(opt_function,  # the function to minimize
                      bounds,  # the bounds on each dimension of x
                      acq_func="EI",  # the acquisition function
                      n_calls=20,  # the number of evaluations of f
                      n_random_starts=10,  # the number of random initialization points
                      random_state=1234)  # the random seed
    print('completed optimization')
    return res.x, res.fun


def create_opt_function(rule, ticker, start_train, end_train):
    def optimize_weights(weight_list):
        # Modify the rules with the new weights
        for i, weight in enumerate(weight_list):
            rule['rules_list'][i]["Percentage"] = weight

        # Create the function params.
        rules_list = rule['rules_list']
        buy_threshold = rule['buy_threshold']
        sell_threshold = rule['sell_threshold']

        # Get the value df
        values_df = get_roi(
            ticker, start_train, end_train, rules_list, buy_threshold, sell_threshold, 1000)

        # return the strategic roi
        strat_roi = -1 * values_df['strategic_values'][-1] / values_df['strategic_values'][0]
        return strat_roi
    return optimize_weights


def train_model(start_train, end_train, ticker, rule):
    opt_function = create_opt_function(rule, ticker, start_train, end_train)
    bounds = rule['bounds']
    trained_rule, train_performance = optimize_roi_and_realizations(opt_function, bounds)
    return trained_rule


def validate_model(start_validate, end_validate, ticker, rule):
    print("validating")
    is_validated = False

    # Create the function params.
    rules_list = rule['rules_list']
    buy_threshold = rule['buy_threshold']
    sell_threshold = rule['sell_threshold']

    # Get the value df
    values_df = get_roi(ticker, start_validate, end_validate, rules_list, buy_threshold, sell_threshold, 1000)

    # return the strategic roi
    strat_roi = -1 * values_df['strategic_values'][-1] / values_df['strategic_values'][0]
    simple_roi = -1 * values_df['simple_values'][-1] / values_df['simple_values'][0]

    if abs(strat_roi) > abs(simple_roi):
        is_validated = True

    return is_validated


def test_model(start_test, end_test, ticker, rule):
    print("testing")
    # Create the function params.
    rules_list = rule['rules_list']
    buy_threshold = rule['buy_threshold']
    sell_threshold = rule['sell_threshold']

    # Get the value df
    values_df = get_roi(ticker, start_test, end_test, rules_list, buy_threshold, sell_threshold, 1000)

    # return the strategic roi
    strat_roi = -1 * values_df['strategic_values'][-1] / values_df['strategic_values'][0]
    simple_roi = -1 * values_df['simple_values'][-1] / values_df['simple_values'][0]

    return simple_roi, strat_roi


def run_ovt(start_test, end_test, ticker):
    # Import the possible strategies
    rules = make_rule_dict_list()

    # Set up the run parameters
    train_dur = datetime.timedelta(days=365)
    validate_dur = datetime.timedelta(days=60)

    is_validated = False
    for rule in rules:
        print(rule['name'])
        # train the model
        start_train = start_test-train_dur-validate_dur
        end_train = start_test #-validate_dur
        trained_rule = train_model(start_train, end_train, ticker, rule)
        print(trained_rule)

        for i, percentage in enumerate(trained_rule):
            rule['rules_list'][i]['Percentage'] = trained_rule[i]

        # validate the model
        start_validate = start_test-validate_dur
        end_validate = start_test
        is_validated = validate_model(start_validate, end_validate, ticker, rule)

        # test the model
        simple_roi, strat_roi = test_model(start_test, end_test, ticker, rule)
        if is_validated:
            break

    if is_validated:
        roi = strat_roi
        name = rule['name']
    else:
        roi = simple_roi
        name = 'None'

    return {
        'ticker': ticker,
        'start_test': start_test,
        'end_test': end_test,
        'strategy': name,
        'training': trained_rule,
        'simple_roi': simple_roi,
        'roi': roi,
    }


if __name__ == "__main__":
    # Define the time of interest
    start_time = datetime.datetime.strptime('2014-01-01', '%Y-%m-%d')
    end_time = datetime.datetime.now()
    test_dur = datetime.timedelta(days=60)
    ticker = 'TSLA'

    # Run the optimization
    results_list = []
    for i in range(40):
        start_test = start_time+test_dur*i
        end_test = start_test+test_dur
        if end_test > datetime.datetime.now():
            break
        roi = run_ovt(start_test, end_test, ticker)
        results_list.append(roi)

    results_df = pandas.DataFrame.from_records(results_list)
    print(results_df)
    results_df.to_csv("ott2.csv")

