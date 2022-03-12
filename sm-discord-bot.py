import discord
import os
import gspread
import schedule
import time
from time import mktime
from datetime import datetime
from datetime import timedelta
import pandas as pd
from bokeh.io import export_png, export_svgs
from bokeh.models import ColumnDataSource, DataTable, TableColumn

# BOT TODO:
#  - add in $2 QUAI reward for following each team member
#  - add in youtube bot rewards to total rewards
#  - output discord_twitter_data as a gsheet / csv for storage / ease of use
#  - remove duplicate discord names from sm rewards sign ups gsheet

## POST-BOT TODO:
#  - curate discord/twitter announcement to ask members to update their sm rewards form + team member follow addition to mainnet rewards
#  - (*NOTE:) inform people if they update their form, it will not be visible in bot until next time the rewards bot updates the sm reward count (monday/friday 8am)

## gsheets
gc = gspread.service_account(filename='smd-service-key.json')
response_sheet_id = '1pPKG2PwrCr1dlZIvGZB8TQZ1_f0Pey-pgEZ1lvDbsbw'
rewards_sheet_id = '1LZGc2MkP7IKuv7-BiXOkAaKCzcQytQtBKPU92kqlFkg'
new_signup_id = '190bKP_EyqZJGi6juWQrpbsxi5pI56iVykYjbNbhkuWI'
response_sheet = gc.open_by_key(response_sheet_id).worksheet("Form Responses 1")
rewards_sheet = gc.open_by_key(rewards_sheet_id).worksheet("Total Rewards")
new_signup_sheet = gc.open_by_key(new_signup_id).worksheet("Form Responses 1")

discord_twitter_dict = {}

# pull from new signup sheet
def pull_new_signup_data():
  print("-- pulling new signup data ---")
  discord_name_col = 2
  twitter_name_col = 3
  discordNames = new_signup_sheet.col_values(discord_name_col)[1:]
  twitterNames = new_signup_sheet.col_values(twitter_name_col)[1:]
  
  for idx, discordname in enumerate(discordNames):
    if '#' in discordname:
      if '@' in twitterNames[idx]:
        twitterNames[idx] = twitterNames[idx].replace('@', '')
      discord_twitter_dict[discordname] = twitterNames[idx]

def pull_old_signup_data():
  ## pull discord / twitter names into key-pair
  discord_name_col = 2
  twitter_name_col = 3
  discordNames = response_sheet.col_values(discord_name_col)[1:]
  twitterNames = response_sheet.col_values(twitter_name_col)[1:]
  
  ## data cleanup on usernames
  count = 0
  for idx, name in enumerate(twitterNames):
    if '@' in name:
      twitterNames[idx] = name.replace('@','')
    if 'https://twitter.com/' in name:
      twitterNames[idx] = name.replace('https://twitter.com/','')
    if 'https://mobile.twitter.com/' in name:
      twitterNames[idx] = name.replace('https://mobile.twitter.com/','')
    if '?' in name:
      name_arr = name.split('?')
      twitterNames[idx] = name_arr[0]
  
  for idx, name in enumerate(twitterNames):
    if 'https://twitter.com/' in name:
      name_arr = name.split('/')
      if 'status' not in name_arr:
        twitterNames[idx] = name_arr[-1:]
  
  for idx, name in enumerate(discordNames):
    if '#' in name:
      if type(twitterNames[idx]) == str:
        discord_twitter_dict[discordNames[idx]] = [twitterNames[idx]]
      else:
        discord_twitter_dict[discordNames[idx]] = twitterNames[idx]
  
  keys_to_pop = []
  for discordName in discord_twitter_dict.keys():
    twt_name = discord_twitter_dict[discordName][0]
    lowercase_name = twt_name.lower()
    if 'status' not in lowercase_name:
      if 'twitter.com/' in lowercase_name:
        updated_name = lowercase_name.replace('twitter.com/','')
        discord_twitter_dict[discordName][0] = updated_name
      elif 'https://twitter.com/' in lowercase_name:
        updated_name = lowercase_name.replace('https://twitter.com/','')
        discord_twitter_dict[discordName][0] = updated_name
      elif 'https://www.twitter.com/' in lowercase_name:
        updated_name = lowercase_name.replace('https://www.twitter.com/','')
        discord_twitter_dict[discordName][0] = updated_name
    else:
      #print("popped " + twt_name)
      keys_to_pop.append(discordName)
  for key in keys_to_pop:
    #print("popped " + discord_twitter_dict[key][0])
    discord_twitter_dict.pop(key)
  
  keys_to_pop = []
  for key, value in discord_twitter_dict.items():
    if isinstance(value, list):
      if value[0] == '':
        keys_to_pop.append(key)
      discord_twitter_dict[key] = value[0]
  
  for empty_key in keys_to_pop:
    discord_twitter_dict.pop(empty_key)


pull_old_signup_data()
pull_new_signup_data()
#print(discord_twitter_dict)

# USE TO OUTPUT LEADERBOARD WEEKLY OR BI-WEEKLY
#schedule.every().day.at("13:30").do(input_rewards_data)
#schedule.every(1).minutes.do(pull_new_signup_data)
#show scheduled jobs pending and last time ran
#print(schedule.get_jobs())

"""
# Loop so that the scheduling task keeps on running at all times
while True:
  #checks whether a scheduled task is pending to run or not
  schedule.run_pending()
  time.sleep(1)
"""


## DISCORD ##
intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

#rewards_command = "!sm-rewards"
#rank_command = "!sm-rank"
signup_command = "!signup"
output_embed_command = "!my-rewards"

sign_up_form = "https://forms.gle/zAArF17s2nNj3scL8"
sm_channel_id = 952233298539712522
quai_guild_id = 887783279053406238

gc = gspread.service_account(filename='smd-service-key.json')
SPREADSHEET_ID = '1LZGc2MkP7IKuv7-BiXOkAaKCzcQytQtBKPU92kqlFkg'
gsheet = gc.open_by_key(SPREADSHEET_ID)
leaderboard_sheet = gsheet.worksheet('Leaderboard')
leaderboard_data = {}

def signup_message(user):
  return f"{user.mention}, It doesn't appear we have you ({user.name}#{user.discriminator}) in our social media rewards sheet, OR we are having trouble with the information you provided.\n\n Try Signing up again with your correctly formatted discord and twitter usernames and your youtube URL here: " + sign_up_form
  
## INPUT LEADERBOARD DATA
def input_rewards_data():
  leaderboard = leaderboard_sheet.get_all_records()
  list_index = 0
  index_to_pop = 0
  for rewards_dict in leaderboard:
    for value in rewards_dict.values():
      list_index += 1
      if value == "Last Update:":
        index_to_pop = list_index
  leaderboard.pop(index_to_pop)
  
  leaderboard_df = pd.DataFrame.from_dict(leaderboard)
  print(leaderboard_df)
  leaderboard_view = leaderboard_df.sort_values(by='Rewards', axis=0, ascending=False)
  rewards_df_sorted = leaderboard_view.values.tolist()
  
  print(rewards_df_sorted)
  
  for user_rewards in rewards_df_sorted:
    rank = user_rewards[0]
    username = user_rewards[1]
    rewards = user_rewards[2]
    leaderboard_data[username] = [rank, rewards]
  
  print("--- inputted rewards leaderboard data ---")


if "mheez#6867" in discord_twitter_dict:
  print("You're in here")
else:
  print("still don't have your data")


## BOT FUNCTIONALITY
@client.event
async def on_ready():
  print("--- Logged in as SM Rewards Bot ---")
  input_rewards_data()
  pull_new_signup_data
  #schedule.every(1).minutes.do(pull_new_signup_data)
  #schedule.every(1.5).minutes.do(input_rewards_data)
  
  
@client.event
async def on_message(message):
  print("checking message")
  if message.author == client.user:
    pull_new_signup_data()
    return

  sm_channel = client.get_channel(sm_channel_id)
  if message.channel.id == sm_channel_id:
    if message.content.startswith(signup_command):
      print("signup message")   
      await sm_channel.send(f"{message.author.mention}, sign up here with your exact discord username ({message.author.name}#{message.author.discriminator}) and twitter name (ex: @username) for accurate rewards: " + sign_up_form, delete_after=20.00)
      await message.delete(delay=5)

    elif message.content.startswith(output_embed_command):
      print("embedded message")
      username = f"{message.author.name}#{message.author.discriminator}"
      if username in discord_twitter_dict.keys():
        print()
        print("user in discord_twitter_dict")
        twitter_name = discord_twitter_dict[username]
        if twitter_name in leaderboard_data:
          user_rank = leaderboard_data[twitter_name][0]
          user_rewards = leaderboard_data[twitter_name][1]
          embed = discord.Embed(title='Social Media Rewards', colour = discord.Colour.blue())
          user_value = []
          user_value.append("Rewards: {}".format(user_rewards))
          user_value.append("Rank: {}".format(user_rank))
          value='\n'.join(user_value)
          name = '{}'.format(username)
          embed.add_field(name=name, value=value, inline=False)
          await sm_channel.send(embed=embed, delete_after=20.00)
          await message.delete(delay=5)
        else:
          await sm_channel.send(f"{message.author.mention} you have signed up but no rewards have been calculated for you. \n\n Please ensure the twitter and youtube info you provided is correct for accurate calculation.\n" + sign_up_form, delete_after=20.00)
          await message.delete(delay=5)
      else:
        await sm_channel.send(f"{message.author.mention} you either have not earned any rewards or have not signed up for the social media rewards program.", delete_after=20.00)
        await message.delete(delay=5)
    else:
      await sm_channel.send("Try sending a command with the following: \n\n To return your total social media rewards:   !my-rewards \n To return the google form where you can signup for social media rewards:   !signup", delete_after=20.00)
      await message.delete(delay=5)


client.run(os.getenv('TOKEN'))

## TODO
# - pull from new sm rewards signup sheet and integrate into key:value store (override old input with new)
# - enable bot to pull from gsheets to keep signup up to date -> update every 5 minutes?
# - create aesthetically pleasing leaderboard post (with plot.png?)
# - handle spam messages?? (test to see if needed)
