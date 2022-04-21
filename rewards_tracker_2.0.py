from typing import Iterable
from numpy import iterable
import tweepy
from datetime import datetime, timezone, timedelta
from urllib.error import HTTPError
import gspread
from google.oauth2 import service_account
#from replit import db
import pickle
from os import path
from operator import itemgetter

# CONSTANTS - Quai Constants for Twitter Requests & multiple Bearer Tokens for enhanced API Access
quai_id = 1306071657174441985
first_quai_tweet = 1459205924573396997
quai_username = 'quainetwork'
first_bearer = "AAAAAAAAAAAAAAAAAAAAAEHkXwEAAAAAFgCxzDEOf484cKicUHiV3DO6qcU%3DodAKdbVDHoucR6dlOzPbB719XrDMisbZAWLufgqORgLCLgKUtO"
second_bearer = "AAAAAAAAAAAAAAAAAAAAANBOYAEAAAAAlLMei9GmJpSazEtiXx6IWZXEbhs%3DYfsE6mbEa2mLrtZKJhjvjzr4gWZ466w1doYhiWGHlwbDyJzTwx"
third_bearer = "AAAAAAAAAAAAAAAAAAAAAJlpZQEAAAAAjwv7Gg01zTG7ck30cyqxiwQcm9U%3DPNHl3UjpTpKdAjtVcrOs8tZqprtwO6TUKl61XWrXzKKVwgkMDA"
fourth_bearer = "AAAAAAAAAAAAAAAAAAAAAJxpZQEAAAAAexanqSH%2B10AH6FDOHTOqAlqiI8g%3D9hHfSUY0qNXjDGBwlBRNqhXelDcDYpNvnW4VGtpiroOAlabxaR"
fifth_bearer = "AAAAAAAAAAAAAAAAAAAAABoZZwEAAAAAWdu%2BFszRiTgPBboHWwzAWIxV7SI%3DaKeaVddnpgh8DJYOZkEw7GFpP7NbAHwuPne4zpbimS8tKpCsXn"

# Gsheets API Setup
SERVICE_ACCOUNT_FILE = 'service-key.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gc = gspread.service_account(filename='service-key.json')
# Gsheets - Sheets for User Data
rewards_sheet_id = '1vsWNnj_yaxlcOvolr4Shac-jWc2rLtI1VLW-OpcvEgg'
new_signup_id = '1ojwwSIF7G8cAT81jVz3R_7I8BcbTKDNPSM6uFTOGQ_s'
gsheet_rewards = gc.open_by_key(rewards_sheet_id)
new_signup_sheet = gc.open_by_key(new_signup_id).worksheet("Form Responses 1")
rm_users_checked = []
bots = [1425707762856644608, 1390749554421780483, 1135574978244440064, 710440106, 1362859031870791684, 1274924713576300544, 1126894279777976320, 830792160706322433, 830792160706322433, 890494541177831424, 1287748747166748673, 1301791405443080192, 984003078818074624, 923050660886732800]

##### Outline for SM BOT 2.0

### Classes (Models) --> write in different files for more organized code? figure out import process for class files
# User_Data Class
class User:
  twitter_id = 0
  youtube_rewards = 0
  todays_rewards = 0
  total_rewards = 0
  todays_rank = "0" # string so it can be adjusted with a "T" in the instance of a tie in rankings
  total_rank = "0" # string so it can be adjusted with a "T" in the instance of a tie in rankings
  last_date_tracked = datetime.strptime('2021-11-12 00:00:00+0000', '%Y-%m-%d %H:%M:%S%z').replace(microsecond=0).isoformat()
  last_twt_id = 0
  current_date = datetime.strptime('2021-11-12','%Y-%m-%d')
  
  def __init__(self, discord_name, twitter_name, youtube_channel):
    self.discord_name = discord_name # also used for Key storage in db
    self.twitter_name = twitter_name # for checking twitter rewards
    self.youtube_channel = youtube_channel # used when integrating with youtube rewards bot
    self.like_retweet_data = Like_Retweet_Data() # storage object for Likes+Retweets Data and Rewards
    self.reply_mention_data = Reply_Mention_Data() # storage object for Replies+Mentions Data and Rewards

  # GETTERS / SETTERS
  def set_rank(self, rank_type, rank):
    if rank_type == "today":
      self.todays_rank = rank
    elif rank_type == "total":
      self.total_rank = rank

  def set_total_rewards(self, total_rewards):
    self.total_rewards = total_rewards

  def set_twitter_id(self, user_id):
    self.twitter_id = user_id

  def set_lrr_data(self, lrr_obj):
    self.like_retweet_data = lrr_obj

  def set_rm_data(self, rm_obj):
    self.reply_mention_data = rm_obj

  def add_lr_rewards(self, tracked_tweet_date):
    self.like_retweet_data.add_rewards(tracked_tweet_date)

  def add_reply_rewards(self, tracked_tweet_date):
    self.reply_mention_data.add_rewards("reply", tracked_tweet_date)

  def add_mention_rewards(self, tracked_tweet_date):
    self.reply_mention_data.add_rewards("mention", tracked_tweet_date)

  def set_current_date(self, current_date):
    self.like_retweet_data.set_current_date(current_date)
    self.reply_mention_data.set_current_date(current_date)
    if self.current_date != current_date:
      self.current_date = current_date
      self.todays_rewards = 0

  # METHODS
  def set_last_tweet_id(self):
    ## stores datetime object in last_date_tracked as the datetime format the twitter api requests can use
    if self.reply_mention_data.last_reply_date > self.reply_mention_data.last_mention_date:
      self.last_twt_id = self.reply_mention_data.last_reply_id
    else:
      self.last_twt_id = self.reply_mention_data.last_mention_id
    
  def calculate_rewards(self):
    #aggregate todays rewards
    todays_lrr_rewards = self.like_retweet_data.todays_rewards
    todays_rm_rewards = self.reply_mention_data.calculate_todays_rewards()
    self.todays_rewards = todays_lrr_rewards + todays_rm_rewards
    #aggragte total rewards
    lrr_rewards = self.like_retweet_data.total_rewards
    rm_rewards = self.reply_mention_data.calculate_total_rewards()
    self.total_rewards = lrr_rewards + rm_rewards

    return self.total_rewards
    
# Like_Retweet_Data Class
class Like_Retweet_Data:
  todays_rewards = 0
  total_rewards = 0
  current_date = datetime.strptime('2021-11-12', '%Y-%m-%d')
  
  # METHODS
  def set_current_date(self, current_date):
    if self.current_date != current_date:
      self.todays_rewards = 0
      self.current_date = current_date
  
  def add_rewards(self, tracked_tweet_date):
    self.total_rewards += 1
    if self.current_date == tracked_tweet_date:
      self.todays_rewards += 1
  
# Reply_Mention_Data Class
class Reply_Mention_Data:
  #reply+mention aggregated data
  todays_rewards = 0
  total_rewards = 0
  current_date = datetime.strptime('2021-11-12', '%Y-%m-%d')
  #reply data
  reply_rewards = 0
  todays_reply_rewards = 0
  total_reply_rewards = 0
  reply_limited = False # limiter for 2 per day
  last_reply_id = 0
  last_reply_date = datetime.strptime('2021-11-12', '%Y-%m-%d')
  #mention data
  mention_rewards = 0
  todays_mention_rewards = 0
  total_mention_rewards = 0
  mention_limited = False # limiter for 2 per day
  last_mention_id = 0
  last_mention_date = datetime.strptime('2021-11-12', '%Y-%m-%d')

  # GETTERS / SETTERS
  def set_current_date(self, current_date):
    if self.current_date != current_date:
      self.todays_rewards = 0
      self.current_date = current_date
  
  # METHODS
  def add_rewards(self, reward_type, tracked_tweet_dt):
    tracked_date_str = tracked_tweet_dt.strftime('%Y-%m-%d')
    tracked_tweet_date = datetime.strptime(tracked_date_str, '%Y-%m-%d')
    
    if reward_type == "reply":
      if self.current_date == tracked_tweet_date:
        if self.reply_limited == False:
          self.todays_reply_rewards += 1
          self.total_reply_rewards += 1
          if self.todays_reply_rewards == 2:
            self.reply_limited = True
          if self.last_reply_date < tracked_tweet_date:
            self.last_reply_date = tracked_tweet_date
      # Resetting todays reply rewards & incrementing to total
      else:
        self.reply_limited = False
        self.todays_reply_rewards = 1
        self.total_reply_rewards += 1
    
    elif reward_type == "mention":
      if self.current_date == tracked_tweet_date:
        if self.mention_limited == False:
          self.todays_mention_rewards += 5
          self.total_mention_rewards += 5
          # Limits reward count if user mentions >= 2 for tracked day
          if self.todays_mention_rewards == 10:
            self.mention_limited = True
          if self.last_mention_date < tracked_tweet_date:
            self.last_mention_date = tracked_tweet_date
      # Resetting todays mention rewards & incrementing to total
      else:
        self.mention_limited = False
        self.todays_mention_rewards = 5
        self.total_mention_rewards += 5
      

  def calculate_todays_rewards(self):
    self.todays_rewards = self.todays_reply_rewards + self.todays_mention_rewards
    return self.todays_rewards

  def calculate_total_rewards(self):
    self.total_rewards = self.total_reply_rewards + self.total_mention_rewards
    return self.total_rewards
  
  def reset_todays_rewards(self):
    self.todays_rewards = 0
    self.todays_reply_rewards = 0
    self.todays_mention_rewards = 0
  
# Twitter_Monitor Class
### (?) add "last" update fun
class Monitor:
  last_check_completed = True # False if there was an error in code or rate limiting issue and the check stopped
  last_lrr_check_completed = True
  last_rm_check_completed = True
  most_recent_tweet = 0 
  last_quai_tweet = 1459205924573396997 # tracks last tweet from quai checked (for Likes+Retweets Checker)
  last_check_date = "" # ?? is this needed if id is stored
  last_signup_index = 0
  current_check_date = "" # set for proper tracking in conditionals of each users todays rewards
  # for client requests -> default is first_bearer token
  current_bearer = first_bearer
  tracked_tweets = []

  # GETTERS / SETTERS
  def get_check_status(self):
    return self.last_check_completed

  def set_check_status(self):
    if self.last_lrr_check_completed and self.last_rm_check_completed:
      self.last_check_completed = True
    else:
      self.last_check_completed = False
    
  def set_lrr_status(self, status, tweet_id=0):
    if status:
      self.last_quai_tweet = self.most_recent_tweet
      self.last_lrr_check_completed = status
    else:
      self.last_lrr_check_completed = status
      self.most_recent_tweet = tweet_id

  def get_last_tweet(self):
    return self.last_quai_tweet
  
  def set_last_tweet(self, tweet_id):
    self.last_quai_tweet = tweet_id
    if tweet_id not in self.tracked_tweets:
      self.tracked_tweets.append(tweet_id)
    
  def get_signup_index(self):
    return self.last_signup_index

  def set_signup_index(self, signup_index):
    self.last_signup_index = signup_index

  def set_current_check_date(self, current_date):
    self.current_check_date = current_date

  def get_bearer_token(self):
      return self.current_bearer
  
  def add_tracked_tweet(self, tweet_id):
    self.tracked_tweets.append(tweet_id)
  
### Accessory Functions

# CLEAN_DATA() FUNCTION -> properly format twitter data to be used in reward tracking
def clean_data(_twitter_usernames):
  for idx, name in enumerate(_twitter_usernames):
    if name != "":
      lowercase_name = name.lower()
      if "@" in lowercase_name:
        _twitter_usernames[idx] = lowercase_name.replace("@","")
      else:
        _twitter_usernames[idx] = "INVALID"
    else:
      _twitter_usernames[idx] = "NONE"
  return _twitter_usernames

# GET_DATE() FUNCTION -> Allow automated script to know when to perform certain actions
def get_current_date():
  last_date_tracked = datetime.strptime('2021-11-12', '%Y-%m-%d').replace(microsecond=0).isoformat()
  timezone_offset = -6.0  # Central Standard Time (UTC−06:00)
  tzinfo = timezone(timedelta(hours=timezone_offset))
  current_time = datetime.now(tzinfo)
  current_date = current_time.strftime('%Y-%m-%d')
  return current_time

# GET_TWEET_DATE() FUNCTION -> enable more accurate comparisons for reply/mention tweet tracking and reward counting
def get_tweet_date(_tweet_created_at):
  datetime_str = _tweet_created_at.strftime('%Y-%m-%d')
  standard_date = datetime.strptime(datetime_str, '%Y-%m-%d')
  return standard_date

# GET_DB_DATA() FUNCTION -> used to setup or pull the Database file & the dictionary for script use
def get_db_data():
  if path.exists("bot_db.pickle") == False:
    rewards_file = open('bot_db.pickle','wb')
    db_data = {}
  else:
    rewards_file = open('bot_db.pickle','rb')
    db_data = pickle.load(rewards_file)
    rewards_file.close()
  return db_data

# PAGINATE() Function (for iterating through quai tweets, likers/retweeters of a quai tweet, a users following (@quainetwork & @alanorwick check), users replies/mentions)
def paginate(_client, _response, _request_type, _user_id=0, _tweet_id=0, _tweet_date="",_db_dict={}):
  if _db_dict !={}:
    monitor = _db_dict["Monitor"]
  pagination = True
  next_token = _response.meta['next_token']
  pagination_count = 0
  paginated_data_count = 0
  non_bot_requests = ["tweets 1.0", "tweets 2.0", "likers", "retweeters"]
  
  while pagination == True:
    if pagination_count > 50 and _request_type not in non_bot_requests:
      print("User ID: ", _user_id, " Has been overpaginated -- likely mark as a potential bot")
      bots.append(_user_id)
      break
    print("Pagination Count: " + str(pagination_count))
    
    # Pulling Tweets since the last tweet tracked - starting check
    if _request_type == "tweets 1.0": # could make an enum for each different type
      new_response = _client.get_users_tweets(id=_user_id, exclude=['retweets', 'replies'], since_id= _tweet_id, tweet_fields='created_at', max_results=100, pagination_token=next_token)
    # Pulling Tweets up until last tweet tracked - resuming check from code break / api limit
    elif _request_type == "tweets 2.0":
      new_response = _client.get_users_tweets(id=_user_id, exclude=['retweets', 'replies'], until_id= _tweet_id, tweet_fields='created_at', max_results=100, pagination_token=next_token)
    elif _request_type == "likers":
      new_response = _client.get_liking_users(id=_tweet_id, pagination_token=next_token)
    elif _request_type == "retweeters":
      new_response = _client.get_retweeters(id=_tweet_id, pagination_token=next_token)
    # Pulling Replies / Mentions based on the last date the bot has tracked the user (if never tracked, passes through quais first tweet date)
    elif _request_type == "replies 1.0":
      new_response = _client.get_users_tweets(id=_user_id,exclude='retweets',start_time=_tweet_date, tweet_fields=['created_at', 'in_reply_to_user_id', 'author_id', 'text'], max_results=100, pagination_token=next_token)
    elif _request_type == "replies 2.0":
      new_response = _client.get_users_tweets(id=_user_id,exclude='retweets', since_id=_tweet_id, tweet_fields=['created_at', 'in_reply_to_user_id', 'author_id', 'text'], max_results=100)
    elif _request_type == "mentions 1.0":
      new_response = _client.get_users_tweets(id=_user_id, exclude=['retweets', 'replies'], start_time=_tweet_date, tweet_fields=['created_at', 'in_reply_to_user_id', 'author_id', 'text'], max_results=100, pagination_token=next_token)
    elif _request_type == "mentions 2.0":
      new_response = _client.get_users_tweets(id=_user_id, exclude=['retweets', 'replies'], since_id=_tweet_id, tweet_fields=['created_at', 'in_reply_to_user_id', 'author_id', 'text'], max_results=100)
    # iterating through paginated data pulled and adding to response data array
    if isinstance(new_response.data, Iterable):
      if _request_type == "tweets 2.0" and _tweet_id:
        if "Monitor" in _db_dict.keys():
          if _tweet_id not in _db_dict["Monitor"].tracked_tweets:
            until_id_tweet = _client.get_tweet(id=_tweet_id)
            _response.data.append(until_id_tweet.data)
      
      for data in new_response.data:
        if data.id not in _response.data:
          _response.data.append(data)
          #print(data.id)
      
      # including the since_id tweet at end of request data array of tweets if not already tracked in the Monitor's tracked tweets
      if _request_type == "tweets 1.0" and _tweet_id not in _response.data:
        if "Monitor" in _db_dict.keys():
          if _tweet_id not in _db_dict["Monitor"].tracked_tweets:
            since_id_twt = _client.get_tweet(id=_tweet_id)
            _response.data.append(since_id_twt.data)
      
      paginated_data_count += 1
      pagination_count += 1
    else:
      print("pulled a 'None' Type for response")
    
    # Checking for more data in latest response
    if "next_token" in new_response.meta.keys() and new_response.meta["result_count"] == 100:
      next_token = new_response.meta["next_token"]
      print("Found next token. Continuing Pagination...")
    else:
      print("*Completed Pagination*")
      print(str(_request_type) + " paginated " + str(pagination_count) + " times and pulled " + str(paginated_data_count) + " pieces of data")
      pagination = False
  
  return _response
  

# CHECK_REQUIREMENTS() FUNCTION -> tied into IMPORT_USERS() user must have more than 50 followers (to verify validity) and be following @alanorwick and @quainetwork on Twitter - and eventually, user must be subscribed to Quai Network on Youtube
  # pull twitter_id/username from db and create client request to get user's following
  # iterate (and possibly paginate) through the following to scan for both quainetwork and alanorwick
  # if following both accounts: store in db, else: remove from db


  
### MAIN FUNCTIONS

## IMPORT_USERS() FUNCTION
def import_users(_db_dict, _new_signup_sheet, _signup_index):
  # Sheet Specific Data - Pulling User Signup Info from Gsheets
  discord_name_col = 2
  twitter_name_col = 3
  youtube_channel_col = 4
  # new signup form data captured in Lists
  discord_data = _new_signup_sheet.col_values(discord_name_col)[1:]
  twitter_data = _new_signup_sheet.col_values(twitter_name_col)[1:]
  youtube_data = _new_signup_sheet.col_values(youtube_channel_col)[1:]

  # format twitter usernames
  clean_twitter_data = clean_data(twitter_data)

  # create a new_user instance from User class for each signup in discord_data list
  if _signup_index != len(discord_data):
    for idx in range(_signup_index, len(discord_data)):
      discord_name = discord_data[idx].lower()
      if "#" in discord_data[idx]:
        if idx <= len(clean_twitter_data)-1:
          twitter_name = clean_twitter_data[idx]
        if idx <= len(youtube_data)-1:
          youtube_channel = youtube_data[idx]
  
        #track the index of the last signed up user to resume here next signup pull
        _signup_index += 1
        # instantiate new_user from User class with provided signup data
        new_user_data = User(discord_name, twitter_name, youtube_channel)

        
        
        # if user has data stored but just needs to update usernames -> move tracked reward data over to new_user
        if discord_name in _db_dict.keys():
          current_user_data = _db_dict[discord_name]
          users_total_rewards = current_user_data.total_rewards
          users_lrr_data = current_user_data.like_retweet_data
          users_rm_data = current_user_data.reply_mention_data
          # reassign old data to new_user obj
          new_user_data.set_total_rewards(users_total_rewards)
          new_user_data.set_lrr_data(users_lrr_data)
          new_user_data.set_rm_data(users_rm_data)
        
          # add the new_user_data into the _db_dict dict
        _db_dict[discord_name] = new_user_data

    # storing the index to resume the update from signup data, to prevent reinstantiating user objects from signup
    _db_dict["Monitor"].set_signup_index(_signup_index)
  print("*Imported Users*")
  return _db_dict


## LIKE_RETWEET_TRACKER() FUNCTION -> manipulate data in Dictionary of User_Data Objs
def like_retweet_tracker(_db_dict, _client):
  rewarded_users = []
  print("*Beginning Like+Retweet Check*")
  check_status = _db_dict["Monitor"].last_lrr_check_completed
  last_twt_id = _db_dict["Monitor"].get_last_tweet()
  up_to_date = True

  print("Last Tweet ID: "+ str(last_twt_id))

  # Start/Restart Check from new/empty db_dict (aka last_quai_tweet = first_quai_tweet) Condition
  if check_status and last_twt_id == first_quai_tweet:
    print("LRR CHECK - Condition 1: True Check Status and Last Tweet = Quai's First Tweet")
    client_tweets = _client.get_users_tweets(id=quai_id, exclude=['retweets', 'replies'], since_id= last_twt_id, tweet_fields='created_at', max_results=100)
    if "next_token" in client_tweets.meta.keys() and client_tweets.meta["result_count"] == 100:
      client_tweets = paginate(_client, client_tweets, "tweets 1.0", quai_id, last_twt_id, _db_dict=_db_dict)
    up_to_date = False
  # Standard Check Procedure Condition
  elif check_status and last_twt_id != first_quai_tweet:
    print("LRR CHECK - Condition 2: True Check Status and Last Tweet != Quai's First Tweet")
    client_tweets = _client.get_users_tweets(id=quai_id, exclude=['retweets', 'replies'], since_id= last_twt_id, tweet_fields='created_at', max_results=100)
    # pulls 100 most recent tweets first, so no need to paginate yet
    if "next_token" in client_tweets.meta.keys() and client_tweets.meta["result_count"] == 100:
      client_tweets = paginate(_client, client_tweets, "tweets 1.0", quai_id, last_twt_id, _db_dict=_db_dict)
    if client_tweets.meta["result_count"] != 0:
      up_to_date = False
  # Resuming Check after Broken Code / Client Request Limit Condition
  elif check_status == False and last_twt_id != first_quai_tweet:
    print("LRR CHECK - Condition 3: False Check Status and Last Tweet != Quai's First Tweet")
    client_tweets = _client.get_users_tweets(id=quai_id, exclude=['retweets', 'replies'], until_id= last_twt_id, tweet_fields='created_at', max_results=100)
    if "next_token" in client_tweets.meta.keys() and client_tweets.meta["result_count"] == 100:
      client_tweets = paginate(_client, client_tweets, "tweets 2.0", quai_id, last_twt_id, _db_dict=_db_dict)
    up_to_date = False
  # Resuming check if no Tweets were accounted for following reset/first start and last_twt_id == first_quai_tweet
  else:
    print("LRR CHECK - Condition 4: False Check Status and Last Tweet == Quai's First Tweet")
    client_tweets = _client.get_users_tweets(id=quai_id, exclude=['retweets', 'replies'], since_id= last_twt_id, tweet_fields='created_at', max_results=100)
    if "next_token" in client_tweets.meta.keys() and client_tweets.meta["result_count"] == 100:
      client_tweets = paginate(_client, client_tweets, "tweets 1.0", quai_id, last_twt_id, _db_dict=_db_dict)
    up_to_date = False
  
    
  # Run main LRR Check, contingent on new quai tweets(not up to date) and tweets were pulled
  if up_to_date == False:

    most_recent_quai_twt = client_tweets.data[0].id
    if _db_dict["Monitor"].last_lrr_check_completed:
      _db_dict["Monitor"].set_lrr_status(False, most_recent_quai_twt)

    for tweet in client_tweets.data:
      if tweet.id not in _db_dict["Monitor"].tracked_tweets:
  
        # pull liking users data from current quai tweet
        likers_response = _client.get_liking_users(tweet.id)
        # Check for more likers - then paginate if so
        if "next_token" in likers_response.meta.keys() and likers_response.meta["result_count"] == 100:
          likers_response = paginate(_client, likers_response, "likers", _tweet_id=tweet.id)
        
        # pull retweeting users data from current quai tweet
        retweeters_response = _client.get_retweeters(tweet.id)
        # Check for more retweeters - then paginate if so
        if "next_token" in retweeters_response.meta.keys() and retweeters_response.meta["result_count"] == 100:
          retweeters_response = paginate(_client, retweeters_response, "retweeters", _tweet_id=tweet.id)
  
        # Filter through likers and retweeters to find overlap: likers+retweeters
        likers_retweeters = []
        # likers / retweeters lists contain user dictionaries from client request
        if isinstance(likers_response.data, Iterable) and isinstance(retweeters_response.data, Iterable):
          for liker in likers_response.data:
            for retweeter in retweeters_response.data:
              # Checking if user liked + retweeted AND is in the user data dict from signup form
              if liker.id == retweeter.id:
                likers_retweeters.append(liker)
        else:
          print("Likers or Retweeters responses were non-iterable for tweet: " + str(tweet.id))
          print("Likers Response" + str(len(likers_response.data)))
          print("Retweeters Response" + str(len(retweeters_response.data)))

        print("# of Likers+Retweeters: " + str(len(likers_retweeters)))

        for liker_retweeter in likers_retweeters:
          for discord_name, user_data in _db_dict.items():
            if discord_name != "Monitor": #filters for users stored (excludes monitor data)
              lower_username = str(liker_retweeter.username).lower()
              if lower_username == user_data.twitter_name:
                tweet_date = tweet.created_at.strftime('%Y-%m-%d')
                if user_data.twitter_id == 0:
                  try:
                    _db_dict[discord_name].twitter_id = liker_retweeter.id
                  except Exception as e:
                    print("Failed to assign twitter id for twitter_name: " + str(user_data.twitter_name) + " | discord_name: " + str(discord_name))
                    print(e)
                _db_dict[discord_name].add_lr_rewards(tweet_date)
                print("Added User Rewards for " + str(discord_name))
                rewarded_users.append(discord_name)
              #else:
                #print("Did not add rewards for " + str(liker_retweeter.username))
        
        _db_dict["Monitor"].set_last_tweet(tweet.id)

        print("Tracked Tweet: " + str(tweet.id))  
  else:
    print("*No new tweets pulled: Check is up to date*")
  
  _db_dict["Monitor"].set_lrr_status(True)
  print("*completed check for likers_retweeters*")
  return _db_dict

## REPLY_MENTIONS_TRACKER() FUNCTION -> manipulate data in Dictionary of User_Data Objs
  ### TEST THIS WITH ONE USER AT A TIME TO UNDERSTAND HOW DATES ARE BEING FILTERED/COMPARED
def reply_mention_tracker(_db_dict, _client):
  print("*Beginning RM Check*")
  _db_dict["Monitor"].last_rm_check_completed = False
  for user, user_data in _db_dict.items():
    if user != "Monitor" and user not in rm_users_checked: # filters against monitor data stored
      print("--- USER CHECK ---")
      print("Checking "+ str(user) + "'s rewards for twitter name: "+ str(user_data.twitter_name))
      last_date_tracked = user_data.last_date_tracked
      """
      # pull user_data's twitter id if it has not been set already
      if user_data.twitter_id == 0:
        try:
          user_profile = _client.get_user(username=user_data.twitter_name)
          user_data.twitter_id = user_profile.data.id
        except:
          print("There was an error pulling the twitter user id for user with twitter name: " + str(user_data.twitter_name) + ", discord name: " + str(user))
      """

      if user_data.twitter_id != 0:
        if user_data.last_twt_id == 0:
          indiv_tweets = _client.get_users_tweets(id=user_data.twitter_id, exclude=['retweets', 'replies'], start_time=last_date_tracked, tweet_fields=['created_at', 'in_reply_to_user_id', 'author_id', 'text'], max_results=100)
          # checking for more tweets, paginate users feed if so
          if "next_token" in indiv_tweets.meta.keys() and indiv_tweets.meta["result_count"] == 100:
            indiv_tweets = paginate(_client, indiv_tweets, "mentions 1.0", _user_id=user_data.twitter_id, _tweet_date=last_date_tracked)
          print("Pulled Individual Tweets")
          
          reply_tweets = _client.get_users_tweets(id=user_data.twitter_id,exclude='retweets', start_time=last_date_tracked, tweet_fields=['created_at', 'in_reply_to_user_id', 'author_id', 'text'], max_results=100)
          # checking for more tweets, paginate users feed if so
          if "next_token" in reply_tweets.meta.keys() and reply_tweets.meta["result_count"] == 100:
            reply_tweets = paginate(_client, reply_tweets, "replies 1.0", _user_id=user_data.twitter_id, _tweet_date=last_date_tracked)
          print("Pulled Tweets with Replies")
        else:
          indiv_tweets = _client.get_users_tweets(id=user_data.twitter_id, exclude=['retweets', 'replies'], since_id=user_data.last_twt_id, tweet_fields=['created_at', 'in_reply_to_user_id', 'author_id', 'text'], max_results=100)
          # checking for more tweets, paginate users feed if so
          if "next_token" in indiv_tweets.meta.keys() and indiv_tweets.meta["result_count"] == 100:
            indiv_tweets = paginate(_client, indiv_tweets, "mentions 2.0", _user_id=user_data.twitter_id, _tweet_id=user_data.last_twt_id)
          print("Pulled Individual Tweets")
          
          reply_tweets = _client.get_users_tweets(id=user_data.twitter_id,exclude='retweets', since_id=user_data.last_twt_id, tweet_fields=['created_at', 'in_reply_to_user_id', 'author_id', 'text'], max_results=100)
          # checking for more tweets, paginate users feed if so
          if "next_token" in reply_tweets.meta.keys() and reply_tweets.meta["result_count"] == 100:
            reply_tweets = paginate(_client, reply_tweets, "replies 2.0", _user_id=user_data.twitter_id, _tweet_id=user_data.last_twt_id)
          print("Pulled Tweets with Replies")


        
        try:
          print("-- attempting to check mention tweets")
          if indiv_tweets.data != None:
            for tweet in indiv_tweets.data:
              if '@quainetwork' in tweet.text or '@QuaiNetwork' in tweet.text:
                try:
                  user_data.add_mention_rewards(tweet.created_at)
                  
                  # For Date comparison without H/M/S
                  tweet_date_str = tweet.created_at.strftime('%Y-%m-%d')
                  tweet_date_dt = datetime.strptime(tweet_date_str, '%Y-%m-%d')
                  if tweet_date_dt > user_data.reply_mention_data.last_mention_date:
                    user_data.reply_mention_data.last_mention_date = tweet_date_dt
                    user_data.reply_mention_data.last_mention_id = tweet.id
                except Exception as e:
                  print(e)
            print("Checked Users Individual Tweets for Mentions")
        except Exception as e:
          print(e)
          print("Unable to iterate through Individual Tweets for ", user)
          
        try:
          print("-- attempting to check reply tweets")
          if reply_tweets.data != None:
            for tweet in reply_tweets.data:
              if tweet not in indiv_tweets.data and tweet.in_reply_to_user_id == quai_id:
                try:
                  user_data.add_reply_rewards(tweet.created_at)
                  
                  # For Date comparison without H/M/S
                  tweet_date_str = tweet.created_at.strftime('%Y-%m-%d')
                  tweet_date_dt = datetime.strptime(tweet_date_str, '%Y-%m-%d')
                  if tweet_date_dt > user_data.reply_mention_data.last_reply_date:
                    user_data.reply_mention_data.last_reply_date = tweet_date_dt
                    user_data.reply_mention_data.last_reply_id = tweet.id
                except Exception as e:
                  print(e)
          print("Checked Users Replies")
        except Exception as e:
          print(e)
          print("Unable to iterate through Reply Tweets for ", user)
        
        user_data.set_last_tweet_id()
        print("*Completed RM Check for ", user)
        rm_users_checked.append(user)
        

  _db_dict["Monitor"].last_rm_check_completed = True
  return _db_dict

def rank_users(_db_dict, _rank_type, _rank_list):
  users_ranked_total = sorted(_rank_list, key=itemgetter(_rank_type), reverse=True)

  rank = 1
  index = 0
  for user_data in users_ranked_total:
    users_rewards = user_data[_rank_type]
    if index == 0:
      next_users_rewards = users_ranked_total[index+1][_rank_type]
      if _rank_type == "Total_Rewards":
        if users_rewards == next_users_rewards:
          _db_dict[user_data["User"]].total_rank = "T" + str(rank)
        else:
          _db_dict[user_data["User"]].total_rank = str(rank)
          rank += 1
      elif _rank_type == "Todays_Rewards":
        if users_rewards == next_users_rewards:
          _db_dict[user_data["User"]].todays_rank = "T" + str(rank)
        else:
          _db_dict[user_data["User"]].todays_rank = str(rank)
          rank += 1
    elif index == len(users_ranked_total)-1:
      previous_users_rewards = users_ranked_total[index-1][_rank_type]
      if _rank_type == "Total_Rewards":
        if users_rewards == previous_users_rewards:
          _db_dict[user_data["User"]].total_rank = "T" + str(rank)
        else:
          _db_dict[user_data["User"]].total_rank = str(rank)
          rank += 1
      elif _rank_type == "Todays_Rewards":
        if users_rewards == previous_users_rewards:
          _db_dict[user_data["User"]].todays_rank = "T" + str(rank)
        else:
          _db_dict[user_data["User"]].todays_rank = str(rank)
          rank += 1
    else:
      next_users_rewards = users_ranked_total[index+1][_rank_type]
      previous_users_rewards = users_ranked_total[index-1][_rank_type]
      if _rank_type == "Total_Rewards":
        if users_rewards == previous_users_rewards or users_rewards == next_users_rewards:
            _db_dict[user_data["User"]].total_rank = "T" + str(rank)
        else:
          _db_dict[user_data["User"]].total_rank = str(rank)
          rank += 1
      elif _rank_type == "Todays_Rewards":
        if users_rewards == previous_users_rewards or users_rewards == next_users_rewards:
            _db_dict[user_data["User"]].todays_rank = "T" + str(rank)
        else:
          _db_dict[user_data["User"]].todays_rank = str(rank)
          rank += 1
  
    index += 1
  return _db_dict

## STORE_TO_DB() FUNCTION -> takes data pulled from signup and rewards tracked for each user in db_dict and stores it back into pickle 
def store_to_db(_db_dict):
  db_file = open('bot_db.pickle','wb')
  pickle.dump(_db_dict, db_file)
  db_file.close()
  print("Total Users Stored: ", len(_db_dict)-1)

def upload_to_gsheets(_db_dict):
  # output user_data dict to gsheets with new columns and in two diffrent tabs 1) total rewards, 2) todays_rewards
  rewards_output = [["Discord", "Twitter", "Youtube", "Total Rewards", "Total Rank", "Todays Rewards", "Todays Rank", "Todays LR Rwds", "Todays R  Rwds", "Todays M Rwds", "Total LR Rwds", "Total R Rwds", "Total M Rwds", "Youtube Rwds"]]
  
  for discord_name, user_data in _db_dict.items():
    if "#" in discord_name:
      rewards_output.append([discord_name, user_data.twitter_name, user_data.youtube_channel, user_data.total_rewards, 
      user_data.total_rank, user_data.todays_rewards, 
      user_data.todays_rank, user_data.like_retweet_data.todays_rewards, 
      user_data.reply_mention_data.todays_reply_rewards, user_data.reply_mention_data.todays_mention_rewards, 
      user_data.like_retweet_data.total_rewards, user_data.reply_mention_data.total_reply_rewards, 
      user_data.reply_mention_data.total_mention_rewards, user_data.youtube_rewards])
    
  timezone_offset = -6.0  # Central Standard Time (UTC−06:00)
  tzinfo = timezone(timedelta(hours=timezone_offset))
  current_time = datetime.now(tzinfo)
  current_time_str = current_time.strftime('%Y-%m-%d %H:%M')
  rewards_output.append(["Last Update:", current_time_str]) 

  for reward_data in rewards_output:
    print(reward_data)
  
  try:
    _rows = str(len(rewards_output)+100)
    ls = gsheet_rewards.add_worksheet(title="Leaderboard - " + str((current_time_str)), rows=_rows, cols="20")
    ls.insert_rows(rewards_output)
  except Exception as e:
    print('ERROR EXCEPTION: ', e)
  print("*Uploaded leaderboard*")
  
  print("*****OUTPUT COMPLETE*****")

## OUTPUT_USER_DATA() FUNCTION
def output_user_data(_db_dict):

  total_ranked = []
  todays_ranked = []
  # Append each key in db_dict with "#" into a list
  for user in _db_dict.keys():
    if "#" in user:
      if _db_dict[user].twitter_id not in bots:
        _db_dict[user].calculate_rewards()
        total_ranked.append({"User":user, "Total_Rewards":_db_dict[user].total_rewards})
        todays_ranked.append({"User":user, "Todays_Rewards":_db_dict[user].todays_rewards})
      else:
        _db_dict[user].bot = True

  _db_dict = rank_users(_db_dict, "Total_Rewards", total_ranked)
  _db_dict = rank_users(_db_dict, "Todays_Rewards", todays_ranked)

  # store to local db file
  store_to_db(_db_dict)

  upload_to_gsheets(_db_dict)

def set_todays_date(_db_dict, current_date):
  # set current date in monitor obj
  _db_dict["Monitor"].set_current_check_date(current_date)
  # set current date for each user's reward object
  for user in _db_dict:
    if user != "Monitor":
      _db_dict[user].set_current_date(current_date)

# MAIN FUNCTION:
def __main__():
  # PULL USER DATA FROM DB
  db_user_data = get_db_data()
  #db_user_data = {}
  
  # PULL CURRENT DATE IN FORMATTED STRING
  current_date = get_current_date()
  
  # PULL MONITOR DATA & IMPORT USERS
  if "Monitor" not in db_user_data.keys():
    print("Monitor not found, creating new instance")
    db_user_data["Monitor"] = Monitor()
    db_user_data = import_users(db_user_data, new_signup_sheet, 0)
  else:
    signup_index = db_user_data["Monitor"].get_signup_index()
    db_user_data = import_users(db_user_data, new_signup_sheet, signup_index)
  
  set_todays_date(db_user_data, current_date)
  
  # Create Twitter API Client
  client = tweepy.Client(bearer_token= first_bearer)

  try:
    # LIKE+RETWEET CHECKER
    db_user_data = like_retweet_tracker(db_user_data, client)
    db_user_data["Monitor"].set_check_status()
    # REPLY_MENTION CHECKER
    db_user_data = reply_mention_tracker(db_user_data, client)
    output_user_data(db_user_data)
  except Exception as e:
    print(e)
    db_user_data["Monitor"].set_check_status()
    client = tweepy.Client(bearer_token= second_bearer)
    try:
      # LIKE+RETWEET CHECKER
      db_user_data = like_retweet_tracker(db_user_data, client)
      db_user_data["Monitor"].set_check_status()
      # REPLY_MENTION CHECKER
      db_user_data = reply_mention_tracker(db_user_data, client)
      output_user_data(db_user_data)
    except Exception as e:
      print(e)
      db_user_data["Monitor"].set_check_status()
      client = tweepy.Client(bearer_token= third_bearer)
      try:
        # LIKE+RETWEET CHECKER
        db_user_data = like_retweet_tracker(db_user_data, client)
        db_user_data["Monitor"].set_check_status()
        # REPLY_MENTION CHECKER
        db_user_data = reply_mention_tracker(db_user_data, client)
        output_user_data(db_user_data)
      except Exception as e:
        print(e)
        db_user_data["Monitor"].set_check_status()
        client = tweepy.Client(bearer_token= fourth_bearer)
        try:
          # LIKE+RETWEET CHECKER
          db_user_data = like_retweet_tracker(db_user_data, client)
          db_user_data["Monitor"].set_check_status()
          # REPLY_MENTION CHECKER
          db_user_data = reply_mention_tracker(db_user_data, client)
          output_user_data(db_user_data)
        except Exception as e:
          print(e)
          db_user_data["Monitor"].set_check_status()
          client = tweepy.Client(bearer_token= fifth_bearer)
          try:
            # LIKE+RETWEET CHECKER
            db_user_data = like_retweet_tracker(db_user_data, client)
            db_user_data["Monitor"].set_check_status()
            # REPLY_MENTION CHECKER
            db_user_data = reply_mention_tracker(db_user_data, client)
            output_user_data(db_user_data)
          except Exception as e:
            print(e)
            print("Error in running check. Failed Output")
            output_user_data(db_user_data)
    
  # OUTPUT_USER_DATA() -> OUTPUT USER RANK & REWARD TO GSHEETS
  #output_user_data(updated_user_data)

##### NOT TO FORGET FOR DISCORD SM BOT:
  # Update Discord SM Bot to properly handle new data
  # create new embedded outputs for total/todays rewards 
  # create new outputs for invalid/empty usernames

#__main__()
#print(bots)

### Functions to check outputted DB data
def check_todays_rewarded(): # check users who were rewarded today
  _db_dict = get_db_data()
  lrr_rewarded = []
  for user, user_obj in _db_dict.items():
    if user != "Monitor":
      if user_obj.like_retweet_data.todays_rewards != 0:
        print(user, ": ", user_obj.like_retweet_data.todays_rewards)
        lrr_rewarded.append(user)
  print('Current Check Date: ', _db_dict["Monitor"].current_check_date)
  print(len(lrr_rewarded))

def check_object_data(_key): # use to check the stored data in Monitor or any individual discord user
  _db_dict = get_db_data()
  _value = _db_dict[_key]
  obj_values = vars(_value)
  for property in obj_values:
    print(property, " : ", obj_values[property])

def check_users_rewards(): # check cumulative user rewards
  _db_dict = get_db_data()
  for user, user_obj in _db_dict.items():
    if user != "Monitor":  
      print(user,": ", user_obj.twitter_id)
      print("Total Rewards: ", user_obj.total_rewards)
      print("Todays Rewards: ", user_obj.todays_rewards)

def get_top_10():
  top_10 = [1,2,3,4,5,6,7,8,9,10]
  _db_dict = get_db_data()
  for user, user_obj in _db_dict.items():
    if user != "Monitor":
      if "T" in user_obj.total_rank:
        rank = int(user_obj.total_rank.strip("T"))
      else:
        rank = int(user_obj.total_rank)
      if rank < 11:
        top_10[rank-1] = "Discord Name: " + user + " | Twitter Name: " + user_obj.twitter_name + " \nTotal Rank: " + str(rank) + " | Total Rewards " + str(user_obj.total_rewards) + "\n"
  
  for data in top_10:
    print(data)

#bots = [1425707762856644608, 1390749554421780483, 1135574978244440064, 710440106, 1362859031870791684, 1274924713576300544, 1126894279777976320, 830792160706322433, 830792160706322433, 890494541177831424, 1287748747166748673, 1301791405443080192, 984003078818074624, 923050660886732800]
#get_top_10()
#check_todays_rewarded()
#check_users_rewards()
#check_object_data("socute#7900") #-> change key to desired key name for object (discord name or Monitor)

db_data = get_db_data()
output_user_data(db_data)



### SHOULD_HAVES TODO:
  # filter out bots (could store in db underneath different key -> just need to update 'user != "Monitor"  instances in script to also exclude bot key)
  # create check requirements function for checking if users satisfy requirements (following alan/quai)
  # clean up the code for unnecessary variables / methods across classes
  # separate code into more managable files for better readibility
    # when separating code -> add better comments to explain business logic / approach better (could help you write better/more efficient code)
  # integrate github with VS Code / Replit to create a better workflow
    # push to Github for review

### SM DISCORD BOT TODO:
  # Figure out a way to transfer pickleDB file over to SM Discord Bot OR Align both pieces of Code (in the meantime continue with gsheets)
  # Align gsheets pull to account from all of the users data
  # create new command prompts and differently styled embedded tweets for each 
    # ex. Total Rewards, Todays Rewards, if Bot = True -> alert them with a notice
    # ex. Twitter Name Check (allows user to check twitter associated, if INVALID/NONE notify before forcing them to check)
    # use discord API to filter out users how are no longer present in the discord?
      # pull guild members, for user in _db_dict -> if user not in guild members -> _db_dict.pop(user)
      # might also be helpful to create a list of these users to remove from the signup sheet?
      # could also create a function that checks for users who have left -> remove from db upon leaving


### COULD-HAVES TODO:
  # Update mention check to pull all quai's tweets where they were mentioned
  # Add requirement to follow @alanorwick and @quainetwork (track tweets but set property in user to be False
    # when checked by discord bot, return "You must be following Alanorwick and QuaiNetwork in order to receive your rewards")
  # update storage of LRR most_recent_tweet to be the "newest_tweet_id" from the meta data in the request
  # Create bot/spam account checker -> set base requirements for followers/following (allow users to keep current rewards 
  # with the opportunity to grow following/prove they're not a spam/bot account in the meantime)
