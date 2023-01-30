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