from django.views import View
from django.http import HttpResponse
from django.shortcuts import render
from urlextract import URLExtract
import threading
import requests
import base64
import hashlib
import re
import time
import twitter
from azure.storage.file import FileService, ContentSettings

apiKey = '811a31748544dd8d3a2d8a13785c2e78ffb2c351b5d56b37168ab6ff6315dc1f'
OAUTH_TOKEN = '9870518e9fde970e38c9ccba3eb5cbedf650b19c'
limit = 2
fileService = FileService(account_name='cs7b04dc31e3552x4267x9c3', account_key='ihwu6KLKRkUv3/dF3ELyhqbsB34jUJGyyVexD3gr2PUhcL3X5XFg/aFumVEHZCUHqqfP+m2UBM1Lni3uw26WcA==')
filesDir = 'fileshare'

def getUserTweets(account_name):
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



def getUserProjects(user):
    resp = requests.get('https://api.github.com/users/{}/repos'.format(user), headers={'Authorization': 'token {}'.format(OAUTH_TOKEN)})
    if resp.status_code != 200:
        return []
    resp = resp.json()
    projects = [project['name'] for project in resp]
    return projects



def saveProjectFilesToAzure(user, project, limit):
    def saveProjectFilesRecursively(user, project, sha, path, files, dirName, limit):
        #print('https://api.github.com/repos/{}/{}/git/trees/{}'.format(user, project, sha))
        resp = requests.get('https://api.github.com/repos/{}/{}/git/trees/{}'.format(user, project, sha), headers={'Authorization': 'token {}'.format(OAUTH_TOKEN)})  
        #print(resp.status_code)
        if resp.status_code == 200:
            resp = resp.json()
            tree = resp['tree']
            trees = []
            blobs = []
            for t in tree:
                if t['type'] == 'blob':
                    blobs.append(t)
                else:
                    trees.append(t)
            for content in blobs:
                if len(files) == limit:
                    return 1
                if content['path'] in [".gitignore", "LICENSE", "README.md"]:
                    continue
                if path != '':
                    newPath = '{}\\{}'.format(path, content['path'])
                else:
                    newPath = content['path']
                dir_sha = content['sha']
                #print("here" + newPath)
                files.append(newPath)
                t = threading.Thread(target=saveFile, args=[newPath.replace('\\', '-'), getFileContent(content['url']), dirName])
                t.setDaemon(False)
                t.start()
            for content in trees:
                if len(files) == limit:
                        return 1
                if path != '':
                    newPath = '{}\\{}'.format(path, content['path'])
                else:
                    newPath = content['path']
                dir_sha = content['sha']
                if saveProjectFilesRecursively(user, project, dir_sha, newPath, files, dirName, limit) == 1:
                    return 1
            return 0
    sha = getProjectLastCommit(user, project)
    #print('sha: ', sha)
    files = []
    dirName = '{}-{}'.format(user, project)
    t = threading.Thread(target=createDir, args=[ dirName])
    t.setDaemon(False)
    t.start()
    saveProjectFilesRecursively(user, project, sha, '', files, dirName, limit)
    return files

def getProjectLastCommit(user, project):
    resp = requests.get('https://api.github.com/repos/{}/{}/commits'.format(user, project), headers={'Authorization': 'token {}'.format(OAUTH_TOKEN)})
    if resp.status_code != 200:
        return []
    resp = resp.json()
    commit = resp[0]['sha']
    return commit


def createDir(dirName):
    fileService.create_directory(filesDir, dirName)

def saveFile(fileName, fileText, dirName):
    fileService.create_file_from_text(filesDir, dirName, fileName, fileText, content_settings=ContentSettings())

def getFileContent(url):
    resp = requests.get(url)
    if resp.status_code != 200:
        return ''
    resp = resp.json()
    if resp['encoding'] == 'base64':
        return base64.b64decode(resp['content'])
    else:
        print(resp['encoding'])
        return resp['content']


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
        return 'clean'
    except:
        return 'clean'

def getFile(dirName, fileName):
    file_ = fileService.get_file_to_text(filesDir, dirName, fileName)
    return file_

class Results(View):
    # def get(self, request, *args, **kwargs):
    #     return HttpResponse(saveProjectFilesToAzure())

    def post(self, request, *args, **kwargs):
        all_urls = []
        all_files = []
        raspuns_twitter = []
        raspuns_github = []
        twitter = request.POST.get("twitter", "nada")
        github = request.POST.get("github", "nada")
        if twitter:
            for el in getUserTweets(twitter):
                for url in getUrlsFromTweet(str(el)):
                    all_urls.append(url)      
            for el in all_urls[:limit]:
                # print("URL:{0} | Result:{1}".format(el, getUrlStatus(el)))
                raspuns_twitter.append({"url": el, "verdict":getUrlStatus(el)})
        
        if github: 
            all_projects = getUserProjects(github)
            print(all_projects)
            for githubProject in all_projects:
                all_files = saveProjectFilesToAzure(github, githubProject, 1)   
                for file_s in all_files:
                    # print("File:{0} | Result:{1}".format(file_s, getAzureFileReport(github, githubProject, file_s)))
                    raspuns_github.append({"file":file_s, "verdict":getAzureFileReport(github, githubProject, file_s)})
        
        print(raspuns_twitter)
        print(raspuns_github)
        answear = {"twitter": raspuns_twitter, "github": raspuns_github}
        return render(request, 'results.html', {'response':answear})