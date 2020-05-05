'''To quickly see what open positions I currently have - using my xls file "TradingJournal (FX) (2020).xlsx '''

import pandas as pd
from pandas import ExcelWriter
from pandas import ExcelFile

df = pd.read_excel(r"/Users/sanduo/Documents/Trading/TradingJournal (FX) (2020).xlsx", \
                   sheet_name = 'Trade Log', \
                  skiprows = 2)
print(df)

# Using the Date column to filter out all the trades I've executed so far
filter = df['Date'].isna()
df_alltrades = df[~filter]
print(df_alltrades)

# Using the Price Out column to identify which trades I have not closed yet, i.e. Open Positions
open_filter = df_alltrades['Price Out'].isna()
open_positions = df_alltrades[open_filter]
open_ccys = open_positions[['L/S','Pair', 'Price In', 'SL', 'TP']]
print(open_ccys)
print('There are {} open positions currently.'.format(open_ccys['Pair'].count()))