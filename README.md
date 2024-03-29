# Random Data Science Projects

# Fall Guys
* fallGuysData.py - script to gather Fall Guys data from last session (from a .log file)
* fallGuysFcns.py - helper functions for above script
* Fall Guys Slim.ipynb - includes code of two .py files, plus some more, in notebook form
* Fall Guys Development.ipynb - "first draft" of data extraction, includes more output than the others

No longer updated here. Repo for FallGuysCharts is located [here](https://github.com/jvmohr/FallGuysCharts).

# Futurama
Code used to get Futurama transcript data as well as one graph. The dataset is located [here](https://www.kaggle.com/josephvm/futurama-seasons-16-transcripts). 
* Futurama Sentiment Analyis.ipynb - notebook that contains sentiment analysis of Futurama transcripts; also availabe [here on Kaggle](https://www.kaggle.com/josephvm/futurama-sentiment-analysis)
* Analysis.ipynb - code that generates one graph (example of using data)
* Gathering Transcripts.ipynb - code that gets transcripts and episode data from various sources (noted near top of notebook) 
* Generate CSV.ipynb - code that converts saved txts from above notebook into a csv file

# NFL/Kicking
Code used to get data from NFL kickers through the 2019 season. An update to the NFL's website has broken this as of now. 
The dataset with data through the 2019 season is located [here](https://www.kaggle.com/josephvm/nfl-kickers-data).
* Kicking.ipynb - code to gather the data and process it, as well as one graph at the end
* kicking.py - helper functions for the notebook

# Soccer
### General Data
Generalized code of that found in MLS_Data to get data for other leagues. 
* Soccer Scraper Driver - notebook used to get data from one league/multiple leagues in one run
* soccer_fcns.py - functions to scrape table, aggregated stats, and game stats and to combine data
* league_data_dict.py - contains data for different leagues (should be used as a template for a league if using this code)
* soccer_table.py - script to get table of a specific season of a league from ESPN
* Soccer Table.ipynb - notebook version of above script, looks a bit nicer
* Soccer Game Data.ipynb - notebook to get game data from ESPN for a league
* Soccer Aggregated Stats.ipynb - notebook to get aggregated stats from ESPN for a league

### MLS_Data
Code used to get data for Major League Soccer (MLS). The dataset is located [here](https://www.kaggle.com/josephvm/major-league-soccer-dataset).
Where the data is coming from can be found near the top of the files. 
(The player data comes from mlssoccer.com and the game data and tables come from espn.com.)  
* mls_table.py - script to get table of standings (year is denoted at top of file)
* mls_player_data.py - script to get player data (year is denoted at top of file and season type is noted at the top of the file (command line argument)) (data source no longer works)
* mls_game_data.py - not done
* MLS Table.ipynb - old notebook version of mls_table.py (old data source)
* All MLS Tables.ipynb - new notebook version of mls_table.py (new data source)
* MLS Player Data.ipynb - notebook version of mls_player_data.py (data source no longer works)
* MLS Game Data From ESPN.ipynb - gets game data based on start and stop date codes given 
* Examples.ipynb - serves as an introduction to the dataset; goes through each csv file and has a short analysis section at the end
* MLS Analysis - Game Scores.ipynb - notebook that analyzes game scores; can be found on Kaggle [here](https://www.kaggle.com/josephvm/mls-analysis-game-scores)

# TF2
* TF2 Data.ipynb - gets playtime, stats, and inventory for Team Fortress 2 and saves refined and raw data in json and html files, respectively
* Steam Total Gametime.ipynb - small notebook to compute total playtime with one of html files saved from previous notebook
* Scrape Player Count.ipynb - notebook to scrape player counts for games on Steam

# Baseball
* Located [here](https://github.com/jvmohr/baseballStuff)
* Mostly code for scraping so far

# Mystery
### Bigfoot
* Scrape Bigfoot Data.ipynb - notebook to scrape bigfoot reportings and articles from www.bfro.net

# Coins
* coin_prices.py - script to get spot and the prices of certain coins
* Graphs.ipynb - notebook that creates graphs of data
* notes.txt - small txt document that contains certain notes

# DBZ/Dokkan
* Scrape Cards.ipynb - notebook to scrape Dokkan cards from its wiki
* Beginning Steps with DBZ Dokkan Battle Card Data.ipynb - notebook to show some beginning analysis on card data; also located [here on Kaggle](https://www.kaggle.com/josephvm/beginning-steps-with-dbz-dokkan-battle-card-data)
