import matplotlib.pyplot as plt

week_days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
months = ['', 'January', 'February', 'March', 'April', 'May', 'June', 
          'July', 'August', 'September', 'October', 'November', 'December']

def listensPerDay(sp_df, q_month, q_year):
    plays_per_day = sp_df[(sp_df['Year'] == q_year) & (sp_df['Month'] == q_month)]['Date'].value_counts().sort_index()

    plt.figure(figsize=(10,6))
    plt.plot(plays_per_day, c='g')
    plt.suptitle('{} {}: Listens Per Day'.format(months[q_month], q_year), fontsize=22)
    plt.xlabel('Day', fontsize=18)
    plt.ylabel('Plays', fontsize=18)
    plt.xlim(1)
    plt.ylim(0)
    return
    
def oldstuff():
    # find the total number of each month
    num_months = {}
    for month in sp_df['Month'].unique():
        tmp = sp_df[sp_df['Month']==month]
        num_months[months[month]] = len(pd.unique(list(zip(tmp['Month'], tmp['Year']))))

    return

