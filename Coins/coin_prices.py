# -*- coding: utf-8 -*-
"""
Created on Mon Mar 30 18:24:31 2020

@author: Joseph
"""

import requests, datetime, os
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

# some of these change more than just year...may be settled now
prov_silver_dict = {
    'ASE':'2021-american-eagle-1-oz-silver-coin',
    'Britannia':'2021-british-britannia-1-oz-silver-coin',
    'Maple Leaf':'2021-canadian-maple-leaf-1-oz-silver-coin',
    'Kangaroo':'2021-australian-kangaroo-1-oz-silver-coin',
    'Kook':'2021-australian-kookaburra-1-oz-silver-coin',
    '2019 Philharmonic':'2021-austrian-philharmonic-1-oz-silver-coin',
}
prov_gold_dict = {
    'ASE':'2021-american-eagle-1-oz-gold-coin',
    'Britannia':'2021-british-britannia-1-oz-gold-coin',
    'Maple Leaf':'2021-canadian-maple-leaf-1-oz-gold-coin',
    'Kangaroo':'2021-australian-kangaroo-1-oz-gold-coin',
}
prov_plat_dict = {
    'ASE':'2020-american-eagle-1-oz-platinum-bu',
    'Britannia':'2020-british-1-oz-platinum-britannia',
    'Maple Leaf':'2020-canadian-maple-leaf-1-oz-platinum-coin-bu',
    'Kangaroo':'2021-australian-kangaroo-1-oz-platinum-coin',
}
prov_temp = "https://www.providentmetals.com/{}.html"

# should just be able to update year for these
jm_silver_dict = {
    'ASE':'2021-1-oz-american-silver-eagle-coin',
    'Britannia':'2021-1-oz-british-silver-britannia-coin',
    'Maple Leaf':'2021-1-oz-canadian-silver-maple-leaf-coin',
    'Kangaroo':'2021-1-oz-australian-silver-kangaroo-coin',
    'Kook':'2021-1-oz-australian-silver-kookaburra-coin',
    '2019 Philharmonic':'2021-austrian-silver-philharmonic-coin',
}
jm_gold_dict = {
    'ASE':'2021-1-oz-american-gold-eagle-coin',
    'Britannia':'2021-1-oz-british-gold-britannia-coin',
    'Maple Leaf':'2021-1-oz-canadian-gold-maple-leaf-coin',
    'Kangaroo':'2021-1-oz-australian-gold-kangaroo-coin',
}
jm_plat_dict = {
    'ASE':'2020-1-oz-american-platinum-eagle',
    'Britannia':'2020-1-oz-british-platinum-britannia-coin',
    'Maple Leaf':'2020-1-oz-canadian-platinum-maple-leaf-coin',
    'Kangaroo':'2021-1-oz-australian-platinum-kangaroo-coin',
}
jm_temp = "https://www.jmbullion.com/{}/"

def get_prices(coin_df, website, web_temp, web_dict, pm, additional):
    today = datetime.datetime.now()
    col_name = website
    coin_df[col_name] = 0.0
    coin_df.loc['Date', col_name] = str(today.month)+"_"+str(today.day)+"_"+str(today.year)
    
    # Gets price for each coin in web_dict
    for coin in web_dict:
        url = web_temp.format(web_dict[coin])
        try: # incase webpage is down for some reason
            r = requests.get(url)
            r.raise_for_status()
        except:
            coin_df.loc[coin, col_name] = np.nan
            continue
        soup = BeautifulSoup(r.text, "html.parser")

        table = soup.find_all("table")[additional] # get the data table
        rows = table.find_all("tr")
        try:
            coin_df.loc[coin, col_name] = float(rows[1].find_all('td')[1].text.strip()[1:].replace(",", ""))
        except:
            coin_df.loc[coin, col_name] = float('nan')
            print('update coin?', coin, website, web_temp, pm)
    
    # Get spot price
    if website == 'Prov':
        if pm == 'silver':
            coin_df.loc['Spot', col_name] = float(soup.find_all('div')[11].contents[1].text[1:].replace(",", ""))
        elif pm == 'gold':
            coin_df.loc['Spot', col_name] = float(soup.find_all('div')[10].contents[1].text[1:].replace(",", ""))
        elif pm == 'platinum':
            coin_df.loc['Spot', col_name] = float(soup.find_all('div')[12].contents[1].text[1:].replace(",", ""))
        
    elif website == 'JM':
        if pm == 'silver':
            coin_df.loc['Spot', col_name] = float(soup.find_all('ul')[40].find_all('li')[2].contents[1].text[1:].replace(",", ""))
        elif pm == 'gold':
            coin_df.loc['Spot', col_name] = float(soup.find_all('ul')[40].find_all('li')[1].contents[1].text[1:].replace(",", ""))
        elif pm == 'platinum':
            coin_df.loc['Spot', col_name] = float(soup.find_all('ul')[40].find_all('li')[3].contents[1].text[1:].replace(",", ""))
    return coin_df

def get_df(prov_dict, jm_dict, metal):
    coin_df = pd.DataFrame.from_dict(prov_dict, orient='index')
    coin_df.columns=['Code']
    coin_df.drop('Code', axis=1, inplace=True)
    coin_df = coin_df.append(pd.Series(name='Date', dtype='object'))
    coin_df = get_prices(coin_df, 'Prov', prov_temp, prov_dict, metal, 0)
    coin_df = get_prices(coin_df, 'JM', jm_temp, jm_dict, metal, 1)
    return coin_df

# Splits the dataframe into two, one for provident and one for jm
def split_df(df):
    prov = pd.DataFrame(df[['Prov']])
    prov.columns = [prov.loc['Date', 'Prov']]
    prov.drop('Date', inplace=True)
    
    jm = pd.DataFrame(df[['JM']])
    jm.columns = [jm.loc['Date', 'JM']]
    jm.drop('Date', inplace=True)
    
    return prov, jm

# Saves it as a transposed version of how it's been dealt with so far
def save_df(df, retailer, metal):
    path = os.path.join('data', retailer+"_"+metal+".csv")
    
    if os.path.exists(path):
        old_df = pd.read_csv(path, index_col=0)
        new_df = old_df.append(df.T)
    else:
        new_df = df.T
    new_df.to_csv(path)
    return

# Gets dfs, splits them, and saves them
def get_today():
    # Get dfs for today
    silver = get_df(prov_silver_dict, jm_silver_dict, 'silver')
    gold = get_df(prov_gold_dict, jm_gold_dict, 'gold')
    plat = get_df(prov_plat_dict, jm_plat_dict, 'platinum')
    
    # Split dfs
    p_silver, j_silver = split_df(silver)
    p_gold, j_gold = split_df(gold)
    p_plat, j_plat = split_df(plat)
    
    # Save them
    save_df(p_silver, 'Provident', 'silver')
    save_df(p_gold, 'Provident', 'gold')
    save_df(p_plat, 'Provident', 'platinum')
    
    save_df(j_silver, 'JM', 'silver')
    save_df(j_gold, 'JM', 'gold')
    save_df(j_plat, 'JM', 'platinum')
    print("CSVs updated.")
    return

if __name__ == "__main__":
    get_today()

