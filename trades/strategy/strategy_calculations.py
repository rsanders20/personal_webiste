import cProfile
import datetime
import io
import os
import pstats

from trades.portfolio import stock_calculations
import matplotlib.pyplot as plt
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
from trades.models import Portfolio, Dollar, Strategy, Signal
import plotly.express as px
import plotly.graph_objs as go
import pathlib
import numpy as np
import scipy


def make_np_date(date_str):
    np_date = np.array(pd.to_datetime(date_str, format='%Y-%m-%d'), dtype=np.datetime64)
    return np_date


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


def get_historic_roi(ticker, start_date, end_date, rules_list, buy_threshold, sell_threshold):
    base_time = start_date
    now_time = end_date
    interval = 1
    day_step = 30
    portfolio_value = 1000
    values_df = get_roi(ticker, base_time, now_time, rules_list, buy_threshold, sell_threshold, portfolio_value)
    historic_performance = []
    last_day = base_time

    strategic_score = 0
    total_score = 0
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
                if strategic_roi > simple_roi:
                    strategic_score += 1
                    total_score += 1
                else:
                    total_score += 1

                last_day = day

    historic_array = np.array(historic_performance)
    historic_df = pd.DataFrame.from_records(historic_array)
    historic_df.columns = ['start_time', 'end_time', 'roi', 'strategy', 'interval']
    fig = px.scatter(historic_df, x = 'start_time', y='roi', color='strategy', marginal_y='box')
    fig.update_layout(clickmode='event')

    score_string = f"Improved {strategic_score}/{total_score} realizations"
    if strategic_score/total_score < 0.5:
        score_color = 'danger'
    elif strategic_score/total_score < 0.75:
        score_color = 'warning'
    else:
        score_color = 'success'

    # fig = px.box(historic_df, x='interval', y='roi', color='strategy')
    return fig, score_string, score_color, -1*strategic_score/total_score


def get_roi(ticker, base_time, now_time, rules_list, buy_threshold, sell_threshold, starting_value):
    early_time = base_time-datetime.timedelta(days=365)
    # ticker_extra_df = stock_calculations.get_yahoo_stock_data([ticker], early_time.strftime("%Y-%m-%d"), now_time.strftime('%Y-%m-%d'))
    ticker_extra_df = get_data([ticker], early_time, now_time)

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
    values_df = get_values(all_days, ticker_full_df, rule_df, buy_threshold, sell_threshold, starting_value)

    # Calculate the portfolio performance and create data frames
    return values_df


def get_values(all_days, ticker_full_df, rule_df, buy_threshold, sell_threshold, starting_value):
    ticker_full_df.loc[:, "sum"] = rule_df['sum']
    sum_array = ticker_full_df['sum'].values
    value_array = ticker_full_df['Close'].values
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
    # profile = cProfile.Profile()
    # profile.enable()
    offset = 0
    for ie, extra_day in enumerate(all_extra_days):
        if extra_day == all_days[0]:
            offset = ie

    rule_results = []
    if rules_list:
        for rule in rules_list:
            weight_list = []
            larger_array = ticker_extra_df[rule["Larger: What?"]].to_numpy()
            smaller_array = ticker_extra_df[rule["Smaller: What?"]].to_numpy()
            # time_array = ticker_extra_df.index.to_numpy()
            for i, day in enumerate(all_days):
                larger_value = larger_array[i+offset+rule['Larger: When?']]
                smaller_value = smaller_array[i+offset+rule['Smaller: When?']]
                weight = 0
                if larger_value > smaller_value*(1+rule['Percentage']/100):
                    weight = rule['Weight']

                weight_list.append(weight)

            rule_results.append(weight_list)
    else:
        weight_list = []
        for i, day in enumerate(all_days):
            weight = 0
            weight_list.append(weight)

        rule_results.append(weight_list)

    rule_df = pd.DataFrame.from_records(rule_results).T
    rule_df.index = all_days
    if rules_list:
        rule_df.columns = ["{}".format(i) for i in range(len(rules_list))]
        rule_df['sum'] = rule_df[list(rule_df.columns)].sum(axis=1)
    else:
        rule_df.columns = ['0']
        rule_df['sum'] = rule_df[list(rule_df.columns)].sum(axis=1)
    # profile.disable()
    # s = io.StringIO()
    # ps = pstats.Stats(profile, stream=s).sort_stats("cumtime")
    # ps.print_stats()
    # with open('test.txt', 'w+') as f:
    #     f.write(s.getvalue())

    return rule_df


def get_data(ticker_list, start_time, end_time):
    ticker=ticker_list[0]
    data_dir = r'./assets/sp500/'
    file = os.path.join(data_dir, ticker+".csv")

    if end_time.weekday() > 4:
        if end_time.weekday() == 5:
            end_time = end_time - datetime.timedelta(days=1)
        elif end_time.weekday() == 6:
            end_time = end_time - datetime.timedelta(days=2)

    if os.path.isfile(file):
        existing_df = pd.read_csv(file)
        if not existing_df.empty:
            df_start_time = datetime.datetime.strptime(existing_df["Date"].iloc[0], '%Y-%m-%d')
            df_end_time = datetime.datetime.strptime(existing_df["Date"].iloc[-1], '%Y-%m-%d')

            if df_start_time.date() <= start_time.date() and df_end_time.date() >= end_time.date():
                existing_df.index = pd.to_datetime(existing_df["Date"], format = '%Y-%m-%d')
                df = existing_df.loc[(existing_df.index>=start_time) & (existing_df.index<=end_time)]
                # print("used existing data")
            else:
                df = stock_calculations.get_yahoo_stock_data([ticker], start_time - datetime.timedelta(days=365 * 2), end_time)
                df.to_csv(file)
        else:
            df = stock_calculations.get_yahoo_stock_data([ticker], start_time - datetime.timedelta(days=365 * 2),
                                                         end_time)
            df.to_csv(file)
    else:
        df = stock_calculations.get_yahoo_stock_data([ticker], start_time-datetime.timedelta(days=365*2), end_time)
        df.to_csv(file)
    return df


def make_spy_graph(ticker, values_df):
    spy_value = go.Figure()
    factor = values_df['simple_values'][0]/values_df['Close'][0]
    spy_value.add_trace(go.Scatter(
        x=values_df.index, y=values_df['simple_values'], name='Simple'
    ))
    spy_value.add_trace(go.Scatter(
        x=values_df.index, y=values_df['strategic_values'], name='Strategic'
    ))
    # spy_value.add_trace(go.Scatter(
    #     x=values_df.index, y=values_df['200']*factor, name='200'
    # ))
    # spy_value.add_trace(go.Scatter(
    #     x=values_df.index, y=values_df['50']*factor, name='50'
    # ))
    spy_value.add_trace(go.Scatter(
        x=values_df.loc[values_df['strategic_decisions'] == 'Sell'].index,
        y=values_df.loc[values_df['strategic_decisions'] == 'Sell', 'Close']*factor,
        mode='markers', name='Sell', marker_symbol='triangle-down', marker_color='Red', marker_size=12
    ))
    spy_value.add_trace(go.Scatter(
        x=values_df.loc[values_df['strategic_decisions'] == 'Buy'].index,
        y=values_df.loc[values_df['strategic_decisions'] == 'Buy', 'Close']*factor,
        mode='markers', name='Buy', marker_symbol='triangle-up', marker_color='Green', marker_size=12
    ))
    spy_value.update_layout(showlegend=True,
                            legend_orientation='h',
                            yaxis=dict(title=f'{ticker} Closing Value ($)'),
                            margin=dict(b=0, r=0, l=0, t=66),
                            paper_bgcolor='#f9f9f9',
                            title='Daily Strategic Decisions'
                            )
    return spy_value


def make_portfolio_graph(values_df, weekly_roi_radio):
    portfolio = go.Figure()
    if weekly_roi_radio == 1:
        portfolio.add_trace(go.Scatter(
            x=values_df.index, y=values_df['simple_values'], name='Simple'
        ))
        portfolio.add_trace(go.Scatter(
            x=values_df.index, y=values_df['strategic_values'], name='Strategic'
        ))

        portfolio.update_layout(legend_orientation='h',
                                yaxis=dict(title='Portfolio Value ($)'),
                                margin=dict(t=0, b=0, r=0, l=0),
                                paper_bgcolor='#f9f9f9'
                                )
    else:
        portfolio.add_trace(go.Scatter(
            x=values_df.index, y=values_df['simple_values'] / 1000, name='Simple'
        ))
        portfolio.add_trace(go.Scatter(
            x=values_df.index, y=values_df['strategic_values'] / 1000, name='Strategic'
        ))

        portfolio.update_layout(legend_orientation='h',
                                yaxis=dict(title='Portfolio ROI []'),
                                margin=dict(t=0, b=0, r=0, l=0),
                                paper_bgcolor='#f9f9f9'
                                )
    return portfolio


def signal_to_dict(signal_list):
    data = []
    for signal in signal_list:
        data.append({'Larger: When?': int(signal.larger_when),
                     'Larger: What?': signal.larger_what,
                     'Smaller: When?': int(signal.smaller_when),
                     'Smaller: What?': signal.smaller_what,
                     'Percentage': signal.percentage,
                     'Weight': signal.weight})
    return data


def get_values_df(row_data, user):
    # print(data[rows[0]])
    ticker = row_data['Name']
    value = row_data['Value']
    strategy_name = row_data['Strategy']
    start_date = datetime.datetime.strptime(row_data['Start Date'][0:10], '%Y-%m-%d')
    end_date = datetime.datetime.now()
    print(start_date, end_date)
    if strategy_name:
        strategy = Strategy.query.filter_by(user_id=user.id, name=strategy_name).one_or_none()
        buy_threshold = strategy.buy_threshold
        sell_threshold = strategy.sell_threshold
        rules_list = signal_to_dict(Signal.query.filter_by(strategy_id=strategy.id).all())
    else:
        rules_list = []
        buy_threshold = 0
        sell_threshold = 0

    print(rules_list)
    values_df = get_roi(ticker, start_date, end_date, rules_list, buy_threshold, sell_threshold, value)

    return values_df
