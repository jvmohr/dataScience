from league_data_dict import league_data_dict
from bs4 import BeautifulSoup

import requests, os, datetime
import pandas as pd
import numpy as np
import time as tm

# For Aggregated Stats
def cleanDF(df):
    df[['RK', 'Team']] = df[['RK', 'Team']].fillna(method="ffill")
    df['RK'] = df['RK'].astype(int)
    return df

def updateDF(new_df, file_name, current_year, folder_name):
    temp_df = pd.read_csv(os.path.join('data', folder_name, 'agg_stats', file_name))
    temp_df = temp_df.drop(temp_df[temp_df['YEAR'] == current_year].index) # drop current year
    return temp_df.append(new_df) # add the updated version

def getSoup(url):
    while True:
        try:
            r = requests.get(url)
            r.raise_for_status()
            break
        except:
            tm.sleep(2)
    return BeautifulSoup(r.text, "html.parser")

def getAggStats(chosen_league, update=True, end_season=2022):
    league = league_data_dict[chosen_league]['Code']
    start_year = league_data_dict[chosen_league]['First Year - Agg Stats']
    folder_name = league_data_dict[chosen_league]['Folder']

    # if folder doesn't exist, make it
    apath = os.path.join('data', folder_name, 'agg_stats')
    if not os.path.exists(apath):
        os.makedirs(apath)

    # Only want to update current season
    if update:
        start_year = end_season - 1

    all_goals_df = pd.DataFrame()
    all_assists_df = pd.DataFrame()
    all_disc_df = pd.DataFrame()

    # For each year
    for year in range(start_year, end_season):
        # Scoring
        url = 'https://www.espn.com/soccer/stats/_/league/{}/season/{}'

        soup = getSoup(url.format(league, year))

        try:
            goals_df, assists_df = pd.read_html(str(soup))
        except:
            print('found no tables in {}'.format(year))
            continue

        goals_df = cleanDF(goals_df)
        goals_df['YEAR'] = year
        assists_df = cleanDF(assists_df)
        assists_df['YEAR'] = year

        # Discipline
        url = 'https://www.espn.com/soccer/stats/_/league/{}/season/{}/view/discipline'
        r = requests.get(url.format(league, year))
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        disc_df = pd.read_html(str(soup))[0]
        disc_df['RK'] = disc_df['RK'].fillna(method='ffill').astype(int)
        disc_df['YEAR'] = year

        # Append
        all_goals_df = all_goals_df.append(goals_df)
        all_assists_df = all_assists_df.append(assists_df)
        all_disc_df = all_disc_df.append(disc_df)

    # if just an update is wanted
    # update the df with the new data
    if update:
        all_goals_df = updateDF(all_goals_df, 'goal_leaders.csv', start_year, folder_name)
        all_assists_df = updateDF(all_assists_df, 'assist_leaders.csv', start_year, folder_name)
        all_disc_df = updateDF(all_disc_df, 'team_discipline.csv', start_year, folder_name)

    # Save them
    all_goals_df.to_csv(os.path.join('data', folder_name, 'agg_stats', 'goal_leaders.csv'), index=False)
    all_assists_df.to_csv(os.path.join('data', folder_name, 'agg_stats', 'assist_leaders.csv'), index=False)
    all_disc_df.to_csv(os.path.join('data', folder_name, 'agg_stats', 'team_discipline.csv'), index=False)
    print('Saved Agg Stats for {}'.format(chosen_league))
    return

# For Table
def getTable(chosen_league, end_season=2022):
    start_year = league_data_dict[chosen_league]['First Year - Table']
    league = league_data_dict[chosen_league]['Code'] # put league or competition here
    folder_name = league_data_dict[chosen_league]['Folder']


    file_name = '{}_{}_tables.csv'.format(start_year, end_season-1)
    url = "https://www.espn.com/soccer/standings/_/league/{}/season/{}"

    # GP W D L GF GA GD P
    cols = ['Place', 'Team', 'GP', 'W', 'D', 'L', 'GF', 'GA', 'GD', 'P'] # may need to change if other leagues have other cols
    table_df = pd.DataFrame([], columns=cols)

    for year in range(start_year, end_season): # possibly change these
        r = requests.get(url.format(league, year))
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        teams_soup = soup.find_all('table')[0].find_all('div', class_='team-link flex items-center clr-gray-03')

        teams = []
        for team in teams_soup:
            teams.append([team.contents[0].text, team.find('img').get('title')])

        stats = soup.find_all('span', class_='stat-cell')

        # convert to np array and reshape
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

    table_df['Year'] = table_df['Year'].astype(int)
    table_df.to_csv(os.path.join('data', folder_name, 'tables', file_name), index=False)
    table_df.to_csv(os.path.join('data', folder_name, 'tables', 'all_tables.csv'), index=False)
    print('Saved Table(s) for {}'.format(chosen_league))
    return

# For Game Stats
def getGameData(chosen_league, url_date, stop_date, commentary=True, end_season=2022, verbose=True):
    # url_date and stop_date like "20210130" (yyyymmdd) 
    league = league_data_dict[chosen_league]['Code']
    folder_name = league_data_dict[chosen_league]['Folder']

    one_week = datetime.timedelta(7)
    match_df = pd.DataFrame()
    events_df = pd.DataFrame()
    year = url_date[:4]
    url = "https://www.espn.com/soccer/fixtures/_/date/{}/league/{}"

    try:
        ma_df = pd.read_csv(os.path.join('data', folder_name, 'game_stats', 'matches.csv'))
        list_of_matches = ma_df['id'].unique()
    except:
        list_of_matches = []

    while True: 
        # Get page for week of games
        tm.sleep(2)
        while True:
            try:
                r = requests.get(url.format(url_date, league))
                r.raise_for_status()
                break
            except:
                print('here1', url.format(url_date, league))
                tm.sleep(2)

        if verbose:
            print('Looking at...', url_date)
        soup = BeautifulSoup(r.text, "html.parser")

        current_date = datetime.datetime.strptime(url_date, "%Y%m%d")

        # get all games
        stuff = soup.find_all('div', attrs={'id':'sched-container'})[0]

        # if there are no games, keep going
        if stuff.text == 'No games scheduled':
            url_date = (current_date + one_week).strftime("%Y%m%d")
            continue

        # zip each chunk of games with it's header (the date)
        for h2, table in zip(stuff.find_all('h2'), stuff.find_all('table')):
            matches = table.find_all('tr', class_=['even has-results', 'odd has-results'])

            # go through each match
            for match in matches:
                match_dict = {}
                parts = match.find_all('span')
                # parts[2].text # score (should be added under matchstats)

                match_dict['id'] = parts[2].find('a').get('href').split('=')[-1]

                if int(match_dict['id']) in list_of_matches: # game already saved
                    continue

                game_url = "https://www.espn.com" + parts[2].find('a').get('href')
                game_url = game_url.replace('report', '{}').replace('matchstats', "{}")

                tm.sleep(2)
                while True:
                    try:
                        r = requests.get(game_url.format('match'))
                        r.raise_for_status()
                        break
                    except:
                        print('here2', game_url.format('match'))
                        tm.sleep(2)
                soup = BeautifulSoup(r.text, "html.parser")

                # if this fails, the game doesn't have data
                # likely postponed
                try:
                    time = soup.find('li', class_='subdued').find_all('div')[0].find('span').get('data-date')
                except:
                    print(match_dict['id'], 'skipped')
                    continue

                # check to see if the game already happened
                # possibly find a better way
                game_status = soup.find('div', class_='game-status').text.strip()
                if game_status == "Postponed":
                    print(match_dict['id'], 'postponed')
                    continue
                elif game_status == "":
                    print(match_dict['id'], 'future match')
                    continue  
                elif game_status == "Canceled":
                    print(match_dict['id'], 'canceled')
                    continue

                # ---------------------------------------------------------
                # ------------------------ GENERAL ------------------------
                # ---------------------------------------------------------
                match_dict['home'] = parts[0].text # home
                match_dict['away'] = parts[-1].text # away
                match_dict['date'] = h2.text.strip()
                match_dict['year'] = year
                match_dict['time (utc)'] = datetime.datetime.strptime(time.replace('Z', 'UTC'), "%Y-%m-%dT%H:%M%Z").strftime("%H:%M%z")
                match_dict['attendance'] = match.find_all('td')[-1].text # attendance
                match_dict['venue'] = match.find_all('td')[-2].text

                # one game per year (or less) 
                # not for points, just for fun (against a top Euro team)
                if match_dict['home'] == "MLS All-Stars":
                    print('skipped All-Star Game ... id:', match_dict['id'])
                    continue

                # ------------------------------------------------------------------
                # --------------------------- MATCHSTATS ---------------------------
                # ------------------------------------------------------------------
                try: # MLS has a regular season and a postseason
                    match_dict['league'] = soup.find('div', class_='game-details header').text.strip().split(',')[0]
                    match_dict['part_of_competition'] = soup.find('div', class_='game-details header').text.strip().split(',')[1]
                except: # most leagues/competitions don't have a postseason
                    match_dict['league'] = soup.find('div', class_='game-details header').text.strip()
                    match_dict['part_of_competition'] = "na"

                # FT/ FT-Pens/ maybe some others
                try: 
                    match_dict['game_status'] = game_status
                except:
                    match_dict['game_status'] = ""

                # important for knockout round games
                # same information could be gathered from 'game_status' 
                # (not sure if this applies to all leagues and older games)
                try:
                    if soup.find('article', class_='sub-module penalty-shootout').get('style') is None:
                        match_dict['shootout'] = True
                    else:
                        match_dict['shootout'] = False
                except:
                    match_dict['shootout'] = False

                # get all stats
                stats = soup.find_all(['span', 'td'], attrs={'data-home-away':['home', 'away']})
                for item in stats:
                    if item.text.strip() != '':
                        match_dict[item.get('data-home-away') + "_" + item.get('data-stat')] = item.text.strip()

                # -----------------------------------------------------------------
                # ----------------------------- GOALS -----------------------------
                # -----------------------------------------------------------------
                goals = soup.find_all('div', class_='team-info players')
                try:
                    home_goals = goals[0].find_all('ul', attrs={'data-event-type':'goal'})[0].find_all('li')
                except:
                    home_goals = []
                try:
                    away_goals = goals[1].find_all('ul', attrs={'data-event-type':'goal'})[0].find_all('li')
                except:
                    away_goals = []

                i = 0
                home_goal_minutes = []
                home_goal_scorers = []
                for goal in home_goals:
                    scorer = goal.contents[0].strip()
                    minute = goal.contents[1].text.strip().replace('(', "").replace(')', "")
                    try:
                        minutes = minute.split(',')
                        for minute in minutes:
                            home_goal_minutes.append(minute)
                            home_goal_scorers.append(scorer)
                    except:
                        home_goal_minutes.append(minute)
                        home_goal_scorers.append(scorer)

                i = 0
                away_goal_minutes = []
                away_goal_scorers = []
                for goal in away_goals:
                    scorer = goal.contents[0].strip()
                    minute = goal.contents[1].text.strip().replace('(', "").replace(')', "")
                    try:
                        minutes = minute.split(',')
                        for minute in minutes:
                            away_goal_minutes.append(minute)
                            away_goal_scorers.append(scorer)
                    except:
                        away_goal_minutes.append(minute)
                        away_goal_scorers.append(scorer)

                match_dict['home_goal_minutes'] = ":".join(home_goal_minutes)
                match_dict['home_goal_scorers'] = ":".join(home_goal_scorers)
                match_dict['away_goal_minutes'] = ":".join(away_goal_minutes)
                match_dict['away_goal_scorers'] = ":".join(away_goal_scorers)

                # ---------------------------------------------------------
                # ------------------------ LINEUPS ------------------------
                # ---------------------------------------------------------
                # get the team formations
                try:
                    soup.find('div', class_='game-details header')
                    match_dict['home_formation'] = soup.find_all('div', class_='formations__text')[0].text
                    match_dict['away_formation'] = soup.find_all('div', class_='formations__text')[1].text
                except:
                    pass

                team = 'home_'
                j = 0 # which block for loop is in
                lineups = soup.find_all('tbody')
                lineups = [group.find_all('div', class_='accordion-header lineup-player') for group in lineups[1:5]]
                if len(lineups) == 3:
                    lineups = [lineups[0], [], lineups[1], lineups[2]]

                for group in lineups:
                    if j == 2: team = 'away_'

                    section = 'starting_' if j % 2 == 0 else 'bench_'
                    i = 1

                    for block in group:
                        # if true, they were subbed in
                        if block.find('span', attrs={'style':' display:inline-block; width: 24px;'}) is None: 
                            if j == 0 or j == 2: # if sub is in starting lineup, they started on the bench
                                lineups[j+1].append(block) # add them to their respective bench
                                continue
                            else: # now add them
                                match_dict[team + section + str(i) + '_num'] = block.find('span', class_='name').contents[-1].strip()
                                match_dict[team + section + str(i)] = block.find('a').text.strip()
                                try:
                                    match_dict[team + section + str(i) + "_minute"] = block.find('span', class_='detail').text
                                except:
                                    match_dict[team + section + str(i) + "_minute"] = 'not given'
                                i += 1
                                continue

                        # starting players and bench players that weren't subbed on
                        match_dict[team + section + str(i) + '_num'] = block.find('span', attrs={'style':' display:inline-block; width: 24px;'}).text
                        match_dict[team + section + str(i)] = block.find('a').text.strip()
                        if j == 1 or j == 3:
                            match_dict[team + section + str(i) + "_minute"] = "na"
                        i += 1
                    j += 1

                # ------------------------------------------------------------------
                # --------------------------- COMMENTARY ---------------------------
                # ------------------------------------------------------------------
                # redo this section...doesn't look too good
                events_list = []
                if commentary:
                    try:
                        while True:
                            try:
                                r = requests.get(game_url.format('commentary'))
                                r.raise_for_status()
                                break
                            except:
                                print('here3', game_url.format('commentary'))
                                tm.sleep(2)
                        soup = BeautifulSoup(r.text, "html.parser")

                        # get all events
                        events = soup.find_all('table')[2].find_all('tr') # switch to 3 for just key events
                        # '2' is key events if all commentary is absent

                        for event in events:
                            events_list.append([match_dict['id'], 
                                                    event.find('td', class_='time-stamp').text, 
                                                    event.find('td', class_='game-details').text.strip()])

                        events_list = events_list[::-1] # reverse it so start of match is at the top


                    except:
                        print(match_dict['id'], 'no commentary')
                        events_list.append([match_dict['id'], '-', 'no commentary'])
                else:
                    events_list.append([match_dict['id'], '-', 'no commentary'])

                # Add data to dataframes - prob should build up lists instead
                match_df = match_df.append(pd.DataFrame(match_dict, index=[0]), ignore_index=True)
                events_df = events_df.append(pd.DataFrame(events_list, columns=['id', 'Time', 'Event']), ignore_index=True)

            # end - for each match

        # move url_date back (or forward? just switch - to + in other places as well)
        url_date = (current_date + one_week).strftime("%Y%m%d")


        # add some stopping condition
        if url_date > stop_date:
            break

    # Save the data
    spath = os.path.join('data', folder_name, 'game_stats', year)
    if not os.path.exists(spath):
        os.makedirs(spath)
    else: # if it's already there, add new data to end of old
        m_df = pd.read_csv(os.path.join(spath, year+'_matches.csv'))
        e_df = pd.read_csv(os.path.join(spath, year+'_events.csv'))
        match_df = m_df.append(match_df, ignore_index=True)
        events_df = e_df.append(events_df, ignore_index=True)

    match_df.to_csv(os.path.join(spath, year+'_matches.csv'), encoding='utf-8-sig', index=False)
    events_df.to_csv(os.path.join(spath, year+'_events.csv'), encoding='utf-8-sig', index=False)

    # Combines the seasons into matches.csv, events.csv
    first_year = league_data_dict[chosen_league]['First Year']
    matches_df = pd.read_csv(os.path.join('data', folder_name, 'game_stats', str(first_year), str(first_year)+'_matches.csv'))
    events_df = pd.read_csv(os.path.join('data', folder_name, 'game_stats', str(first_year), str(first_year)+'_events.csv'))

    # Read in first one
    for year in range(first_year+1, end_season):
        # read it in
        m_df = pd.read_csv(os.path.join('data', folder_name, 'game_stats', str(year), str(year)+'_matches.csv'))
        e_df = pd.read_csv(os.path.join('data', folder_name, 'game_stats', str(year), str(year)+'_events.csv'))

        # combine it
        matches_df = matches_df.append(m_df, ignore_index=True)
        events_df = events_df.append(e_df, ignore_index=True)

    matches_df.to_csv(os.path.join('data', folder_name, 'game_stats', 'matches.csv'), encoding='utf-8-sig', index=False)
    events_df.to_csv(os.path.join('data', folder_name, 'game_stats', 'events.csv'), encoding='utf-8-sig', index=False)

    print('Saved Game Data for {}'.format(chosen_league))
    return

# To combine data
def combineData(leagues, folder_name):
    # if folders don't exist, make them
    epath = os.path.join('data', folder_name)
    if not os.path.exists(epath):
        os.makedirs(epath)

    if not os.path.exists(os.path.join(epath, 'agg_stats')):
        os.makedirs(os.path.join(epath, 'agg_stats'))

    all_data_dict = {}

    # for each league
    for league in leagues:
        # for each file
        for path in [os.path.join('agg_stats','goal_leaders.csv' ), 
                     os.path.join('agg_stats', 'team_discipline.csv'), 
                     os.path.join('agg_stats', 'assist_leaders.csv'), 
                     os.path.join('game_stats', 'matches.csv'), 
                     os.path.join('game_stats', 'events.csv'), 
                     os.path.join('tables', 'all_tables.csv'), 
                    ]:

            temp_df = pd.read_csv(os.path.join('data', league_data_dict[league]['Folder'], path))

            # don't need to add it to events
            if 'events.csv' not in path:
                temp_df['League'] = league

            if path not in all_data_dict.keys():
                all_data_dict[path] = pd.DataFrame()

            # append it
            all_data_dict[path] = all_data_dict[path].append(temp_df, ignore_index=True)

    # Save the data
    for key in all_data_dict:
        if 'agg_stats' in key:
            filename = key
        else:
            filename = key.split('\\')[1] # may need to change what key is split on

        all_data_dict[key].to_csv(os.path.join(epath, filename), index=False) 
    
    print('Combined Data for {}'.format(', '.join(leagues)))
    return
