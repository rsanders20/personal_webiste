import datetime
import os

from trades.manual import stock_calculations
import matplotlib.pyplot as plt
import pandas as pd
from trades.models import Portfolio, Dollar
from trades.manual.stock_calculations import flatten_df, make_np_date
import plotly.express as px
import plotly.graph_objs as go
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


        roi_positive_list.append(roi_indicator)

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
            rules_list = buy_or_sell_indicator(spy_full_df, week)

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

    spy_df = pd.DataFrame.from_records(spy_statistics)
    if spy_df.empty:
        return weekly_strategic_df, weekly_choice_df, weekly_df, spy_full_df, px.line()

    fig = px.box(spy_df, x='interval', y='roi', color='strategy')

    fig.update_layout(margin=dict(t=0, b=0, r=0, l=0),
                      paper_bgcolor='#f9f9f9')

    return weekly_strategic_df, weekly_choice_df, weekly_df, spy_full_df, fig


def make_portfolio_graph(strategic_df, dca_df, weekly_roi_radio):
    time_values = strategic_df.columns
    n_weeks = len(time_values)
    cash_values = np.array([100 * (i + 1) for i in range(n_weeks)])

    if weekly_roi_radio == 2:
        total_return = strategic_df.to_numpy()[-1, :] - cash_values
        weekly_return = dca_df.to_numpy()[-1, :] - cash_values

        portfolio_return = go.Figure()
        portfolio_return.add_trace(go.Scatter(
            x=time_values, y=weekly_return, name='DCA'
        ))
        portfolio_return.add_trace(go.Scatter(
            x=time_values, y=total_return, name='Strategic'
        ))
        portfolio_return.update_layout(legend_orientation='h',
                                       yaxis=dict(title='Change in Portfolio Value ($)'),
                                       margin=dict(t=0, b=0, r=0, l=0),
                                       paper_bgcolor='#f9f9f9'
                                       )
        return portfolio_return
    else:
        total_value = strategic_df.to_numpy()[-1, :]
        weekly_value = dca_df.to_numpy()[-1, :]

        portfolio_value = go.Figure()
        portfolio_value.add_trace(go.Scatter(
            x=time_values, y=weekly_value, name='DCA'
        ))
        portfolio_value.add_trace(go.Scatter(
            x=time_values, y=total_value, name='Strategic'
        ))
        portfolio_value.add_trace(go.Scatter(
            x=time_values, y=cash_values, name='Cash'
        ))
        portfolio_value.update_layout(legend_orientation='h',
                                      yaxis=dict(title='Portfolio Value ($)'),
                                      margin=dict(t=0, b=0, r=0, l=0),
                                      paper_bgcolor='#f9f9f9'
                                      )

        return portfolio_value


def make_spy_value_graph(spy_full_df, choice_df):
    buy_correct = []
    buy_wrong = []
    sell_correct = []
    sell_wrong = []
    choice_dates = choice_df.index
    choice_list = choice_df.to_numpy()[0]
    for date, choice in zip(choice_dates, choice_list):
        next_week = date + datetime.timedelta(days=7)
        spy_value = \
        spy_full_df.iloc[abs(spy_full_df.index - date) == min(abs(spy_full_df.index - date))]['Close'].to_numpy()[0]
        next_spy_value = \
        spy_full_df.iloc[abs(spy_full_df.index - next_week) == min(abs(spy_full_df.index - next_week))][
            'Close'].to_numpy()[0]

        if choice == "invest":
            if next_spy_value > spy_value:
                buy_correct.append([date, spy_value])
            else:
                buy_wrong.append([date, spy_value])
        else:
            if next_spy_value > spy_value:
                sell_wrong.append([date, spy_value])
            else:
                sell_correct.append([date, spy_value])

    buy_correct_array = np.array(buy_correct)
    sell_correct_array = np.array(sell_correct)
    buy_wrong_array = np.array(buy_wrong)
    sell_wrong_array = np.array(sell_wrong)

    spy_value = go.Figure()
    spy_value.add_trace(go.Scatter(
        x=spy_full_df.index, y=spy_full_df['Close'], name='SPY',
    ))
    if sell_correct_array.any():
        spy_value.add_trace(go.Scatter(
            x=sell_correct_array[:, 0], y=sell_correct_array[:, 1],
            mode='markers', name='Sell (Correct)', marker_symbol='triangle-up',
            marker_color='Red', marker_size=12
        ))
    if sell_wrong_array.any():
        spy_value.add_trace(go.Scatter(
            x=sell_wrong_array[:, 0], y=sell_wrong_array[:, 1],
            mode='markers', name='Sell (Wrong)', marker_symbol='triangle-down',
            marker_color='Red', marker_size=12
        ))

    if buy_correct_array.any():
        spy_value.add_trace(go.Scatter(
            x=buy_correct_array[:, 0], y=buy_correct_array[:, 1],
            mode='markers', name='Buy (Correct)', marker_symbol='triangle-up',
            marker_color='Green', marker_size=12
        ))
    if buy_wrong_array.any():
        spy_value.add_trace(go.Scatter(
            x=buy_wrong_array[:, 0], y=buy_wrong_array[:, 1],
            mode='markers', name='Buy (Wrong)', marker_symbol='triangle-down',
            marker_color='Green', marker_size=12
        ))

    spy_value.add_trace(go.Scatter(
        x=spy_full_df.index, y=spy_full_df['200'], name='200 Day'
    ))
    spy_value.add_trace(go.Scatter(
        x=spy_full_df.index, y=spy_full_df['50'], name='50 Day'
    ))

    spy_value.update_layout(showlegend=True,
                            legend_orientation='h',
                            xaxis=dict(range=[spy_full_df.index[0], spy_full_df.index[-1]]),
                            yaxis=dict(title='SPY Closing Value ($)'),
                            margin=dict(t=0, b=0, r=0, l=0),
                            paper_bgcolor='#f9f9f9'
                            )

    return spy_value


def get_historic_roi(ticker, start_date, end_date, rules_list, buy_threshold, sell_threshold):
    base_time = start_date
    now_time = end_date
    interval = 1
    day_step = 30
    values_df = get_roi(ticker, base_time, now_time, rules_list, buy_threshold, sell_threshold)
    historic_performance = []
    last_day = base_time
    for day in values_df.index:
        if (day-last_day).days > day_step:
            start_time = day
            end_time = start_time + datetime.timedelta(days=interval*365)
            if values_df.index[-1] > end_time:
                interval_df = values_df.iloc[(values_df.index >= start_time) & (values_df.index <= end_time)]
                simple_roi = interval_df['simple_values'].iloc[-1]/interval_df['simple_values'][0]
                historic_performance.append([start_time, end_time, simple_roi, 'simple', interval])
                strategic_roi = interval_df['strategic_values'].iloc[-1]/interval_df['strategic_values'].iloc[0]
                historic_performance.append([start_time, end_time, strategic_roi, 'strategic', interval])

                last_day = day

    historic_array = np.array(historic_performance)
    historic_df = pd.DataFrame.from_records(historic_array)
    historic_df.columns = ['start_time', 'end_time', 'roi', 'strategy', 'interval']
    fig = px.scatter(historic_df, x = 'start_time', y='roi', color='strategy', marginal_y='box')
    fig.update_layout(clickmode='event')
    # fig = px.box(historic_df, x='interval', y='roi', color='strategy')
    return fig


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
    all_extra_days = ticker_extra_df.index.values

    # Make the daily trades for the simple and strategic strategy
    rule_df = make_decisions(ticker_extra_df, all_extra_days, all_days, rules_list)
    values_df = get_values(all_days, ticker_full_df, rule_df, buy_threshold, sell_threshold)

    # Calculate the portfolio performance and create data frames

    return values_df


def get_values(all_days, ticker_full_df, rule_df, buy_threshold, sell_threshold):
    ticker_full_df.loc[:, "sum"] = rule_df['sum']
    sum_array = ticker_full_df['sum'].values
    value_array = ticker_full_df['Close'].values
    starting_value = 1000.00
    strategic_value_list = []
    strategic_decision_list = []
    strategic_state_list = []
    simple_value_list = []

    i = 0
    for sum, value in zip(sum_array, value_array):
        action='Hold'
        if sum > buy_threshold:
            action = "Buy"
        elif sum < sell_threshold:
            action = "Sell"

        if i == 0:
            # strategic_value_list.append(starting_value)
            # strategic_decision_list.append("Buy")
            # strategic_state_list.append("Invested")
            strategic_value_list.append(starting_value)
            if action == "Buy":
                strategic_state_list.append("Invested")
                strategic_decision_list.append(action)
            elif action == "Sell":
                strategic_state_list.append("Cash")
                strategic_decision_list.append(action)
            else:  # Hold
                # When in doubt, buy in to start the investment.  This is a difference to the historic method.
                strategic_state_list.append("Invested")
                strategic_decision_list.append("Buy")
            simple_value_list.append(starting_value)
        else:
            simple_value_list.append(simple_value_list[i-1]*value/value_array[i-1])
            if strategic_decision_list[i-1] == 'Buy':
                strategic_value_list.append(strategic_value_list[i-1]*value/value_array[i-1])
                strategic_state_list.append("Invested")
                if action == 'Buy':
                    strategic_decision_list.append("Hold")
                else:
                    strategic_decision_list.append(action)
            elif strategic_decision_list[i-1] == 'Sell':
                strategic_value_list.append(strategic_value_list[i-1])
                strategic_state_list.append("Cash")
                if action== 'Sell':
                    strategic_decision_list.append("Hold")
                else:
                    strategic_decision_list.append(action)
            else: #Hold
                if strategic_state_list[i-1] == 'Invested':
                    strategic_value_list.append(strategic_value_list[i-1]*value/value_array[i-1])
                    strategic_state_list.append("Invested")
                    if action == 'Buy':
                        strategic_decision_list.append("Hold")
                    else:
                        strategic_decision_list.append(action)
                else:
                    strategic_value_list.append(strategic_value_list[i-1])
                    strategic_state_list.append("Cash")
                    if action == 'Sell':
                        strategic_decision_list.append("Hold")
                    else:
                        strategic_decision_list.append(action)

        i = i+1
    ticker_full_df.loc[:, "simple_values"] = simple_value_list
    ticker_full_df.loc[:, "strategic_values"] = strategic_value_list
    ticker_full_df.loc[:, "strategic_decisions"] = strategic_decision_list
    ticker_full_df.loc[:, "strategic_state"] = strategic_state_list

    return ticker_full_df


def make_decisions(ticker_extra_df, all_extra_days, all_days, rules_list):
    offset = 0
    for ie, extra_day in enumerate(all_extra_days):
        if extra_day == all_days[0]:
            offset = ie

    rule_results = []
    for rule in rules_list:
        weight_list = []
        for i, day in enumerate(all_days):
            larger_time = all_extra_days[i+offset+rule['Larger: When?']]
            smaller_time = all_extra_days[i+offset+rule['Smaller: When?']]

            # larger_time = all_days[i+rule['Larger: When?']]
            # smaller_time = all_days[i+rule['Smaller: When?']]

            larger_value = ticker_extra_df.iloc[ticker_extra_df.index==larger_time][rule['Larger: What?']].values
            smaller_value = ticker_extra_df.iloc[ticker_extra_df.index.values==smaller_time][rule['Smaller: What?']].values

            weight = 0
            if larger_value > smaller_value*(1+rule['Percentage']/100):
                weight = rule['Weight']

            weight_list.append(weight)

        rule_results.append(weight_list)

    rule_df = pd.DataFrame.from_records(rule_results).T
    rule_df.index = all_days
    rule_df.columns = ["{}".format(i) for i in range(len(rules_list))]
    rule_df['sum'] = rule_df[list(rule_df.columns)].sum(axis=1)

    return rule_df

