import pandas as pd,numpy as np, warnings,seaborn as sns, matplotlib.pyplot as plt, requests
from bs4 import BeautifulSoup
import sys 
sys.path.insert(0, '..')
import warnings
warnings.filterwarnings('ignore')

ids = pd.read_csv('csvs/ids.csv')

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