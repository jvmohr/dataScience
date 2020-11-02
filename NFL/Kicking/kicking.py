# -*- coding: utf-8 -*-
"""
Created on Sun Jan 19 17:18:13 2020

@author: Joseph
"""

import requests, os
from bs4 import BeautifulSoup
import pandas as pd

headers = ["Rank", "Player", "Team", "Pos", "FGM", "FG Att", "Pct", "Blk", "Lng", 
"1-19_A-M", "1-19_Pct", 
"20-29_A-M", "20-29_Pct", 
"30-39_A-M", "30-39_Pct", 
"40-49_A-M", "40-49_Pct", 
"50+_A-M", "50+_Pct", 
"XPM", "XPA", "XP_Pct", "XP_Blk"]

# gets stats from nfl.com and saves them as dataframes
def get_and_save_stats(season='post', start=2010, to=2020, rewrite=False):
    i = 0
    for year in range(start, to):
        # perform a check, if already saved, don't retrieve
        if (not rewrite) and os.path.exists(os.path.join("data", season, "kickers_"+season+"_"+str(year)+".pkl")):
            i += 1
            continue
        
        url = "http://www.nfl.com/stats/categorystats?archive=true&conference=null&statisticCategory=FIELD_GOALS&season="+str(year)+"&seasonType="+season.upper()+"&experience=&tabSeq=0&qualified=false&Submit=Go"
        r = requests.get(url)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find_all("table")[0] # get the data table
        rows = table.find_all("tr")[2:]
        
        kickers = []
        for row in rows: # go through all kickers
            kicker = []
            pieces = row.find_all("td")
            for piece in pieces:
                kicker.append(piece.text.strip())
            kickers.append(kicker)
        
        kickers_df = pd.DataFrame(kickers, columns=headers)
        kickers_df = kickers_df.drop(['Rank', 'Pos'], axis=1)
        
        # there are two Wayne Walkers in 1968, the other also appears in 1967
        if year==1968 and season=='reg':
            kickers_df.iloc[22]['Player'] = 'Wayne Walker (1)'
        kickers_df.to_pickle(os.path.join("data", season, "kickers_"+season+"_"+str(year)+".pkl"))
    if i > 0:
        print(i, " files already existed")
    return

# does some preprocessing work to dataframe, like dropping pcts and splitting attempted and made for ranges
def read_year_to_combine(year, season="post", ranges=True):
    kickers_df = pd.read_pickle(os.path.join("data", season, "kickers_"+season+"_"+str(year)+".pkl"))
    kickers_df = kickers_df.drop(['Pct', '1-19_Pct', '20-29_Pct', '30-39_Pct', '40-49_Pct', '50+_Pct', 'XP_Pct'], axis=1)
    
    # split attempts and made apart for fg ranges
    for col in ['1-19_A-M', '20-29_A-M', '30-39_A-M', '40-49_A-M', '50+_A-M']:
        kickers_df[col] = kickers_df[col].str.replace("--", "0-0", regex=False)
        am = kickers_df[col]
        a = am.apply(lambda x: x.split('-')[0])
        m = am.apply(lambda x: x.split('-')[1])
        kickers_df = kickers_df.drop([col], axis=1)
        if ranges:
            kickers_df[col[:-2]] = a
            kickers_df[col[:-3]+'M'] = m
    
    plh_df = kickers_df[['Player', 'Team']]
    kickers_df = kickers_df.drop(['Player', 'Team'], axis=1)
    for col in kickers_df.columns:
        kickers_df[col] = kickers_df[col].str.replace("--", "0", regex=False)
    final_df = kickers_df.astype('int32') # convert types
    return pd.concat([plh_df, final_df], axis=1)

# combines range(start, end) from season and returns that summed dataframe
def combine_years(season='post', start=2010, to=2020, teams=False, ranges=True):
    total_df = read_year_to_combine(start, season, ranges)
    total_df.set_index('Player', inplace=True)
    team_df = total_df['Team']
    long_df = total_df['Lng']
    total_df.drop(['Team', 'Lng'], axis=1, inplace=True)
    total_df['PSs'] = 1
    
    for year in range(start+1, to):
        df = read_year_to_combine(year, season, ranges)
        df = df.set_index('Player')
        df['PSs'] = 1
        
        # Separate columns
        team = df['Team']
        long = df['Lng']
        df.drop(['Team', 'Lng'], axis=1, inplace=True)
        
        # Add
        total_df = total_df.add(df, axis=0, fill_value=0)
        team_df = pd.DataFrame(team_df).add(pd.DataFrame(team), axis=0, fill_value="")
        
        long_df = pd.concat([long_df, long], axis=1, sort=True)
    total_df['Lng'] = long_df.max(axis=1)
    if teams:
        total_df['Team'] = team_df
    return total_df

# to generate csvs for Kaggle
def generate_csv(season='reg', start=2000, to=2020):
    for year in range(start, to):
        read_year_to_combine(year, season).to_csv(os.path.join('csvs', season, season+'_'+str(year)+'.csv'), index=False)
    combine_years(season, start, to, teams=True).to_csv(os.path.join('csvs', 'combined_'+season+"_"+str(start)+"_"+str(to-1)+'.csv'))
    return

