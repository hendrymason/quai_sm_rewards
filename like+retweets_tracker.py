from ast import operator
from re import T
from typing import Iterable
import tweepy
from datetime import *
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

# dicts to track and store everything -> {username: [likes+retweets, replies, mentions, engagement rewards], ...}
sm_rewards = {}
username_userID = {}
tweets_tracked = {}
# class to track global var in functions
class tweets_monitor:
    tweet_count = 0
    last_tweet_id = 1459205924573396997 #first tweet id as default

    def addTweet(self):
        self.tweet_count += 1

# checks if file is empty by checking for second row in csv
def is_empty(file):
    with open(file) as csvfile:
        reader = csv.reader(csvfile)
        for i, _ in enumerate(reader):
            if i:  # found the second row
                return False
    return True

# open tweet input csv and create a dictionary from the file data

with open('tweets.csv') as twts:
    for line in twts:
        not_empty = is_empty("tweets.csv")
        if not_empty:
            twt_array = line.strip().split(',')
            tweets_tracked[twt_array[0]] = datetime(twt_array[1])
twts.close()

#create monitor for tracking tweets and date of last tweet used
monitor = tweets_monitor()

# sort tweets_tracked dict for most up to date tweet
if tweets_tracked:
    tweets_data_list = []
    for tweet_id in tweets_tracked:
        newTweetDict = {}
        newTweetDict['tweet_id'] = twt_array[0]
        newTweetDict['created_at'] = twt_array[1]
        tweets_data_list.append(newTweetDict)
    # sort tweets_data_list by date
    tweets_data_list.sort(key = operator.itemgetter('created_at'))
    monitor.last_tweet_id = tweets_data_list[0]['created_at']

# 1. LIKES+RETWEET REWARDS: iterate through tweet objects to collect retweeters, likers, and replies and assign user's their respective rewards
# iterate through each tweet and request those who liked and those who tweeted, sorting those who did both into likers_retweeters
def like_retweet_check(_tweet_dict, _client, _tweets, _monitor):
    for tweet in _tweets.data:
        if tweet.id not in _tweet_dict:
            
            _tweet_dict[tweet.id] = tweet.created_at
            _monitor.addTweet()
            _monitor.last_tweet_id = tweet.id
            
            likers_list = []
            retweeters_list = []
            likers_retweeters = []
            
            print("--new tweet --")
            print(str(_monitor.tweet_count))
            print(str(_monitor.last_tweet_id))

            # make request to get those who liked, then make request to get those who retweeted
            likers = _client.get_liking_users(tweet.id)
            retweeters = _client.get_retweeters(tweet.id)
            #set last tweet id in monitor for next client in the instance of a rate limit
            _monitor.last_tweet_id= tweet.id
            
            # pull username into liker list from likers data
            if isinstance(likers.data, Iterable):
                for liker in likers.data:
                    # this conditional is placed here to create the dict with usernames and ids to be used later
                    if liker not in username_userID:
                        username_userID[liker.username] = [liker.id]
                    likers_list.append(liker.username)
            
            # pull username into retweeter list from retweeters data 
            if isinstance(retweeters.data, Iterable):
                for retweeter in retweeters.data:
                    # this conditional is placed here to create the dict with usernames and ids to be used later
                    if retweeter not in username_userID:
                        username_userID[retweeter.username] = [retweeter.id]
                    retweeters_list.append(retweeter.username)
            
            # create new list of users who BOTH liked and retweeted
            likers_retweeters = [username for username in likers_list if username in retweeters_list]
            # increment users rewards or add user to dict based on like+retweet list
            for username in likers_retweeters:
                if username in sm_rewards:
                    sm_rewards[username][1] = sm_rewards[username][1] + 1
                else:
                    sm_rewards[username] = [username_userID[username][0], 1]
            
#implement try except clause for handling rate limiting
try:
    #create api client
    print('first client activated')
    client1 = tweepy.Client(bearer_token= first_bearer)
    tweets_client1 = client1.get_users_tweets(id=quai_id, exclude=['retweets', 'replies'], since_id= monitor.last_tweet_id, tweet_fields='created_at', max_results=100)
    like_retweet_check(tweets_tracked, client1, tweets_client1, monitor)
except:
    #generate new client with second bearer token and request with date of last tweet checked
    print('second client activated')
    client2 = tweepy.Client(bearer_token= second_bearer)
    tweets_client2 = client2.get_users_tweets(id=quai_id, exclude=['retweets', 'replies'], until_id=monitor.last_tweet_id, tweet_fields='created_at', max_results=100)
    like_retweet_check(tweets_tracked, client2, tweets_client2, monitor)

# EXPORT OUTPUT: export to csv file to use in reply_mentions_tracker
field_names = ['username','user id', 'like+retweet rewards']
with open('input.csv', 'w') as f:
    writer = csv.DictWriter(f, fieldnames=field_names)
    for user in sm_rewards.keys():
        f.write("%s,%s,%s\n" % (user, sm_rewards[user][0], sm_rewards[user][1]))
# EXPORT TWEET DICT FOR FUTURE USE:
tweet_field_names = ['created_at','tweet_id']
with open('tweets.csv','w') as t:
    tWriter = csv.DictWriter(t, fieldnames =tweet_field_names)
    for twtID in tweets_tracked.keys():
        t.write("%s,%s\n" % (twtID, tweets_tracked[twtID]))
print('end script')
