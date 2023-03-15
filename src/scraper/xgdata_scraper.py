# import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
import requests
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os
import logging
import unidecode
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# ###################################################################################
# configure Firebase db access
# ###################################################################################
cred = credentials.Certificate("src/scraper/serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# ###################################################################################
# configure logger
# ###################################################################################
# check for logs directory
LOGSDATADIR = ("src/scraper/data/logs")
CHECK_FOLDER = os.path.isdir(LOGSDATADIR)

# If folder doesn't exist, then create it.
if not CHECK_FOLDER:
    os.makedirs(LOGSDATADIR)

# Create logger file and configuration
LOGSDATAFILE = (LOGSDATADIR + '/scraperDebugLog')
logging.basicConfig(level=logging.DEBUG, filename=LOGSDATAFILE)

# ###################################################################################
# configure constants
# ###################################################################################
# url for fpl data
fpl_url = 'https://fantasy.premierleague.com/api/bootstrap-static/'

# url for fpl detailed asset data
fpl_asset_data_url = 'https://fantasy.premierleague.com/api/element-summary/'

# create urls for all seasons of all leagues
base_url = 'https://understat.com/league'
# leagues = ['La_liga', 'EPL', 'Bundesliga', 'Serie_A', 'Ligue_1', 'RFPL']
# seasons = ['2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022']
leagues = ['EPL']
seasons = ['2022']

# create base url for the asset data
asset_data_url = 'https://understat.com/player'

# these are the fpl team codes mapped to xgdata team codes
eplteams = [
    { "name": "Aston Villa", "id": "71", "code": 7 },
    { "name": "Everton", "id": "72", "code": 11 },
    { "name": "Southampton", "id": "74", "code": 20 },
    { "name": "Leicester", "id": "75", "code": 13 },
    { "name": "Crystal Palace", "id": "78", "code": 31 },
    { "name": "Chelsea", "id": "80", "code": 8 },
    { "name": "West Ham", "id": "81", "code": 21 },
    { "name": "Tottenham", "id": "82", "code": 6 },
    { "name": "Arsenal", "id": "83", "code": 3 },
    { "name": "Newcastle United", "id": "86", "code": 4 },
    { "name": "Liverpool", "id": "87", "code": 14 },
    { "name": "Manchester City", "id": "88", "code": 43 },
    { "name": "Manchester United", "id": "89", "code": 1 },
    { "name": "Brighton", "id": "220", "code": 36 },
    { "name": "Wolverhampton Wanderers", "id": "229", "code": 39 },
    { "name": "Leeds", "id": "245", "code": 2 },
    { "name": "Brentford", "id": "244", "code": 94 },
    { "name": "Fulham", "id": "228", "code": 54 },
    { "name": "Nottingham Forest", "id": "249", "code": 17},
    { "name": "Bournemouth", "id": "73", "code": 91},

    # { "name": "Burnley", "id": "92", "code": 90 },
    # { "name": "Watford", "id": "90", "code": 57 },
    # { "name": "Norwich", "id": "79", "code": 45 },
    # { "name": "West Bromwich Albion", "id": "76", "code": 35 },
    # { "name": "Sheffield United", "id": "238", "code": 49 },
]

# ###################################################################################
# create data output directory if none exists
# ###################################################################################
# check for data directory
DATADIR = ("src/scraper/data")
CHECK_FOLDER = os.path.isdir(DATADIR)

# If folder doesn't exist, then create it.
if not CHECK_FOLDER:
    os.makedirs(DATADIR)

# ##########################################
# check for fpl detailed data directory
FPLDATADIR = ("src/scraper/data/fpldetaileddata")
CHECK_FOLDER = os.path.isdir(FPLDATADIR)

# If folder doesn't exist, then create it.
if not CHECK_FOLDER:
    os.makedirs(FPLDATADIR)

# ##########################################
# check for groups data directory
GROUPSDATADIR = ("src/scraper/data/groupsdata")
CHECK_FOLDER = os.path.isdir(GROUPSDATADIR)

# If folder doesn't exist, then create it.
if not CHECK_FOLDER:
    os.makedirs(GROUPSDATADIR)

# ##########################################
# check for stats data directory
STATSDATADIR = ("src/scraper/data/statsdata")
CHECK_FOLDER = os.path.isdir(STATSDATADIR)

# If folder doesn't exist, then create it.
if not CHECK_FOLDER:
    os.makedirs(STATSDATADIR)

# ##########################################
# check for shot data directory
SHOTDATADIR = ("src/scraper/data/shotdata")
CHECK_FOLDER = os.path.isdir(SHOTDATADIR)

# If folder doesn't exist, then create it.
if not CHECK_FOLDER:
    os.makedirs(SHOTDATADIR)

# ##########################################
# check for matches data directory
MATCHESDATADIR = ("src/scraper/data/matchesdata")
CHECK_FOLDER = os.path.isdir(MATCHESDATADIR)

# If folder doesn't exist, then create it.
if not CHECK_FOLDER:
    os.makedirs(MATCHESDATADIR)

# ###################################################################################
# get fpl data from endpoint and build output
# ###################################################################################
try:
    fpl_res = requests.get(fpl_url)
    fpl_res.raise_for_status()
    # access JSON content
    fpl_json_data = fpl_res.json()

    # output json response output for error checking
    with open('./src/scraper/data/fpldata.json', 'w+') as outfile:
      json.dump(fpl_json_data, outfile, indent=4, sort_keys=True)

except HTTPError as http_err:
    print('HTTP error occurred: {http_err}')
except Exception as err:
    print('Other error occurred: {err}')


# ###################################################################################
# get xG Data from endpoint
# ###################################################################################
full_data = dict()
for league in leagues:

  season_data = dict()
  for season in seasons:
    url = base_url+'/'+league+'/'+season
    res = requests.get(url)
    soup = BeautifulSoup(res.content, "lxml")

    # Based on the structure of the webpage, xgdata is in JSON variables under <script> tags
    scripts = soup.find_all('script')

    # ###############################################################################
    # Find data for teams
    # ###############################################################################
    string_with_json_obj = ''
    for script in scripts:
        if 'teamsData' in str(script.string):
            string_with_json_obj = script.string.strip()

    # strip unnecessary symbols and get only JSON data
    ind_start = string_with_json_obj.index("('")+2
    ind_end = string_with_json_obj.index("')")
    team_json_data = string_with_json_obj[ind_start:ind_end]
    team_json_data = team_json_data.encode('utf8').decode('unicode_escape')

    # print("string: "+json_data)
    # result = data.to_json(orient="split")

    # convert JSON data into Python dictionary
    data = json.loads(team_json_data)
    
    # Get teams and their relevant ids and put them into separate dictionary
    teams = {}
    for id in data.keys():
      teams[id] = data[id]['title']

    # check to see if season data available
    if (data[id]['history']):
      # EDA to get a feeling of how the JSON is structured
      # Column names are all the same, so we just use first element
      columns = []
      # Check the sample of values per each column
      values = []

      for id in data.keys():
        columns = list(data[id]['history'][0].keys())
        values = list(data[id]['history'][0].values())
        break

      # Getting data for all teams if season data available
      dataframes = {}
      for id, team in teams.items():
        teams_data = []
        for row in data[id]['history']:
          teams_data.append(list(row.values()))
        df = pd.DataFrame(teams_data, columns=columns)
        dataframes[team] = df
        # print('Added data for {}.'.format(team))

      for team, df in dataframes.items():
        dataframes[team]['ppda_coef'] = dataframes[team]['ppda'].apply(lambda x: x['att']/x['def'] if x['def'] != 0 else 0)
        dataframes[team]['oppda_coef'] = dataframes[team]['ppda_allowed'].apply(lambda x: x['att']/x['def'] if x['def'] != 0 else 0)
    else:
      # Produce blank data if season data unavailable
      dataframes = {}
      for id, team in teams.items():
        columns=['matches', 'wins', 'draws', 'loses', 'scored', 'missed', 'pts', 'xG', 'npxG', 'xGA', 'npxGA', 'npxGD', 'ppda_coef', 'oppda_coef', 'deep', 'deep_allowed', 'xpts', 'xG_diff', 'xGA_diff', 'xpts_diff', 'xG90', 'xGA90']
        teams_data = [0] * len(columns)
        df = pd.DataFrame([teams_data], columns=columns)
        dataframes[team] = df

    cols_to_sum = ['xG', 'xGA', 'npxG', 'npxGA', 'deep', 'deep_allowed', 'scored', 'missed', 'xpts', 'wins', 'draws', 'loses', 'pts', 'npxGD']
    cols_to_mean = ['ppda_coef', 'oppda_coef']

    frames = []
    for team, df in dataframes.items():
      sum_data = pd.DataFrame(df[cols_to_sum].sum()).transpose()
      mean_data = pd.DataFrame(df[cols_to_mean].mean()).transpose()
      final_df = sum_data.join(mean_data)
      final_df['team'] = team
      final_df['matches'] = len(df)
      frames.append(final_df)

    full_stat = pd.concat(frames)

    full_stat = full_stat[['team', 'matches', 'wins', 'draws', 'loses', 'scored', 'missed', 'pts', 'xG', 'npxG', 'xGA', 'npxGA', 'npxGD', 'ppda_coef', 'oppda_coef', 'deep', 'deep_allowed', 'xpts']]
    full_stat.sort_values('pts', ascending=False, inplace=True)
    full_stat.reset_index(inplace=True, drop=True)
    full_stat['position'] = range(1,len(full_stat)+1)

    full_stat['xG_diff'] = full_stat['xG'] - full_stat['scored']
    full_stat['xGA_diff'] = full_stat['xGA'] - full_stat['missed']
    full_stat['xpts_diff'] = full_stat['xpts'] - full_stat['pts']

    full_stat['xG90'] = full_stat['xG'] / full_stat['matches']
    full_stat['xGA90'] = full_stat['xGA'] / full_stat['matches']

    # get timestamp
    dateTimeObj = datetime.now()
    timestampStr = dateTimeObj.strftime("%d-%b-%Y (%H:%M:%S.%f)")
    full_stat['date'] = timestampStr

    cols_to_int = ['wins', 'draws', 'loses', 'scored', 'missed', 'pts', 'deep', 'deep_allowed']
    full_stat[cols_to_int] = full_stat[cols_to_int].astype(int)

    col_order = ['position', 'team', 'matches', 'wins', 'draws', 'loses', 'scored', 'missed', 'pts', 'xG', 'xG_diff', 'npxG', 'xG90', 'xGA', 'xGA_diff', 'npxGA', 'xGA90', 'npxGD', 'ppda_coef', 'oppda_coef', 'deep', 'deep_allowed', 'xpts', 'xpts_diff', 'date']
    full_stat = full_stat[col_order]
    full_stat = full_stat.set_index('position')
    # print(full_stat.head(20))

    season_data[season] = full_stat

  df_season = pd.concat(season_data)
  full_data[league] = df_season

data = pd.concat(full_data)
data.head()
data.to_csv('./src/scraper/data/xgdata_scrape.csv')

# build final json output file
team_dataset = json.loads(team_json_data)
json_data = data.to_json(orient='records')
parsed_full_data = json.loads(json_data)
for data in team_dataset:
    for team in eplteams:
        if data == team['id']:
            team_dataset[data]['code'] = team['code']
            for teamHistory in team_dataset[data]['history']:
                teamHistory['code'] = team['code']
                teamHistory['id'] = team['id']
    for team in parsed_full_data:
        if team_dataset[data]['title'] == team['team']:
            team_dataset[data]['matches'] = team['matches']
            team_dataset[data]['wins'] = team['wins']
            team_dataset[data]['draws'] = team['draws']
            team_dataset[data]['loses'] = team['loses']
            team_dataset[data]['scored'] = team['scored']
            team_dataset[data]['missed'] = team['missed']
            team_dataset[data]['pts'] = team['pts']
            team_dataset[data]['xG'] = team['xG']
            team_dataset[data]['npxG'] = team['npxG']
            team_dataset[data]['xGA'] = team['xGA']
            team_dataset[data]['npxGA'] = team['npxGA']
            team_dataset[data]['npxGD'] = team['npxGD']
            team_dataset[data]['ppda_coef'] = team['ppda_coef']
            team_dataset[data]['oppda_coef'] = team['oppda_coef']
            team_dataset[data]['deep'] = team['deep']
            team_dataset[data]['deep_allowed'] = team['deep_allowed']
            team_dataset[data]['xpts'] = team['xpts']
            team_dataset[data]['xpts_diff'] = team['xpts_diff']
            team_dataset[data]['xG_diff'] = team['xG_diff']
            team_dataset[data]['xGA_diff'] = team['xGA_diff']
            team_dataset[data]['xG90'] = team['xG90']
            team_dataset[data]['xGA90'] = team['xGA90']
    for team in fpl_json_data['teams']:
        if team_dataset[data]['code'] == team['code']:
            team_dataset[data]['code'] = team['code']
            team_dataset[data]['name'] = team['name']
            team_dataset[data]['short_name'] = team['short_name']
            team_dataset[data]['id'] = team['id']

# ###################################################################################
# Find data for assets
# ###################################################################################
string_with_json_obj = ''
for script in scripts:
    if 'playersData' in str(script.string):
        string_with_json_obj = script.string.strip()

# strip unnecessary symbols and get only JSON data
ind_start = string_with_json_obj.index("('")+2
ind_end = string_with_json_obj.index("')")
json_data = string_with_json_obj[ind_start:ind_end]
json_data = json_data.encode('utf8').decode('unicode_escape')

# print("string: "+json_data)
# result = data.to_json(orient="split")

# convert JSON data into Python dictionary
data = json.loads(json_data)

# get assets and their relevant ids and put them into separate dictionary
assets = {}
for di in data:
  assets[di['id']]={}
  for k in di.keys():
      if k =='id': continue
      assets[di['id']][k]=di[k]

# get timestamp
dateTimeObj = datetime.now()
timestampStr = dateTimeObj.strftime("%d-%b-%Y (%H:%M:%S.%f)")

# add relevant data to each asset
for asset in assets:
  for team in eplteams:
    if assets[asset]['team_title'] == team['name']:
      assets[asset]['team_code'] = team['code']
      assets[asset]['date'] = timestampStr

#####################################################################################
# add asset xgdata to fpl asset to build final asset data output
# ###################################################################################
fpl_asset_data = fpl_json_data['elements']
asset_db_data = [{}] * len(fpl_asset_data)
team_fixtures_db_data = [{}] * 20
for idx, fpl_asset in enumerate(fpl_asset_data):
  # set asset team "title"
  for team in eplteams:
    if fpl_asset['team_code'] == team['code']:
      fpl_asset['team_title'] = team['name']
      for data in team_dataset:
        if data == team['id']:
          fpl_asset['GA'] = team_dataset[data]['missed']
          fpl_asset['xGA'] = team_dataset[data]['xGA']
          fpl_asset['xGA90'] = team_dataset[data]['xGA90']
          fpl_asset['xGA_diff'] = team_dataset[data]['xGA_diff']
  # reset each asset to zero
  fpl_asset['date'] = 0 #assets[asset]['date']
  fpl_asset['games'] = 0
  fpl_asset['key_passes'] = 0
  fpl_asset['position'] = 0
  fpl_asset['npg'] = 0
  fpl_asset['npxG'] = 0
  fpl_asset['shots'] = 0
  fpl_asset['xA'] = 0
  fpl_asset['xG'] = 0
  fpl_asset['xGBuildup'] = 0
  fpl_asset['xGChain'] = 0
  fpl_asset['xG_diff'] = 0
  fpl_asset['npxG_diff'] = 0
  fpl_asset['xA_diff'] = 0
  fpl_asset['xG90'] = 0
  fpl_asset['npxG90'] = 0
  fpl_asset['xA90'] = 0
  fpl_asset['npg_minutes'] = 0
  fpl_asset['goals90'] = 0
  fpl_asset['goals_minutes'] = 0
  fpl_asset['npg90'] = 0
  fpl_asset['shots90'] = 0
  fpl_asset['kp90'] = 0

  # create blank data files for each asset
  blank_groupsdataset = {"groupsdata": []}
  blank_statsdataset = {"statsdata": []}
  blank_shotdataset = {"shotdata": []}
  blank_matchesdataset = {"matchesdata": []}

  # asset id to string
  asset_id_string = str(fpl_asset['id'])

  # #################################################################################
  # Get FPL detailed data for asset
  try:
    fpl_asset_data_res = requests.get(fpl_asset_data_url + asset_id_string + '/')
    fpl_asset_data_res.raise_for_status()
    # access JSON content
    fpl_asset_json_data = fpl_asset_data_res.json()

  except HTTPError as http_err:
    print('HTTP error occurred: {http_err}')
  except Exception as err:
    print('Other error occurred: {err}')

  # store response in asset file
  with open(FPLDATADIR + '/asset_' + asset_id_string + '_fpldetaileddata.json', 'w+') as outfile:
    json.dump(fpl_asset_json_data, outfile, indent=4, sort_keys=True)

  # write asset detailed data to db
  db.collection('assetdetaileddata').document(asset_id_string).set(fpl_asset_json_data)

  # add fixtures data to relevant team data
  for i, team in enumerate(team_dataset):
    if team_dataset[team]['id'] == fpl_asset['team']:
      team_fixtures_db_data[i] = team_dataset[team]
      team_fixtures_db_data[i]['fixtures'] = fpl_asset_json_data['fixtures']

  ###################################################################################
  # dump blank groups data into temp file
  GROUPSDATAFILETEMP = (GROUPSDATADIR + '/asset_' + asset_id_string + '_groupsdata_temp.json')
  with open(GROUPSDATAFILETEMP, 'w+') as outfile:
    json.dump(blank_groupsdataset, outfile, indent=4, sort_keys=True)

  # check if this asset's groups data file already exists
  GROUPSDATAFILE = (GROUPSDATADIR + '/asset_' + asset_id_string + '_groupsdata.json')
  CHECK_GROUPSDATAFILE = os.path.isfile(GROUPSDATAFILE)

  # if asset groups data file exists, first delete it
  if CHECK_GROUPSDATAFILE:
      os.remove(GROUPSDATAFILE)

  # rename asset groups data temp file
  os.rename(
    GROUPSDATAFILETEMP,
    GROUPSDATAFILE
  )

  ###################################################################################
  # dump blank stats data into temp file
  STATSDATAFILETEMP = (STATSDATADIR + '/asset_' + asset_id_string + '_statsdata_temp.json')
  with open(STATSDATAFILETEMP, 'w+') as outfile:
    json.dump(blank_statsdataset, outfile, indent=4, sort_keys=True)

  # check if this asset's stats data file already exists
  STATSDATAFILE = (STATSDATADIR + '/asset_' + asset_id_string + '_statsdata.json')
  CHECK_STATSDATAFILE = os.path.isfile(STATSDATAFILE)

  # if asset stats data file exists, first delete it
  if CHECK_STATSDATAFILE:
      os.remove(STATSDATAFILE)

  # rename asset stats data temp file
  os.rename(
    STATSDATAFILETEMP,
    STATSDATAFILE
  )

  ###################################################################################
  # dump blank asset shot data into temp file
  SHOTDATAFILETEMP = (SHOTDATADIR + '/asset_' + asset_id_string + '_shotdata_temp.json')
  with open(SHOTDATAFILETEMP, 'w+') as outfile:
    json.dump(blank_shotdataset, outfile, indent=4, sort_keys=True)

  # check if this asset's shot data file already exists
  SHOTDATAFILE = (SHOTDATADIR + '/asset_' + asset_id_string + '_shotdata.json')
  CHECK_SHOTDATAFILE = os.path.isfile(SHOTDATAFILE)

  # if asset shot data file exists, first delete it
  if CHECK_SHOTDATAFILE:
      os.remove(SHOTDATAFILE)

  # rename asset shot data temp file
  os.rename(
    SHOTDATAFILETEMP,
    SHOTDATAFILE
  )

  ###################################################################################
  # dump blank asset matches data into temp file
  MATCHESDATAFILETEMP = (MATCHESDATADIR + '/asset_' + asset_id_string + '_matchesdata_temp.json')
  with open(MATCHESDATAFILETEMP, 'w+') as outfile:
    json.dump(blank_matchesdataset, outfile, indent=4, sort_keys=True)

  # check if this asset's matches data file already exists
  MATCHESDATAFILE = (MATCHESDATADIR + '/asset_' + asset_id_string + '_matchesdata.json')
  CHECK_MATCHESDATAFILE = os.path.isfile(MATCHESDATAFILE)

  # if asset matches data file exists, first delete it
  if CHECK_MATCHESDATAFILE:
      os.remove(MATCHESDATAFILE)

  # rename asset matches data temp file
  os.rename(
    MATCHESDATAFILETEMP,
    MATCHESDATAFILE
  )

  # #################################################################################
  # search for asset xG data, if in database
  for asset in assets:
    fpl_asset_name = unidecode.unidecode(fpl_asset['web_name'])
    xg_asset_name = unidecode.unidecode(assets[asset]['player_name'])
    if fpl_asset_name.replace("-", " ") in xg_asset_name.replace("-", " "):
      fpl_asset['team_code']
      if fpl_asset['team_title'] in assets[asset]['team_title']:
        fpl_asset['xg_code'] = asset
        fpl_asset['games'] = assets[asset]['games']
        fpl_asset['key_passes'] = assets[asset]['key_passes']
        fpl_asset['position'] = assets[asset]['position']
        fpl_asset['npg'] = assets[asset]['npg']
        fpl_asset['npxG'] = assets[asset]['npxG']
        fpl_asset['shots'] = assets[asset]['shots']
        fpl_asset['xA'] = assets[asset]['xA']
        fpl_asset['xG'] = assets[asset]['xG']
        fpl_asset['xGBuildup'] = assets[asset]['xGBuildup']
        fpl_asset['xGChain'] = assets[asset]['xGChain']
        fpl_asset['xG_diff'] = fpl_asset['goals_scored'] - float(assets[asset]['xG'])
        fpl_asset['npxG_diff'] = int(fpl_asset['npg']) - float(assets[asset]['npxG'])
        fpl_asset['xA_diff'] = fpl_asset['assists'] - float(assets[asset]['xA'])
        if int(fpl_asset['minutes']) != 0:
          fpl_asset['shots90'] = float(assets[asset]['shots']) / (int(fpl_asset['minutes']) / 90)
          fpl_asset['goals90'] = float(assets[asset]['goals']) / (int(fpl_asset['minutes']) / 90)
          fpl_asset['npg90'] = float(assets[asset]['npg']) / (int(fpl_asset['minutes']) / 90)
          fpl_asset['kp90'] = float(assets[asset]['key_passes']) / (int(fpl_asset['minutes']) / 90)
          fpl_asset['xG90'] = float(assets[asset]['xG']) / (int(fpl_asset['minutes']) / 90)
          fpl_asset['npxG90'] = float(assets[asset]['npxG']) / (int(fpl_asset['minutes']) / 90)
          fpl_asset['xA90'] = float(assets[asset]['xA']) / (int(fpl_asset['minutes']) / 90)
          if int(assets[asset]['goals']) != 0:
            fpl_asset['goals_minutes'] = float(fpl_asset['minutes']) / int(assets[asset]['goals'])
          if int(assets[asset]['npg']) != 0:
            fpl_asset['npg_minutes'] = float(fpl_asset['minutes']) / int(assets[asset]['npg'])

        # get detailed data for asset
        url = asset_data_url+'/'+asset
        res = requests.get(url)
        soup = BeautifulSoup(res.content, "lxml")

        # Based on the structure of the webpage, shot data is in JSON variables under <script> tags
        scripts = soup.find_all('script')

        # Find detailed data for asset
        string_with_data_json_obj = ''
        for script in scripts:
          if 'groupsData' in str(script.string):
            string_with_groups_data_json_obj = script.string.strip()

            # strip unnecessary symbols and get only JSON data
            ind_start = string_with_groups_data_json_obj.index("('")+2
            ind_end = string_with_groups_data_json_obj.index("')")
            asset_groups_json_data = string_with_groups_data_json_obj[ind_start:ind_end]
            asset_groups_json_data = asset_groups_json_data.encode('utf8').decode('unicode_escape')

            # convert JSON data into Python dictionary
            groups_data = json.loads(asset_groups_json_data)

            # build final dataset
            final_groupsdataset = {"groupsdata": (groups_data)}

            # dump asset groups data into temp file
            with open(GROUPSDATAFILETEMP, 'w+') as outfile:
              json.dump(final_groupsdataset, outfile, indent=4, sort_keys=True)

            # write asset groups data to db
            db.collection('assetgroupsdata').document(asset_id_string).set(final_groupsdataset)

            # if asset groups data file exists, first delete it
            CHECK_GROUPSDATAFILE = os.path.isfile(GROUPSDATAFILE)
            if CHECK_GROUPSDATAFILE:
                os.remove(GROUPSDATAFILE)

            # rename asset groups data temp file
            os.rename(
              GROUPSDATAFILETEMP,
              GROUPSDATAFILE
            )

          if 'minMaxPlayerStats' in str(script.string):
            string_with_stats_data_json_obj = script.string.strip()

            # strip unnecessary symbols and get only JSON data
            ind_start = string_with_stats_data_json_obj.index("('")+2
            ind_end = string_with_stats_data_json_obj.index("')")
            asset_stats_json_data = string_with_stats_data_json_obj[ind_start:ind_end]
            asset_stats_json_data = asset_stats_json_data.encode('utf8').decode('unicode_escape')

            # convert JSON data into Python dictionary
            stats_data = json.loads(asset_stats_json_data)

            # build final dataset
            final_statsdataset = {"statsdata": (stats_data)}

            # dump asset stats data into temp file
            with open(STATSDATAFILETEMP, 'w+') as outfile:
              json.dump(final_statsdataset, outfile, indent=4, sort_keys=True)

            # write asset stats data to db
            db.collection('assetstatdata').document(asset_id_string).set(final_statsdataset)

            # if asset stats data file exists, first delete it
            CHECK_STATSDATAFILE = os.path.isfile(STATSDATAFILE)
            if CHECK_STATSDATAFILE:
                os.remove(STATSDATAFILE)

            # rename asset stats data temp file
            os.rename(
              STATSDATAFILETEMP,
              STATSDATAFILE
            )

          if 'shotsData' in str(script.string):
            string_with_data_json_obj = script.string.strip()

            # strip unnecessary symbols and get only JSON data
            ind_start = string_with_data_json_obj.index("('")+2
            ind_end = string_with_data_json_obj.index("')")
            asset_shots_json_data = string_with_data_json_obj[ind_start:ind_end]
            asset_shots_json_data = asset_shots_json_data.encode('utf8').decode('unicode_escape')

            # convert JSON data into Python dictionary
            shot_data = json.loads(asset_shots_json_data)

            # ensure correct naming and format of x and y co-ords for each shot
            # deliberately reversed for display on map, and extract penalty info
            for shot in shot_data:
              shot['x'] = float(shot['Y'])
              shot['y'] = float(shot['X'])

            # build final dataset
            final_shotdataset = {"shotdata": (shot_data)}

            # dump asset shot data into temp file
            with open(SHOTDATAFILETEMP, 'w+') as outfile:
              json.dump(final_shotdataset, outfile, indent=4, sort_keys=True)

            # write asset shot data to db
            db.collection('assetshotdata').document(asset_id_string).set(final_shotdataset)

            # if asset shot data file exists, first delete it
            CHECK_SHOTDATAFILE = os.path.isfile(SHOTDATAFILE)
            if CHECK_SHOTDATAFILE:
                os.remove(SHOTDATAFILE)

            # rename asset shot data temp file
            os.rename(
              SHOTDATAFILETEMP,
              SHOTDATAFILE
            )

          if 'matchesData' in str(script.string):
            string_with_matches_data_json_obj = script.string.strip()

            # strip unnecessary symbols and get only JSON data
            ind_start = string_with_matches_data_json_obj.index("('")+2
            ind_end = string_with_matches_data_json_obj.index("')")
            asset_matches_json_data = string_with_matches_data_json_obj[ind_start:ind_end]
            asset_matches_json_data = asset_matches_json_data.encode('utf8').decode('unicode_escape')

            # convert JSON data into Python dictionary
            matches_data = json.loads(asset_matches_json_data)

            # build final dataset
            final_matchesdataset = {"matchesdata": (matches_data)}

            # dump asset matches data into temp file
            with open(MATCHESDATAFILETEMP, 'w+') as outfile:
              json.dump(final_matchesdataset, outfile, indent=4, sort_keys=True)

            # write asset matches data to db
            db.collection('assetmatchesdata').document(asset_id_string).set(final_matchesdataset)

            # if asset matches data file exists, first delete it
            CHECK_MATCHESDATAFILE = os.path.isfile(MATCHESDATAFILE)
            if CHECK_MATCHESDATAFILE:
                os.remove(MATCHESDATAFILE)

            # rename asset matches data temp file
            os.rename(
              MATCHESDATAFILETEMP,
              MATCHESDATAFILE
            )

  # #################################################################################
  # copy data into database holding array ready to be written to db
  asset_db_data[idx] = {key: fpl_asset[key] for key in fpl_asset.keys() & {'id','key_passes','games','position','npg','npxG','shots','xA','xG','xGBuildup','xGChain','xG_diff','npxG_diff','xA_diff','xG90','npxG90','xA90','npg_minutes','goals90','goals_minutes','npg90','shots90','kp90','GA','xGA','xGA90','xGA_diff'}}

# write asset data to database
db.collection('assetdata').document('general').set({"assets": asset_db_data})

# write databse file for error checking
database_file_data = {"assets": asset_db_data}
with open('./src/scraper/data/database_file.json', 'w+') as outfile:
  json.dump(database_file_data, outfile, indent=4, sort_keys=True)

# build final output
final_dataset = {"assets": (fpl_asset_data)}
with open('./src/scraper/data/xgdata_assets_temp.json', 'w+') as outfile:
  json.dump(final_dataset, outfile, indent=4, sort_keys=True)

# write team data to db
db.collection('teamdata').document('general').set({"teams": team_fixtures_db_data})

final_dataset = {"teams": team_fixtures_db_data}
with open('./src/scraper/data/xgdata_teams_temp.json', 'w+') as outfile:
   json.dump(final_dataset, outfile, indent=4, sort_keys=True)

# #####################################################################################
# copy temp data files to final output files
# #####################################################################################
ASSETFILE = ("src/scraper/data/xgdata_assets.json")
CHECK_ASSETFILE = os.path.isfile(ASSETFILE)

# if asset data file exists, first delete it
if CHECK_ASSETFILE:
    os.remove(ASSETFILE)

# rename asset data temp file
os.rename('./src/scraper/data/xgdata_assets_temp.json', './src/scraper/data/xgdata_assets.json')

TEAMFILE = ("src/scraper/data/xgdata_teams.json")
CHECK_TEAMFILE = os.path.isfile(TEAMFILE)

# if team data file exists, first delete it
if CHECK_TEAMFILE:
    os.remove(TEAMFILE)

# rename team data temp file
os.rename('./src/scraper/data/xgdata_teams_temp.json', './src/scraper/data/xgdata_teams.json')
