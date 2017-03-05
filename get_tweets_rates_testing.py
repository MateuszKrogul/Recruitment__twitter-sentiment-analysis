# -*- coding: utf-8 -*-
import json, pandas, vincent
from collections import defaultdict
from datetime import datetime
from nltk.corpus import stopwords
import string

def process_data(frequency, period):
    #TODO input control e.g. first date <= last date
    #TODO use frequency
    #tweets = []
    dates = []
    pos_values =[]
    neg_values= []

    with open("data.json", 'r') as f:
        for line in f:
            tweet = json.loads(line)
            tweet_date = datetime.strptime(tweet['created_at'],'%a %b %d %H:%M:%S +0000 %Y')
            if tweet_date < period[0]:
                continue
            if tweet_date > period[1]:
                break

            dates.append(tweet['created_at'])
            if tweet['sentiment'] == 'positive':
                pos_values.append(1)
                neg_values.append(0)
            if tweet['sentiment'] == 'negative':
                pos_values.append(0)
                neg_values.append(1)


    # positive tweets data
    pos_ones = pos_values
    pos_idx = pandas.DatetimeIndex(dates)
    pos_tweets = pandas.Series(pos_ones, index=pos_idx, name= 'Ratios').astype(float)
    resapmled_data = pos_tweets.resample(frequency).sum().fillna(0)

    # negative tweets data
    neg_ones = neg_values
    neg_idx = pandas.DatetimeIndex(dates)
    neg_tweets = pandas.Series(neg_ones, index=neg_idx).astype(float)
    neg_tweets_resampled = neg_tweets.resample(frequency).sum().fillna(0)


    # caclulation positive tweets contribution in all tweets in specific period
    for i in range(0,len(resapmled_data)):

        resapmled_data[i] = round(resapmled_data[i]/ (resapmled_data[i] + neg_tweets_resampled[i]),2)

    return resapmled_data
