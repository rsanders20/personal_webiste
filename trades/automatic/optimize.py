import time

from skopt import gp_minimize
import numpy as np

np.random.seed(237)
import datetime
from trades.automatic.historical_calculations import get_roi, get_historic_roi
import pandas as pd


def create_starting_values():
    rules_list = [
        {'Larger: When?': -12, 'Larger: What?': 'Close', 'Smaller: When?': 0, 'Smaller: What?': 'Close',
         'Percentage': 1.0, "Weight": -2.0},
        {'Larger: When?': 0, 'Larger: What?': 'Close', 'Smaller: When?': -1, 'Smaller: What?': 'Close',
         'Percentage': 1.0, "Weight": -1.0},
        {'Larger: When?': 0, 'Larger: What?': 'Close', 'Smaller: When?': -3, 'Smaller: What?': 'Close',
         'Percentage': 1.0, "Weight": -1.0},
        {'Larger: When?': 0, 'Larger: What?': 'Close', 'Smaller: When?': -7, 'Smaller: What?': 'Close',
         'Percentage': 1.0, "Weight": -1.0},
    ]

    bounds = []
    for rule in rules_list:
        lower_bound = rule['Percentage']*0.5
        upper_bound = rule['Percentage']*3.0
        bounds.append((lower_bound, upper_bound))

    buy_threshold = -2.5
    sell_threshold = -2.5
    ticker = 'SPY'

    year = 2000
    base_time = datetime.datetime.strptime(f'{year}-01-01', '%Y-%m-%d')
    # now_time = base_time+datetime.timedelta(days=365*10)
    now_time = datetime.datetime.now()
    # bounds = [(0.5, 3.0), (0.5, 1.5), (0.5, 1.5), (0.5, 1.5)]
    goal= "realizations"

    return rules_list, buy_threshold, sell_threshold, ticker, base_time, now_time, bounds, goal


def create_single_solutions(rules_list, buy_threshold, sell_threshold, ticker, base_time, now_time, bounds, goal):
    optimize_weights_function = create_optimize_function(rules_list, buy_threshold, sell_threshold, ticker,
                                                         base_time, now_time, goal)
    results = optimize_roi(optimize_weights_function, bounds)
    print(results)
    return results


def create_optimize_function(rules_list, buy_threshold, sell_threshold, ticker, base_time, now_time, goal):
    if goal == "roi":
        def optimize_weights(weight_list):
            for i, weight in enumerate(weight_list):
                rules_list[i]["Percentage"] = weight

            values_df = get_roi(ticker, base_time, now_time, rules_list, buy_threshold, sell_threshold)
            roi = -1 * values_df['strategic_values'][-1] / values_df['strategic_values'][0]
            print(weight_list, roi)
            return roi

        return optimize_weights

    elif goal == "realizations":
        def optimize_weights(weight_list):
            for i, weight in enumerate(weight_list):
                rules_list[i]["Percentage"] = weight

            fig, score_string, score_color, opt_score = get_historic_roi(
                ticker, base_time, now_time, rules_list, buy_threshold, sell_threshold)
            print(weight_list, opt_score)
            return opt_score

        return optimize_weights


def optimize_roi(optimize_weights_function, bounds):
    tic = time.time()
    res = gp_minimize(optimize_weights_function,  # the function to minimize
                      bounds,  # the bounds on each dimension of x
                      acq_func="EI",  # the acquisition function
                      n_calls=50,  # the number of evaluations of f
                      n_random_starts=15,  # the number of random initialization points
                      random_state=1234)  # the random seed

    # fig = plot_evaluations(res, bins=20)
    # plot_objective(res, n_samples=50)
    # plt.savefig("test_objective.png")
    # plot_evaluations(res)
    # plt.savefig("test_evaluations.png")
    toc=time.time()
    # results_dict = {'res_x1': res.x[0], 'res_x2': res.x[1], 'res_x3': res.x[2], 'res_x4': res.x[3], 'res_fun': res.fun}
    return res.x


if __name__ == "__main__":
    #TODO:
    # Instead, add in some more signals to optimize.
    # Run this optimization on all 500 stocks 2000-2010
    # Can I use the last years performance to adjust portfolio holding?
    # Start Jan 2013, end Jan 2015
    # Look at SPY to see how long "winning" and "losing" go (generally, there are years where it doesn't work great).
    # Strategy:  For each stock at the start of the year, run 10 yrs of last data to build optimized factors using the realizations method.
    # Select the 10 stocks that had the best return over the last year.  Sum the final ROI for all stocks.
    # Each year, re-generate the factors for all stocks, and repeat.

    rules_list, buy_threshold, sell_threshold, ticker, base_time, now_time, bounds, goal = create_starting_values()
    create_single_solutions(rules_list, buy_threshold, sell_threshold, ticker, base_time, now_time, bounds, goal)

    # create_yearly_solutions(rules_list, buy_threshold, sell_threshold, ticker)
    # run_yearly_solutions(rules_list, buy_threshold, sell_threshold, ticker)
    # test_data_speed()
    # optimize_roi()

    # timing_function()
    # test_optimize()
    # test_optimize_6D()
