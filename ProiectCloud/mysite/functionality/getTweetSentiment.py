from textblob import TextBlob
from getUserTweets import *
import re

def cleanTweet(tweet):
    return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split())

def getTweetSentiment(tweet):
    analysis = TextBlob(cleanTweet(tweet))
    if analysis.sentiment.polarity > 0:
        return 'This denotes positive feelings!:)'
    elif analysis.sentiment.polarity == 0:
        return 'This denotes neutral feelings!'
    else:
        return 'This denotes negative feelings!:('

if __name__ == '__main__':
    tweets = getUserTweets()
    print(getTweetSentiment(tweets[0]['text']))