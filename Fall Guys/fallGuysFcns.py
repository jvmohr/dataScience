from fallGuysStructures import *
import os, datetime, time
import pandas as pd
import numpy as np

HOURS_DIFFERENTIAL = 6

def cleanLines(lines):
    return [line.replace('[', '').replace(']', '').replace('>', '').strip() for line in lines]

# splits show into show data and rounds
def roundSplit(lines):
    lines = cleanLines(lines)
    splits = []
    # start of each round in highlights section
    for i, line in enumerate(lines):
        if 'Round' in line:
            splits.append(i)
    
    splits.append(0)
    # split it into rounds
    rounds = [lines[splits[i-1]:splits[i]] if i != len(splits)-1 else lines[splits[i-1]:]
              for i in range(1, len(splits))]
    
    return lines[1:splits[0]], rounds

# takes registered and connected lines
# returns start times for rounds
# (time at which game is found)
def getStartTimes(reg, conne):
    startTimes = []
    
    for i in range(len(conne)):
        try:
            registeredTime = datetime.datetime.strptime(reg[i].split('at: ')[-1], '%m/%d/%Y %I:%M:%S %p')
        except:
            registeredTime = datetime.datetime.strptime(reg[i].split('check - ')[-1], '%m/%d/%Y %I:%M:%S %p')
        connectedTime = datetime.datetime.strptime(conne[i].split(': [')[0], '%H:%M:%S.%f')
        
        d = (connectedTime - registeredTime)
        startTimes.append(registeredTime + (d - datetime.timedelta(days=d.days+1, hours=HOURS_DIFFERENTIAL)))
    
    return startTimes

def getTimeTaken(start, end):
    d = datetime.datetime.strptime(end, '%H:%M:%S.%f') - start
    # start time was already adjusted for HOURS_DIFFERENTIAL, so need to again
    return str(d - datetime.timedelta(days=d.days, hours=HOURS_DIFFERENTIAL))[2:] # so hours isn't included

# expand on this later
def getSeason(start_time):
    season_starts = {1: datetime.datetime.strptime("08/04/2020 11:00:00 AM", '%m/%d/%Y %I:%M:%S %p'), 
                    2: datetime.datetime.strptime("10/08/2020 11:00:00 AM", '%m/%d/%Y %I:%M:%S %p'), 
                    3: datetime.datetime.strptime("12/15/2020 11:00:00 AM", '%m/%d/%Y %I:%M:%S %p') }
    
    curr_day = start_time - datetime.timedelta(hours=HOURS_DIFFERENTIAL) # offset timezone
    
    for ky in sorted(list(season_starts.keys()), reverse=True):
        if curr_day > season_starts[ky]:
            return ky
        
    return 'undetermined'
    

# gets lines for CompletedEpisode section of a show
def getShowLines(lines, marker):
    finalLines = []
    tempLines = lines[marker:]
    for line in tempLines:
        if line == '': 
            continue
        if '>' == line[0] or '[Round' in line or '[Complet' in line:
            finalLines.append(line)
            continue
        if ':' in line:
            break
            
    return finalLines

# get map info lines (qual percent and # participants)
def getExtraRoundInfoLines(possLines): # rename?
    rnds = []
    currRnd = possLines[0][1].split()[0]
    currSID = possLines[0][0]
    prevLine = possLines[0][2]
    
    # get last line before map switches (and server ID)
    for i, (serverID, line, line_num) in enumerate(possLines):
        rnd = line.split()[0]
        
        if rnd != currRnd: 
            currRnd = rnd
            currSID = serverID
            rnds.append(possLines[i-1][1])
            if (prevLine + 1) == line_num: # sometimes server changes map due to a dropout
                rnds.pop()      
        elif serverID != currSID:
            currRnd = rnd
            currSID = serverID
            rnds.append(possLines[i-1][1])
            if (prevLine + 1) == line_num:
                rnds.pop()
        prevLine = line_num
    
    rnds.append(possLines[-1][1])      
    return rnds

# preprocessGrade1 has been retired
# remove lines in-between completed games
def preprocessGrade2(lines):
    #print(len(lines))
    lines2 = []
    allGood = False
    badgeID = False
    for line in lines:
        if '[CATAPULT] Login Succeeded' in line:
            allGood = True
        if 'BadgeId:' in line:
            badgeID = True
        if badgeID:
            if '[ClientGlobalGameState] ShutdownNetworkManager' in line:
                badgeID = False
                allGood = False
                lines2.append(line)

        if allGood:
            lines2.append(line)
    lines = lines2
    #print(len(lines))
    return lines

# changes to the data extraction removed the need for this
def preprocessGrade3(lines):
    #print(len(lines))
    start_conn = -1
    to_remove = []
    in_conn = False
    for i, line in enumerate(lines):
        if "[StateConnectToGame] We're connected to the server!" in line:
            start_conn = i
            in_conn = True
        if 'reports that it is not yet ready to accept connections.' in line:
            if in_conn:
                to_remove.append([start_conn, i])
                in_conn = False
    
    temp_lines = []
    for i, line in enumerate(lines):
        for check in to_remove:
            if i >= check[0] and i <= check[1]:
                continue
            temp_lines.append(line)
            
    #print(len(temp_lines))
    return temp_lines

# remove spectated rounds
def preprocessGrade4(lines):
    #print(len(lines))
    start_round = -1
    to_remove = []
    in_spec = False
    for i, line in enumerate(lines):
        if "Received instruction that server is ending a round, and to rejoin" in line:
            if in_spec: # finals hit this text before shutdown 
                to_remove.append([start_round, i])
                in_spec = False
            start_round = i
        if 'permission=Spectator' in line:
            in_spec = True
        if '[ClientGameManager] Shutdown' in line:
            if in_spec:
                to_remove.append([start_round, i])
                in_spec = False
                
    # remove selected lines
    temp_lines = []
    for i, line in enumerate(lines):
        to_append = True
        for check in to_remove:
            if i >= check[0] and i <= check[1]:
                to_append = False
        if to_append or 'Received disconnect reason from Catapult:' in line:
            temp_lines.append(line)
    
    #print(len(temp_lines))
    return temp_lines

# gets rid of shows in which the user got disconnected ()
def preprocessGrade5(lines):
    #print(len(lines))
    
    start_conn = -1
    to_remove = []
    in_conn = False # really just after first show starts
    end_ep = False
    
    for i, line in enumerate(lines):
        if '[CATAPULT] Login Succeeded' in line:
            if in_conn and not end_ep:
                to_remove.append([start_conn, i-1])
            start_conn = i
            in_conn = True
            end_ep = False
            
        if '[CompletedEpisodeDto]' in line:
            end_ep = True
                
    # remove selected lines
    temp_lines = []
    for i, line in enumerate(lines):
        to_append = True
        for check in to_remove:
            if i >= check[0] and i <= check[1]:
                to_append = False
        if to_append or 'Received disconnect reason from Catapult:' in line:
            temp_lines.append(line)
         
    #print(len(temp_lines))
    return temp_lines

# helper function (to account for if round wraps around midnight)
def subtractHours(a, b):
    c = (datetime.datetime.strptime(b, '%H:%M:%S.%f') - datetime.datetime.strptime(a, '%H:%M:%S.%f'))
    return str(c - datetime.timedelta(days=c.days))

# save data in csvs
def saveData(show, roundsList):
    new_shows_df = pd.DataFrame(pd.Series(show)).T
    new_rounds_df = pd.DataFrame(roundsList)
    try:
        #load them
        shows_df = pd.read_csv(os.path.join('data', 'shows.csv'))
        rounds_df = pd.read_csv(os.path.join('data', 'rounds.csv'))
        
        if str(show['Start Time'])[:21] in [tm[:21] for tm in shows_df['Start Time'].tolist()]:
            return False
        
        # append
        shows_df = shows_df.append(new_shows_df, ignore_index=True)
        rounds_df = rounds_df.append(new_rounds_df, ignore_index=True)
    except: # first time
        shows_df = new_shows_df
        rounds_df = new_rounds_df
        print('first time...creating csvs')
    
    # write them to their respective files
    shows_df.to_csv(os.path.join('data', 'shows.csv'), index=False)
    rounds_df.to_csv(os.path.join('data', 'rounds.csv'), index=False)
    return True

# gets path for each session, in order
def getSessions():
    # if running sessionX.txt, don't rerun preprocessing... (bool if session in argument path)
    def splitMe(x):
        return int(x.split('.txt')[0].split('session')[1])

    paths = []
    ss = sorted(os.listdir(os.path.join('personal', 'data', 'archive')), key=splitMe)
    for s in ss:
        paths.append(os.path.join('data', 'archive', s))
        
    return paths

# gets round times
def getRoundTimes(startRoundLines, userEndRoundLines, actualEndRoundLines):
    roundTimes = []
    for a, b in zip(startRoundLines, userEndRoundLines):
        roundTimes.append(subtractHours(a, b))

    # get total round time
    actualRoundTimes = []
    for a, b in zip(startRoundLines, actualEndRoundLines):
        try:
            actualRoundTimes.append(subtractHours(a, b))
        except ValueError:
            actualRoundTimes.append('uncertain')
    
    return roundTimes, actualRoundTimes

def getTZ():
    # https://stackoverflow.com/a/10854983
    offset = time.timezone if (time.localtime().tm_isdst == 0) else time.altzone
    tz = offset / 60 / 60 
    return int(tz) # set time zone each time

# ***********************************************************************************
# for exploration *******************************************************************
# ***********************************************************************************
# in case of fire, use this code
# don't save rounds_df down here as some parts of it are changed

def undoSeconds(x):
    if x == 'uncertain': return x
    
    w = str(x)
    ms = w.split('.')[1]
    ms = int(str(round(float('0.'+ms), 3)).split('.')[1]+'000')
    y = int(w.split('.')[0])
    m = y // 60
    s = y - (60*m)

    return '0:'+datetime.datetime(1, 1, 1, minute=m, second=s, microsecond=ms).strftime("%M:%S.%f")

#rounds_df['Bonus Tier'] = rounds_df['Bonus Tier'].apply(lambda x: x if x != 3 else float('nan'))
#rounds_df['Time Spent'] = rounds_df['Time Spent'].apply(undoSeconds)
#rounds_df['Round Length'] = rounds_df['Round Length'].apply(undoSeconds)
#rounds_df.to_csv(os.path.join('personal', 'data', 'rounds.csv'), index=False)

def getSeconds(x):
    if x == 'uncertain': return x
    w = datetime.datetime.strptime(x, '%H:%M:%S.%f').time()
    return float(str(w.hour + w.minute * 60 + w.second) + '.' + str(w.microsecond))

def getShowSeconds(x):
    w = datetime.datetime.strptime(x, '%M:%S.%f').time()
    return float(str(w.minute * 60 + w.second) + '.' + str(w.microsecond))

def getDataFrames():
    print('get rid of personal in path')
    shows_df = pd.read_csv(os.path.join('personal', 'data', 'shows.csv'))
    rounds_df = pd.read_csv(os.path.join('personal', 'data', 'rounds.csv'))
    
    shows_df['Game Mode'] = shows_df['Game Mode'].apply(lambda x: x.strip())
    shows_df['Time Taken'] = shows_df['Time Taken'].apply(getShowSeconds)
    rounds_df['Time Spent'] = rounds_df['Time Spent'].apply(getSeconds)
    rounds_df['Round Length'] = rounds_df['Round Length'].apply(getSeconds)
    rounds_df['Bonus Tier'] = rounds_df['Bonus Tier'].fillna(3) 

    qual_df = rounds_df[rounds_df['Qualified']].copy()
    qual_df['Round Length'] = qual_df['Round Length'].astype(float);
    return shows_df, rounds_df, qual_df

def getMapInfoDataFrame(rounds_df, qual_df):
    grouped_rounds = rounds_df.groupby('Map')
    grouped_rounds_sum = grouped_rounds.sum()
    grouped_rounds_mean = grouped_rounds.mean()
    bonus_tiers_counts = grouped_rounds['BadgeId'].value_counts()

    grouped_rounds_dict = {
        'Name': [rounds_info_dict[round_]['Name'] if round_ in rounds_info_dict.keys() else None for round_ in grouped_rounds_sum.index.tolist()], 
        'Type': [rounds_info_dict[round_]['Type'] if round_ in rounds_info_dict.keys() else None for round_ in grouped_rounds_sum.index.tolist()], 
        'Attempts': grouped_rounds.count()['Show ID'], # attempts
        'Times Qualified': grouped_rounds_sum['Qualified'].astype(int), # times qualified
        'Percent Qualified': grouped_rounds_mean['Qualified']*100, # percent qualified
        'Average Position': grouped_rounds_mean['Position'], # avg position
        'Average Qual Position': qual_df.groupby('Map').mean()['Position'], # avg position when qualified
        'Average Qual Time (s)': qual_df.groupby('Map').mean()['Time Spent'], # avg time when qualified
        'Fastest Qual Time (s)': qual_df.groupby('Map').min()['Time Spent'],
        'Average Qual Round Times (s)': qual_df.groupby('Map').mean()['Round Length'], # avg round time when qualified
        'Total Kudos': grouped_rounds_sum['Kudos'] + grouped_rounds_sum['Bonus Kudos'], # total kudos
        'Total Fame': grouped_rounds_sum['Fame'] + grouped_rounds_sum['Bonus Fame'], # total fame
        'Average Kudos': 0, # placeholder
        'Average Fame': 0, # placeholder
        'Average Team Score': grouped_rounds_mean['Team Score'], # avg team score
        # avg bonus tier? replace nan (no bonus) with something?
        'Bonus: Gold': rounds_df.groupby('Map')['BadgeId'].value_counts()[:, 'gold'],
        'Bonus: Silver': rounds_df.groupby('Map')['BadgeId'].value_counts()[:, 'silver'],
        'Bonus: Bronze': rounds_df.groupby('Map')['BadgeId'].value_counts()[:, 'bronze'],
        'Average Tier': rounds_df.groupby('Map')['Bonus Tier'].mean()
    }

    grouped_rounds_dict['Average Kudos'] = grouped_rounds_dict['Total Kudos'] / grouped_rounds_dict['Attempts']
    grouped_rounds_dict['Average Fame'] = grouped_rounds_dict['Total Fame'] / grouped_rounds_dict['Attempts']
    grouped_rounds_dict['Bonus: Gold'] = grouped_rounds_dict['Bonus: Gold'].fillna(0).astype(int)

    maps_df = pd.DataFrame(grouped_rounds_dict).sort_values('Attempts', ascending=False)
    maps_df['Bonus: Gold'] = maps_df['Bonus: Gold'].fillna(0).astype(int)
    maps_df['Bonus: Silver'] = maps_df['Bonus: Silver'].fillna(0).astype(int)
    maps_df['Bonus: Bronze'] = maps_df['Bonus: Bronze'].fillna(0).astype(int)
    # maps_df['Bonus: NoneQ'] = maps_df['Times Qualified'] - maps_df['Bonus: Gold'] - maps_df['Bonus: Silver'] - maps_df['Bonus: Bronze']
    return maps_df

# call once for finals_df and once for non_finals_df
def getRoundInfo(df, finals=False):
    if finals:
        df['Round Num'] = 'final' 
    else:
        df['Round Num'] += 1
    
    new_df = pd.DataFrame(index=df.groupby('Round Num').sum().index)
    new_df['Attempted'] = df.groupby('Round Num').count()['Qualified'].astype(int)
    new_df['Qualified'] = df.groupby('Round Num').sum()['Qualified'].astype(int)
    new_df['Percent'] = 100 * new_df['Qualified'] / new_df['Attempted']
    
    return new_df

def getRoundInfoDataFrame(rounds_df):
    finals_df = rounds_df[np.isin(rounds_df['Map'], list_of_finals)].copy() # just finals
    non_finals_df = rounds_df[~np.isin(rounds_df['Map'], list_of_finals)].copy() # remove finals

    rounds_data_df = getRoundInfo(non_finals_df)
    rounds_data_df = rounds_data_df.append(getRoundInfo(finals_df, finals=True))
    return rounds_data_df

def getShowStats(shows_df):
    shows_dict = {
        'Total Shows': len(shows_df),
        'Total Wins': shows_df['Crowns'].sum(),
        'Total Finals': shows_df['Final'].sum(),
        'Average Time (s)': shows_df['Time Taken'].mean(),
        'Average Rounds': shows_df['Rounds'].mean(),
        'Average Kudos': shows_df['Kudos'].mean(),
        'Average Fame': shows_df['Fame'].mean(),
        '% Made Finals': 100 * shows_df['Final'].sum() / len(shows_df),
        '% Won': 100 * shows_df['Crowns'].sum() / len(shows_df),
        'Total Time (hours)': shows_df['Time Taken'].sum() / 60 / 60,
        'Minutes Per Win': shows_df['Time Taken'].sum() / 60 / shows_df['Crowns'].sum(),
    }
    return shows_dict

def getShowsInfoDataFrame(shows_df):
    overall_shows_dict = {}
    for season in shows_df['Season'].unique():
        temp_df = shows_df[shows_df['Season']==season]
        overall_shows_dict[season] = getShowStats(temp_df)

    overall_shows_dict['total'] = getShowStats(shows_df)
    return pd.DataFrame.from_dict(overall_shows_dict, orient='index')

def getPlaylistInfoDataFrame(shows_df):
    overall_shows_dict = {}
    for pl in shows_df['Game Mode'].unique():
        temp_df = shows_df[shows_df['Game Mode']==pl]
        overall_shows_dict[pl] = getShowStats(temp_df)

    overall_shows_dict['total'] = getShowStats(shows_df)
    return pd.DataFrame.from_dict(overall_shows_dict, orient='index')

