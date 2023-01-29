import pandas as pd,numpy as np, warnings,seaborn as sns, matplotlib.pyplot as plt, requests
from bs4 import BeautifulSoup
import sys 
import warnings
import time
from IPython.display import display
warnings.filterwarnings('ignore')
sys.path.insert(0, '..')

# Establishing the global variable .csv file of team IDs
ids = pd.read_csv('csvs/ids.csv')

# GLOBAL LISTS AND DICTIONARIES
convert_dict = {'OREB':int,
               'DREB':int,
               'REB':int,
               'AST':int,
               'STL':int,
               'BLK':int,
               'TO':int,
               'PF':int,
               'PTS':int,
               'FGM':int,
               'FGA':int,
               '3PM':int,
               '3PA':int,
               'FTM':int,
               'FTA':int}

col_order = ['Player',
                 'PTS',
                 'FGM',
                 'FGA',
                 '3PM',
                 '3PA',
                 'FTM',
                 'FTA',
                 'OREB',
                 'DREB',
                 'REB',
                 'AST',
                 'STL',
                 'BLK',
                 'TO',
                 'PF',
                 'PTS/FGA',
                 'Position']

# Calculate possessions
def calculate_possessions(fga,orebs,tos,fta):
    value = (fga-orebs) + tos + (0.475*fta)
    return value

# Simple function to get a team's schedule for the season
def get_schedule(team):

  current_season = '2022-23'
  url = "https://www.espn.com/mens-college-basketball/team/schedule/_/id/"

  if team not in ids.team.unique().tolist():
    raise ValueError("Invalid Team Name")

  team_link = ids[ids.team == team].link.item()
  team_id = str(ids[ids.team == team].id.item())
  url = url + team_id + "/" + team_link


 # Initial Get Request and splliting the raw HTML by gameId 
  r = requests.get(url).text
  test = r.split('gameId')

  # Cleaning and organizing resulting dataframe
  dfs = pd.read_html(url)
  df= dfs[0]
  df.columns = df.iloc[1,:].tolist()
  things_to_avoid = ['Canceled','Postponed']
  #df = df[~df.RESULT.isin(things_to_avoid)]
  df = df.iloc[2:,[0,1]]
  df = df[df.DATE != 'DATE']
  df['GAME_ID'] = [test[i][1:10] for i in range(1,len(df)+1)]
  df.OPPONENT = df.OPPONENT.str.replace("*","")
  df.OPPONENT = df.OPPONENT.str.replace("\d","")
  df.OPPONENT = df.OPPONENT.str.replace('vs','')
  
  return df

def clean_dataframe(input_df: pd.DataFrame) -> pd.DataFrame:
 

    # Creatimg a copy of the DataFrame and adding the stats which I track
    df = input_df.copy()
    df['FGM'] = [i[0] for i in df.FG.str.split('-')]
    df['FGA'] = [i[1] for i in df.FG.str.split('-')]
    df['3PM'] = [i[0] for i in df['3PT'].str.split('-')]
    df['3PA'] = [i[1] for i in df['3PT'].str.split('-')]
    df['FTM'] = [i[0] for i in df.FT.str.split('-')]
    df['FTA'] = [i[1] for i in df.FT.str.split('-')]

    # Filling empty minutes with zeroes.  They show up in different data formats
    #if type(df.MIN[0]) == str:
        #df.MIN = 0

    # Converting datatypes before calculations
    df = df.astype(convert_dict)
    df['PTS/FGA'] = round((df.PTS/df.FGA),2).fillna(0)
    # Adding a summary row
    df = df.append(df.sum(numeric_only = True),ignore_index = True)

    # Manually creating a new row
    # Assigning 'team' to the player and "" to the position.  This is where the aggregates will live
    last_row = len(df) - 1
    df = df[col_order]
    df.iloc[last_row,0] = 'Team'
    df.iloc[last_row,17] = ""

    # Converting to integer where possible
    for col in df.columns:

        if col != "PTS/FGA":
            
            try:
                df[col] = df[col].astype(int)
            except ValueError as e:
                continue

    # Every now and again, I'm left with residual NaNs, filling those
    df = df.fillna("")

    return df

def create_home_and_away_simple_dataframe(game_id:int,
                                          disp: bool = False) -> tuple:

    url = f'https://www.espn.com/mens-college-basketball/boxscore/_/gameId/{game_id}'
    r = requests.get(url)
    soup = BeautifulSoup(r.content,'lxml')

    if r.status_code != 200:

        raise Exception("Possibly invalid game_id.  Request did not return status code 200")

    #Isolate the home team, away team, and game date.  Away team is always first
    away_team,home_team = [team.strip().title() for team in [i for i in str(soup.find('title')).split('-') if " vs. " in i][0].replace('helmet="true">',"").split(" vs.")]
    game_date = str(soup.find("title")).split("-")[-1].split("|")[0].strip()
    
    #Infer tables with Pandas
    dfs = pd.read_html(url)

    # Pandas pulls in a lot of dataframes
    # Filterint to only retrieve the entries we're interested in
    away_players,away_stats,home_players,home_stats = dfs[1:5]
    # Renaming the column in the home and away players dataframe to "player"
    away_players.columns,home_players.columns = ['Player'],['Player']

    # Remove entries we don't need
    away_players = away_players.iloc[1:len(away_players),]
    away_players = away_players.loc[away_players.Player != "bench"]

    # Remove entries we don't need
    home_players = home_players.iloc[1:len(home_players),]
    home_players = home_players.loc[home_players.Player != "bench"]
    # Grabbing the last letter from the player column and isolating it into it's own column
    # This becomes the position (G,F,C)
    home_players['Position'] = [i[-1] for i in home_players.Player]
    away_players['Position'] = [i[-1] for i in away_players.Player]
    home_players['Player'] = [i[:-2].strip() for i in home_players.Player]
    away_players['Player'] = [i[:-2].strip() for i in away_players.Player]

    # Pandas doesn't recognize the first row as a header, so I'm manually assigning it to the stats dataframes
    away_stats.columns = away_stats.iloc[0,:].tolist()
    home_stats.columns = home_stats.iloc[0,:].tolist()

    # Removing column break headers
    if "FG" in home_stats.columns:

      home_stats = home_stats.loc[home_stats.FG != "FG"]
      away_stats = away_stats.loc[away_stats.FG != "FG"]

    elif "MIN" in home_stats.columns:

      home_stats = home_stats.loc[home_stats.MIN != "MIN"]
      away_stats = away_stats.loc[away_stats.MIN != "MIN"]
    
    else:
       print("Neither Column Exists")
       return home_stats,away_stats

    # Removing the last row as it's all null values
    home_stats = home_stats.iloc[:len(home_stats)-1,]
    away_stats = away_stats.iloc[:len(away_stats)-1,]

    # Merge the players and stats togther
    home_df = home_players.join(home_stats).iloc[:-1].fillna("")
    away_df = away_players.join(away_stats).iloc[:-1].fillna("")

    home_df = clean_dataframe(home_df)
    away_df = clean_dataframe(away_df)

     #Create outer index
    away_df = pd.concat({away_team:away_df})
    home_df = pd.concat({home_team:home_df})

    # Set the Team PTS/FGA to zero
    home_df.loc[home_df.Player == "Team",'PTS/FGA'] = int(0)
    away_df.loc[away_df.Player == "Team",'PTS/FGA'] = int(0)

    if disp:
        display(away_df,home_df)
        return

    return home_df,away_df

def get_agg_boxscore(game_id,disp = True):

    # If we run this before the game has started, it throws a ValueError
    try:
        df_away,df_home = create_home_and_away_simple_dataframe(game_id)
    except ValueError as e:
        raise Exception("Game likely hasn't started, returned no data")

    # Cleaning data
    last_row = len(df_away)
    df_away = df_away.iloc[last_row-1:]
    df_away = df_away[["PTS",
          "FGM",
          "FGA",
          "3PM",
          "3PA",
          "FTM",
          "FTA",
          "OREB",
          "DREB",
          "TO"]].reset_index().drop('level_1',1).rename(columns = {'level_0':'Team'}).set_index("Team")

    last_row = len(df_home)
    df_home = df_home.iloc[last_row-1:]
    df_home = df_home[["PTS",
          "FGM",
          "FGA",
          "3PM",
          "3PA",
          "FTM",
          "FTA",
          "OREB",
          "DREB",
          "TO"]].reset_index().drop('level_1',1).rename(columns = {'level_0':'Team'}).set_index("Team")

    # Aggregating and calculating new fields
    away_team_dreb = df_away.DREB.item()
    home_team_dreb = df_home.DREB.item()
    df_home['OR%'] = 0
    df_away['OR%'] = 0
    if df_home.OREB.item() >0:
      df_home['OR%'] = 100*round(df_home.OREB.item()/(df_home.OREB.item() + away_team_dreb),2)
    if df_away.OREB.item() >0:
      df_away['OR%'] = 100*round(df_away.OREB.item()/(df_away.OREB.item() + home_team_dreb),2)
    final_df = pd.concat([df_away,df_home])

    final_df['POS'] = final_df.apply(lambda x: calculate_possessions(x.FGA,x.OREB,x.TO,x.FTA),axis = 1).astype(float).fillna(0)
    final_df['PTS_POS'] = round(final_df.PTS / final_df.POS,2).fillna(0)
    final_df['3PT%'] = 100*round(final_df['3PM'] / final_df['3PA'],2).fillna(0)
    final_df['FG%'] = 100*round(final_df.FGM/final_df.FGA,2).fillna(0)
    final_df["TS%"] = round(100*final_df.PTS/(2*(final_df.FGA + 0.475*final_df.FTA)),2).fillna(0)
    final_df['TO%'] = round(100*(final_df.TO/final_df.POS),2).fillna(0)
    final_df['POS'] = np.floor(final_df.POS).astype(int).fillna(0)
    col_order = ['PTS',
                'FGM',
                'FGA',
                '3PM',
                '3PA',
                'FTM',
                'FTA',
                'OREB',
                'DREB',
                'TO',
                'POS',
                'PTS_POS',
                '3PT%',
                'FG%',
                'OR%',
                'TS%',
                'TO%']
    final_df = final_df[col_order]

    # If the user ONLY wants to display the dataframe
    if disp:

      display(final_df.rename_axis("").astype(object).transpose())

    #Otherwise return the dataframe
    return final_df.rename_axis("").astype(object).transpose()

def get_game_timestamp_half(game_id):
  """
  Returns a tuple:
    [0]: The current timestamp of the half currently being played
    [1]: Which half is currently being played
  """
  url = "https://www.espn.com/mens-college-basketball/playbyplay/_/gameId/"
  url = url + str(game_id)

  half = 2
  all_dfs = pd.read_html(url)
  if np.isnan(all_dfs[0].iloc[0,2]):
    half = 1
  
  target_df = df = pd.read_html(url)[1]
  current_time = df.iloc[0,0]
  return current_time,half


def scrape_game_stats_real_time(game_id,max_retries = 14,glob = True,disp = True):
  last_reported_timestamp = 0
  retry_iter = 0
  limbo_df = pd.DataFrame()

  if glob:

    global test_df
    while True:

      try:

        timestamp,half = get_game_timestamp_half(game_id)
      except ValueError as e:

        raise Exception("Game hasn't started")

      if timestamp != last_reported_timestamp:
        last_reported_timestamp = timestamp
        temp_df = get_agg_boxscore(game_id = game_id,disp = True)
        temp_df['Half'] = half
        temp_df['Timestamp'] = timestamp
        test_df = pd.concat([test_df,temp_df])
        test_df.to_csv("test_df.csv")
        create_home_and_away_simple_dataframe(game_id,disp = True)
        retry_iter = 0

        if disp:
          try:
            plot_game_trends(test_df,half = half,color1 = 'black',color2 = 'red')
          except:
            pass

        time.sleep(np.random.randint(10,20))
      else:
        retry_iter +=1
        if retry_iter > max_retries:
          break
        print(f"Retry number {retry_iter} of {max_retries}")
        time.sleep(np.random.randint(15,22))
       
      
  
  else:
    while True:

      try:
        timestamp,half = get_game_timestamp_half(game_id)
      except:
        raise Exception("Game hasn't started")

      if timestamp != last_reported_timestamp:
        last_reported_timestamp = timestamp
        temp_df = get_agg_boxscore(game_id = game_id,disp = True)
        temp_df['Half'] = half
        temp_df['Timestamp'] = timestamp
        limbo_df = pd.concat([limbo_df,temp_df])
        limbo_df.to_csv("limbo_df.csv")
        create_home_and_away_simple_dataframe(game_id,disp = True)
        time.sleep(np.random.randint(10,20))
      else:
        retry_iter +=1
        if retry_iter == max_retries:
          break
        print(f"Retry number {retry_iter} of {max_retries}")
        time.sleep(np.random.randint(20,25))
    return limbo_df

def plot_game_trends(test_df,half = 1,color1 = 'black',color2 = 'red'):
  melted = test_df.reset_index()
  for i in melted.columns.tolist()[1:18]:
    plt.figure(figsize = (14,8))
    sns.lineplot(data = melted[melted.Half ==half].iloc[1:,:],
                x = 'Timestamp',
                y = i,
                hue = 'Team',
                palette = [color2,color1])
    plt.title(f"{melted.Team.tolist()[0]} vs {melted.Team.tolist()[1]}: {i.replace('_',' ')}")
    plt.ylabel(i.replace('_',' '))
    plt.xlabel('Time Remaining, 2nd Half')
    if half == 1:
      plt.xlabel('Time Remaining, 1st Half')
    plt.show();