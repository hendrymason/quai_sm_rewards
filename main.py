import os
import time
import schedule
from datetime import datetime, timezone, timedelta
import gspread
import pandas as pd
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from reply_mentions_csv_tracker import reply_mentions_main_bot
from like_retweet_csv_tracker import like_retweet_main_bot


#TODO:
### CHECK PAGINATION FOR LIKERS & RETWEETERS
### UPDATE service-key.json WITH NEW GSPREAD PROJECT SERVICE FILE

# Gsheets
SERVICE_ACCOUNT_FILE = 'service-key.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gc = gspread.service_account(filename='service-key.json')
SPREADSHEET_ID = '1LZGc2MkP7IKuv7-BiXOkAaKCzcQytQtBKPU92kqlFkg'
gsheet = gc.open_by_key(SPREADSHEET_ID)
rewards_sheet = gsheet.worksheet('Total Rewards')

def get_data_in_batch():
  ##Handle Username,Rewards Row and Last Update: datetime.now() Row
  try:
    service = build('sheets', 'v4', credentials=creds)
    # Call the Sheets API
    RANGE_NAME = "Total Rewards"
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')
        return

    print('Values Updated:')
    for row in values:
      print(row)
      # Print columns A and B, which correspond to indices 0 and 1.
      print('%s, %s' % (row[0], row[1]))
  except HttpError as err:
    print(err)
  
def input_from_rewards_sheet():
  sheet_rewards = {}
  rewards_data = rewards_sheet.get_all_records()
  list_index = 0
  for rewards_dict in rewards_data:
    for value in rewards_dict.values():
      if value == "Last Update:":
        rewards_data.pop(list_index)
    list_index += 1
  print(rewards_data)
  rewards_df = pd.DataFrame.from_dict(rewards_data)
  print(rewards_df)
  rewards_view = rewards_df.sort_values(by='Rewards', axis=0, ascending=False)
  rewards_df_sorted = rewards_view.values.tolist()
  
  for data_list in rewards_df_sorted:
    sheet_rewards[data_list[0]] = data_list[1]
  print(sheet_rewards)
  return sheet_rewards

def get_csv_rewards():
  print("get_csv_rewards - reading reward data")
  csv_rewards = {}
  with open("total_twitter_rewards.csv") as ttr:
    line_index = 0
    for line in ttr:
      line_array = line.strip().split(': ')
      if line_index == 0:
        line_index += 1
        continue
      elif len(line_array) == 2 and line_array[0] != "Last Updated":
        csv_rewards[line_array[0]] = int(line_array[1])
  return csv_rewards

def get_leaderboards(rewards):
  leaderboard_output = [['Rank','Username','Rewards']]
  top10 = [['Rank','Username','Rewards']]
  rank_index = 1
  for key, value in rewards.items():
    leaderboard_output.append([rank_index, key, value])
    if rank_index <= 10:
      top10.append([rank_index, key, value])
    rank_index += 1
  return top10, leaderboard_output
    
def output_to_rewards_sheet():
  ls = gsheet.worksheet('Leaderboard')
  t10s =  gsheet.worksheet('Top 10')
  
  print("output_to_rewards_sheet - starting output")
  output_dict = get_csv_rewards()
  final_output = [['Username','Rewards']]
  for key, value in output_dict.items():
    final_output.append([key, value])
  
  timezone_offset = -6.0  # Central Standard Time (UTC−06:00)
  tzinfo = timezone(timedelta(hours=timezone_offset))
  final_output.append(["Last Update:", str(datetime.now(tzinfo))])

  #update Total Rewards Sheet
  gsheet.del_worksheet(rewards_sheet)
  _rows = str(len(final_output) + 100)
  new_rewards_sheet = gsheet.add_worksheet(title="Total Rewards", rows=_rows, cols="20")
  new_rewards_sheet.insert_rows(final_output)

  #update Leaderboard & Top 10 Sheets
  gsheet.del_worksheet(ls)
  gsheet.del_worksheet(t10s)
  print("*deleted leaderboards*")
  top10, total_leaderboard = get_leaderboards(output_dict)
  _rows = str(len(total_leaderboard))
  ls = gsheet.add_worksheet(title="Leaderboard", rows=_rows, cols="20")
  t10s = gsheet.add_worksheet(title="Top 10", rows="100", cols="20")
  ls.insert_rows(total_leaderboard)
  t10s.insert_rows(top10)

  print()
  print("-- Total Rewards Uploaded -- ")
  #print(final_output)
  print("-- Leaderboard Uploaded -- ")
  #print(total_leaderboard)
  print("-- Top 10 Uploaded --")
  #print(top10)

def count_twitter_rewards():
  like_retweet_main_bot()
  reply_mentions_main_bot()
  output_to_rewards_sheet()

#count_twitter_rewards()


### have discord bot check with scheduler for update at 7:30am, if updated today then send leaderboard in leaderboard annoucnements
## UTC TIME +6 HRS AHEAD OF CSTR
schedule.every().day.at("13:00").do(count_twitter_rewards)
#show scheduled jobs pending and last time ran
print(schedule.get_jobs())

# Loop so that the scheduling task keeps on running at all times
while True:
  #checks whether a scheduled task is pending to run or not
  schedule.run_pending()
  time.sleep(1)



