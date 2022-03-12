from typing import Iterable
import tweepy
from datetime import datetime, timezone, timedelta
import csv
from urllib.error import HTTPError

# Gsheets
#gc = gspread.service_account(filename='service-key.json')
#sm_sheet = gc.open_by_key('1pPKG2PwrCr1dlZIvGZB8TQZ1_f0Pey-pgEZ1lvDbsbw')
# columns: 1. discord name, 2. twitter name, 3. youtube name, 4. like+retweet points, 5. reply points, 6. mention points, 
#           7. YT subscriber points, 8. YT comment points, 9. role, 10. role multiplier, 11. Total $QUAI Earned
#output_sheet = sm_sheet.add_worksheet(title="Rewards Bot Tracked Data", rows=2000, cols=10)
# columns: 1. Rank, 2. Role, 3. Total $QUAI Earned
#leaderboard_sheet = sm_sheet.add_worksheet(title="Social Media Leaderboard", rows=100, cols=5) 


# CONST
quai_id = 1306071657174441985
quai_username = 'quainetwork'
first_tweet_date = '2021-11-20 00:00:00+0000'
last_twt_dt = datetime.strptime(first_tweet_date, '%Y-%m-%d %H:%M:%S%z')
# quai_profile = client.get_user(username=quai_username.data
first_bearer = "AAAAAAAAAAAAAAAAAAAAAEHkXwEAAAAAFgCxzDEOf484cKicUHiV3DO6qcU%3DodAKdbVDHoucR6dlOzPbB719XrDMisbZAWLufgqORgLCLgKUtO"
second_bearer = "AAAAAAAAAAAAAAAAAAAAANBOYAEAAAAAlLMei9GmJpSazEtiXx6IWZXEbhs%3DYfsE6mbEa2mLrtZKJhjvjzr4gWZ466w1doYhiWGHlwbDyJzTwx"
third_bearer = "AAAAAAAAAAAAAAAAAAAAAJlpZQEAAAAAjwv7Gg01zTG7ck30cyqxiwQcm9U%3DPNHl3UjpTpKdAjtVcrOs8tZqprtwO6TUKl61XWrXzKKVwgkMDA"
fourth_bearer = "AAAAAAAAAAAAAAAAAAAAAJxpZQEAAAAAexanqSH%2B10AH6FDOHTOqAlqiI8g%3D9hHfSUY0qNXjDGBwlBRNqhXelDcDYpNvnW4VGtpiroOAlabxaR"
fifth_bearer = "AAAAAAAAAAAAAAAAAAAAABoZZwEAAAAAWdu%2BFszRiTgPBboHWwzAWIxV7SI%3DaKeaVddnpgh8DJYOZkEw7GFpP7NbAHwuPne4zpbimS8tKpCsXn"
timezone_offset = -6.0  # Central Standard Time (UTC−06:00)
tzinfo = timezone(timedelta(hours=timezone_offset))
current_time = str(datetime.now(tzinfo))

# dicts to track and store everything -> {username: [likes+retweets, replies, mentions, engagement rewards], ...}
sm_rewards = {}
twitter_data = {}
users_checked = []

# create an array to remove team usernames from dict
team_usernames = ['The_NFT_King', 'alanorwick', 'max_bibeau','0heezus0','owenrobertson48','ShreekaraS','mechanikalk', 'Juuuuuddi', 'QuaiNetwork']

# function: checks if file is empty by checking for second row in csv
def is_empty(file):
  with open(file) as file_alias:
    reader = csv.reader(file_alias)
    for i, _ in enumerate(reader):
      if i:  # found the second row
        return False
    return True


def read_rewards_data():
  # sorts through an input file and adds users to a dictionary with a value of an array containing the data in its row
  with open('user_data_storage.csv') as uds:
    print("RM CHECK -- reading UDS")
    line_count = 0
    for line in uds:
      if line_count == 0:
        line_count += 1
        continue
      else:
        user_data = line.strip().split(',')
        if user_data[0] == 'User Data':
          current_user = user_data[1]
          user_id = user_data[2]
          lr_rewards = 0
          reply_rewards = 0
          mention_rewards = 0
          #print("Added new user: ")
          print(current_user + " read from UDS")
          sm_rewards[current_user] = [user_id, lr_rewards, reply_rewards, mention_rewards]
    #print("--after UDS read--")
    print(sm_rewards)
  uds.close()
  
  with open('like_retweet_rewards.csv') as lrr:
    print("RM CHECK -- Reading LRR")
    line_counter = 0
    for line in lrr:
      if line_counter == 0:
        line_counter += 1
      else:
        user_array = line.strip().split(',')
        if len(user_array) == 3:
          if user_array[1] not in team_usernames:
            # set user id & rewards from like+retweets output
            print(user_array)
            current_user = user_array[1]
            user_id = int(user_array[0])
            lr_rewards = int(user_array[2])
            if current_user in sm_rewards.keys():
              print("UDS: " + current_user + " in sm_rewards")
              sm_rewards[current_user][1] = lr_rewards
              print("UDS: " + current_user + " updated lr rewards")
            else:
              reply_rewards = 0
              mention_rewards = 0
              sm_rewards[current_user] = [user_id, lr_rewards, reply_rewards, mention_rewards]
              print(current_user + " added to sm_rewards")
      #print("--after like_retweet_rewards read--")
      #print(sm_rewards)
  lrr.close()

  with open('tweet_monitor_data.csv') as md:
    print("RM CHECK -- Reading monitor data")
    uptodate_twtID = ''
    for line in md:
      line_arr = line.strip().split(': ')
      if line_arr[0] == "Last tweet ID":
        uptodate_twtID = line_arr[1]
      elif line_arr[0] == "Most Recent Tweet Pull":
        last_twt_pull = line_arr[1]
      elif line_arr[0] == "Last twtID for RM Check":
        print("RM Check -- TMD, getting last_twtID")
        try:
          last_twtID = line_arr[1]
          
          client = tweepy.Client(bearer_token= fifth_bearer)
          tweet = client.get_tweet(id=last_twtID, tweet_fields='created_at')
          tweet_dt = tweet.data.created_at
          tweet_dt_str = tweet_dt.strftime('%Y-%m-%d %H:%M:%S%z')
          last_twt_dt = datetime.strptime(tweet_dt_str, '%Y-%m-%d %H:%M:%S%z')
          print(last_twt_dt)
          last_twt_dt = last_twt_dt.replace(microsecond=0).isoformat()
          print(last_twt_dt)
        except HTTPError as err:
          print(err)
  md.close()
  print("successfully read like+retweet reads and tweet monitor data")
  print('uptodate_twtID: ' + str(uptodate_twtID))
  print('last_twt_pull: ' + str(last_twt_pull))
  with open('tweet_monitor_data.csv', 'w') as tmd:
    tmd.write("%s: %s\n" % ("Last Check Complete", True))
    tmd.write("%s: %s\n" % ("Last tweet ID", uptodate_twtID))
    tmd.write("%s: %s\n" % ("Last twtID for RM Check", uptodate_twtID))
    tmd.write("Most Recent Tweet Pull: " + str(last_twt_pull))
  tmd.close()
  return last_twt_dt

def read_uds():
  with open('user_data_storage.csv') as uds:
    print("RM CHECK -- reading user data storage")
    empty_result = is_empty('user_data_storage.csv')
    
    if empty_result != True:
      print("user_data_storage has data")
      line_index = 0
      for line in uds:
        user_data = line.strip().split(',')
        if line_index == 0:
          line_index += 1
          continue
        elif user_data[0] == "User Data":
          current_user = user_data[1]
          user_id = user_data[2]
          lr_rewards = user_data[3]
          reply_rewards = user_data[4]
          mention_rewards = user_data[5]
          twitter_data[current_user] = [user_id, lr_rewards, reply_rewards, mention_rewards]
    else:
        print("user data storage is empty")
  uds.close()
  return twitter_data
  

def sort_list(_list): 
  if _list:
    ## Bubble sort algo to ensure tweets are sorted youngest to oldest
    for n in range(len(_list)-1, 0, -1):
      for i in range(n):
        if _list[i] > _list[i + 1]:
          # swapping data if the element is less than next element in the array
          _list[i], _list[i + 1] = _list[i + 1], _list[i]
    
    high_to_low = []
    l = len(_list) - 1
    for j in _list:
        high_to_low.append(_list[l])
        l -= 1
    return high_to_low

def reply_mentions_check(_bearer_token, _last_twt_dt):
    client = tweepy.Client(bearer_token= _bearer_token)
    print(_last_twt_dt)
    for currentUser in sm_rewards:
        if currentUser not in users_checked:
          print("--- USER CHECK ---")
          print(currentUser)
          user_tweets_holder = []
          user_replies = []
          user_mentions = []
          #sorted_replies = []
          #sorted_mentions = []
          mention_count = 0
          reply_count = 0
          
          
          #request all users individual tweets (with no retweets and replies) THEN request all users tweets with no retweets
          #print("RM CHECK -- attempting to pull tweets")
          indiv_tweets = client.get_users_tweets(id=sm_rewards[currentUser][0], exclude=['retweets', 'replies'], start_time = _last_twt_dt, tweet_fields=['created_at', 'in_reply_to_user_id', 'author_id', 'text'], max_results=100)
            #print("pulled individual tweets")
          no_retweets = client.get_users_tweets(id=sm_rewards[currentUser][0], exclude='retweets', start_time = _last_twt_dt, tweet_fields=['created_at', 'in_reply_to_user_id', 'author_id', 'text'], max_results=100)
          #print("pulled no_retweets tweets")
          
          #sort tweets to get just the user reply tweets
          if isinstance(no_retweets.data, Iterable):
            for tweet in no_retweets.data:
              user_tweets_holder.append(tweet.id)
              if tweet not in indiv_tweets and tweet.in_reply_to_user_id == quai_id:
                reply_count += 1
                user_replies.append(int(tweet.id))

          #count all users mentions of quai (not replies)
          if isinstance(indiv_tweets.data, Iterable):
            for tweet in indiv_tweets.data:
              if '@quainetwork' in tweet.text or '@QuaiNetwork' in tweet.text:
                mention_count += 1
                user_mentions.append(int(tweet.id))
              
          #reward user for their specific replies
          sm_rewards[currentUser][2] = reply_count
          #reward users for specific mentions
          sm_rewards[currentUser][3] = mention_count * 5

          users_checked.append(currentUser)


def sort_rewards(dict_to_sort):
  print("sorting data from dictionary")
  dict_list = list(dict_to_sort.items())
  l = len(dict_list)
  for i in range(l-1):
    for j in range(i+1):
      if dict_list[i][1] > dict_list[j][1]:
        toMove = dict_list[i]
        dict_list[i] = dict_list[j]
        dict_list[j] = toMove
  sorted_dict = dict(dict_list)
  return sorted_dict


def aggregate_total(dict_to_aggregate):
  print("RM CHECK -- aggregating data from dictionary")
  aggregate_rewards = {}
  for user in dict_to_aggregate.keys():
    user_total = int(dict_to_aggregate[user][1]) + int(dict_to_aggregate[user][2]) + int(dict_to_aggregate[user][3])
    aggregate_rewards[user] = int(user_total)
  sorted_agg_rewards = sort_rewards(aggregate_rewards)
  print("RM CHECK -- aggregated and sorted data from dictionary")
  return sorted_agg_rewards


def update_all_data():
  twitter_data = read_uds()
  if twitter_data:
    print("RM CHECK -- twitter_data NOT empty, adding sm_rewards value to twitter_data")
    for user in sm_rewards.keys():
      if user in twitter_data.keys():
        twitter_data[user][1] = int(twitter_data[user][1]) + int(sm_rewards[user][1])
        twitter_data[user][2] = int(twitter_data[user][2]) + int(sm_rewards[user][2])
        twitter_data[user][3] = int(twitter_data[user][3]) + int(sm_rewards[user][3])
  else:
    print("RM CHECK -- twitter_data empty, adding sm_rewards value to twitter_data")
    for user in sm_rewards.keys():
      twitter_data[user] = sm_rewards[user]
  updated_agg_rewards = aggregate_total(twitter_data)
  return updated_agg_rewards


def output_data(dict_to_output):
  """
  with open('tweet_monitor_data.csv','w') as tmd:
    print('RM CHECK -- updating tweet monitor data')
    tmdwriter = csv.writer('tweet_monitor_data.csv')
    for line in tmd:
      line_arr = line.strip().split(': ')
      if line_arr[0] == "Last tweet ID":
        last_twt_id = line_arr[1]
      if line_arr[0] == "Last twtID for RM Check":
        tmd.write("%s: %s\n" % ("Last twtID for RM Check", last_twt_id))
  tmd.close()
  """
  
  with open('total_twitter_rewards.csv', 'w') as ttr:
    print("RM CHECK -- outputting to total twitter rewards")
    ttr_field_names = ['Username', 'Total Rewards']
    ttrWriter = csv.DictWriter(ttr, fieldnames=ttr_field_names)
    ttrWriter.writeheader()
    for username in dict_to_output:
      ttr.write("%s: %s\n" % (username, dict_to_output[username]))
    ttr.write('\n')
    ttr.write('Last Updated: '+ current_time)
  ttr.close()

  with open('reply_mention_rewards.csv','w') as rmr:
    print("RM CHECK -- outputting to reply_mention_rewards")
    rmr_field_names = ['Username', 'Reply Rewards', 'Mention Rewards', 'Note: This Data is from last check of Replies and Mentions only (aggregate data can be found in user_data_storage.csv)']
    rmrWriter = csv.DictWriter(rmr, fieldnames=rmr_field_names)
    rmrWriter.writeheader()
    for user in sm_rewards:
      rmr.write("%s: %s, %s\n" % (user, sm_rewards[user][2], sm_rewards[user][3]))
    rmr.write('\n')
    rmr.write('Last Updated: ' + current_time)
  rmr.close()
  
  with open('user_data_storage.csv','w') as new_uds:
    print("RM CHECK -- outputting to user data storage")
    new_uds_fields_names = ['Label','Username', 'Twitter ID', 'Like+Retweet Rewards','Reply Rewards','Mention Rewards']
    new_udsWriter = csv.DictWriter(new_uds, fieldnames=new_uds_fields_names)
    new_udsWriter.writeheader()
    
    for user in twitter_data.keys():
      if len(twitter_data[user]) == 4:
        new_uds.write("%s,%s,%s,%s,%s,%s\n" % ("User Data", user, twitter_data[user][0], twitter_data[user][1], twitter_data[user][2], twitter_data[user][3]))
    new_uds.write('\n')
    new_uds.write('Last Updated: ' + current_time)
  new_uds.close()

            

def reply_mentions_main(_bearer_token, _last_twt_dt):
    
  if _bearer_token == first_bearer:
    client_version = "client1"
  elif _bearer_token == second_bearer:
    client_version = "client2"
  elif _bearer_token == third_bearer:
    client_version = "client3"
  elif _bearer_token == fourth_bearer:
    client_version = "client4"
  elif _bearer_token == fifth_bearer:
    client_version = "client5"
  else:
    print("_bearer_token unrecognized")
    
  print("REPLY_MENTIONS " + client_version + " - " + client_version + " activated. passing tweet data paramaters to " + client_version + " for reply mentions check")

  reply_mentions_check(_bearer_token, _last_twt_dt)
  print("completed reply_mentions_check")
  
  updated_agg_rewards = update_all_data()
  print("updated aggregate rewards")
  
  output_data(updated_agg_rewards)
  print("outputted user_data_storage and total_twitter_rewards")
  print("outputted tweet_monitor_data")
  print()
  print("REPLY_MENTIONS - successful output, end of script")

## TODO:
# - ADD PROPER ERROR OUTPUT TO EXCEPTION HANDLERS
def reply_mentions_main_bot():
  try:
    last_tweet_dt = read_rewards_data()
    print("RM CHECK (main) -- read tweet data")
    reply_mentions_main(third_bearer, last_tweet_dt)
  except:
    try:
      reply_mentions_main(fourth_bearer, last_tweet_dt)
    except:
      try:
        reply_mentions_main(fifth_bearer, last_tweet_dt)
      except:
        print("REPLY_MENTIONS - unsuccessful output -- threw exception")
      #print(sm_rewards)
