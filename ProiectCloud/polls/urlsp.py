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
from urlextract import URLExtract
import requests
import time 

#try with akras14 and 1
apiKey = '811a31748544dd8d3a2d8a13785c2e78ffb2c351b5d56b37168ab6ff6315dc1f'

def getUserTweets(account_name, limit):
    api = twitter.Api(consumer_key='og0R0hgBR7TZDuvWiiRMAdaJn',
    consumer_secret='XvDnJGgTQ6jRwJFTp3D4LlutMSAmu0SoK1lAiZWu2YOvHRriTK',
    access_token_key='750821522479181824-tOJiIbWX01gPoVsVadtmOKgno3tFuF8',
    access_token_secret='FB9Py94PpcBCzMqaqZuwDhws7QbRI6B2XLK2f1igOiS1X')

    #print(api.VerifyCredentials())
    tweets = api.GetUserTimeline(screen_name=account_name, count=limit)
    #tweets = [i.AsDict() for i in t]
    return tweets


def getUrlsFromTweet(tweet):
    extractor = URLExtract()
    urls = extractor.find_urls(str(tweet))
    return urls

def getUrlStatus(url):
    def scan(url):
        resp = requests.post('https://www.virustotal.com/vtapi/v2/url/scan?apikey={}'.format(apiKey), params={'url': url})
        if resp.status_code == 204:
            return 'api limit'
        if resp.status_code != 200:
            return None
        resp = resp.json()
        if resp['response_code'] != 1:
            return None
        return 'loading'
    def getReportNoWait(url):
        resp = requests.post('https://www.virustotal.com/vtapi/v2/url/report?apikey={}'.format(apiKey), params={'resource': url})
        if resp.status_code == 204:
            return 'api limit'
        if resp.status_code != 200:
            return None
        resp = resp.json()
        if resp['response_code'] == 1:
            return resp
        elif resp['response_code'] == -2:
            return 'loading'
        else:
            return scan(url)
    f = True
    while f:
        report = getReportNoWait(url)
        if report in ['api limit', 'loading']:
            time.sleep(20)
            continue
        f = False
    if report['positives'] > report['total'] // 2:
        return 'infected'
    return 'clean'


class MyURLsView(View):
  
     def post(self, request, *args, **kwargs):
        account = request.POST.get("account", "nada")
        tweet_no = int(request.POST.get("tweets_no", 0)) 

        print (account, tweet_no)

        tweets = getUserTweets(account, tweet_no)
        urls=[]
        pairs=[]
        for tweet in tweets:
            urls.append(getUrlsFromTweet(tweet))
        for url in urls:
            for el in url:
                print('URL:{0} | Result:{1}'.format(el, getUrlStatus(el)))
                pairs.append('URL:{0} | Result:{1}'.format(el, getUrlStatus(el)))         
      
        print(pairs)
        return render(request, 'table_body.html', {'response':pairs})
        
   
