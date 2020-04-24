import datetime
import os

from trades.manual import stock_calculations
import matplotlib.pyplot as plt
import pandas as pd
from trades.models import Portfolio, Dollar
from trades.manual.stock_calculations import flatten_df, make_np_date
import plotly.express as px
import pathlib
import numpy as np
import scipy


def make_simple_portfolio(all_weeks, spy_full_df):
    weekly_value = []

    for i, week in enumerate(all_weeks):
        if i ==0:
            weekly_value.append([100])
        else:
            week_length = len(weekly_value[0])
            start_time = make_np_date(week-datetime.timedelta(days=7))
            end_time = make_np_date(week)
            week_data = spy_full_df.loc[(spy_full_df.index.values <= end_time) & (spy_full_df.index.values >= start_time)]
            starting_close = week_data['Close'][0]
            ending_close = week_data['Close'][-1]
            week_roi = ending_close/starting_close
            new_week = [0 for i in range(week_length)]
            new_week.append(100)
            for week_value in weekly_value:
                week_value.append(week_value[-1]*week_roi)
            weekly_value.append(new_week)

    weekly_array = np.array(weekly_value)
    weekly_df = pd.DataFrame.from_records(weekly_array)
    weekly_df.index = all_weeks
    weekly_df.columns = all_weeks

    return weekly_df


def roi_indicator(spy_full_df, week, n_days):
    start_time = make_np_date(week - datetime.timedelta(days=n_days))
    if start_time < make_np_date(spy_full_df.index[0]):
        start_time = make_np_date(spy_full_df.index[0])

    end_time = make_np_date(week)

    week_data = spy_full_df.loc[(spy_full_df.index.values <= end_time) & (spy_full_df.index.values >= start_time)]
    starting_close = week_data['Close'][0]
    ending_close = week_data['Close'][-1]
    week_roi = ending_close / starting_close

    # ROI Indicator
    if week_roi > 1.0:
        indicator = True
    else:
        indicator = False

    return indicator


def make_strategic_portfolio(all_weeks, spy_full_df, buy_or_sell, positive_rule, and_or, negative_rule):
    weekly_value = []
    weekly_choice = []

    for i, week in enumerate(all_weeks):
        if i ==0:
            weekly_value.append([100])
            weekly_choice.append(['invest'])
        else:
            week_length = len(weekly_value[0])
            start_time = make_np_date(week-datetime.timedelta(days=7))
            end_time = make_np_date(week)
            week_data = spy_full_df.loc[(spy_full_df.index.values <= end_time) & (spy_full_df.index.values >= start_time)]
            starting_close = week_data['Close'][0]
            ending_close = week_data['Close'][-1]
            week_roi = ending_close/starting_close

            new_week = [0 for i in range(week_length)]
            new_week_choice = ['nothing' for i in range(week_length)]

            # roi_pos_4 = roi_indicator(spy_full_df, week, 28)
            # roi_pos_3 = roi_indicator(spy_full_df, week, 21)
            # roi_pos_2 = roi_indicator(spy_full_df, week, 14)
            # roi_pos_1 = roi_indicator(spy_full_df, week, 7)
            # roi_pos_list = [roi_pos_1, roi_pos_2, roi_pos_3, roi_pos_4]

            roi_pos = roi_indicator(spy_full_df, week, 7*positive_rule)
            roi_neg = roi_indicator(spy_full_df, week, 7*negative_rule)

            # If the current week was positive, do nothing with the new week
            # update the existing weeks, and sell
            #if roi_pos_1 and not roi_pos_3:
            if buy_or_sell == "sell":
                if and_or == "and":
                    if roi_pos and not roi_neg:
                        action = "sell"
                    else:
                        action = "buy"
                else:
                    if roi_pos or not roi_neg:
                        action = "sell"
                    else:
                        action = "buy"
            else:
                if and_or == "and":
                    if roi_pos and not roi_neg:
                        action = "buy"
                    else:
                        action = "sell"
                else:
                    if roi_pos or not roi_neg:
                        action = "buy"
                    else:
                        action = "sell"

            if action=="sell":
                new_week.append(100)
                new_week_choice.append('nothing')

                for i, week_value in enumerate(weekly_value):
                    if weekly_choice[i][-1] == 'invest':
                        week_value.append(week_value[-1] * week_roi)
                    elif weekly_choice[i][-1] == 'nothing':
                        week_value.append(week_value[-1])
                    elif weekly_choice[i][-1] == 'sell':
                        week_value.append(week_value[-1])

                for week_choice in weekly_choice:
                    week_choice.append('sell')

                weekly_value.append(new_week)
                weekly_choice.append(new_week_choice)

            # If the current week was negative, invest the new week
            # update the existing weeks, and stay invested
            else:
                new_week.append(100)
                new_week_choice.append('invest')
                for j, week_value in enumerate(weekly_value):
                    if weekly_choice[j][-1] == 'invest':
                        week_value.append(week_value[-1] * week_roi)
                    elif weekly_choice[j][-1] == 'nothing':
                        week_value.append(week_value[-1])
                    elif weekly_choice[j][-1] == 'sell':
                        week_value.append(week_value[-1])

                for week_choice in weekly_choice:
                    week_choice.append('invest')

                weekly_value.append(new_week)
                weekly_choice.append(new_week_choice)

    weekly_array = np.array(weekly_value)
    weekly_df = pd.DataFrame.from_records(weekly_array)
    weekly_df.index = all_weeks
    weekly_df.columns = all_weeks

    return weekly_df


def get_spy_roi(buy_or_sell, positive_rule, and_or, negative_rule):
    # TODO:  Save SPY data to avoid network calls
    # TODO: add in data from 1990 to allow for longer term strategies
    # TODO:  add in a buffer year for easier looking backward calcs.

    base_time = datetime.datetime.strptime("2000-01-03", "%Y-%m-%d")
    now_time = datetime.datetime.strptime("2020-04-13", "%Y-%m-%d")
    spy_full_df = stock_calculations.get_yahoo_stock_data(['SPY'], base_time.strftime("%Y-%m-%d"), now_time.strftime('%Y-%m-%d'))
    n_days = (now_time-base_time).days
    n_weeks = np.round(n_days/7)+1
    print(n_weeks)
    all_weeks = [base_time+datetime.timedelta(days=7*i_days) for i_days in range(int(n_weeks))]

    weekly_strategic_df = make_strategic_portfolio(all_weeks, spy_full_df, buy_or_sell, positive_rule, and_or, negative_rule)
    weekly_df = make_simple_portfolio(all_weeks, spy_full_df)

    spy_statistics = []
    for interval in [364*i for i in [1, 5, 10]]:
        print(interval)
        for i, week in enumerate(all_weeks):
            if week + datetime.timedelta(interval) < now_time:
                end_time = week+datetime.timedelta(interval)

                # Dollar Cost Averaging (Simple)
                interval_df = weekly_df.iloc[(weekly_df.index >= week) & (weekly_df.index < end_time), (weekly_df.columns>=week) & (weekly_df.columns <= end_time)]
                interval_sum = interval_df.iloc[:, -1].sum()
                interval_invested = 100*len(interval_df.index)
                interval_roi = interval_sum/interval_invested

                roi_dict = {
                    'interval': interval,
                    'roi': interval_roi,
                    'start_time': week,
                    'end_time': end_time,
                    'invested_value': interval_invested,
                    'interval_sum': interval_sum,
                    'strategy': 'DCA'
                }
                spy_statistics.append(roi_dict)

                # Dollar Cost Averaging (Strategic)
                interval_df = weekly_strategic_df.iloc[(weekly_strategic_df.index >= week) & (weekly_strategic_df.index < end_time), (weekly_strategic_df.columns>=week) & (weekly_strategic_df.columns <= end_time)]
                interval_sum = interval_df.iloc[:, -1].sum()
                interval_invested = 100*len(interval_df.index)
                interval_roi = interval_sum/interval_invested

                roi_dict = {
                    'interval': interval,
                    'roi': interval_roi,
                    'start_time': week,
                    'end_time': end_time,
                    'invested_value': interval_invested,
                    'interval_sum': interval_sum,
                    'strategy': 'Strategic'
                }
                spy_statistics.append(roi_dict)

    spy_df = pd.DataFrame.from_records(spy_statistics)
    print(spy_df.iloc[spy_df['roi'].idxmax()])
    fig = px.box(spy_df, x='interval', y='roi', color='strategy')
    fig.update_layout(title='ROI from 1-1-2000 to 4-13-2020')

    return fig

