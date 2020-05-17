'''To quickly see what open positions I currently have - using my xls file "TradingJournal (FX) (2020).xlsx '''

import pandas as pd
import numpy as np

df = pd.read_excel(r"/Users/sanduo/Documents/Trading/TradingJournal (FX) (2020).xlsx", \
                   sheet_name = 'Trade Log', \
                  skiprows = 2)
print(df.head())

# Using the Date column to filter out all the trades I've executed so far
filter = df['Date'].isna()
df_alltrades = df[~filter]

# Using the Price Out column to identify which trades I have not closed yet, i.e. Open Positions
open_filter = df_alltrades['Price Out'].isna()
open_positions = df_alltrades[open_filter]
pd.options.display.float_format = '{:,.4f}'.format # Format with commas and round off to 2dp

open_ccys = open_positions[['L/S','Notional','Pair', 'Price In', 'SL', 'TP']]
print(open_ccys)
print('There are {} open positions currently.'.format(open_ccys['Pair'].count()))

# Show Exposure in each currencies
pd.options.mode.chained_assignment = None  # safely disable SettingWithCopyWarning warning

map={'L':1, 'S':-1} # map for +ve and -ve exposures
sign = open_ccys['L/S'].map(map)
open_ccys['Notional'] *= sign

open_ccys['pricing_notional'] = open_ccys['Notional'] * open_ccys['Price In'] * (-1)
open_ccys['base_ccy'] = open_ccys['Pair'].str[:3]
open_ccys['pricing_ccy'] = open_ccys['Pair'].str[-3:]

base = open_ccys[['base_ccy','Notional']].rename(columns={'base_ccy':'currency','Notional':'notional'})
pricing = open_ccys[['pricing_ccy', 'pricing_notional']].rename(columns={'pricing_ccy':'currency','pricing_notional':'notional'})
combined = base.append(pricing)


# Use current exchange rates XXXUSD to convert all to USD exposures
usd_rates_df = df[['xxxusd','rates']].dropna()
merged = pd.merge(combined, usd_rates_df, left_on='currency', right_on='xxxusd', how='left')
merged['exposure(usd)'] = merged.notional * merged.rates

exposures = merged.groupby('currency')['exposure(usd)'].sum().reset_index()
exposures_sorted = exposures.sort_values('exposure(usd)')
print(exposures_sorted)

# Plot exposures
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
from datetime import datetime
sns.set(style="darkgrid")
fig, ax = plt.subplots(figsize=(8,4))
# Format y ticks
fmt = '${x:,.0f}'
tick = mtick.StrMethodFormatter(fmt)
ax.yaxis.set_major_formatter(tick)
# Bar plot
sns.barplot(x='currency', y='exposure(usd)', data=exposures_sorted, palette="rocket", ax=ax)

ax.set_title('Open Exposures (in USD)\n-{}-'.format(datetime.now().strftime("%d/%m/%Y %H:%M")))
ax.set_ylabel('')
ax.set_xlabel('')


### Visualize MTM and distance to SL and TP

# Vlookup / Merge usd_rates_df with open_ccys twice, based on base_ccy and pricing_ccy
base_live = pd.merge(open_ccys, usd_rates_df, left_on='base_ccy', right_on='xxxusd', how='left')
open_ccys_live = pd.merge(base_live, usd_rates_df, left_on='pricing_ccy', right_on='xxxusd', suffixes=['_base','_pricing'], how='left')

# Get current price 'last' - rates_base/rates_pricing
open_ccys_live['last'] = open_ccys_live['rates_base']/open_ccys_live['rates_pricing']

# Calculate pnl % gain (+) or loss (-)
open_ccys_live['chg_pct']=((open_ccys_live['last']/open_ccys_live['Price In'])-1)*100
open_ccys_live['sl_pct']=((open_ccys_live['SL']/open_ccys_live['Price In'])-1)*100
open_ccys_live['tp_pct']=((open_ccys_live['TP']/open_ccys_live['Price In'])-1)*100

# Plot pnl_pct, on barh plot
fig2, ax2 = plt.subplots(figsize=(10,5))

sns.barplot(x='sl_pct', y='Pair', data=open_ccys_live, label='SL', color='red', alpha=0.3, ax=ax2)
sns.barplot(x='tp_pct', y='Pair', data=open_ccys_live, label='TP', color='green', alpha=0.3, ax=ax2)

open_ccys_live.loc[(open_ccys_live['chg_pct'] >= 0) & (open_ccys_live['L/S']=='L'), 'positive_pnl'] = open_ccys_live['chg_pct']
open_ccys_live.loc[(open_ccys_live['chg_pct'] < 0) & (open_ccys_live['L/S']=='S'), 'positive_pnl'] = open_ccys_live['chg_pct']
open_ccys_live.loc[(open_ccys_live['chg_pct'] >= 0) & (open_ccys_live['L/S']=='S'), 'negative_pnl'] = open_ccys_live['chg_pct']
open_ccys_live.loc[(open_ccys_live['chg_pct'] < 0) & (open_ccys_live['L/S']=='L'), 'negative_pnl'] = open_ccys_live['chg_pct']

sns.barplot(x='positive_pnl', y='Pair', data=open_ccys_live, label='MTM', color='green', ax=ax2)
sns.barplot(x='negative_pnl', y='Pair', data=open_ccys_live, label='MTM', color='red', ax=ax2)

ax2.set_title('Marked To Market\n-{}-'.format(datetime.now().strftime("%d/%m/%Y %H:%M")))
ax2.set_ylabel('CCY Pair')
ax2.set_xlabel('% PnL')
ax2.xaxis.set_major_formatter(mtick.PercentFormatter())
plt.show()