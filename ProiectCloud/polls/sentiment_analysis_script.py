from textblob import TextBlob
import re
from django.views import View
from django.http import HttpResponse

def cleanTweet(tweet):
    return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split())

def getTweetSentiment(tweet):
    if tweet == "nada":
    	return 'No tweet found! Please provide with us with a tweet!'
    analysis = TextBlob(cleanTweet(tweet))
    if analysis.sentiment.polarity > 0:
        return 'This denotes positive feelings!:)'
    elif analysis.sentiment.polarity == 0:
        return 'This denotes neutral feelings!'
    else:
        return 'This denotes negative feelings!:('

class DoSentimentAnalysis(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse(getTweetSentiment())

    def post(self, request, *args, **kwargs):
        tweet = request.POST.get("tweet", "nada")

        answer = getTweetSentiment(tweet)

        return HttpResponse(answer)
        
        
   


