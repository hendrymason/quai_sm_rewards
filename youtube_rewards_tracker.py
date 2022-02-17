from googleapiclient.discovery import build
import pandas as pd
import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from datetime import *
import csv

scopes = ["https://www.googleapis.com/auth/youtube.readonly"]

youtubeAPIkey='AIzaSyB0KLbArvb1Katbv3yurJyjik7SIdoualo'
youtube=build('youtube','v3',developerKey=youtubeAPIkey)
quaiChannelID ='UCA7wfK91O1CmwHm4LELnNHw'

# pull all of Quai's subcribers

# Disable OAuthlib's HTTPS verification when running locally.
# *DO NOT* leave this option enabled in production.
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

api_service_name = "youtube"
api_version = "v3"
client_secrets_file = "client_secret_1068463803050-s0gjvok338ibmurv313b8nnvu3trt1fl.apps.googleusercontent.com.json"

# Get credentials and create an API client
flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
    client_secrets_file, scopes)
credentials = flow.run_console()
youtube = googleapiclient.discovery.build(api_service_name, api_version, credentials=credentials)

request = youtube.subscriptions().list(
    part="snippet",
    channelId="UCA7wfK91O1CmwHm4LELnNHw",
    mine=True,
    mySubscribers=True
)
response = request.execute()

# for subscriber in list, add to dict as rewardsDict[uuserName] = 5
rewardsDict = {}
for i in response:
    rewardsDict[i.subscriberSnippet.title] = 5  

# pull all of Quai's videos
request = youtube.search().list(
        part="snippet",
        forMine=True,
        maxResults=50,
        type="video"
    )
response = request.execute()
quaiVideos = []
for v in response:
    quaiVideos.append(v.id.videoId)

# iterate through each video and pull all comments
for vidID in quaiVideos:
    request = youtube.commentThreads().list(
        part="snippet",
        maxResults=100,
        videoId=vidID
    )
    response = request.execute()

    for commentThread in response:
        commentOwner = commentThread.topLevelComment.snippet.authorDisplayName
        # for each comment, check for user in rewardDict.keys() and if they are, rewardsDict[userName]++
        if commentOwner in rewardsDict.keys():
            rewardsDict[commentOwner] += 1
        for comment in commentThread.replies.comments:
            commentOwner = comment.snippet.authorDisplayName
            # for each comment, check for user in rewardDict.keys() and if they are, rewardsDict[userName]++
            if commentOwner in rewardsDict.keys():
                rewardsDict[commentOwner] += 1

# sort dictionary from highest to lowest with bubble sort algo
rewardsList = list(rewardsDict.items())
l = len(rewardsList)
for i in range(l-1):
    for j in range(i+1, l):
        if rewardsList[i][1] > rewardsList[j][1]:
            toMove = rewardsList[i]
            rewardsList[i] = rewardsList[j]
            rewardsList[j] = toMove
    sortedRewardsDict= dict(rewardsList)
print(sortedRewardsDict)

# output dictionary in an excel file
date_outputted = date.today()
field_names = ['Youtube Username','Total Rewards']
with open('youtube_rewards.csv', 'w') as f:
    writer = csv.DictWriter(f, fieldnames=field_names)
    writer.writeheader()
    for key in sortedRewardsDict:
        f.write("%s: %s\n" % (key, sortedRewardsDict[key]))
    f.write('\n')
    f.write('Last Updated: '+ str(date_outputted))
print('end script')
