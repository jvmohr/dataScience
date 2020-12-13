# after regular season, add that data to overall csv
# same after post

import requests, os, datetime, sys
from bs4 import BeautifulSoup
import pandas as pd

if len(sys.argv) > 1:
    argument = sys.argv[1]
else:
    argument = 'reg'

year = 2020
if argument == 'post':
    url_insert = str(year) + "&season_type=PS"
    file_start = 'post_' + str(year)
else:
    url_insert = str(year)
    file_start = str(year)

starting_urls = ["https://www.mlssoccer.com/stats/season?year={}&group=g".format(url_insert),
                    "https://www.mlssoccer.com/stats/season?year={}&group=assists".format(url_insert),
                    "https://www.mlssoccer.com/stats/season?year={}&group=fouls&sort=desc&order=YC".format(url_insert),
                    "https://www.mlssoccer.com/stats/season?year={}&group=goalkeeping".format(url_insert)]
dfs = []
descriptions = []

# For each of four stats
for url in starting_urls:
    print('Examining:  ' + url)

    r = requests.get(url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    trs = soup.find_all('tr')
    trs_players = trs[1:]

    # Gets the header row
    header = []
    description = []
    for item in trs[0].contents:
        try:
            header.append(item.text)
        except: # last element is a blank string in contents
            break
        description.append(item.get('title'))

    descriptions.extend(zip(header, description)) # switch to set
    players = []

    # Breaks after last page
    while True:
        # For each player
        for tr_player in trs_players:
            player = []

            # For each data item
            for item in tr_player.contents:
                try:
                    player.append(item.text)
                except:
                    break
            players.append(player)

        # Get link to next page
        try:
            url = soup.find('link', attrs={'rel':'next'}).get('href')
        except:
            break

        # Get next page
        r = requests.get(url)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        trs = soup.find_all('tr')
        trs_players = trs[1:] # disregards the header
    # end while - all pages of a stat

    dfs.append(pd.DataFrame(players, columns=header))
# end for - gathering stats

# merge first 3
if argument == 'post':
    x = pd.merge(dfs[0], dfs[1], how='left', on=['Player', 'POS', 'GP', 'GS', 'A'], copy=True)
    outfield_df = pd.merge(x, dfs[2], how='left', on=['Player', 'POS', 'GP', 'GS', 'A', 'SHTS', 'SOG', 'MINS', 'G'], copy=True)
else:
    x = pd.merge(dfs[0], dfs[1], how='left', on=['Player', 'Club', 'POS', 'GP', 'GS', 'A'], copy=True)
    outfield_df = pd.merge(x, dfs[2], how='left', on=['Player', 'Club', 'POS', 'GP', 'GS', 'A', 'SHTS', 'SOG', 'MINS', 'G'], copy=True)

# Add some columns
# shots on goal percentage column (shots on goal divided by shots)
outfield_df['SOG%'] = (100 * outfield_df['SOG'].astype('int') / outfield_df['SHTS'].astype('int')).round(2)
gk_df = dfs[3]

outfield_df['Year'] = year
gk_df['Year'] = year

outfield_df['Season'] = argument
gk_df['Season'] = argument

# Get current date
today = datetime.datetime.now()
new_folder = str(today.month)+"_"+str(today.day)+"_"+str(today.year)
path = os.path.join('data', 'player_stats', new_folder)
os.makedirs(path)

# Save csvs in folder month_date_year
outfield_df.to_csv(os.path.join(path, file_start+'all_players.csv'), index=False)
gk_df.to_csv(os.path.join(path, file_start+'goalkeeper.csv'), index=False)

# Add it to past player data
all_outfield_df = pd.read_csv(os.path.join('data', 'player_stats', '1996_2019_all_players.csv'))
all_gk_df = pd.read_csv(os.path.join('data', 'player_stats', '1996_2019_goalkeeper.csv'))
all_outfield_df = all_outfield_df.append(outfield_df, ignore_index=True)
all_gk_df = all_gk_df.append(gk_df, ignore_index=True)
all_outfield_df.to_csv(os.path.join('data', 'player_stats', 'all_players.csv'), index=False)
all_gk_df.to_csv(os.path.join('data', 'player_stats', 'all_goalkeepers.csv'), index=False)
