#%%

import os
from datetime import datetime
from io import StringIO
from dotenv import load_dotenv
import praw
from bs4 import BeautifulSoup
import pandas as pd
from google.cloud import storage
from google.oauth2 import service_account
from airtable import Airtable

load_dotenv()

gcp_credentials = service_account.Credentials.from_service_account_file(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))

#%%

# inputs
subreddit = 'machinelearning'
submissions_time_filter = 'day'
comments_n_max = 100
gcs_bucket = 'reddit-links'
gcs_filename = f"landing/df_links_{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.csv"

#%%

r = praw.Reddit(
    user_agent='reddit-links by /u/andrewm4894',
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET")
)

links = []

submissions = r.subreddit(subreddit).top(submissions_time_filter)
for submission in submissions:
    links.append([submission.permalink, submission.url, submission.score, submission.upvote_ratio])
    for comment in submission.comments.list()[0:comments_n_max]:
        if 'href' in comment.body_html:
            soup = BeautifulSoup(comment.body_html, 'html.parser')
            for a in soup.find_all('a'):
                link = a.get('href')
                links.append([comment.permalink, link, comment.score, 0])

df_links = pd.DataFrame(links, columns=['permalink', 'link', 'score', 'upvote_ratio'])
print(df_links.shape)
print(df_links.head())


#%%

# save csv to gcs
gcs = storage.Client(credentials=gcp_credentials)
f = StringIO()
df_links.to_csv(f)
f.seek(0)
gcs.get_bucket(gcs_bucket).blob(gcs_filename).upload_from_file(f, content_type='text/csv')


#%%

base_key = os.environ['AIRTABLE_BASE_KEY']
table_name = 'r/machinelearning'

airtable = Airtable(base_key, table_name, api_key=os.environ['AIRTABLE_KEY'])

for row in df_links.to_dict(orient='rows'):
    print(row)
    airtable.insert(row)


records = airtable.get_all(maxRecords=5)
df_air = pd.DataFrame.from_records((r['fields'] for r in records))

print(df_air.head())


#%%



#%%