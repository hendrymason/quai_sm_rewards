from ast import operator
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
# quai_profile = client.get_user(username=quai_username.data
first_bearer = "AAAAAAAAAAAAAAAAAAAAAEHkXwEAAAAAFgCxzDEOf484cKicUHiV3DO6qcU%3DodAKdbVDHoucR6dlOzPbB719XrDMisbZAWLufgqORgLCLgKUtO"
second_bearer = "AAAAAAAAAAAAAAAAAAAAANBOYAEAAAAAlLMei9GmJpSazEtiXx6IWZXEbhs%3DYfsE6mbEa2mLrtZKJhjvjzr4gWZ466w1doYhiWGHlwbDyJzTwx"

# use this client var to activate tweepy methods
client = tweepy.Client(bearer_token= first_bearer)

# dicts to track and store everything -> {username: [likes+retweets, replies, mentions, engagement rewards], ...}
sm_rewards = {}
username_userID = {}

# 1. LIKES+RETWEET REWARDS: iterate through tweet objects to collect retweeters, likers, and replies and assign user's their respective rewards
# request Quai's Timeline of Tweets
tweets = client.get_users_tweets(id=quai_id, exclude=['retweets', 'replies'], tweet_fields='created_at', max_results=100)
tweet_count = 0
# iterate through each tweet and request those who liked and those who tweeted, sorting those who did both into likers_retweeters
for tweet in tweets.data:
    
    tweet_count += 1
    likers_list = []
    retweeters_list = []
    likers_retweeters = []
    
    # make request to get those who liked, then make request to get those who retweeted
    likers = client.get_liking_users(tweet.id)
    retweeters = client.get_retweeters(tweet.id)
    
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
            sm_rewards[username] = [username_userID[username][0], 1, 0, 0, 0]

# CALCULATE TOTAL: Check reward count for each user
print('Username   Total Rewards')
print('------------------------')
for user in sm_rewards:
    total_rewards = sm_rewards[user][1] + sm_rewards[user][2] + sm_rewards[user][3] + sm_rewards[user][4]
    print(user + '  |  ' + str(total_rewards))

# export to csv file to store in excel
output_dict = {}
for user in sm_rewards:
    total_rewards = sm_rewards[user][1] + sm_rewards[user][2] + sm_rewards[user][3] + sm_rewards[user][4]
    output_dict[user] = total_rewards

field_names = ['username','user id', 'like+retweet rewards']
with open('input.csv', 'w') as f:
    writer = csv.DictWriter(f, fieldnames=field_names)
    for user in sm_rewards.keys():
        f.write("%s,%s,%s\n" % (user, sm_rewards[user][0], sm_rewards[user][1]))
print('end script')
