import requests, os, datetime, json
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

# Grabs the current table and not past ones

# TO CHANGE ------------------------------
# switch these to command line arguments
year = '2020' # if season is split over two years (ie 2020-2021), put the first year here
folder_name = 'epl'
league = 'ENG.1'
old_csv = '2001_2020_tables.csv'
# ----------------------------------------

# GP W D L GF GA GD P
cols = ['Place', 'Team', 'GP', 'W', 'D', 'L', 'GF', 'GA', 'GD', 'P'] # may need to switch these for other leagues (but prob not)
table_df = pd.DataFrame([], columns=cols)

url = "https://www.espn.com/soccer/standings/_/league/{}/season/{}".format(league, year) 

r = requests.get(url)
r.raise_for_status()
soup = BeautifulSoup(r.text, "html.parser")

teams_soup = soup.find_all('table')[0].find_all('div', class_='team-link flex items-center clr-gray-03')
teams = []

for team in teams_soup:
    teams.append([team.contents[0].text, team.find('img').get('title')])

stats = soup.find_all('span', class_='stat-cell')

# Convert to np array and reshape
stats = [item.text for item in stats]
np_stats = np.array(stats).reshape(-1, 8)

final_arr = np.concatenate((np.array(teams).reshape(-1, 2), np_stats), axis=1)
temp_df = pd.DataFrame(final_arr, columns=cols)
temp_df['Year'] = year
table_df = table_df.append(temp_df, ignore_index=True)

# if folder doesn't exist, make it
tpath = os.path.join('data', folder_name, 'tables')
if not os.path.exists(tpath):
    os.makedirs(tpath)
    
table_df.to_csv(os.path.join('data', folder_name, 'tables', year + '_table.csv'), index=False)

# Add it to past tables
if old_csv != '':
    all_tables_df = pd.read_csv(os.path.join('data', folder_name, 'tables', old_csv))
    all_tables_df = all_tables_df.append(table_df, ignore_index=True)
    all_tables_df.to_csv(os.path.join('data', folder_name, 'tables', 'all_tables.csv'), index=False)
