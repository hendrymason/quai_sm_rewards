from typing import Iterable
import tweepy
from datetime import datetime, timezone, timedelta
import csv

# PURPOSE: a bot intended to compile a twitter users activity toward a targetted twitter & reward the user based on said interaction level

## NOTES: 
#   {name : [1 $QUAI likes+retweets, 1 $QUAI reply to @quainetwork (with max 2 per day), 5 $QUAI individual tweet about @quainetwork, 
#   retweets, likes, and replies to your individual tweet about $QUAI -> 5 $QUAI per 10 engagements]}

# CONST
quai_id = 1306071657174441985
quai_username = 'quainetwork'
first_bearer = "AAAAAAAAAAAAAAAAAAAAAEHkXwEAAAAAFgCxzDEOf484cKicUHiV3DO6qcU%3DodAKdbVDHoucR6dlOzPbB719XrDMisbZAWLufgqORgLCLgKUtO"

second_bearer = "AAAAAAAAAAAAAAAAAAAAANBOYAEAAAAAlLMei9GmJpSazEtiXx6IWZXEbhs%3DYfsE6mbEa2mLrtZKJhjvjzr4gWZ466w1doYhiWGHlwbDyJzTwx"
third_bearer = "AAAAAAAAAAAAAAAAAAAAAJlpZQEAAAAAjwv7Gg01zTG7ck30cyqxiwQcm9U%3DPNHl3UjpTpKdAjtVcrOs8tZqprtwO6TUKl61XWrXzKKVwgkMDA"
fourth_bearer = "AAAAAAAAAAAAAAAAAAAAAJxpZQEAAAAAexanqSH%2B10AH6FDOHTOqAlqiI8g%3D9hHfSUY0qNXjDGBwlBRNqhXelDcDYpNvnW4VGtpiroOAlabxaR"
fifth_bearer = "AAAAAAAAAAAAAAAAAAAAABoZZwEAAAAAWdu%2BFszRiTgPBboHWwzAWIxV7SI%3DaKeaVddnpgh8DJYOZkEw7GFpP7NbAHwuPne4zpbimS8tKpCsXn"


# dicts to track and store everything -> {username: [likes+retweets, replies, mentions, engagement rewards], ...}
sm_rewards = {}
username_userID = {}
db_tweets_tracked = []
all_tweets_tracked = []
last_sm_rewards = {}

# class to track global var in functions
class tweets_monitor:
  last_tweet_id = 1459205924573396997 #first tweet id as default
  twtID_for_reply_mentions = 0
  completed_check = False
  resuming_update = False
  new_tweet_count = 0
  db_tweet_count = 0
  db_last_tweet_id = 0
  
  def addedNewTweet(self):
    self.new_tweet_count += 1
  
  def addedDBTweet(self):
    self.db_tweet_count += 1
  
  def get_total_tweets(self):
    return self.db_tweet_count + self.new_tweet_count


# function: checks if file is empty by checking for second row in csv
def is_empty(file):
  with open(file) as file_alias:
    reader = csv.reader(file_alias)
    for i, _ in enumerate(reader):
      if i:  # found the second row
        return "not empty"
    return "empty"


# function: sort all_tweets_tracked dict for most up to date tweet
def sort_List(_list): 
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



def read_tweet_data(_monitor):
  with open('tweet_monitor_data.csv') as ctd:
    empty_result = is_empty('tweet_monitor_data.csv')
    if empty_result == "not empty":
      for line in ctd:
        line_array = line.strip().split(': ')
        
        if line_array[0] == "Last Check Complete":
          _monitor.completed_check = bool(line_array[1])
        
        if line_array[0] == "Last tweet ID" and _monitor.completed_check == True:
          _monitor.db_last_tweet_id = int(line_array[1])
          _monitor.twtID_for_reply_mentions = line_array[1]
          _monitor.last_tweet_id = int(line_array[1])
          print(str(_monitor.last_tweet_id))
    
    print("read_tweet_data function - closed client data file. set last_tweet_id to " + str(_monitor.last_tweet_id))
  
  #print("read_tweet_data function - last check was not completed, reading user reward data")
  
# open tweet input csv and create a dictionary from the file data
  with open("tweetsDB.csv") as twts:
    print("read_tweet_data function - opened input data file")
    empty_result = is_empty("tweetsDB.csv")
    
    for line in twts:
      if empty_result == "not empty":
        twt_array = line.strip().split(': ')
        if twt_array[0] == "Valid Tweet Tracked":
          db_tweets_tracked.append(int(twt_array[1]))
          _monitor.addedDBTweet()
    
    print("read_tweet_data function - inputted " + str(_monitor.db_tweet_count) + " tweets to db_tweets_tracked.")
    
    if _monitor.completed_check == False and _monitor.db_tweet_count > 0:
      _monitor.last_tweet_id = int(db_tweets_tracked[-1])
      _monitor.twtID_for_reply_mentions = int(db_tweets_tracked[-1])
      print("read_tweet_data function - set last_tweet_id to " + str(_monitor.last_tweet_id))

# function: output to rewards csv
def output_rewards_data():
  # EXPORT OUTPUT: export to csv file to use in reply_mentions_tracker
  lrr_field_names = ['UserID','Username', 'Like+Retweet Rewards', 'Note: This Data is from last check of Likes+Retweets only (aggregate data can be found in user_data_storage.csv)']
  with open('like_retweet_rewards.csv', 'w') as lrr:
    writer = csv.DictWriter(lrr, fieldnames=lrr_field_names)
    writer.writeheader()
    for user in sm_rewards.keys():
      lrr.write("%s,%s,%s\n" % (username_userID[user], user, sm_rewards[user]))
    lrr.write("\n")
    lrr.write('Last Update: '+ str(datetime.now()))
  lrr.close()

# function: output to tweet csvs
def output_tweet_data(_monitor, up_to_date):
  if up_to_date:
    tweets_sorted = sort_List(db_tweets_tracked)
  else:
    tweets_sorted = sort_List(all_tweets_tracked)
  if len(tweets_sorted) > 0 and _monitor.completed_check:
    _monitor.last_tweet_id = int(tweets_sorted[0])
    print("output function: set last tweet id: " + str(_monitor.last_tweet_id))
  # EXPORT TWEET DATA FOR FUTURE USE:
  with open("tweetsDB.csv",'w') as t:
    for tweetID in tweets_sorted:
      t.write("%s: %s\n" % ("Valid Tweet Tracked", tweetID))
    if len(tweets_sorted) > 0:
      t.write('\n')
    t.write('Last Update: '+ str(datetime.now()))
  # USE THIS CSV AS A REFERENCE WHEN RECEIVING MOST RECENT TWEETID
  with open('tweet_monitor_data.csv', 'w') as ctd:
    ctd.write("%s: %s\n" % ("Last Check Complete", _monitor.completed_check))
    ctd.write("%s: %s\n" % ("Last tweet ID", _monitor.last_tweet_id))
    ctd.write("%s: %s\n" % ("Last twtID for RM Check", _monitor.twtID_for_reply_mentions))
    ctd.write("Most Recent Tweet Pull: " + str(datetime.now()))


def up_to_date_check(_tweets):
  print("running up to date check")
  if _tweets.data == None:
    print("Data pulled from client had no new tweets, db_tweets_tracked is up to date")
    return True
  #extra handling/checking
  if len(db_tweets_tracked) > 0:
    db_tweets_sorted = sort_List(db_tweets_tracked)
    print("sorted db_tweets")
    db_most_recent_twt = int(db_tweets_sorted[0])
    client_most_recent_twt = int(_tweets.data[0].id)
    
    if client_most_recent_twt == db_most_recent_twt:
      print("db_tweets_tracked file is up to date, however, this means monitor.last_tweet_id was wrong on client call")
      return True
    else:
      print("not up to date, latest tweet in client is not most recent in db_tracked_tweets")
      return False
  else:
    print("not up to date, db_tweets_tracked is empty")
    return False


def paginate(_client, response, _id, user_type):
  pagination = True
  collected_data = []
  next_token = response.meta['next_token']
  pagination_count = 0
  while pagination == True:
    if user_type == "likes":
      new_response = _client.get_liking_users(id=_id, pagination_token=next_token)
    elif user_type == "retweets":
      new_response = _client.get_retweeters(id=_id, pagination_token=next_token)
      
    if new_response.data != None:
      for tweet_data in new_response.data:
        collected_data.append(tweet_data)
      pagination_count += 1
    else:
        print("pulled a 'None' Type for response")
    
    try:
      if new_response.meta["next_token"]:
        next_token = new_response.meta["next_token"]
    except:
      print("done paginating")
      print("paginated " + user_type + " " + str(pagination_count) + " times.")
      pagination = False
  
  return collected_data
      
# iterate through tweet objects to collect retweeters, likers, and replies and assign user's their respective rewards
# iterate through each tweet and request those who liked and those who tweeted, sorting those who did both into likers_retweeters
def like_retweet_check(_client, _tweets, _monitor):
  _monitor.completed_check = False
  for tweet in _tweets.data:
    if tweet.id not in db_tweets_tracked:
      
      all_tweets_tracked.append(tweet.id)
      _monitor.addedNewTweet()
      _monitor.last_tweet_id = int(tweet.id)
      
      likers_list = []
      retweeters_list = []
      likers_retweeters = []
      
      print("-- new tweet --")
      print(str(_monitor.new_tweet_count))
      print(str(tweet.id))

      # make request to get those who liked, then make request to get those who retweeted
      """
      likers = _client.get_liking_users(tweet.id)
      retweeters = _client.get_retweeters(tweet.id)
      """

      likers_response = _client.get_liking_users(tweet.id)
      retweeters_response = _client.get_retweeters(tweet.id)

      likers_data = likers_response.data
      retweeters_data = retweeters_response.data

      # attempt to pull pagination token and paginate through next set of responses
      try:
        if len(likers_data) == 100:
          if likers_response.meta['next_token']:
            paginated_data = paginate(_client, likers_response, tweet.id, "likes")
            for data in paginated_data:
              likers_data.append(data)
      except:
          print("likers_response did not need to be paginated")
        
      try:
        if len(retweeters_data) == 100:
          if retweeters_response.meta['next_token']:
            paginated_data = paginate(_client, retweeters_response, tweet.id, "retweets")
            for data in paginated_data:
              retweeters_data.append(data)
      except:
          print("retweeters_response list did not need to be paginated")

        
      # pull username into liker list from likers data
      if isinstance(likers_data, Iterable):
        for liker in likers_data:
          if liker not in username_userID:
           username_userID[liker.username] = liker.id
          likers_list.append(liker.username)
      # pull username into retweeter list from retweeters data 
      if isinstance(retweeters_data, Iterable):
        for retweeter in retweeters_data:
          if retweeter not in username_userID:
            username_userID[retweeter.username] = retweeter.id
          retweeters_list.append(retweeter.username)


              
      # create new list of users who BOTH liked and retweeted
      likers_retweeters = [username for username in likers_list if username in retweeters_list]

      # increment users rewards or add user to dict based on like+retweet list
      for username in likers_retweeters:
          if username in sm_rewards:
              sm_rewards[username] = sm_rewards[username] + 1
          else:
              sm_rewards[username] = 1
                
    
    # confirm check has ran through all tweets by checking for first tweet or starting last_tweet_id in preset db
    #if _monitor.last_tweet_id == 1459205924573396997 or _monitor.last_tweet_id == _monitor.db_last_tweet_id:
    _monitor.completed_check = True
    print("like+retweet_check - monitor completed check: " + str(_monitor.completed_check))

    for tweet_id in db_tweets_tracked:
        if tweet_id not in all_tweets_tracked:
            all_tweets_tracked.append(tweet_id)
    sort_List(all_tweets_tracked)
    _monitor.last_tweet_id = int(all_tweets_tracked[0])
    print("like+retweet_check - last_tweet_id: " + str(_monitor.last_tweet_id))


def client_script(_bearer_token, _monitor):
  client = tweepy.Client(bearer_token= _bearer_token)
    
  if _bearer_token == first_bearer:
    client_version = "client1"
    script_version = "1"
  elif _bearer_token == second_bearer:
    client_version = "client2"
    script_version = "2"
  elif _bearer_token == third_bearer:
    client_version = "client3"
    script_version = "3"
  elif _bearer_token == fourth_bearer:
    client_version = "client4"
    script_version = "4"
  elif _bearer_token == fifth_bearer:
    client_version = "client5"
    script_version = "5"
  else:
    print("_bearer_token unrecognized")

    
  print("LIKE+RETWEET " + client_version + " - " + client_version + " activated. passing tweet data paramaters to " + client_version + " tweet pull request")
    
  # conditon: check was not completed/set to false and the starting tweet is initial tweet (starting point)
  if _monitor.completed_check == False and _monitor.last_tweet_id == 1459205924573396997:
    print(client_version + " - " + str(_monitor.completed_check) + " monitor complete check v" + script_version + ".1")
    print(client_version + " - last_tweet_id: " + str(_monitor.last_tweet_id))
    tweets_client = client.get_users_tweets(id=quai_id, exclude=['retweets', 'replies'], since_id= _monitor.last_tweet_id, tweet_fields='created_at', max_results=100)
    up_to_date = False
  
  # conditon: check was not completed/set to false during update, already counted rewards prior (half-completed check)
  elif _monitor.completed_check == False and _monitor.last_tweet_id != 1459205924573396997 and _monitor.resuming_update == True:
    print(client_version + " - " + str(_monitor.completed_check) + " monitor complete check v" + script_version + ".2")
    print(client_version + " - last_tweet_id: " + str(_monitor.last_tweet_id))
    tweets_client = client.get_users_tweets(id=quai_id, exclude=['retweets', 'replies'], since_id= _monitor.last_tweet_id, tweet_fields='created_at', max_results=100)
    up_to_date = False
  
  # conditon: check was not completed/set to false and the starting tweet is not initial tweet (half-completed check)
  elif _monitor.completed_check == False and _monitor.last_tweet_id != 1459205924573396997:
    print(client_version + " - " + str(_monitor.completed_check) + " monitor complete check v" + script_version + ".3")
    print(client_version + " - last_tweet_id: " + str(_monitor.last_tweet_id))
    tweets_client = client.get_users_tweets(id=quai_id, exclude=['retweets', 'replies'], until_id= _monitor.last_tweet_id, tweet_fields='created_at', max_results=100)
    up_to_date = False
  
  # conditon: check was completed/set to true and the starting tweet is not initial tweet (following successful updates)
  elif _monitor.completed_check and _monitor.last_tweet_id != 1459205924573396997:
    print(client_version + " - " + str(_monitor.completed_check) + " monitor complete check v" + script_version + ".4")
    print(client_version + " - last_tweet_id: " + str(_monitor.last_tweet_id))
    tweets_client = client.get_users_tweets(id=quai_id, exclude=['retweets', 'replies'], since_id= _monitor.last_tweet_id, tweet_fields='created_at', max_results=100)
    print("pulled tweets from client")
    up_to_date = up_to_date_check(tweets_client)
    _monitor.resuming_update = True
    print("tweets up to date: " + str(up_to_date))

  # conditon: check was completed/set to true but the starting tweet is initial tweet (?)
  elif _monitor.completed_check and _monitor.last_tweet_id == 1459205924573396997:
    print(client_version + " - " + str(_monitor.completed_check) + " monitor complete check v" + script_version + ".5")
    print(client_version + " - last_tweet_id: " + str(_monitor.last_tweet_id))
    tweets_client = client.get_users_tweets(id=quai_id, exclude=['retweets', 'replies'], since_id= _monitor.last_tweet_id, tweet_fields='created_at', max_results=100)
    up_to_date = False

  else: # handler takes file data and re-writes it back to its original data state with updated "Last Updated" Fields
    up_to_date = True
  
  print("LIKE+RETWEET " + client_version + " - " + client_version + " tweet pull request complete.")
    
  if up_to_date == False:
    print(client_version + " - tweets tracked not up to date. starting like_retweet check")
    like_retweet_check(client, tweets_client, _monitor)
    print(client_version + " - like+retweet tracker complete.")
  
  print(client_version + " - begin outputting data to csv files")
  
  output_tweet_data(_monitor, up_to_date)
  output_rewards_data()

  print("LIKE+RETWEET " + client_version + " - outputted tweet data and rewards to csv")
 
  print("LIKE+RETWEET " + client_version + " end script - successful output.")
  timezone_offset = -6.0  # Central Standard Time (UTC−06:00)
  tzinfo = timezone(timedelta(hours=timezone_offset))
  print(str(datetime.now(tzinfo)))


## Main Bot Logic
def like_retweet_main_bot():
  try:
    monitor = tweets_monitor()
    read_tweet_data(monitor)
    client_script(third_bearer, monitor)
  except:
    try:
      client_script(fourth_bearer, monitor)
    except:
      try:
        client_script(fifth_bearer, monitor)
      except:
        output_tweet_data(monitor, False)
        print("LIKE+RETWEET - unsuccessful output -- threw exception")
