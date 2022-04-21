import discord
from discord.ext import tasks, commands
import os
import gspread
import pandas as pd

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

## pull discord / twitter names from sheets
discord_name_col = 2
twitter_name_col = 3

old_discord_data = response_sheet.col_values(discord_name_col)[1:]
old_twitter_data = response_sheet.col_values(twitter_name_col)[1:]

new_discord_data = new_signup_sheet.col_values(discord_name_col)[1:]
new_twitter_data = new_signup_sheet.col_values(twitter_name_col)[1:]

discord_twitter_dict = {}

remove_char = ['@', "www.", "https://", "twitter", ".com/", "mobile."]  

# clean gsheets twitter username data
def clean_twitter_data(username_list):
  
  for idx, name in enumerate(username_list):
    if name != "":
      for r in remove_char:
        lowercase = username_list[idx].lower()
        if r in lowercase:
          username_list[idx] = lowercase.replace(r, '')
      if '?' in lowercase:
        username_list[idx] = ''

  return username_list

  
# pull from new signup sheet
def pull_new_signup_data(_twitter_data, _discord_data):
  print("--- pulling new signup data ---")
  new_twitter_names = clean_twitter_data(_twitter_data)
  
  for idx, discord_name in enumerate(_discord_data):
    lowercase_discord = discord_name.lower()
    if '#' in lowercase_discord:
      if idx <= len(new_twitter_names)-1:
        discord_twitter_dict[lowercase_discord] = new_twitter_names[idx]


def pull_old_signup_data(_twitter_data, _discord_data):
  print("--- pulling old signup data ---")
  old_twitter_names = clean_twitter_data(_twitter_data)
  
  ## data cleanup on usernames
  for idx, name in enumerate(old_twitter_names):
    lowercase_twitter = name.lower()
    if 'quai' not in lowercase_twitter and lowercase_twitter != "":
      old_twitter_names[idx] = lowercase_twitter
  
  ## add discord x twitter pair to dict
  for idx, name in enumerate(_discord_data):
    lowercase_discord = name.lower()
    if '#' in lowercase_discord:
      discord_twitter_dict[lowercase_discord] = old_twitter_names[idx]


pull_old_signup_data(old_twitter_data, old_discord_data)
pull_new_signup_data(new_twitter_data, new_discord_data)

#print("-- filtered discord twitter dict --")
#print(discord_twitter_dict)


## DISCORD ##
intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

signup_command = "!signup"
output_embed_command = "!my-rewards"
twitter_command = "!twitter="

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

def input_rewards_data():
  rank_col = 1
  username_col = 2
  rewards_col = 3

  rank_data = leaderboard_sheet.col_values(rank_col)[1:]
  username_data = leaderboard_sheet.col_values(username_col)[1:]
  rewards_data = leaderboard_sheet.col_values(rewards_col)[1:]

  for idx, username in enumerate(username_data):
    lowercase_user = username.lower()
    leaderboard_data[lowercase_user] = [rank_data[idx], rewards_data[idx]]

  print(leaderboard_data)
    
  
## INPUT LEADERBOARD DATA
def input_rewards_data_df():
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
  leaderboard_view = leaderboard_df.sort_values(by='Rewards', axis=0, ascending=False)
  rewards_df_sorted = leaderboard_view.values.tolist()
  
  for user_rewards in rewards_df_sorted:
    rank = user_rewards[0]
    username = user_rewards[1].lower()
    rewards = user_rewards[2]
    leaderboard_data[username] = [rank, rewards]

  print("------LEADERBOARD DATA--------")
  for key, value in leaderboard_data.items():
    print("TWITTER NAME: " + str(key) + "--- VALUE: " + str(value))



"""
print("-------DISCORD_TWITTER_DATA-------")
for key,value in discord_twitter_dict.items():
  print("DISCORD: " + str(key) + "--- TWITTER: " + str(value))
"""
## BOT FUNCTIONALITY
#requested_signup = False
@tasks.loop(seconds=180)
async def pull_signup():
  #if requested_signup:
  pull_new_signup_data(new_twitter_data, new_discord_data)
    #requested_signup = False
  print("--- looped and pulled signup data ---")

@tasks.loop(hours=24)
async def pull_rewards():
  input_rewards_data()
  print("--- looped and pulled reward data ---")
  
@client.event
async def on_ready():
  print("--- Logged in as SM Rewards Bot ---")
  input_rewards_data()
  pull_new_signup_data(new_twitter_data, new_discord_data)
  
@client.event
async def on_message(message):
  print(message)
  if message.channel.id == sm_channel_id:
    #print(message)
    print("checking message")
    
    if message.author == client.user:
      return
    
    sm_channel = client.get_channel(sm_channel_id)
    if message.content.startswith(signup_command):
      print("signup message")   
      await sm_channel.send(f"{message.author.mention}, sign up here with your exact discord username ({message.author.name}#{message.author.discriminator}) and twitter name (ex: @username) for accurate rewards: " + sign_up_form)
      print(f"{message.author.name}#{message.author.discriminator} requested signup")

    elif message.content.startswith(output_embed_command):
      print("embedded message")
      nickname = message.author.name.lower()
      username = f"{nickname}#{message.author.discriminator}"
      if username in discord_twitter_dict.keys():
        print("user in discord_twitter_dict")
        twitter_name = discord_twitter_dict[username]
        print(twitter_name)
        if twitter_name in leaderboard_data:
          user_rank = leaderboard_data[twitter_name][0]
          user_rewards = leaderboard_data[twitter_name][1]
          embed = discord.Embed(title='Social Media Rewards', colour = discord.Colour.blue())
          user_value = []
          user_value.append("Rank: #{}".format(user_rank))
          user_value.append("Rewards: {} $QUAI".format(user_rewards))
          value='\n'.join(user_value)
          name = '{}'.format(username)
          embed.add_field(name=name, value=value, inline=False)
          await sm_channel.send(embed=embed)
          print(f"{message.author.name}#{message.author.discriminator} was sent their rewards")
        else:
          await sm_channel.send(f"{message.author.mention} you have signed up but no rewards have been calculated for you yet. This bot (temporarily) only displays your twitter rewards. Youtube rewards will be calculated soon. \n\n If you signed up today, please wait until tomorrow's rewards calculation to be assigned to you. \n\n You can also try the command '!twitter=your twitter username' to access your twitter rewards directly for the time being. \n\n If you are still experiencing issues, Please ensure the twitter and youtube info you provided in the signup form is correct for accurate calculation." + sign_up_form)
          print(f"{message.author.name}#{message.author.discriminator} was found in signup form but not found in sm rewards")
          print("")
      else:
        await sm_channel.send(f"{message.author.mention} you either have not earned any rewards or have not signed up for the social media rewards program. Keep in mind this bot (temporarily) only displays your twitter rewards. Youtube rewards will be calculated soon. \n\n You can also try the command '!twitter=your twitter username' to access your twitter rewards directly for the time being. \n\n If issues still persist, try signing up again with EXACT formatting from your discord and social media names on the new rewards form.\n" + sign_up_form)
        print(f"{message.author.name}#{message.author.discriminator} was not found in the database")

    elif message.content.startswith(twitter_command):
      twitter_name = message.content.split('=')[1].lower()
      if '@' in twitter_name:
        twitter_name = twitter_name.replace('@','')
      if twitter_name in leaderboard_data:
        user_rank = leaderboard_data[twitter_name][0]
        user_rewards = leaderboard_data[twitter_name][1]
        embed = discord.Embed(title='Twitter Rewards', colour = discord.Colour.blue())
        user_value = []
        user_value.append("Rank: #{}".format(user_rank))
        user_value.append("Rewards: {} $QUAI".format(user_rewards))
        value='\n'.join(user_value)
        name = '{}'.format(twitter_name)
        embed.add_field(name=name, value=value, inline=False)
        await sm_channel.send(embed=embed)
        print(f"{message.author.name}#{message.author.discriminator} was sent rewards for {twitter_name}")
      else:
        await sm_channel.send(f"{message.author.mention} it doesn't appear {twitter_name} is within our rewards yet. \n\n Check if you're using the command properly, example: '!twitter=twitterUsername'")
        print(f"{message.author.name}#{message.author.discriminator} asked for {twitter_name} twitter's rewards, but they were not found")
    else:
      await sm_channel.send("Try sending a command with the following: \n\n To return your total social media rewards:   !my-rewards \n To return the google form where you can signup for social media rewards:   !signup \n To directly access twitter rewards: !twitter=[your twitter username]", delete_after=20.00)
      print(f"{message.author.name}#{message.author.discriminator} sent an improper command")

pull_signup.start()
pull_rewards.start()
client.run(os.getenv('TOKEN'))

## TODO
# - pull from new sm rewards signup sheet and integrate into key:value store (override old input with new)
# - enable bot to pull from gsheets to keep signup up to date -> update every 5 minutes?
# - create aesthetically pleasing leaderboard post (with plot.png?)
# - handle spam messages?? (test to see if needed)
