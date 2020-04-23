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
        logging.info(f'... submission.permalink = {submission.permalink} ...')
        logging.info(f'... submission.url = {submission.url} ...')
        link_num = 1
        submission_date = pd.to_datetime(submission.created_utc, unit='s').strftime('%Y-%m-%d')
        added_utc = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        link_id = f'{submission.id}_{link_num}'
        links.append([
            link_id, submission_date, submission.created_utc, added_utc, 'submission',
            submission.title, submission.permalink, submission.url, submission.score, submission.upvote_ratio
        ])
        # try also get urls from text of the submission
        submission_urls = extractor.find_urls(submission.selftext)
        if len(submission_urls) > 0:
            for submission_url in submission_urls:
                logging.info(f'... submission_url = {submission_url} ...')
                link_num += 1
                link_id = f'{submission.id}_{link_num}'
                links.append([
                    link_id, submission_date, submission.created_utc, added_utc, 'submission', submission.title,
                    submission.permalink, submission_url, submission.score, submission.upvote_ratio
                ])
        # pull links from comments related to each submission using bs4
        for comment in submission.comments.list()[0:comments_max]:
            logging.info(f'... comment.permalink = {comment.permalink} ...')
            if 'href' in comment.body_html:
                comment_date = pd.to_datetime(comment.created_utc, unit='s').strftime('%Y-%m-%d')
                soup = BeautifulSoup(comment.body_html, 'html.parser')
                link_num = 0
                # add a row for each link found by bs4
                for a in soup.find_all('a'):
                    link_num += 1
                    link_id = f'{comment.id}_{link_num}'
                    link = a.get('href')
                    logging.info(f'... link = {link} ...')
                    links.append([
                        link_id, comment_date, comment.created_utc, added_utc, 'comment', submission.title,
                        comment.permalink, link,
                        comment.score, 0
                    ])

    # create a df for all links
    df_links = pd.DataFrame(
        links,
        columns=[
            'id', 'created_date', 'created_utc', 'added_utc', 'type',
            'title', 'permalink', 'link', 'score', 'upvote_ratio'
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
            domain = None
            pass
        domains.append(domain)
    df_links['domain'] = domains
    df_links['domain'] = df_links['domain'].str.lower().str.replace('www.', '')

    # connect to airtable
    airtable = Airtable(airtable_base_key, airtable_table_name, api_key=os.environ['AIRTABLE_KEY'])
    # append rows to airtable
    for row in df_links.to_dict(orient='rows'):
        airtable.insert(row)

    # result message
    result_message = f' ... df_links.shape = {df_links.shape} ...'
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

