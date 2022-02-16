from ast import operator
from re import T
from typing import Iterable
from xmlrpc.client import Boolean
import tweepy
from datetime import *
import csv
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# PURPOSE: a bot intended to compile a twitter users activity toward a targetted twitter & reward the user based on said interaction level

## NOTES: 
#   {name : [1 $QUAI likes+retweets, 1 $QUAI reply to @quainetwork (with max 2 per day), 5 $QUAI individual tweet about @quainetwork, 
#   retweets, likes, and replies to your individual tweet about $QUAI -> 5 $QUAI per 10 engagements]}

# Gsheets
#gc = gspread.service_account(filename='service-key.json')
#sm_sheet = gc.open_by_key('1pPKG2PwrCr1dlZIvGZB8TQZ1_f0Pey-pgEZ1lvDbsbw')
#output_sheet = sm_sheet.add_worksheet(title="Rewards Bot Tracked Data", rows=2000, cols=10) 
# columns: 1. discord name, 2. twitter name, 3. youtube name, 4. like+retweet points, 5. reply points, 6. mention points, 
#           7. YT subscriber points, 8. YT comment points, 9. multiplier, 10.aggregate total

# CONST
quai_id = 1306071657174441985
quai_username = 'quainetwork'
first_bearer = "AAAAAAAAAAAAAAAAAAAAAEHkXwEAAAAAFgCxzDEOf484cKicUHiV3DO6qcU%3DodAKdbVDHoucR6dlOzPbB719XrDMisbZAWLufgqORgLCLgKUtO"
second_bearer = "AAAAAAAAAAAAAAAAAAAAANBOYAEAAAAAlLMei9GmJpSazEtiXx6IWZXEbhs%3DYfsE6mbEa2mLrtZKJhjvjzr4gWZ466w1doYhiWGHlwbDyJzTwx"


# dicts to track and store everything -> {username: [likes+retweets, replies, mentions, engagement rewards], ...}
sm_rewards = {}
username_userID = {}
db_tweets_tracked = []
all_tweets_tracked = []


# class to track global var in functions
class tweets_monitor:
    new_tweet_count = 0
    db_tweet_count = 0
    last_tweet_id = 1459205924573396997 #first tweet id as default
    completed_check = False
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
def sort_List(list_to_sort): 
    if list_to_sort:
        ## Bubble sort algo to ensure tweets are sorted youngest to oldest
        l = len(list_to_sort)
        for i in range(l-1):
            for j in range(i+1):
                if list_to_sort[i] > list_to_sort[j]: # highest to lowest
                    toMove = list_to_sort[i]
                    list_to_sort[i] = list_to_sort[j]
                    list_to_sort[j] = toMove
    return list_to_sort


def read_tweet_data(_monitor):
    print("read_tweet_data function - reading user reward data")
    with open("like_retweet_rewards.csv") as lrr:
        empty_result = is_empty("like_retweet_rewards.csv")
        if empty_result == "not empty":
            for line in lrr:
                line_array = line.strip().split(',')
                if len(line_array) == 3:
                    username_userID[line_array[1]] = line_array[0]
                    sm_rewards[line_array[1]] = line_array[2]
    print("read_tweet_data function - reading tweet data")
    with open('client_tweet_data.csv') as ctd:
        empty_result = is_empty('client_tweet_data.csv')
        if empty_result == "not empty":
            for line in ctd:
                line_array = line.strip().split(': ')
                if line_array[0] == "Last Check Complete":
                    _monitor.completed_check = bool(line_array[1])
                if line_array[0] == "Last tweet ID" and _monitor.completed_check == True:
                    _monitor.last_tweet_id = line_array[1]
                    _monitor.db_last_tweet_id = line_array[1]
        print("read_tweet_data function - closed client data file. set last_tweet_id to " + str(_monitor.last_tweet_id))
    # open tweet input csv and create a dictionary from the file data
    with open("tweetsDB.csv") as twts:
        print("read_tweet_data function - opened input data file")
        empty_result = is_empty("tweetsDB.csv")
        line_count = 0
        for line in twts:
            line_count += 1
            if empty_result == "not empty":
                twt_array = line.strip().split(': ')
                if twt_array[0] == "Valid Tweet Tracked":
                    db_tweets_tracked.append(twt_array[1])
                    _monitor.addedDBTweet()
        print("read_tweet_data function - inputted " + str(_monitor.db_tweet_count) + " tweets to db_tweets_tracked.")
        if _monitor.completed_check == False and _monitor.db_tweet_count > 0:
            _monitor.last_tweet_id = db_tweets_tracked[-1]
            print("read_tweet_data function - set last_tweet_id to " + str(_monitor.last_tweet_id))


# function: output to rewards csv
def output_rewards_data():
    # EXPORT OUTPUT: export to csv file to use in reply_mentions_tracker
    field_names = ['username','user id', 'like+retweet rewards']
    with open('like_retweet_rewards.csv', 'w') as f:
        writer = csv.DictWriter(f, fieldnames=field_names)
        for user in sm_rewards.keys():
            f.write("%s,%s,%s\n" % (username_userID[user], user, sm_rewards[user]))
        f.write("\n")
        f.write('Last Update: '+ str(datetime.now()))


# function: output to tweet csvs
def output_tweet_data(_monitor, up_to_date):
    if up_to_date:
        tweets_sorted = sort_List(db_tweets_tracked)
    else:
        tweets_sorted = sort_List(all_tweets_tracked)
    if len(tweets_sorted) > 0 and _monitor.completed_check:
        _monitor.last_tweet_id = tweets_sorted[0]
        print("output function: set last tweet id: " + str(_monitor.last_tweet_id))
    # EXPORT TWEET DATA FOR FUTURE USE:
    with open("tweetsDB.csv",'w') as t:
        tWriter = csv.writer(t)
        for tweetID in tweets_sorted:
            t.write("%s: %s\n" % ("Valid Tweet Tracked", tweetID))
        if len(tweets_sorted) > 0:
            t.write('\n')
        t.write('Last Update: '+ str(datetime.now()))
    # USE THIS CSV AS A REFERENCE WHEN RECEIVING MOST RECENT TWEETID
    with open('client_tweet_data.csv', 'w') as ctd:
        ctdWriter = csv.writer(ctd)
        ctd.write("%s: %s\n" % ("Last Check Complete", _monitor.completed_check))
        ctd.write("%s: %s\n" % ("Last tweet ID", _monitor.last_tweet_id))
        ctd.write("Most Recent Tweet Pull: " + str(datetime.now()))


def up_to_date_check(_tweets, _input_list):
    print("running up to date check")
    if _tweets.data == None:
        return True
    if len(_input_list) > 0:
        compare_list = []
        client_tweet_count = 0
        for tweet in _tweets.data:
            compare_list.append(tweet.id)
            client_tweet_count += 1
        if client_tweet_count > len(db_tweets_tracked):
            return False
        print("finished adding tweets to compare list")
        sorted_input_list = sort_List(_input_list)
        sorted_compare_list = sort_List(compare_list)
        print("finished sorting tweets in each list, comparing now")
        if sorted_compare_list[0] == sorted_input_list[0]:
            return True
            print("Up to Date")
        else:
            return False
            print("Not Up to Date")
    else:
        return False
        print("Not Up to Date, Input file is empty")

# iterate through tweet objects to collect retweeters, likers, and replies and assign user's their respective rewards
# iterate through each tweet and request those who liked and those who tweeted, sorting those who did both into likers_retweeters
def like_retweet_check(_client, _tweets, _monitor):
    _monitor.completed_check = False
    for tweet in _tweets.data:
        if tweet.id not in db_tweets_tracked:
            
            all_tweets_tracked.append(tweet.id)
            _monitor.addedNewTweet()
            _monitor.last_tweet_id = tweet.id
            
            likers_list = []
            retweeters_list = []
            likers_retweeters = []
            
            print("-- new tweet --")
            print(str(_monitor.new_tweet_count))
            print(str(tweet.id))

            # make request to get those who liked, then make request to get those who retweeted
            likers = _client.get_liking_users(tweet.id)
            retweeters = _client.get_retweeters(tweet.id)
            
            # pull username into liker list from likers data
            if isinstance(likers.data, Iterable):
                for liker in likers.data:
                    # this conditional is placed here to create the dict with usernames and ids to be used later
                    if liker not in username_userID:
                        username_userID[liker.username] = liker.id
                    likers_list.append(liker.username)
            
            # pull username into retweeter list from retweeters data 
            if isinstance(retweeters.data, Iterable):
                for retweeter in retweeters.data:
                    # this conditional is placed here to create the dict with usernames and ids to be used later
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
    _monitor.last_tweet_id = all_tweets_tracked[0]
    print("like+retweet_check - last_tweet_id: " + str(monitor.last_tweet_id))


## Main Bot Logic
try:
    client1 = tweepy.Client(bearer_token= first_bearer)
    monitor = tweets_monitor()
    
    print("main1 - client1 and monitor created. passing monitor to read data function")
    
    read_tweet_data(monitor)
    
    print("main1 - read data. passing tweet data paramaters to client1 tweet pull request")
    
    # conditon: check was not completed/set to false and the starting tweet is initial tweet (starting point)
    if monitor.completed_check == False and monitor.last_tweet_id == 1459205924573396997:
        print("main1 - " + str(monitor.completed_check) + " monitor complete check v1.1")
        print("main1 - last_tweet_id: " + str(monitor.last_tweet_id))
        tweets_client1 = client1.get_users_tweets(id=quai_id, exclude=['retweets', 'replies'], since_id= monitor.last_tweet_id, tweet_fields='created_at', max_results=100)
        up_to_date = False
    
    # conditon: check was not completed/set to false and the starting tweet is not initial tweet (half-completed check)
    elif monitor.completed_check == False and monitor.last_tweet_id != 1459205924573396997:
        print("main1 - " + str(monitor.completed_check) + " monitor complete check v1.2")
        print("main1 - last_tweet_id: " + str(monitor.last_tweet_id))
        tweets_client1 = client1.get_users_tweets(id=quai_id, exclude=['retweets', 'replies'], until_id= monitor.last_tweet_id, tweet_fields='created_at', max_results=100)
        up_to_date = False
    
    # conditon: check was completed/set to true and the starting tweet is not initial tweet (following successful updates)
    elif monitor.completed_check and monitor.last_tweet_id != 1459205924573396997:
        print("main1 - " + str(monitor.completed_check) + " monitor complete check v1.3")
        print("main1 - last_tweet_id: " + str(monitor.last_tweet_id))
        tweets_client1 = client1.get_users_tweets(id=quai_id, exclude=['retweets', 'replies'], since_id= monitor.last_tweet_id, tweet_fields='created_at', max_results=100)
        up_to_date = up_to_date_check(tweets_client1, db_tweets_tracked)
        print(up_to_date)

    # conditon: check was completed/set to true but the starting tweet is initial tweet (?)
    elif monitor.completed_check and monitor.last_tweet_id == 1459205924573396997:
        print("main1 - " + str(monitor.completed_check) + " monitor complete check v1.4")
        print("main1 - last_tweet_id: " + str(monitor.last_tweet_id))
        tweets_client1 = client1.get_users_tweets(id=quai_id, exclude=['retweets', 'replies'], since_id= monitor.last_tweet_id, tweet_fields='created_at', max_results=100)
        up_to_date = False

    else: # handler takes file data and re-writes it back to its original data state with updated "Last Updated" Fields
        up_to_date = True
    
    print("main1 - client1 tweet pull request complete.")
    
    if up_to_date == False:
        print("main1 - tweets tracked not up to date. starting like_retweet check")
        like_retweet_check(client1, tweets_client1, monitor)
        print("main1 - like+retweet tracker complete.")
    
    print("main1 - begin outputting data to csv files")
    
    output_tweet_data(monitor, up_to_date)
    output_rewards_data()
   
    print('main1 end script - successful output on client1')
except:
    try:
        client2 = tweepy.Client(bearer_token= second_bearer)

        print("main2 - client2 activated. passing tweet data paramaters to client2 tweet pull request")
        
        # conditon: check was not completed/set to false and the starting tweet is initial tweet (starting point)
        if monitor.completed_check == False and monitor.last_tweet_id == 1459205924573396997:
            print("main2 - " + str(monitor.completed_check) + " monitor complete check v2.1")
            print("main2 - last_tweet_id: " + str(monitor.last_tweet_id))
            tweets_client2 = client2.get_users_tweets(id=quai_id, exclude=['retweets', 'replies'], since_id=monitor.last_tweet_id, tweet_fields='created_at', max_results=100)
            up_to_date = False
        
        # conditon: check was not completed/set to false and the starting tweet is not initial tweet (half-completed check)
        elif monitor.completed_check == False and monitor.last_tweet_id != 1459205924573396997:
            print("main2 - " + str(monitor.completed_check) + " monitor complete check v2.2")
            print("main2 - last_tweet_id: " + str(monitor.last_tweet_id))
            tweets_client2 = client2.get_users_tweets(id=quai_id, exclude=['retweets', 'replies'], until_id=monitor.last_tweet_id, tweet_fields='created_at', max_results=100)
            up_to_date = False

        # conditon: check was completed/set to true and the starting tweet is not initial tweet (following successful updates)
        elif monitor.completed_check and monitor.last_tweet_id != 1459205924573396997:
            print("main2 - " + str(monitor.completed_check) + " monitor complete check v2.3")
            print("main2 - last_tweet_id: " + str(monitor.last_tweet_id))
            tweets_client2 = client2.get_users_tweets(id=quai_id, exclude=['retweets', 'replies'], since_id=monitor.last_tweet_id, tweet_fields='created_at', max_results=100)
            up_to_date = up_to_date_check(tweets_client2, db_tweets_tracked)
            print(up_to_date)
        
        # conditon: check was completed/set to true but the starting tweet is initial tweet (?)
        elif monitor.completed_check and monitor.last_tweet_id == 1459205924573396997:
            print("main2 - " + str(monitor.completed_check) + " monitor complete check v2.4")
            print("main2 - last_tweet_id: " + str(monitor.last_tweet_id))
            tweets_client2 = client2.get_users_tweets(id=quai_id, exclude=['retweets', 'replies'], since_id=monitor.last_tweet_id, tweet_fields='created_at', max_results=100)
            up_to_date = up_to_date_check(tweets_client2, db_tweets_tracked)
            print(up_to_date)
        
        else: # handler takes file data and re-writes it back to its original data state with updated "Last Updated" Fields
            up_to_date = True

        print("main2 - client2 tweet pull request complete.")
        
        if up_to_date == False:
            print("main2 - tweets tracked not up to date. starting like_retweet check")
            like_retweet_check(client2, tweets_client2, monitor)
            print("main2 - like+retweet tracker complete.")
        
        print("main2 - begin outputting data to csv files")

        output_rewards_data()
        output_tweet_data(monitor, up_to_date)

        print('main2 end script - successful output on client2')
    except:
        output_tweet_data(monitor, False)
        
        print("EXCEPTION: end script - unsuccessful output: function error or the clients were rate limited")




## NEW BUSINESS LOGIC FOR HANDLING GSHEET UPDATES:
# - add gsheet api
# - pull citizen's twitter username data from column in social media rewards gsheet, store as key-value pair (sm_rewards{})
# - within the key-value pair, store the csv cell location of their rewards
# - when iterating through the final dictionary, add the latest reward value to update
