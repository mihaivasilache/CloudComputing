from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth import authenticate, login
from django.views import View
from django.shortcuts import redirect  
from django.shortcuts import render_to_response
from django.template.context import RequestContext
import json
from django.conf import settings
from tweepy.parsers import Parser
from django.shortcuts import render
from django.utils.datastructures import MultiValueDictKeyError
from django.http import HttpResponse
import twitter


#try with akras14 and 1

def getUserTweets(name, number):
    api = twitter.Api(consumer_key='og0R0hgBR7TZDuvWiiRMAdaJn',
    consumer_secret='XvDnJGgTQ6jRwJFTp3D4LlutMSAmu0SoK1lAiZWu2YOvHRriTK',
    access_token_key='750821522479181824-tOJiIbWX01gPoVsVadtmOKgno3tFuF8',
    access_token_secret='FB9Py94PpcBCzMqaqZuwDhws7QbRI6B2XLK2f1igOiS1X')

    #print(api.VerifyCredentials())
    t = api.GetUserTimeline(screen_name=name, count=number)
    tweets = [i.AsDict() for i in t]
    text = [i['text'] for i in tweets]
  
    return text


class DoMyStuff(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse(getUserTweets())

    def post(self, request, *args, **kwargs):
        account = request.POST.get("account", "nada")
        tweet_no = int(request.POST.get("tweets_no", 0)) 

        print (account, tweet_no)

        answer = getUserTweets(account, tweet_no)

        return render(request, 'table_body.html', {'response':answer})
        
   
