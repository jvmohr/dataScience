import requests, os, datetime, json
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

year = '2020'

# GP W D L GF GA GD P
cols = ['Place', 'Team', 'GP', 'W', 'D', 'L', 'GF', 'GA', 'GD', 'P']
table_df = pd.DataFrame([], columns=cols)

url = "https://www.espn.com/soccer/standings/_/league/USA.1/season/{}".format(year)

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

table_df.to_csv(os.path.join('data', 'tables', year + '_tables.csv'), index=False)

# Add it to past tables
all_tables_df = pd.read_csv(os.path.join('data', 'tables', '2003_2019_tables.csv'))
all_tables_df = all_tables_df.append(table_df, ignore_index=True)
all_tables_df.to_csv(os.path.join('data', 'tables', 'all_tables.csv'), index=False)
