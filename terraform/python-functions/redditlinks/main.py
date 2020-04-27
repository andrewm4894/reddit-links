# -*- coding: utf-8 -*-
import json
import base64
import logging
import os
from datetime import datetime
from urllib.parse import urlparse
import praw
from bs4 import BeautifulSoup
import pandas as pd
from airtable import Airtable
from urlextract import URLExtract


def redditlinks(event, context):
    """Triggered from a message on a Cloud Pub/Sub topic.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """

    print('... start ...')

    logging.info('... begin ...')

    # get data from event into a dict
    event_data_json = json.loads(base64.b64decode(event['data']).decode('utf-8'))

    logging.info('... event_data_json ...')
    logging.info(event_data_json)

    subreddit = event_data_json['subreddit']
    submissions_time_filter = event_data_json['time_filter']
    comments_max = int(event_data_json['comments_max'])
    airtable_base_key = event_data_json['airtable_base']
    airtable_table_name = event_data_json['airtable_table']

    # create a url extractor
    extractor = URLExtract()

    # connect to reddit
    r = praw.Reddit(
        user_agent='reddit-links by /u/andrewm4894',
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET")
    )

    # create list to collect links into
    links = []

    # get reddit submissions
    submissions = r.subreddit(subreddit).top(submissions_time_filter)

    # process each submission
    for submission in submissions:
        submission_date = pd.to_datetime(submission.created_utc, unit='s').strftime('%Y-%m-%d')
        last_seen = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        link = submission.url
        links.append([
            link, submission_date, submission.created_utc, last_seen, 'submission',
            submission.title, submission.permalink, submission.score, submission.upvote_ratio
        ])
        # try also get urls from text of the submission
        submission_urls = extractor.find_urls(submission.selftext)
        if len(submission_urls) > 0:
            for submission_url in submission_urls:
                links.append([
                    submission_url, submission_date, submission.created_utc, last_seen, 'submission', submission.title,
                    submission.permalink, submission.score, submission.upvote_ratio
                ])
        # pull links from comments related to each submission using bs4
        for comment in submission.comments.list()[0:comments_max]:
            if 'href' in comment.body_html:
                comment_date = pd.to_datetime(comment.created_utc, unit='s').strftime('%Y-%m-%d')
                soup = BeautifulSoup(comment.body_html, 'html.parser')
                # add a row for each link found by bs4
                for a in soup.find_all('a'):
                    link = a.get('href')
                    links.append([
                        link, comment_date, comment.created_utc, last_seen, 'comment',
                        submission.title, comment.permalink, comment.score, 0
                    ])

    # create a df for all links
    df_links = pd.DataFrame(
        links,
        columns=[
            'link', 'created_date', 'created_utc', 'last_seen', 'type',
            'title', 'permalink', 'score', 'upvote_ratio'
        ]
    )
    df_links['permalink'] = 'https://www.reddit.com' + df_links['permalink']
    df_links['created_utc'] = pd.to_datetime(df_links['created_utc'], unit='s').astype('str')

    # try get domain for each link
    domains = []
    for link in df_links.link:
        try:
            domain = urlparse(link).netloc
        except:
            domain = 'N/A'
            pass
        domains.append(domain)
    df_links['domain'] = domains
    df_links['domain'] = df_links['domain'].str.lower().str.replace('www.', '')

    logging.info(f' ... df_links.shape = {df_links.shape} ...')

    logging.info('... send to airtable ...')

    # connect to airtable
    airtable = Airtable(airtable_base_key, airtable_table_name, api_key=os.environ['AIRTABLE_KEY'])

    inserted_count = 0
    updated_count = 0

    for i, row in df_links.iterrows():
        airtable_records = airtable.search('link', row['link'])
        if len(airtable_records) == 0:
            logging.info('... new record ({})...'.format(row['link']))
            record_fields = {
                'link': row['link'],
                'domain': row['domain'],
                'first_seen': row['created_utc'],
                'last_seen': row['created_utc'],
                'first_added': row['last_seen'],
                'last_added': row['last_seen'],
                'times_seen': 1,
                'score_avg': row['score'],
                'score_min': row['score'],
                'score_max': row['score'],
                'score_sum': row['score'],
                'title_list': row['title'],
                'last_title': row['title'],
                'permalink_list': row['permalink'],
                'last_permalink': row['permalink'],
            }
            airtable.insert(record_fields)
            logging.info('... inserted ...')
            inserted_count += 1
        elif len(airtable_records) > 0:
            for record in airtable_records:
                logging.info('... update record ({})...'.format(row['link']))
                record_id = record['id']
                old = airtable.get(record_id)['fields']
                new_score_avg = (old['score_sum'] + row['score']) / (old['times_seen'] + 1)
                new_score_min = old['score_min'] if old['score_min'] <= row['score'] else row['score']
                new_score_max = old['score_max'] if old['score_max'] >= row['score'] else row['score']
                new_score_sum = old['score_sum'] + row['score']
                new_times_seen = old['times_seen'] + 1
                if row['title'] not in old['title_list']:
                    new_title_list = '{}|{}'.format(old['title_list'], row['title'])
                else:
                    new_title_list = old['title_list']
                if row['permalink'] not in old['permalink_list']:
                    new_permalink_list = '{}|{}'.format(old['permalink_list'], row['permalink'])
                else:
                    new_permalink_list = old['permalink_list']
                record_fields = {
                    'link': old['link'],
                    'domain': old.get('domain', 'N/A'),
                    'first_seen': old['first_seen'],
                    'last_seen': row['created_utc'],
                    'first_added': old['first_added'],
                    'last_added': row['last_seen'],
                    'times_seen': new_times_seen,
                    'score_avg': new_score_avg,
                    'score_min': new_score_min,
                    'score_max': new_score_max,
                    'score_sum': new_score_sum,
                    'title_list': new_title_list,
                    'last_title': row['title'],
                    'permalink_list': new_permalink_list,
                    'last_permalink': row['permalink'],
                }
                airtable.update(record_id, record_fields)
                logging.info('... updated ...')
                updated_count += 1

    logging.info('... inserted_count = {} ...'.format(inserted_count))
    logging.info('... updated_count = {} ...'.format(updated_count))

    # result message
    result_message = f' ... df_links.shape = {df_links.shape} ...'
    result_message += f'... inserted_count = {inserted_count} ...'
    result_message += f'... updated_count = {updated_count} ...'
    logging.info(result_message)

    # build response
    response = {
        "statusCode": 200,
        "event": event,
        "context": context,
        "message": event_data_json,
        "result_message": result_message
    }
    logging.info(response)

    return response

