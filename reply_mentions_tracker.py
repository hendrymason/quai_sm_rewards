import re
from typing import Iterable
import tweepy
from datetime import *
import csv
import time


# CONST
quai_id = 1306071657174441985
quai_username = 'quainetwork'
first_tweet_date = '2021-11-20T00:00:00Z'
# quai_profile = client.get_user(username=quai_username.data
first_bearer = ""
second_bearer = ""
third_bearer = ""
fourth_bearer = ""

# dicts to track and store everything -> {username: [likes+retweets, replies, mentions, engagement rewards], ...}
sm_rewards = {}
twitter_data = {}

# set most recent quai twitter for scaling and preventing recounts
most_recent_quai_twt = 0
last_quai_twt_date = ''

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


def read_tweet_data():
    with open('tweet_monitor_data.csv') as ctd:
        print("reading tweet_monitor_data for last quai tweet")
        empty_result = is_empty('tweet_monitor_data.csv')
        if empty_result != True:
            for line in ctd:
                twt_data_line = line.strip().split(": ")
                if "Last Updated Tweet ID for Reply_Mentions" in twt_data_line:
                    most_recent_quai_twt = twt_data_line[1]
    ctd.close()
    
    # sorts through an input file and adds users to a dictionary with a value of an array containing the data in its row
    with open('like_retweet_rewards.csv') as lr:
        line_counter = 0
        for line in lr:
            if line_counter == 0:
                line_counter += 1
                continue
            else:
                user_array = line.strip().split(',')
                if len(user_array) == 3 and user_array[1] not in team_usernames:
                    # set user id & rewards from like+retweets output
                    sm_rewards[user_array[1]] = [int(user_array[0]), int(user_array[2]), 0, 0]
    lr.close()
    # utilize reply/mention arrays [] as to accommodate for scale and ensure more accurate tracking overtime
    with open('user_data_storage.csv') as ud:
        print("reading user data storage")
        empty_result = is_empty('user_data_storage.csv')
        if empty_result != True:
            print("user data storage has data")
            line_index = 0
            for line in ud:
                if line_index == 0:
                    line_index += 1
                    continue
                elif "User Data" in line:
                    user_data = line.strip().split(',')
                    current_user = user_data[1]
                    twitter_data[current_user] = [user_data[2], user_data[3], user_data[4], user_data[5]]
                elif "Last Updated" in line:
                    break
            print("successfully read user data storage")
        else:
            print("user data storage is empty")
    ud.close()

def reply_mentions_check(_bearer_token):
    client = tweepy.Client(bearer_token= _bearer_token)
    if most_recent_quai_twt != 0:
        quai_twt_pull = client.get_tweet(id=most_recent_quai_twt, tweet_fields="created_at")
        last_quai_twt_date = quai_twt_pull.data.created_at
    for currentUser in sm_rewards:
            
            user_replies = []
            user_mentions = []
            mention_count = 0
            reply_count = 0

            #check if valid
            if len(sm_rewards[currentUser]) == 4:
                if currentUser in twitter_data:
                    #request all users individual tweets (with no retweets and replies) THEN request all users tweets with no retweets
                    indiv_tweets = client.get_users_tweets(id=sm_rewards[currentUser][0], exclude=['retweets', 'replies'], start_time = last_quai_twt_date, tweet_fields=['created_at', 'in_reply_to_user_id', 'author_id', 'text'], max_results=100)
                    no_retweets = client.get_users_tweets(id=sm_rewards[currentUser][0], exclude='retweets', start_time = last_quai_twt_date, tweet_fields=['created_at', 'in_reply_to_user_id', 'author_id', 'text'], max_results=100)
                else:
                    #request all users individual tweets (with no retweets and replies) THEN request all users tweets with no retweets
                    indiv_tweets = client.get_users_tweets(id=sm_rewards[currentUser][0], exclude=['retweets', 'replies'], start_time = first_tweet_date, tweet_fields=['created_at', 'in_reply_to_user_id', 'author_id', 'text'], max_results=100)
                    no_retweets = client.get_users_tweets(id=sm_rewards[currentUser][0], exclude='retweets', start_time = first_tweet_date, tweet_fields=['created_at', 'in_reply_to_user_id', 'author_id', 'text'], max_results=100)
                
                #sort tweets to get just the user reply tweets
                if isinstance(no_retweets.data, Iterable):
                    for tweet in no_retweets.data:
                        if tweet not in indiv_tweets and tweet.in_reply_to_user_id == quai_id:
                            reply_count += 1
                            user_replies.append(tweet.id)

                #count all users mentions of quai (not replies)
                if isinstance(indiv_tweets.data, Iterable):
                    for tweet in indiv_tweets.data:
                        if '@quainetwork' in tweet.text or '@QuaiNetwork' in tweet.text:
                            mention_count += 1
                            user_mentions.append(tweet.id)
                
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
                sm_rewards[currentUser][2] = reply_count
                #reward users for specific mentions
                sm_rewards[currentUser][3] = mention_count * 5


def sort_rewards(dict_to_sort):
    print("sorting data from dictionary")
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
    print("aggregating data from dictionary")
    aggregate_rewards = {}
    for user in dict_to_aggregate.keys():
        user_total = int(dict_to_aggregate[user][1]) + int(dict_to_aggregate[user][2]) + int(dict_to_aggregate[user][3])
        aggregate_rewards[user] = int(user_total)
    sorted_agg_rewards = sort_rewards(aggregate_rewards)
    print("aggregated and sorted data from dictionary")
    return sorted_agg_rewards


def update_all_data():
    if twitter_data:
        print("twitter_data NOT empty, adding sm_rewards value to twitter_data")
        for user in sm_rewards.keys():
            if user in twitter_data.keys():
                twitter_data[user][1] = int(twitter_data[user][1]) + int(sm_rewards[user][1])
                twitter_data[user][2] = int(twitter_data[user][2]) + int(sm_rewards[user][2])
                twitter_data[user][3] = int(twitter_data[user][3]) + int(sm_rewards[user][3])
    else:
        print("twitter_data empty, adding sm_rewards value to twitter_data")
        for user in sm_rewards.keys():
            twitter_data[user] = sm_rewards[user]
    updated_agg_rewards = aggregate_total(twitter_data)
    return updated_agg_rewards


def output_data(dict_to_output):
    ttr_field_names = ['Username', 'Total Rewards']
    with open('total_twitter_rewards.csv', 'w') as ttr:
        print("outputting to total twitter rewards")
        udsWriter = csv.DictWriter(ttr, fieldnames=ttr_field_names)
        udsWriter.writeheader()
        for username in dict_to_output:
            ttr.write("%s: %s\n" % (username, dict_to_output[username]))
        ttr.write('\n')
        ttr.write('Last Updated: '+ str(datetime.now()))
    ttr.close()
    uds_field_names = ['Username', 'Like+Retweet Rewards','Reply Rewards','Mention Rewards']
    with open('user_data_storage.csv','w') as uds:
        print("outputting to user data storage")
        udsWriter = csv.DictWriter(uds, fieldnames=uds_field_names)
        udsWriter.writeheader()
        for user in twitter_data.keys():
            usr_val = twitter_data[user]
            uds.write("%s,%s,%s,%s,%s,%s\n" % ("User Data", user, usr_val[0], usr_val[1], usr_val[2], usr_val[3]))
            """
            for twtID in usr_val[4]:
                if type(twtID) == int:
                    uds.write("%s: %s\n" % ("User Reply Tweet", twtID))
            for twtID in usr_val[5]:
                if type(twtID) == int:
                    uds.write("%s: %s\n" % ("User Mention Tweet", twtID))
            """
        uds.write("Last Updated: " + str(datetime.now()))
    uds.close()

def reply_mentions_main(_bearer_token):
    
    if _bearer_token == first_bearer:
        client_version = "client1"
    elif _bearer_token == second_bearer:
        client_version = "client2"
    elif _bearer_token == third_bearer:
        client_version = "client3"
    elif _bearer_token == fourth_bearer:
        client_version = "client4"
    else:
        print("_bearer_token unrecognized")
    
    print(client_version + " - " + client_version + " activated. passing tweet data paramaters to " + client_version + " for reply mentions check")

    reply_mentions_check(_bearer_token)
    print("completed reply_mentions_check")
    
    updated_agg_rewards = update_all_data()
    print("updated aggregate rewards")
    
    output_data(updated_agg_rewards)
    print('successful output, end of script')

try:
    read_tweet_data()
    print("read tweet data")
    reply_mentions_main(second_bearer)
except:
    reply_mentions_main(third_bearer)


# end output: sm_rewards[user] = [int(user_id), int(like+retweets rewards), int(reply rewards), int(mention rewards)]
# data file output for each user:
#index0:username,index1:user_id,index2:like+retweets pts,index3:replies pts,index4:mentions pts
