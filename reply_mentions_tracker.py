import re
from typing import Iterable
import tweepy
from datetime import *
import csv
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials

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
# quai_profile = client.get_user(username=quai_username.data
first_bearer = "AAAAAAAAAAAAAAAAAAAAAEHkXwEAAAAAFgCxzDEOf484cKicUHiV3DO6qcU%3DodAKdbVDHoucR6dlOzPbB719XrDMisbZAWLufgqORgLCLgKUtO"
second_bearer = "AAAAAAAAAAAAAAAAAAAAANBOYAEAAAAAlLMei9GmJpSazEtiXx6IWZXEbhs%3DYfsE6mbEa2mLrtZKJhjvjzr4gWZ466w1doYhiWGHlwbDyJzTwx"

# dicts to track and store everything -> {username: [likes+retweets, replies, mentions, engagement rewards], ...}
sm_rewards = {}
twitter_data = {}

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

# sorts through an input file and adds users to a dictionary with a value of an array containing the data in its row
with open('like_retweet_rewards.csv') as c:
    for line in c:
        user_array = line.strip().split(',')
        if len(user_array) == 3 and user_array[1] not in team_usernames:
            sm_rewards[user_array[1]] = user_array[1:]
            sm_rewards[user_array[1]][0] = int(user_array[0]) # set user id from like+retweets output
            sm_rewards[user_array[1]][1] = int(user_array[2]) # set rewards from like+retweets output
            # ^sm_rewards[key: username] = value: [0: int(twitter user_id), 1: int(like+retweets rewards)]
# end output: [0: int(user_id), 1: int(like+retweets rewards), 2: int(reply rewards), 3: int(mention rewards), 4: reply_array[], 5: mentions_array[]]
# utilize reply/mention arrays [] as to accommodate for scale and ensure more accurate tracking overtime
print(sm_rewards)
with open('user_data_storage.csv') as ud:
    empty_result = is_empty('user_data_storage.csv')
    if empty_result != True:
        for line in ud:
            if "Last Updated" in line:
                break
            elif "User Data" in line:
                user_data = line.strip().split(',')
                current_user = user_data[1]
                twitter_data[current_user] = [user_data[2], user_data[3], user_data[4], user_data[5], [],[]]
            elif "Reply" in line:
                reply_data = line.strip().split(': ')
                twitter_data[current_user][4].append(reply_data[1])
            elif "Mention" in line:
                mention_data = line.strip().split(': ')
                twitter_data[current_user][5].append(mention_data[1])
print(twitter_data)
#['1201327349486084096', '66', '4', ['1490147959517843463', '1488743566914437120', '1488742095284174853', '1488347476897964033'], []]
# iterate through users in dictionary and reward based on cross referencing their replies with quai's mentions
first_tweet_date = '2021-11-20T00:00:00Z'
today = datetime.now().isoformat()
user_count = 0
def reply_mentions_check(_client):
    for currentUser in sm_rewards:
            
            reply_data = []
            user_replies = []
            user_mentions = []
            mention_count = 0
            reply_count = 0

            #check if valid
            if len(sm_rewards[currentUser]) == 2:
        
                #request all users individual tweets (with no retweets and replies) THEN request all users tweets with no retweets
                indiv_tweets = _client.get_users_tweets(id=sm_rewards[currentUser][0], exclude=['retweets', 'replies'], start_time = first_tweet_date, tweet_fields=['created_at', 'in_reply_to_user_id', 'author_id', 'text'], max_results=100)
                no_retweets = _client.get_users_tweets(id=sm_rewards[currentUser][0], exclude='retweets', start_time = first_tweet_date, tweet_fields=['created_at', 'in_reply_to_user_id', 'author_id', 'text'], max_results=100)
                
                #sort tweets to get just the user reply tweets
                if isinstance(no_retweets.data, Iterable):
                    for tweet in no_retweets.data:
                        if tweet not in indiv_tweets:
                            reply_data.append(tweet)

                #count all users mentions of quai (not replies)
                if isinstance(indiv_tweets.data, Iterable):
                    for tweet in indiv_tweets.data:
                        if '@quainetwork' in tweet.text or '@QuaiNetwork' in tweet.text:
                            mention_count += 1
                            user_mentions.append(tweet.id)
                
                # filter through tweets to ensure no more than 2 replies are counted for a single day
                for tweet in reply_data:
                    if tweet.in_reply_to_user_id == quai_id:
                        reply_count += 1
                        user_replies.append(tweet.id)
                
                # for day in days:
                #     replies_today = 0
                #     if replies_today == 2:
                #         continue
                #     else:
                #         for tweet in reply_data:
                #             if tweet.in_reply_to_user_id == quai_id and day == tweet.created_at:
                #                 reply_count += 1
                #                 replies_today += 1
                
                #reward user for their specific replies
                sm_rewards[currentUser].append(reply_count)
                #reward users for specific mentions
                sm_rewards[currentUser].append(mention_count * 5)

                #store user REPLY tweets array to check later, make script faster
                sm_rewards[currentUser].append(user_replies)
                #store user MENTION tweets array to check later, make script faster
                sm_rewards[currentUser].append(user_mentions)
                #twitter_data[username] = 
                #   [0:user_id, 1:like+retweets, 2:replies, 3:mentions, 4:reply array, 5:mention array]
                #sm_rewards[username] = [0:user_id, 1:like+retweets]  

def sort_rewards(dict_to_sort):
    aggRewards_List = list(dict_to_sort.items())
    l = len(aggRewards_List)
    for i in range(l-1):
        for j in range(i+1):
            if aggRewards_List[i][1] > aggRewards_List[j][1]:
                toMove = aggRewards_List[i]
                aggRewards_List[i] = aggRewards_List[j]
                aggRewards_List[j] = toMove
    aggRewards_Dict = dict(aggRewards_List)
    return aggRewards_Dict

def aggregate_total(dict_to_aggregate):
    aggregate_rewards = {}
    for user in dict_to_aggregate.keys():
        user_total = dict_to_aggregate[user][1] + dict_to_aggregate[user][2] + dict_to_aggregate[user][3]
        aggregate_rewards[user] = user_total
    sorted_agg_rewards = sort_rewards(aggregate_rewards)
    return sorted_agg_rewards

def update_all_data():
    for user in sm_rewards.keys():
        if twitter_data:
            if user in twitter_data.keys():
                twitter_data[user][1] = int(twitter_data[user][1]) + int(sm_rewards[user][1])
                twitter_data[user][2] = int(twitter_data[user][2]) + int(sm_rewards[user][2])
                twitter_data[user][3] = int(twitter_data[user][3]) + int(sm_rewards[user][3])
                for twtID in sm_rewards[user][4]:
                    if twtID not in twitter_data[user][4]:
                        twitter_data[user][4].append(twtID)
                for twtID in sm_rewards[user][5]:
                    if twtID not in twitter_data[user][5]:
                        twitter_data[user][5].append(twtID)
        else:
            twitter_data[user] = sm_rewards[user]
    updated_agg_rewards = aggregate_total(twitter_data)
    return updated_agg_rewards

def output_data(dict_to_output):
    with open('total_twitter_rewards.csv', 'w') as f:
        for username in dict_to_output:
            f.write("%s: %s\n" % (username, dict_to_output[username]))
        f.write('\n')
        f.write('Last Updated: '+ str(datetime.now()))
    #uds_field_names = ['Username', 'Like+Retweet Rewards','Reply Rewards','Mention Rewards','Reply Tweets Array', 'Mentions Tweets Array']
    with open('user_data_storage.csv','w') as uds:
        for user in dict_to_output.keys():
            usr_val = dict_to_output[user]
            uds.write("%s,%s,%s,%s,%s,%s\n" % ("User Data", user, usr_val[0], usr_val[1], usr_val[2], usr_val[3]))
            for twtID in usr_val[4]:
                if type(usr_val[4]) == str:
                    uds.write("%s: %s\n" % ("User Reply Tweet", twtID))
            for twtID in usr_val[5]:
                if type(usr_val[4]) == str:
                    uds.write("%s: %s\n" % ("User Mention Tweet", twtID))
        uds.write("Last Updated: " + str(datetime.now()))
## FIX: MAKE THIS FILE A FUNCTION TIE INTO LIKE+RETWEET TRACKER
## FIX: ADD WAIT FUNCTION TO HANDLE RATE REQUESTS WITHIN LIKE+RETWEET TRACKER
try:
    print("reply-mentions: client1 activated")
    client1 = tweepy.Client(bearer_token= first_bearer)
    reply_mentions_check(client1)
    print(sm_rewards)
    updated_agg_rewards = update_all_data()
    output_data(updated_agg_rewards)
    print('Successful output from client1: end of script')
except:
    print("reply-mentions: client2 activated")
    client2 = tweepy.Client(bearer_token= second_bearer)
    reply_mentions_check(client2)
    print(sm_rewards)
    updated_agg_rewards = update_all_data()
    output_data(updated_agg_rewards)
    print('Successful output from client2: end of script')

# end output: sm_rewards[user] = [0: int(user_id), 1: int(like+retweets rewards), 
# 2: int(reply rewards), 3: int(mention rewards), 4: reply_array[], 5: mentions_array[]]
# data file output for each user:
#   index0:username,index1:user_id,index2:like+retweets pts,index3:replies pts,index4:mentions pts
#   reply_array[]
#   mentions_array[]
