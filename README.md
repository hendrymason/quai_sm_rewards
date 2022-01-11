# quai_sm_rewards
A python-based script that iterates through @quainetwork's twitter timeline to garner total likes/tweets/mentions and aggregate the reward values in accordance with the twitter user who performed said action.

1. Maintain a dictionary of { "name": [retweets, likes, replies], "name2": [retweets, likes, replies]}
- Sort through all tweets (initially) and create a dictionary containing mainnet rewards criteria for each person starting at 0
2. Pull @QuaiNetwork tweets, check replies, retweets, and likes. Add in the + for each index. ex. @Cole retweets {"cole": [n+1, n, n]}
- After creating a name for each person, sort through where their name is found and increment++ that index in their array
3. Search tweets containing @QuaiNetwork then do the same process
- follow same process except for mentions of quainetwork
* consider saving the last tweet ID so as to keep a reference for when to begin the next social media rewards aggregation
