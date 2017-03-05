# -*- coding: utf-8 -*-
import tweepy, logging, json, re, pickle, nltk, csv, time, datetime
from tweepy import OAuthHandler
from tweepy import Stream
from tweepy.streaming import StreamListener
from collections import defaultdict
from nltk.corpus import stopwords
import string
import os.path
from get_tweets_rates_testing import process_data
import threading
from threading import Lock, Thread
import plotly
import plotly.plotly as py
import plotly.graph_objs as go
import plotly.tools as tls
import pandas as pd
from pandas_datareader import data as web
from get_tweets_rates_testing import process_data

#TODO
#- store data in database e.g. MySQL


#API Data --secure hidden--
consumer_key = '*************************'
consumer_secret = '**************************************************'
access_token = '**************************************************'
access_secret = '*********************************************'

#API Authorisation
auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token,access_secret)

api = tweepy.API(auth)

#logging configuration
logger = logging.getLogger(__name__)
#TODO change path to FileHandler
logHandler = logging.FileHandler('logFile.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# Tokenisation
emoticons_str = r"""
    (?:
        [:=;] # Eyes
        [oO\-]? # Nose (optional)
        [D\)\]\(\]/\\OpP] # Mouth
    )"""
regex_str = [
    emoticons_str,
    r'<[^>]+>', # HTML tags
    r'(?:@[\w_]+)', # @-mentions
    r"(?:\#+[\w_]+[\w\'_\-]*[\w_]+)", # hash-tags
    r'http[s]?://(?:[a-z]|[0-9]|[$-_@.&amp;+]|[!*\(\),]|(?:%[0-9a-f][0-9a-f]))+', # URLs

    r'(?:(?:\d+,?)+(?:\.?\d+)?)', # numbers
    r"(?:[a-z][a-z'\-_]+[a-z])", # words with - and '
    r'(?:[\w_]+)', # other words
    r'(?:\S)' # anything else
]
tokens_re = re.compile(r'('+'|'.join(regex_str)+')', re.VERBOSE | re.IGNORECASE)
emoticon_re = re.compile(r'^'+emoticons_str+'$', re.VERBOSE | re.IGNORECASE)

def tokenize(tweet):
    return tokens_re.findall(tweet)

punctuation = list(string.punctuation)
stop = stopwords.words('english') + punctuation + ['rt', 'via']

def preprocess(tweet, lowercase=False):
    tokens = tokenize(tweet)
    if lowercase:
        tokens = [token if emoticon_re.search(token) else token.lower() for token in tokens]
    tokens = [token for token in tokens if token not in stop and not token.startswith(("http",))]
    return tokens

def get_words(tweets):
    all_words = []
    for (words,sentiment) in tweets:
        all_words.extend(words)
    return all_words

def get_words_features(word_list):
    word_list = nltk.FreqDist(word_list)
    words_features = word_list.keys()
    return words_features

def extract_features(tweet_words):
    tweet_words = set(tweet_words)
    features = {}
    for word in word_features:
        features['contains(%s)' % word] = (word in tweet_words)
    return features

def send_to_plotly_real_time():
    global call_plotly_counter
    global real_time_tweets
    while True:
        try:
            real_time_tweets_lock.acquire()
            temp_list_of_tweets = real_time_tweets
            real_time_tweets = []
            real_time_tweets_lock.release()

            if len(temp_list_of_tweets) < 1: continue
            # porcess data
            pos_dates=[]
            neg_dates=[]
            pos_ones=[]
            neg_ones=[]

            for (date,sentiment) in temp_list_of_tweets:
                if sentiment == 'positive':
                    pos_dates.append(date)
                    pos_ones.append(1)
                else:
                    neg_dates.append(date)
                    neg_ones.append(1)

            pos_idx = pd.DatetimeIndex(pos_dates)
            pos_tweets = pd.Series(pos_ones, index=pos_idx, name= 'Positive')
            pos_tweets = pos_tweets.resample('1S').sum().fillna(0)
            pos_tweets = pos_tweets.to_frame()

            neg_idx = pd.DatetimeIndex(neg_dates)
            neg_tweets = pd.Series(neg_ones, index=neg_idx, name= 'Negative')
            neg_tweets = neg_tweets.resample('1S').sum().fillna(0)
            neg_tweets = neg_tweets.to_frame()

            df = pd.DataFrame({"Positive":pos_tweets['Positive'],"Negative":neg_tweets['Negative']})

            # send to plotly
            if len(pos_ones) > 0:
                dates = df['Positive'].index
                pos_tweets_count = df['Positive']
                pos_tweets_stream = py.Stream(pos_tweets_stream_id)
                try:
                    pos_tweets_stream.open()
                    pos_tweets_stream.write(dict(x=dates,y=pos_tweets_count))

                    call_plotly_lock.acquire()
                    call_plotly_counter += 1
                    logger.info("call_plotly_counter: " + str(call_plotly_counter))
                    call_plotly_lock.release()

                    pos_tweets_stream.close()
                except:
                    logger.error("Error on send_to_plotly_real_time pos")


            if len(neg_ones) > 0:
                dates = df['Negative'].index
                neg_tweets_count = df['Negative']
                neg_tweets_stream = py.Stream(neg_tweets_stream_id)
                try:
                    neg_tweets_stream.open()
                    neg_tweets_stream.write(dict(x=dates,y=neg_tweets_count))

                    call_plotly_lock.acquire()
                    call_plotly_counter += 1
                    logger.info("call_plotly_counter: " + str(call_plotly_counter))
                    call_plotly_lock.release()

                    neg_tweets_stream.close()
                except:
                    logger.error("Error on send_to_plotly_real_time neg")

            time.sleep(3)
        except KeyboardInterrupt:
            pos_tweets_stream.close()
            neg_tweets_stream.close()

def send_to_plotly_daily(start=datetime.datetime.combine(datetime.datetime.today() - datetime.timedelta(days=31), datetime.time.min),end=datetime.datetime.combine(datetime.datetime.today() - datetime.timedelta(days=1), datetime.time.max)):
    global call_plotly_counter
    period =[start,end]
    tweets_rates = process_data("D",period=period)
    tweets_rates = tweets_rates.to_frame()
    google = web.DataReader('GOOG', 'yahoo', start, end)
    df = pd.DataFrame({"GOOG":google['Close'],"tweet":tweets_rates['Ratios']})

    dates = df['GOOG'].index
    prices = df['GOOG']
    prices_stream = py.Stream(prices_stream_id)
    try:
        prices_stream.open()
        prices_stream.write(dict(x=dates,y=prices))

        call_plotly_lock.acquire()
        call_plotly_counter += 1
        logger.info("call_plotly_counter: " + str(call_plotly_counter))
        call_plotly_lock.release()

        prices_stream.close()
    except:
        logger.error("Error on send_to_plotly_daily prices. API calls limit has been reached or no internet connection")



    dates = df['tweet'].index
    ratios = df['tweet']
    ratios_stream = py.Stream(ratios_stream_id)
    try:
        ratios_stream.open()
        ratios_stream.write(dict(x=dates,y=ratios))

        call_plotly_lock.acquire()
        call_plotly_counter += 1
        logger.info("call_plotly_counter: " + str(call_plotly_counter))
        call_plotly_lock.release()

        ratios_stream.close()
    except:
        logger.error("Error on send_to_plotly_daily tweet ratio. API calls limit has been reached or no internet connection")



def setup_plotly():
    # --secure hidden--
    plotly.tools.set_credentials_file(username='piruet', api_key='********************',stream_ids=['**********','**********','**********','**********'])
    stream_ids = tls.get_credentials_file()['stream_ids']
    global pos_tweets_stream_id
    global neg_tweets_stream_id
    global prices_stream_id
    global ratios_stream_id

    pos_tweets_stream_id = stream_ids[0]
    neg_tweets_stream_id = stream_ids[1]
    prices_stream_id = stream_ids[2]
    ratios_stream_id = stream_ids[3]


    stream_real_time_tweets_pos = go.Stream(
        token = stream_ids[0],
        maxpoints=120
    )
    stream_real_time_tweets_neg = go.Stream(
        token = stream_ids[1],
        maxpoints=120
    )
    stream_daily_prices = go.Stream(
        token = stream_ids[2]
    )
    stream_daily_ratios = go.Stream(
        token = stream_ids[3]
    )
    trace_real_time_tweets_pos = go.Bar(
        x=[],
        y=[],
        name= 'positive tweets',
        stream=stream_real_time_tweets_pos
    )
    trace_real_time_tweets_neg = go.Bar(
        x=[],
        y=[],
        name='negative tweets',
        stream=stream_real_time_tweets_neg
    )
    trace_daily_prices = go.Scatter(
        x=[],
        y=[],
        name = 'stock price',
        mode = 'lines+markers',
        stream=stream_daily_prices
    )
    trace_daily_ratios = go.Scatter(
        x=[],
        y=[],
        name = 'positive tweets ratio',
        mode = 'lines+markers',
        stream=stream_daily_ratios,
        yaxis='y2'
    )
    # real time
    data = go.Data([trace_real_time_tweets_pos,trace_real_time_tweets_neg])
    layout = go.Layout(
        title='positive and negative tweets about Google',
        barmode='stack',
        yaxis= dict(
            title='number of tweets'
        )
    )
    fig = go.Figure(data=data, layout=layout)
    py.plot(fig, filename='real_time_tweets',auto_open=False)

    # daily
    data = go.Data([trace_daily_prices,trace_daily_ratios])
    layout = go.Layout(
        title = 'Google stock prices and positive tweets ratios',
        yaxis = dict(
            title= 'stock prices'
        ),
        yaxis2 = dict(
            title = 'positive tweets ratios',
            overlaying ='y',
            side= 'right'
        )
    )
    fig = go.Figure(data=data, layout=layout)
    py.plot(fig, filename='Prices_and_ratios',auto_open=False)

class MyStreamListener(StreamListener):

    def on_data(self, data):
        global isFirst
        global isDailyGraphUpToDate
        try:
            with open("data.json", "a") as f:
                try:
                    tweet = json.loads(data)
                except:
                    logger.error("Error on_data: Error while trying to load jason data")
                    return
                classification = classifier.classify(extract_features(preprocess(tweet['text'], lowercase=True)))
                data_to_save = defaultdict()
                data_to_save['created_at'] = tweet['created_at']
                data_to_save['sentiment'] = classification
                f.write(json.dumps(data_to_save) + '\n')

                # add tweet to temp list
                real_time_tweets_lock.acquire()
                real_time_tweets.append((data_to_save['created_at'],data_to_save['sentiment']))
                real_time_tweets_lock.release()

                if isFirst:
                    with open('program_data.json', 'w') as f:
                        data = {}
                        data['isFirst'] = "False"
                        f.write(json.dumps(data))
                    isFirst = False
                    setup_plotly()


                    # send all daily data to plotly
                    #end = datetime.datetime.combine(datetime.datetime.today() - datetime.timedelta(days=2), datetime.time.min)
                    send_to_plotly_daily()
                    isDailyGraphUpToDate = True

                execute_daily_time = "09:00"
                if not isDailyGraphUpToDate and datetime.datetime.now().strftime('%H:%M:%S') > execute_daily_time and datetime.datetime.now().strftime('%H:%M:%S') < "23:59":
                    # daily send to plotly
                    #today date
                    #start = datetime.datetime.strptime(datetime.datetime.today().strftime('%Y%m%d'),'%Y%m%d')
                    #start = datetime.datetime.combine(datetime.datetime.today() - datetime.timedelta(days=1), datetime.time.min)
                    send_to_plotly_daily()
                    isDailyGraphUpToDate = True

                if isDailyGraphUpToDate and datetime.datetime.now().strftime('%H:%M:%S') > "00:00" and datetime.datetime.now().strftime('%H:%M:%S') < execute_daily_time:
                    isDailyGraphUpToDate = False

                return True
        except BaseException as e:
            logger.error("Error on_data {}".format(str(e)))
        return True

    def on_error(self, status):
        logger.info("status: {}".format(status))
        return True

classifier = None
word_features = None
if os.path.exists("classifier_program_data"):
    with open("classifier_program_data", 'rb') as f:
        classifier = pickle.load(f)
        logger.info("classifier loaded from file")
    with open("word_features_program_data", 'rb') as f:
        word_features = pickle.load(f)
else:
    # get training data
    learning_tweets = []
    if os.path.exists("learning_tweets_program_data"):
        with open("learning_tweets_program_data",'rb') as f:
            learning_tweets = pickle.load(f)
            logger.info("pickle data loaded")
    else:
        with open("learning_tweets.json","r") as f:
            for tweet in f:
                tweet = json.loads(tweet)
                words = preprocess(tweet["text"], lowercase=True)
                learning_tweets.append((words,tweet["sentiment"]))
        with open("learning_tweets_program_data",'wb') as f:
            pickle.dump(learning_tweets,f)
            logger.info("pickle data saved")

    word_features = get_words_features(get_words(learning_tweets))
    training_set = nltk.classify.apply_features(extract_features, learning_tweets)

    # train classifier
    logger.info("Start classifier training")
    classifier = nltk.NaiveBayesClassifier.train(training_set)
    logger.info("Classifier training done")

    # save classifier
    with open("classifier_program_data", 'wb') as f:
        pickle.dump(classifier, f)
    with open("word_features_program_data", 'wb') as f:
        pickle.dump(word_features, f)

isFirst = True
# TODO change to pickle if json not needed
if os.path.exists('program_data.json'):
    with open('program_data.json', 'r') as f:
        data = json.loads(f.read())
    if data['isFirst'] == 'True': isFirst = True
    else: isFirst = False
else:
    with open('program_data.json', 'w') as f:
        data = {}
        data['isFirst'] = "True"
        f.write(json.dumps(data))

isDailyGraphUpToDate = False
logger.info('isDailyGraphUpToDate set to: False')

real_time_tweets_lock = Lock()
real_time_tweets = []

stream_ids = tls.get_credentials_file()['stream_ids']
pos_tweets_stream_id = None
neg_tweets_stream_id = None
ratios_stream_id = None
prices_stream_id = None
if len(stream_ids) > 0:
    pos_tweets_stream_id = stream_ids[0]
    neg_tweets_stream_id = stream_ids[1]
    prices_stream_id = stream_ids[2]
    ratios_stream_id = stream_ids[3]

# start sending real time data to plotly in thread
thread = Thread(target=send_to_plotly_real_time)
thread.start()

call_plotly_lock = Lock()
call_plotly_counter = 0

# start receiving data
while True:
    try:
        logger.info("Start receive streaming")
        stream = Stream(auth, MyStreamListener())
        stream.filter(track=['#Google'])
    except:
        logger.error("Error on receiving stream")
