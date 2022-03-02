from re import U
from typing import Iterable
import tweepy
from datetime import *
import csv

# CONST
quai_id = 1306071657174441985
quai_username = 'quainetwork'
# quai_profile = client.get_user(username=quai_username.data
first_bearer = ""
second_bearer = ""

# dicts to track and store everything -> {username: [likes+retweets, replies, mentions, engagement rewards], ...}
sm_rewards = {}

# create an array to remove team usernames from dict
team_usernames = ['The_NFT_King', 'alanorwick', 'max_bibeau','0heezus0','owenrobertson48','ShreekaraS','mechanikalk', 'Juuuuuddi', 'QuaiNetwork']
# sorts through an input file and adds users to a dictionary with a value of an array containing the data in its row
with open('input.csv') as c:
    for line in c:
        user_array = line.strip().split(',')
        if user_array[0] not in team_usernames:
            sm_rewards[user_array[0]] = user_array[1:]
            sm_rewards[user_array[0]][0] = int(user_array[1])
            sm_rewards[user_array[0]][1] = int(user_array[2])


# iterate through users in dictionary and reward based on cross referencing their replies with quai's mentions
first_tweet_date = first_tweet = '2021-11-20T00:00:00Z'
today = datetime.now().isoformat()
user_count = 0
def reply_mentions_check(_client):
    for currentUser in sm_rewards:
            
            reply_tweets = []
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
                            reply_tweets.append(tweet)

                #count all users mentions of quai (not replies)
                if isinstance(indiv_tweets.data, Iterable):
                    for tweet in indiv_tweets.data:
                        if '@quainetwork' in tweet.text or '@QuaiNetwork' in tweet.text:
                            mention_count += 1
                
                # filter through tweets to ensure no more than 2 replies are counted for a single day
                for tweet in reply_tweets:
                            if tweet.in_reply_to_user_id == quai_id:
                                reply_count += 1
                
                # for day in days:
                #     replies_today = 0
                #     if replies_today == 2:
                #         continue
                #     else:
                #         for tweet in reply_tweets:
                #             if tweet.in_reply_to_user_id == quai_id and day == tweet.created_at:
                #                 reply_count += 1
                #                 replies_today += 1
                
                #reward user for their specific replies
                sm_rewards[currentUser].append(reply_count)
                #reward users for specific mentions
                sm_rewards[currentUser].append(mention_count * 5)

try:
    client1 = tweepy.Client(bearer_token= first_bearer)
    reply_mentions_check(client1)
except:
    client2 = tweepy.Client(bearer_token= second_bearer)
    reply_mentions_check(client2)

date_outputted = date.today()
field_names = ['Username','Total Rewards']
with open('output.csv', 'w') as f:
    writer = csv.DictWriter(f, fieldnames=field_names)
    # for user in sm_rewards.keys():
    #     if len(sm_rewards[user]) == 3:
    #         f.write("%s,%s,%s\n" % (user, sm_rewards[user][0], sm_rewards[user][1]))
    #     else:
    #         f.write("%s,%s,%s,%s,%s\n" % (user, sm_rewards[user][0], sm_rewards[user][1], sm_rewards[user][2], sm_rewards[user][3]))
    # f.write('\n')
    writer.writeheader()
    for user in sm_rewards.keys():
        total_rewards = sm_rewards[user][1] + sm_rewards[user][2] + sm_rewards[user][3]
        f.write("%s: %s\n" % (user, total_rewards))
    f.write('\n')
    f.write('Last Updated: '+ str(date_outputted))
print('end script')
