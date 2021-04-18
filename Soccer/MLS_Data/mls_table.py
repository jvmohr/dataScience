import requests, os, datetime, json
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

year = '2021'

url = "https://en.wikipedia.org/wiki/{}_Major_League_Soccer_season"

r = requests.get(url.format(year))
r.raise_for_status()
soup = BeautifulSoup(r.text, "html.parser")

check = False
headers = []
for header in soup.find_all(['h1', 'h2', 'h3', 'h4']):
    if 'standings' in header.text.lower():
        check = True
        continue
    if check and ('division' in header.text.lower() or 'conference'in header.text.lower()):
        if 'eastern' in header.text.lower() or 'central' in header.text.lower() or 'western' in header.text.lower():
            headers.append(header.text.split('[')[0])   
    else:
        check = False 

if len(headers) < 2:
    if year == 2001 or year == 2000: # only seasons with 3 conferences
        headers = ['Eastern Conference', 'Central Conference', 'Western Conference']
    else: 
        headers = ['Eastern Conference', 'Western Conference']

    # print("couldn't find conferences/divisons for {}, guessing {}".format(year, headers))

headers.append('Overall')

if year == 2011:
    headers = ['Overall', 'Eastern Conference', 'Western Conference']

dfs = pd.read_html(r.text)

i = 0
table_dfs = []
for df in dfs:
    if 'Pts' in df.columns:
        df.columns = [x.split('.')[0].replace('vte', '') for x in df.columns]
        df = df.rename(columns={'Club': 'Team', 'Qualification[a]': 'Qualification', 
                 'Unnamed: 10': 'Qualification', 'Pld': 'GP', 'GP*': 'GP', 
                 'T': 'D', 'Western Conference': 'Team', 'Eastern Conference': 'Team', 
                 '(sw)': 'SW', '(sl)': 'SL', 'P': 'GP', 'SOW': 'SW'})
        df['Conference'] = headers[i]
        df['Year'] = year
        table_dfs.append(df)
        i += 1

    elif len(df) > 1 and 'Pts' in df.loc[1].values:
        df.columns = df.loc[1].values
        df = df.drop([0, 1]).reset_index(drop=True)
        if np.nan in df.columns:
            df = df.drop(np.nan, axis=1)
        df.columns = [x.split('.')[0].replace('vte', '') for x in df.columns]
        df = df.rename(columns={'Club': 'Team', 'Qualification[a]': 'Qualification', 
                 'Unnamed: 10': 'Qualification', 'Pld': 'GP', 'GP*': 'GP', 
                 'T': 'D', 'Western Conference': 'Team', 'Eastern Conference': 'Team', 
                 '(sw)': 'SW', '(sl)': 'SL', 'P': 'GP', 'SOW': 'SW'})
        df['Conference'] = headers[i]
        df['Year'] = year
        table_dfs.append(df)
        i += 1
    if i == 3 and (year == 2018 or year == 2020): # 2018 has an extra table and 2020 has many
        break

# print("year: {}, headers: {}".format(year, headers))
if len(headers) != len(table_dfs):
    print(len(headers), len(table_dfs), 'mismatched headers and table sizes')

# concat and write
new_table_df = pd.concat(table_dfs).reset_index(drop=True)
new_table_df.to_csv(os.path.join('data', 'tables', '{}_table.csv'.format(year)), index=False)

# append to old tables and write
prev_df = pd.read_csv(os.path.join('data', 'tables', 'through_2020_tables.csv'))
updated_df = prev_df.append(new_table_df, ignore_index=False)
updated_df.to_csv(os.path.join('data', 'tables', 'all_tables.csv'), index=False)
