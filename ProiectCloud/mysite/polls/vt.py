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
import hashlib
import requests
import time
import os


""" Auxiliary """

from azure.storage.file import FileService, ContentSettings

fileService = FileService(account_name='cs7b04dc31e3552x4267x9c3', account_key='ihwu6KLKRkUv3/dF3ELyhqbsB34jUJGyyVexD3gr2PUhcL3X5XFg/aFumVEHZCUHqqfP+m2UBM1Lni3uw26WcA==')
filesDir = 'fileshare'
fileService.create_share(filesDir)

""" VT """
apiKey = '811a31748544dd8d3a2d8a13785c2e78ffb2c351b5d56b37168ab6ff6315dc1f'

def getFile(dirName, fileName):
    file_ = fileService.get_file_to_text(filesDir, dirName, fileName)
    return file_


""" Main logic """
def getAzureFileReport(githubUser, githubProject, fileName):
    if githubUser == "nada" or githubProject == "nada" or fileName == "nada":
        return "Please provide all the fields!"
    def scan(fileName, fileText, wait=False):
        resp = requests.post('https://www.virustotal.com/vtapi/v2/file/scan?apikey={}'.format(apiKey), files={'file': (fileName, fileText)})
        if resp.status_code == 204:
            return 'api limit'
        if resp.status_code != 200:
            return None
        resp = resp.json()
        if resp['response_code'] != 1:
            return None
        fileSha = resp['sha1']
        if wait == True:
            return getReportWait(fileName, fileText)
        return 'loading'
    def getReportNoWait(fileName, fileText):
        h = hashlib.sha1()
        h.update(fileText)
        fileSha = h.hexdigest()
        resp = requests.post('https://www.virustotal.com/vtapi/v2/file/report?apikey={}&resource={}'.format(apiKey, fileSha))
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
            return scan(fileName, fileText, False)
    try:
        dirName = '{}-{}'.format(githubUser, githubProject)
        file_ = getFile(dirName, fileName.replace('\\', '-').replace('/', '-'))
        if file_ == None:
            return 'file not in azure'
        fileText = file_.content.encode('utf-8')
        f = True
        while f:
            report = getReportNoWait(fileName, fileText)
            print(report)
            if report in ['api limit', 'loading']:
                time.sleep(20)
                continue
            f = False
        if report['positives'] > report['total'] // 2:
            return 'The sample is infected!'
        return 'The sample is clean!'
    except:
        return 'The sample is clean!'


class VIView(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse(getAzureFileReport())

    def post(self, request, *args, **kwargs): 
        user = request.POST.get("user", "nada")
        project = request.POST.get("project", "nada")
        fileName = request.POST.get("file_name", "nada") 
        answer = getAzureFileReport(user, project, fileName)
        return HttpResponse(answer)


        
   
