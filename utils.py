import os
import pandas as pd
import numpy as np
from talib.abstract import *
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler, StandardScaler, RobustScaler
import pickle

# Remove chaining warning
pd.options.mode.chained_assignment = None
# Remove summary printing
pd.options.display.max_rows = None

def get_data(stock_symbol, is_detrend=False):
    """ Returns a n_step array """
    # Data frame w/ open, close, high, low, volume values and reverse
    df = pd.read_csv('data/{}'.format(stock_symbol + ".csv")).reset_index()

    #if(is_detrend):
    #    df = detrend(df)

    inputs = {
       'open': df['Open'],
       'high': df['High'],
       'low':  df['Low'],
       'close': df['Close'],
       'volume': df['Volume']
    }  
    
    t_df = pd.DataFrame()  

    t_df['close'] = inputs['close']

    t_df['trix'] = TRIX(inputs, timeperiod=14)
    t_df['macd'] = MACD(inputs, fastperiod=12, slowperiod=26, signalperiod=9)[0] 
    t_df['mfi'] = MFI(inputs, timeperiod=14)
    t_df['cci'] = CCI(inputs, timeperiod=14)
    t_df['aru'] = AROON(inputs, timeperiod=14)[0]
    t_df['ard'] = AROON(inputs, timeperiod=14)[1]
    t_df['rsi'] = RSI(inputs, timeperiod=14)
    t_df['willr'] = WILLR(inputs, timeperiod=14) 

    first_valid_row = t_df.apply(pd.Series.first_valid_index).max()

    t_df = t_df.iloc[first_valid_row:]
    return t_df.to_numpy()

def get_split_data(stock_symbol, ratio, detrend):
    data = get_data(stock_symbol, detrend)

    price = data[:,0]
    data = data[:,1:]

    data_size = data.shape[0]
    end_row_train = (int)(data_size * (ratio / 100))

    data_split = {}
    data_split["train"] = [price[:end_row_train], data[:end_row_train]]
    data_split["test"] = [price[end_row_train:], data[end_row_train:]]
    
    return data_split

def fit(data_split, mode, symbol):	
    if(mode == 'train'):
        scaler = MinMaxScaler((0.1, 1))
        data_split[mode][1] = np.round(scaler.fit_transform(data_split[mode][1]), 2) # round to nearest two
	# save scaler to disk
        with open('scalers/scaler-{}.p'.format(symbol), 'wb') as fp:
            pickle.dump(scaler, fp)
    else:
        # load scaler
        scaler = pickle.load(open('scalers/scaler-{}.p'.format(symbol), 'rb'))
        data_split[mode][1] = np.round(scaler.fit_transform(data_split[mode][1]), 2) # round to nearest two

def detrend(df):
    del df[df.columns[0]]
    new_df = df.diff(periods=1).iloc[1:]
    new_df = new_df.add(abs(new_df.min()))
    return new_df

def view_signals(prices, signals):
    df = pd.DataFrame()
    s = np.array(signals).flatten()
    df['Close'] = prices.flatten()
    df['Buy'] = pd.Series(np.where(s == 2, 1, 0))
    df['Sell'] = pd.Series(np.where(s == 0, 1, 0))
    plt.figure(figsize=(20, 5))
    plt.plot(df['Close'], zorder=0)
    plt.scatter(df[df['Buy'] == 1].index.tolist(), df.loc[df['Buy'] ==
                                                          1, 'Close'].values, zorder=1, label='skitscat', color='green', s=30, marker=".")

    plt.scatter(df[df['Sell'] == 1].index.tolist(), df.loc[df['Sell'] ==
                                                           1, 'Close'].values, zorder=1, label='skitscat', color='red', s=30, marker=".")
    plt.xlabel('Timestep')
    plt.ylabel('Close Price')
    plt.show()


def maybe_make_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
