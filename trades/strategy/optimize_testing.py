import os
import time

from skopt import gp_minimize
from skopt.plots import plot_convergence, plot_evaluations, plot_objective
from skopt.benchmarks import branin, hart6
from skopt.acquisition import gaussian_ei
import plotly.express as px
import numpy as np

from trades.strategy import strategy_calculations
from trades.strategy.optimize import create_optimize_function, optimize_roi
from trades.manual import stock_calculations

np.random.seed(237)
import datetime
import matplotlib.pyplot as plt
from trades.strategy.strategy_calculations import get_roi, get_historic_roi
import pandas as pd
from functools import partial
import cProfile
import pstats


def f(x, noise_level=0.1):
    return np.sin(5 * x[0]) * (1 - np.tanh(x[0] ** 2))\
           + np.random.randn() * noise_level


def test_optimize():
    noise_level = 0.1
    plt.rcParams["figure.figsize"] = (8, 14)

    x = np.linspace(-2, 2, 400).reshape(-1, 1)
    fx = np.array([f(x_i, noise_level=0.0) for x_i in x])

    res = gp_minimize(f,  # the function to minimize
                      [(-2.0, 2.0)],  # the bounds on each dimension of x
                      acq_func="EI",  # the acquisition function
                      n_calls=15,  # the number of evaluations of f
                      n_random_starts=5,  # the number of random initialization points
                      noise=0.1 ** 2,  # the noise level (optional)
                      random_state=1234)  # the random seed
    x_gp = res.space.transform(x.tolist())

    for n_iter in range(5):
        gp = res.models[n_iter]
        curr_x_iters = res.x_iters[:5 + n_iter]
        curr_func_vals = res.func_vals[:5 + n_iter]

        # Plot true function.
        plt.subplot(5, 2, 2 * n_iter + 1)
        plt.plot(x, fx, "r--", label="True (unknown)")
        plt.fill(np.concatenate([x, x[::-1]]),
                 np.concatenate([fx - 1.9600 * noise_level,
                                 fx[::-1] + 1.9600 * noise_level]),
                 alpha=.2, fc="r", ec="None")

        # Plot GP(x) + contours
        y_pred, sigma = gp.predict(x_gp, return_std=True)
        plt.plot(x, y_pred, "g--", label=r"$\mu_{GP}(x)$")
        plt.fill(np.concatenate([x, x[::-1]]),
                 np.concatenate([y_pred - 1.9600 * sigma,
                                 (y_pred + 1.9600 * sigma)[::-1]]),
                 alpha=.2, fc="g", ec="None")

        # Plot sampled points
        plt.plot(curr_x_iters, curr_func_vals,
                 "r.", markersize=8, label="Observations")

        # Adjust plot layout
        plt.grid()

        if n_iter == 0:
            plt.legend(loc="best", prop={'size': 6}, numpoints=1)

        if n_iter != 4:
            plt.tick_params(axis='x', which='both', bottom='off',
                            top='off', labelbottom='off')

        # Plot EI(x)
        plt.subplot(5, 2, 2 * n_iter + 2)
        acq = gaussian_ei(x_gp, gp, y_opt=np.min(curr_func_vals))
        plt.plot(x, acq, "b", label="EI(x)")
        plt.fill_between(x.ravel(), -2.0, acq.ravel(), alpha=0.3, color='blue')

        next_x = res.x_iters[5 + n_iter]
        next_acq = gaussian_ei(res.space.transform([next_x]), gp,
                               y_opt=np.min(curr_func_vals))
        plt.plot(next_x, next_acq, "bo", markersize=6, label="Next query point")

        # Adjust plot layout
        plt.ylim(0, 0.1)
        plt.grid()

        if n_iter == 0:
            plt.legend(loc="best", prop={'size': 6}, numpoints=1)

        if n_iter != 4:
            plt.tick_params(axis='x', which='both', bottom='off',
                            top='off', labelbottom='off')

    plt.savefig("test.png")


def test_optimize_6d():
    x = np.linspace(-2, 2, 400).reshape(-1, 1)
    fx = np.array([f(x_i, noise_level=0.0) for x_i in x])
    bounds = [(0., 1.)] * 6
    res = gp_minimize(hart6,  # the function to minimize
                      bounds,  # the bounds on each dimension of x
                      acq_func="EI",  # the acquisition function
                      n_calls=100,  # the number of evaluations of f
                      n_random_starts=10,  # the number of random initialization points
                      random_state=1234)  # the random seed

    # fig = plot_evaluations(res, bins=20)
    fig = plot_objective(res, n_samples=50)
    plt.savefig("test.png")


def create_many_solutions(rules_list, buy_threshold, sell_threshold, ticker):
    results_list = []
    first_year = 2000
    for i in range(20):
        year = first_year+i
        base_time = datetime.datetime.strptime(f'{year}-01-01', '%Y-%m-%d')
        now_time = base_time+datetime.timedelta(days=365)
        optimize_weights_function = create_optimize_function(rules_list, buy_threshold, sell_threshold, ticker, base_time, now_time, "roi")
        yearly_results = optimize_roi(optimize_weights_function, base_time)
        print(base_time)
        results_list.append(yearly_results)

    data_dir = r'./assets/opt/'
    file = os.path.join(data_dir, ticker+".csv")
    results_df = pd.DataFrame.from_records(results_list)
    print(results_df)
    # results_df.to_csv(file)


def test_multiple_solutions(rules_list, buy_threshold, sell_threshold, ticker):
    yearly_solutions = []
    data_dir = r'./assets/opt/'
    file = os.path.join(data_dir, ticker+".csv")
    results_df = pd.read_csv(file, index_col="index")
    results_array = results_df.to_numpy()
    for result in results_array:
        start_time = datetime.datetime.strptime(result[5], '%Y-%m-%d')+datetime.timedelta(days=365)
        end_time = start_time+datetime.timedelta(days=365)
        for i, weight in enumerate(result[0:4]):
            rules_list[i]["Percentage"] = weight
        values_df = get_roi(ticker, start_time, end_time, rules_list, buy_threshold, sell_threshold)

        simple_roi = values_df['simple_values'].iloc[-1] / values_df['simple_values'][0]
        strategic_roi = values_df['strategic_values'].iloc[-1] / values_df['strategic_values'].iloc[0]
        improvement = strategic_roi-simple_roi
        result_dict = {
            "training_start":datetime.datetime.strptime(result[5], '%Y-%m-%d'),
            "test_start": start_time,
            "w1": result[0],
            "w2": result[1],
            "w3": result[2],
            "w4": result[3],
            "training_roi": result[4],
            "test_simple_roi": simple_roi,
            "test_strategic_roi": strategic_roi,
            "improvement": improvement}
        yearly_solutions.append(result_dict)

    yearly_df = pd.DataFrame.from_records(yearly_solutions)
    print(yearly_df)
    yearly_df.to_csv(file.replace(".csv", "_yr.csv"))


def test_data_speed():
    now_time = datetime.datetime.now()
    base_time = now_time-datetime.timedelta(days=100)
    tic = time.time()
    df1 = strategy_calculations.get_data(["SPY"], base_time, now_time)
    print(df1.head())
    toc = time.time()
    print(f"With existing data: {toc-tic}")

    tic=time.time()
    df2 = stock_calculations.get_yahoo_stock_data(["SPY"], base_time, now_time)
    print(df2.head())
    toc = time.time()
    print(f"With downloaded data: {toc-tic}")