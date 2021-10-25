import matplotlib.pyplot as plt
import pandas as pd
from calendar import monthrange
import os, json, datetime

week_days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
full_weekdays = {'Sun': 'Sunday', 'Mon': 'Monday', 'Tue': 'Tuesday', 
                 'Wed': 'Wednesday', 'Thu': 'Thursday', 'Fri': 'Friday', 'Sat': 'Saturday'}
months = ['', 'January', 'February', 'March', 'April', 'May', 'June', 
          'July', 'August', 'September', 'October', 'November', 'December']

# plt.style.use('seaborn')
# make a style?

# reads in files from dire
def getData(dire='MyData'):
    records = pd.DataFrame()
    files = 0
    for file in os.listdir(dire):
        if 'StreamingHistory' in file:
            files += 1
            records = records.append(pd.read_json(os.path.join(dire, file)), ignore_index=True)

    print('{} plays found across {} files.'.format(len(records), files))    
    return records

# converts uploaded data to a DataFrame
def getDataV(files):
    records = pd.DataFrame()
    num_files = 0
    for file in files:
        num_files += 1
        records = records.append(pd.DataFrame.from_dict(json.loads(files[file]['content'])), ignore_index=True)

    print('{} plays found across {} files.'.format(len(records), num_files))    
    return records

def addTimeData(sp_df, tzd):
    sp_df['Month'] = sp_df['endTime'].apply(lambda x: (datetime.datetime.strptime(x, '%Y-%m-%d %H:%M')+datetime.timedelta(hours=tzd)).month)
    sp_df['Date'] = sp_df['endTime'].apply(lambda x: (datetime.datetime.strptime(x, '%Y-%m-%d %H:%M')+datetime.timedelta(hours=tzd)).day)
    sp_df['Year'] = sp_df['endTime'].apply(lambda x: (datetime.datetime.strptime(x, '%Y-%m-%d %H:%M')+datetime.timedelta(hours=tzd)).year)
    sp_df['Day'] = sp_df['endTime'].apply(lambda x: week_days[(datetime.datetime.strptime(x, '%Y-%m-%d %H:%M')+datetime.timedelta(hours=tzd)).weekday()])
    sp_df['Hour'] = sp_df['endTime'].apply(lambda x: (datetime.datetime.strptime(x, '%Y-%m-%d %H:%M')+datetime.timedelta(hours=tzd)).hour)
    return sp_df


# ***********************************************************
# ***********************************************************
# STATS 
# ***********************************************************
# ***********************************************************
def getMinutes(sp_df):
    return sp_df['msPlayed'].sum() / 1000 / 60 # minutes

def getTopTracks(sp_df):
    df = sp_df.groupby(['artistName', 'trackName'])['msPlayed'].count().reset_index()
    df = df.sort_values(by='msPlayed', ascending=False)
    df.columns = ['Artist', 'Track', 'Plays']
    df = df[['Track', 'Artist', 'Plays']]
    return df

def getTopArtists(sp_df):
    a_df = pd.DataFrame(sp_df['artistName'].value_counts())
    b_df = pd.DataFrame((sp_df.groupby(['artistName'])['msPlayed'].sum() / 1000 / 60).sort_values(ascending=False))
    a_df['msPlayed'] = b_df
    a_df.columns = ['Plays', 'Minutes Listened To']
    return a_df


# ***********************************************************
# ***********************************************************
# PLOTS
# ***********************************************************
# ***********************************************************
def listensPerDay(sp_df, q_month, q_year):
    plays_per_day = sp_df[(sp_df['Year'] == q_year) & (sp_df['Month'] == q_month)]['Date'].value_counts().sort_index()

    fig = plt.figure(figsize=(10,6))
    plt.plot(plays_per_day, c='g')
    plt.suptitle('{} {}: Listens Per Day'.format(months[q_month], q_year), fontsize=22)
    plt.xlabel('Day', fontsize=18)
    plt.ylabel('Plays', fontsize=18)
    plt.xlim(1)
    plt.ylim(0)
    return fig
    
def oldstuff():
    # find the total number of each month
    num_months = {}
    for month in sp_df['Month'].unique():
        tmp = sp_df[sp_df['Month']==month]
        num_months[months[month]] = len(pd.unique(list(zip(tmp['Month'], tmp['Year']))))

    return

# plays per day of week
def playsDayWeek(sp_df):
    # bar graph
    day_count = sp_df.groupby(['Day']).count()['artistName'].reindex(['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'])
    day_count.plot.bar(color='darkred')
    plt.suptitle('Plays Per Day of the Week')
    plt.ylabel('Plays')
    return plt.gcf()

# total per month
def totalMonth(sp_df):
    day_count = sp_df.groupby(['Month']).count()['artistName']
    day_count.index = list(map(lambda x: months[x], day_count.index.tolist()))
    ax = day_count.plot.bar(color='darkgreen')
    plt.suptitle('Plays Per Month')
    plt.ylabel('Plays')
    return plt.gcf(), day_count

# average per day per month
def avgDayPerMonth(sp_df):
    day_count = sp_df.groupby(['Month']).count()['artistName']

    months_dict = {}

    for t in pd.unique(list(zip(sp_df['Month'], sp_df['Year']))):
        if t[0] not in months_dict:
            months_dict[t[0]] = 0
        months_dict[t[0]] += monthrange(t[1], t[0])[1]

    stt = datetime.datetime.strptime(sp_df.loc[0]['endTime'].split()[0], '%Y-%m-%d')
    end = datetime.datetime.strptime(sp_df.loc[len(sp_df)-1]['endTime'].split()[0], '%Y-%m-%d')

    # subtract off for start and end
    months_dict[stt.month] -= stt.day - 1
    months_dict[end.month] -= monthrange(end.year, end.month)[1] - end.day

    # get the averages
    for key in months_dict.keys():
        day_count[key] /= months_dict[key]

    day_count.index = list(map(lambda x: months[x], day_count.index.tolist()))
    day_count.plot.bar(color='g')
    plt.suptitle('Average Plays Per Day In Each Month')
    plt.ylabel('Average Plays')
    return day_count

# plays by hour
def playsByHour(sp_df):
    # for the text above the bars (autolabel)
    # https://matplotlib.org/stable/gallery/lines_bars_and_markers/barchart.html#sphx-glr-gallery-lines-bars-and-markers-barchart-py 
    plt.subplots(figsize=(12,5))
    hour_plays = sp_df.groupby('Hour')['artistName'].count()

    # fill in empty hours
    for i in range(24):
        if i not in hour_plays.index:
            hour_plays[i] = 0

    hour_plays = hour_plays.sort_index()

    ax = hour_plays.plot.bar(color='limegreen')
    plt.suptitle('Plays Per Hour', size=22)
    plt.xticks(rotation=0)
    plt.ylabel('Plays')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    def autolabel(rects):
        """Attach a text label above each bar in *rects*, displaying its height."""
        for rect in rects:
            height = rect.get_height()
            ax.annotate('{}'.format(height),
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom')


    autolabel(ax.containers[0])
    return plt.gcf(), hour_plays

# top tracks by day of week
def topTrackByDay(sp_df):
    wd_tracks = sp_df.groupby('Day')['trackName'].value_counts()
    tracks = []
    plays = []

    for day in week_days:
        plays.append(wd_tracks[day][0])
        tracks.append(wd_tracks[day].index[0])

    def autolabel(rects):
        """Attach a text label above each bar in *rects*, displaying its height."""
        for i, rect in enumerate(rects):
            height = rect.get_height()
            ax.annotate(tracks[i],
                        xy=(rect.get_x() + rect.get_width() / 2, .5),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', rotation=90)
    fig, ax = plt.subplots(figsize=(6, 6))
    rects = plt.bar(week_days, plays, color='lightgreen')
    plt.suptitle('Top Track of Each Day of the Week')
    plt.ylabel('Plays')
    autolabel(rects)
    return plt.gcf(), wd_tracks

# top artist(s) by day of week
def topArtistByDay(sp_df):
    wd_artists = sp_df.groupby('Day')['artistName'].value_counts()
    artists = []
    plays = []

    for day in week_days:
        plays.append(wd_artists[day][0])
        artists.append(wd_artists[day].index[0])

    def autolabel(rects):
        """Attach a text label above each bar in *rects*, displaying its height."""
        for i, rect in enumerate(rects):
            height = rect.get_height()
            ax.annotate(artists[i],
                        xy=(rect.get_x() + rect.get_width() / 2, 1),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', rotation=90, color='w')

    fig, ax = plt.subplots(figsize=(6, 6))
    rects = plt.bar(week_days, plays, color='darkred')
    plt.suptitle('Top Artist of Each Day of the Week')
    autolabel(rects)
    return plt.gcf(), wd_artists

# top artist(s) by day of week
def topArtistByDayPie(sp_df):
    wd_artists = sp_df.groupby('Day')['artistName'].value_counts()

    fig, axes = plt.subplots(nrows=3, ncols=3, figsize=(24,20))

    # early morning
    ax = axes.flatten()[0]
    df = sp_df[ (sp_df['Hour'] > 6) & (sp_df['Hour'] < 11)]
    new_plays = df['artistName'].value_counts().sort_values(ascending=False)
    total = new_plays.sum()
    new_plays = new_plays[:5]
    new_plays['Other'] = total - new_plays.sum() 

    ax.pie(new_plays, labels=new_plays.index, 
           explode=[.15 if i == 0 else 0 for i in range(len(new_plays))], 
           shadow=True, 
           autopct=lambda x: '{:.1f}'.format(x))
    ax.set_title('Top Early Morning Artists (between 6 and 11)')

    # late night
    ax = axes.flatten()[1]
    df = sp_df[ (sp_df['Hour'] > 22) | (sp_df['Hour'] < 4)]
    new_plays = df['artistName'].value_counts().sort_values(ascending=False)
    total = new_plays.sum()
    new_plays = new_plays[:5]
    new_plays['Other'] = total - new_plays.sum() 

    ax.pie(new_plays, labels=new_plays.index, 
           explode=[.15 if i == 0 else 0 for i in range(len(new_plays))], 
           shadow=True, autopct=lambda x: '{:.1f}'.format(x))
    ax.set_title('Top Late Night Artists (between 10 and 4)')

    # through each weekday
    for ax, day in zip(axes.flatten()[2:], week_days):
        plays = wd_artists[day]

        total = plays.sum()
        new_plays = plays[:5]
        new_plays['Other'] = total - new_plays.sum()
        artists = new_plays.index

        ax.pie(new_plays, labels=artists, 
               explode=[.15 if i == 0 else 0 for i in range(len(new_plays))], 
               shadow=True, 
               autopct=lambda x: '{:.1f}'.format(x))
        ax.set_title('Top Artists of {}'.format(full_weekdays[day]))
        
    return plt.gcf(), wd_artists

