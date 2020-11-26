import os, datetime
import pandas as pd

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
        registeredTime = datetime.datetime.strptime(reg[i].split('at: ')[-1], '%m/%d/%Y %H:%M:%S %p')
        connectedTime = datetime.datetime.strptime(conne[i].split(': [')[0], '%H:%M:%S.%f')
        
        d = (connectedTime - registeredTime)
        startTimes.append(registeredTime + (d - datetime.timedelta(days=d.days, hours=HOURS_DIFFERENTIAL)))
    
    return startTimes

def getTimeTaken(start, end):
    d = datetime.datetime.strptime(end, '%H:%M:%S.%f') - start
    # start time was already adjusted for HOURS_DIFFERENTIAL, so need to again
    return str(d - datetime.timedelta(days=d.days, hours=HOURS_DIFFERENTIAL))[2:] # so hours isn't included

# edit this later change
# grab the last Seasonthing in txt file - countdown in .log
# if its larger than the last one, then the season reset
def getSeason():
    return 2

# gets lines for CompletedEpisode section of a show
def getShowLines(lines, marker):
    finalLines = []
    tempLines = lines[marker:]
    for line in tempLines:
        if line == '':
            continue
        if '>' not in line and '[Round' not in line and '[Complet' not in line:
            break
        if line != "":
            finalLines.append(line)
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
        if to_append:
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