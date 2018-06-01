import re
from urlextract import URLExtract
import time
import requests

apiKey = '811a31748544dd8d3a2d8a13785c2e78ffb2c351b5d56b37168ab6ff6315dc1f'

def getUrlsFromTweet(tweet):
    extractor = URLExtract()
    urls = extractor.find_urls(tweet)
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

if __name__ == '__main__':
    urls = getUrlsFromTweet('akbsnbsaj http://google.com bfk. https://facebook.com fd')
    print(urls)
    print(getUrlStatus(urls[0]))
    print(getUrlStatus('http://efsdfggbhbf.com'))