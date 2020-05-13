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


def buy_or_sell_indicator(spy_full_df, week):
    roi_positive_list = []
    down_crossing_200_list = []
    up_crossing_200_list = []
    down_crossing_50_list = []
    up_crossing_50_list = []
    for n_days in [7, 14, 21, 28]:
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
            roi_indicator = True
        else:
            roi_indicator = False

        # if week_data['200'][0] > week_data['Close'][0] and week_data['200'][-1] < week_data['Close'][-1]:
        #     down_crossing_200 = True
        # else:
        #     down_crossing_200 = False
        #
        # if week_data['200'][0] < week_data['Close'][0] and week_data['200'][-1] > week_data['Close'][-1]:
        #     up_crossing_200 = True
        # else:
        #     up_crossing_200 = False
        #
        # if week_data['50'][0] > week_data['Close'][0] and week_data['50'][-1] < week_data['Close'][-1]:
        #     down_crossing_50 = True
        # else:
        #     down_crossing_50 = False
        #
        # if week_data['50'][0] < week_data['Close'][0] and week_data['50'][-1] > week_data['Close'][-1]:
        #     up_crossing_50 = True
        # else:
        #     up_crossing_50 = False


        roi_positive_list.append(roi_indicator)
        # down_crossing_200_list.append(down_crossing_200)
        # up_crossing_200_list.append(up_crossing_200)
        # down_crossing_50_list.append(down_crossing_50)
        # up_crossing_50_list.append(up_crossing_50)

    roi_negative_list = []
    for roi_indicator in roi_positive_list:
        roi_negative_list.append(not roi_indicator)

    avg_list = [week_data['Close'][-1]>week_data['200'][-1],
               week_data['Close'][-1]<week_data['200'][-1],
               week_data['Close'][-1] > week_data['50'][-1],
               week_data['Close'][-1] < week_data['50'][-1]
               ]

    rules_list = roi_positive_list + roi_negative_list + avg_list
                 # + up_crossing_200_list +down_crossing_200_list + up_crossing_50_list + down_crossing_50_list

    return rules_list


def make_strategic_portfolio(all_weeks, spy_full_df, buy_or_sell, rule_1_index, and_or, rule_2_index):
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

            # roi_pos_1 = roi_indicator(spy_full_df, week, 7)
            # roi_pos_2 = roi_indicator(spy_full_df, week, 14)
            # roi_pos_3 = roi_indicator(spy_full_df, week, 21)
            # roi_pos_4 = roi_indicator(spy_full_df, week, 28)
            # up_cross_200_1
            # up_cross_200_2
            # up_cross_200_3
            # up_cross_200_4
            #roi_positive 1-4 weeks
            #roi_negative 1-4 weeks
            #200 day upcrossing in last 4,8 weeks
            #200 day downcrossing in last 4,8 weeks
            #50 day up-crossing in last 2, 4 weeks
            #50 day down-cross in last 2,4 weeks
            rules_list = buy_or_sell_indicator(spy_full_df, week)

            # rules_list = [roi_pos_1,
            #               roi_pos_2,
            #               roi_pos_3,
            #               roi_pos_4,
            #               not roi_pos_1,
            #               not roi_pos_2,
            #               not roi_pos_3,
            #               not roi_pos_3]

            rule_1 = rules_list[rule_1_index]
            rule_2 = rules_list[rule_2_index]

            # If the current week was positive, do nothing with the new week
            # update the existing weeks, and sell
            #if roi_pos_1 and not roi_pos_3:
            if buy_or_sell == "sell":
                if and_or == "and":
                    if rule_1 and rule_2:
                        action = "sell"
                    else:
                        action = "buy"
                else:
                    if rule_1 or rule_2:
                        action = "sell"
                    else:
                        action = "buy"
            else:
                if and_or == "and":
                    if rule_1 and rule_2:
                        action = "buy"
                    else:
                        action = "sell"
                else:
                    if rule_1 or rule_2:
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

    weekly_choice_array = np.array(weekly_choice)
    weekly_choice_df = pd.DataFrame.from_records(weekly_choice_array)
    weekly_choice_df.index = all_weeks
    weekly_choice_df.columns = all_weeks

    return weekly_df, weekly_choice_df


def get_spy_roi(base_time, now_time, buy_or_sell, rule_1_index, and_or, rule_2_index):
    # Create the SPY dataframe
    early_time = base_time-datetime.timedelta(days=365)
    spy_extra_df = stock_calculations.get_yahoo_stock_data(['SPY'], early_time.strftime("%Y-%m-%d"), now_time.strftime('%Y-%m-%d'))
    spy_extra_df['25'] = spy_extra_df.Close.rolling(window=25).mean()
    spy_extra_df['50'] = spy_extra_df.Close.rolling(window=50).mean()
    spy_extra_df['100'] = spy_extra_df.Close.rolling(window=100).mean()
    spy_extra_df['200'] = spy_extra_df.Close.rolling(window=200).mean()

    # Trim the dataframe to remove the extra time
    np_end_date = stock_calculations.make_np_date(now_time)
    np_start_date = stock_calculations.make_np_date(base_time)
    spy_full_df = spy_extra_df.loc[
        (spy_extra_df.index.values <= np_end_date) & (spy_extra_df.index.values >= np_start_date)]

    # Create a list of each monday between the start and end time
    n_days = (now_time-base_time).days
    n_weeks = np.round(n_days/7)+1
    print(n_weeks)
    all_weeks = [base_time+datetime.timedelta(days=7*i_days) for i_days in range(int(n_weeks))]

    # Make the daily trades for the simple and strategic strategy
    weekly_strategic_df, weekly_choice_df = make_strategic_portfolio(all_weeks, spy_full_df, buy_or_sell, rule_1_index, and_or, rule_2_index)
    weekly_df = make_simple_portfolio(all_weeks, spy_full_df)

    # Calculate the portfolio performance and create data frames
    spy_statistics = []
    for interval in [364*i for i in [5]]:
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

    rules_list = {}
    buy_threshold = 0.9
    sell_threshold = 0.1
    get_roi('SPY', base_time, now_time, rules_list, buy_threshold, sell_threshold)

    spy_df = pd.DataFrame.from_records(spy_statistics)
    if spy_df.empty:
        return weekly_strategic_df, weekly_choice_df, weekly_df, spy_full_df, px.line()

    fig = px.box(spy_df, x='interval', y='roi', color='strategy')

    fig.update_layout(margin=dict(t=0, b=0, r=0, l=0),
                      paper_bgcolor='#f9f9f9')

    return weekly_strategic_df, weekly_choice_df, weekly_df, spy_full_df, fig


def get_roi(ticker, base_time, now_time, rules_list, buy_threshold, sell_threshold):
    early_time = base_time-datetime.timedelta(days=365)
    ticker_extra_df = stock_calculations.get_yahoo_stock_data([ticker], early_time.strftime("%Y-%m-%d"), now_time.strftime('%Y-%m-%d'))
    ticker_extra_df['50'] = ticker_extra_df.Close.rolling(window=50).mean()
    ticker_extra_df['200'] = ticker_extra_df.Close.rolling(window=200).mean()

    # Trim the dataframe to remove the extra time
    np_end_date = stock_calculations.make_np_date(now_time)
    np_start_date = stock_calculations.make_np_date(base_time)
    ticker_full_df = ticker_extra_df.loc[
        (ticker_extra_df.index.values <= np_end_date) & (ticker_extra_df.index.values >= np_start_date)]

    # Create a list of each trading day
    all_days = ticker_full_df.index.values

    # Make the daily trades for the simple and strategic strategy
    rules_list = [{'Name': 'Good Last Wk', 'Signal': 'Bullish', 'Duration': 7, 'Type': 'Close', 'Current > Past': True, "Weight": 0.5},
                  {'Name': 'Bad Last 3 Wks', 'Signal': 'Bullish', 'Duration': 21, 'Type': 'Close', 'Current > Past': False, "Weight": 0.5}]
    rule_df = make_decisions(ticker_extra_df, all_days, np_start_date, np_end_date, rules_list)
    strategic_df, simple_df = get_values(all_days, ticker_full_df, rule_df, buy_threshold, sell_threshold)

    # Calculate the portfolio performance and create data frames

    return []


def get_values(all_days, ticker_full_df, rule_df, buy_threshold, sell_threshold):
    ticker_full_df['sum'] = rule_df['sum']
    sum_array = ticker_full_df['sum'].values
    value_array = ticker_full_df['Close'].values
    starting_value = 1000.00
    strategic_value_list = []
    strategic_decision_list = []
    strategic_state_list = []
    simple_value_list = []
    for i, sum, value in enumerate(zip(sum_array, value_array)):
        action='Hold'
        if sum > buy_threshold:
            action = "Buy"
        elif sum < sell_threshold:
            action = "Sell"

        if i ==0:
            strategic_value_list.append(starting_value)
            strategic_decision_list.append(action)
            if action == "Buy":
                strategic_state_list.append("Invested")
            else:
                strategic_state_list.append("Cash")
            simple_value_list.append(starting_value)
        else:
            simple_value_list.append(simple_value_list[i-1]*value/value_array[i-1])
            if strategic_decision_list[i-1] == 'Buy':
                strategic_value_list.append(strategic_value_list[i-1]*value/value_array[i-1])
            elif strategic_decision_list[i-1] == 'Sell':
                strategic_value_list.append(strategic_value_list[i-1])
            else:
                if strategic_state_list[i-1] == 'Invested':
                    strategic_value_list.append(strategic_value_list[i-1]*value/value_array[i-1])
                else:
                    strategic_value_list.append(strategic_value_list[i-1])



        print(sum, value)

    print(sum_array, type(sum_array))


    print("here")
    return [], []


def make_decisions(ticker_full_df, all_days, np_start_date, np_end_ate, rules_list):
    rule_results = []
    for rule in rules_list:
        weight_list = []
        for day in all_days:
            past_day = day-np.timedelta64(rule['Duration'], 'D')
            current_value = ticker_full_df.iloc[ticker_full_df.index==day][rule['Type']].values
            past_value = ticker_full_df.iloc[ticker_full_df.index.values==past_day][rule['Type']].values

            sign = -1.0
            if rule['Signal'] == 'Bullish':
                sign = 1.0

            weight = 0
            if current_value > past_value and rule['Current > Past']:
                weight += rule['Weight']*sign

            if past_value > current_value and not rule['Current > Past']:
                weight += rule['Weight']*sign

            weight_list.append(weight)

        rule_results.append(weight_list)

    rule_df = pd.DataFrame.from_records(rule_results).T
    rule_df.index = all_days
    rule_df.columns = ["{}".format(i['Name']) for i in rules_list]
    rule_df['sum'] = rule_df[list(rule_df.columns)].sum(axis=1)
    print(rule_df)

    return rule_df

