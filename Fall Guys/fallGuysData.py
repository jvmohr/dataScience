import os, datetime, sys
import pandas as pd
from fallGuysFcns import *

if len(sys.argv) > 2:
    fileName = sys.argv
else:
    fileName = 'Player.log'
    
# change these
HOURS_DIFFERENTIAL = 6 # have to subtract 6

# jump is good, not sure on others
list_of_finals = ['round_fallmountain', 'round_hex', 'round_royalfumble', 'round_jump_showdown']

with open('totalshows.txt') as f:
    total_shows = f.read()
total_shows = int(total_shows.strip())


# if data folder doesn't exist, make it
if not os.path.exists('data'):
    os.makedirs('data')
    
with open(os.path.join('C:\\Users','Joseph','AppData','LocalLow','Mediatonic','FallGuys_client',fileName)) as f:
    lines = f.read()

lines = lines.split('\n')
lines = preprocessGrade2(lines)

# get first line of each new show and usernames used for show
prevUser = '!!!!!!!!!!!!!!!'
lookUser = True
inRound = False
inARound = False
gameMode = 'main_show'

episodeMarkers = []
usernames = []
partySizes = []

# times
reg = []
conne = []
startRoundLines = []
userEndRoundLines = []
actualEndRoundLines = []

possLines = []
gameModes = []
# to find the actual number of players that qualified (for racing rounds)
prevNumLine = ""
numLines = []

# **********************************************************
# go through lines, looking for certain things**************
# **********************************************************
for i, line in enumerate(lines):
    # for username
    if lookUser and 'Sending login request' in line:
        usernames.append(line.split(' player ')[-1].split(' networkID')[0].replace(',', ''))
        prevUser = usernames[-1]
        lookUser = False
    # for type of show (main or alternate) (also called playlist)
    elif 'Chosen Show:' in line: # appears before entering matchmaking solo/group
        gameMode = line.split(':')[-1]
    # signifies start of looking for new episode
    # get size of party
    elif 'Party Size' in line or 'Begin matchmaking solo' in line:
        gameModes.append(gameMode)
        if 'Begin matchmaking solo' in line:
            partySize = 1
        else:
            partySize = int(line.split(' ')[-1].strip())
    # for show start time
    elif '[QosManager] Registered' in line or 'QosManager: Registered' in line: # for registered time (date)
        reg.append(line)
    elif "[StateConnectToGame] We're connected to the server!" in line: # for connection time
        conne.append(line)
    # for server ID and map lines
    elif 'Received NetworkGameOptions from ' in line: 
        tmp = line.split('roundID=')[-1]
        serverID = line.split(' ')[4]
        if 'Default' not in tmp:
            possLines.append([serverID, tmp])
    # for start round times and players that qualified from previous round
    elif 'state from Countdown to Playing' in line:
        startRoundLines.append(line.split(': [')[0])
        inRound = True
        inARound = True
        # append last # players achieving obj when hit new round
        if prevNumLine != "":
            numLines.append(prevNumLine.split('=')[-1])
            prevNumLine = ""
    elif '[ClientGameSession] NumPlayersAchievingObjective=' in line: # for total number of players that quality
        prevNumLine = line
    # for end round / player active in round times
    elif '[ClientGameManager] Handling unspawn for player FallGuy' in line and prevUser in line:
        if inRound:
            userEndRoundLines.append(line.split(': [')[0])
            inRound = False
    elif 'Changing local player state to: SpectatingEliminated' in line:
        if inRound:
            userEndRoundLines.append(line.split(': C')[0])
            inRound = False
        if inARound:
            actualEndRoundLines.append(line.split(': C')[0])
            inARound = False
    elif 'Changing state from Playing to GameOver' in line: # 'Changing state from GameOver to Results'
        if inARound:
            inARound = False
            actualEndRoundLines.append(line.split(': [')[0])
    # overall show data
    elif '[CompletedEpisodeDto]' in line: # marker for a good show
        partySizes.append(partySize)
        episodeMarkers.append(i)
        lookUser = True

# append last # achieving obj
numLines.append(prevNumLine.split('=')[-1])

# if no episodes found, end
if len(episodeMarkers) == 0:
    print('no episodes found') # change
        
# **********************************************************        
# get time user spent in each round ************************        
# (time round starts until they either finish or are eliminated) (just qualify I think)
# **********************************************************
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

# gets start times for each show
startTimes = getStartTimes(reg, conne)


# **********************************************************
# for each show/episode ************************************
# **********************************************************
roundIdx = 0
for showIdx, (j, user) in enumerate(zip(episodeMarkers, usernames)):
    this_show = total_shows
    total_shows += 1
    
    # get lines for this show
    final_lines = getShowLines(lines, j)
    
    # split data
    showData, rounds = roundSplit(final_lines)
    
    # set show data
    show_dict = {}
    show_dict['Show ID'] = this_show # id
    show_dict['Start Time'] = startTimes[showIdx]
    show_dict['Season'] = getSeason() 
    show_dict['Time Taken'] = getTimeTaken(startTimes[showIdx], final_lines[0].split(': ==')[0]) # approximate time taken
    show_dict['Game Mode'] = gameModes[showIdx]
    show_dict['Final'] = rounds[-1][0].split('|')[-1].strip() in list_of_finals # final
    show_dict['Rounds'] = len(rounds) # num rounds
    show_dict['Username'] = user
    show_dict['Party Size'] = partySizes[showIdx]
    show_dict['addID'] = final_lines[0].split(': ==')[0] # end time
    
    # add other show data
    for line in showData:
        show_dict[line.split(':')[0]] = line.split(':')[1].strip()
    
    # ********************************************
    # get data for each round in show ************
    # ********************************************
    rounds_list = []
    rnds = getExtraRoundInfoLines(possLines)
    
    # for each round in the show/episode
    for round_ in rounds: # for list in 2D list
        round_dict = {'Show ID': this_show, 
                      'Round Num': round_[0].split(' ')[1].strip(), 
                      'Map': round_[0].split('|')[1].strip()}
        round_dict['Time Spent'] = roundTimes[roundIdx]
        round_dict['Round Length'] = actualRoundTimes[roundIdx]
        
        # add rest of data from list
        for line in round_[1:]:
            round_dict[line.split(':')[0]] = line.split(':')[1].strip()
        
        # add extra information
        rnd = rnds[roundIdx]
        splts = rnd.split()
        round_dict['Participants'] = splts[4].split('=')[-1] # num people
        round_dict['Qualification Percent'] = splts[7].split('=')[-1].replace(',', '') # qual %
        round_dict['Actual Num Qual'] = numLines[roundIdx]
        
        roundIdx += 1
        rounds_list.append(round_dict)
    
    # ********************************************
    # save ***************************************
    # ******************************************** 
    # save show_dict to one table
    # save each dict in rounds_list to another table
    if not saveData(show_dict, rounds_list):
        # print('already in csvsv')
        total_shows -= 1
    else:
        pass # print('saved')

print('csvs saved successfully')

with open('totalshows.txt', 'w') as f:
    f.write(str(total_shows))