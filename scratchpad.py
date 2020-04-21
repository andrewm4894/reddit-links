#%%

import os
from dotenv import load_dotenv
import praw

load_dotenv()

#%%

r = praw.Reddit(
    user_agent='reddit-links by /u/andrewm4894',
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET")
)

#%%

submissions = r.subreddit('machinelearning').top(limit=5)

#%%

for submission in submissions:
    print(submission.title, submission.url)

#%%

comments = submission.comments

#%%

for comment in comments:
    print(comment.body)

#%%