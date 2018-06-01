from django.views import View
from django.http import HttpResponse
from textblob import TextBlob
from django.shortcuts import render
import threading
import requests
import base64
import hashlib
import re
from polls.vt import getAzureFileReport 


""" storage """
from azure.storage.file import FileService, ContentSettings

fileService = FileService(account_name='cs7b04dc31e3552x4267x9c3', account_key='ihwu6KLKRkUv3/dF3ELyhqbsB34jUJGyyVexD3gr2PUhcL3X5XFg/aFumVEHZCUHqqfP+m2UBM1Lni3uw26WcA==')
filesDir = 'fileshare'
#fileService.create_share(filesDir)

def getFiles(dirName):
    files = []
    try:
        generator = fileService.list_directories_and_files(filesDir, dirName)
        for file_or_dir in generator:
            files.append({'name': file_or_dir.name, 'length': file_or_dir.properties.content_length})
    except Exception as e:
        print(e)
        files = []
    return files

def getFile(dirName, fileName):
    file_ = fileService.get_file_to_text(filesDir, dirName, fileName)
    return file_

def createDir(dirName):
    fileService.create_directory(filesDir, dirName)

def saveFile(fileName, fileText, dirName):
    fileService.create_file_from_text(filesDir, dirName, fileName, fileText, content_settings=ContentSettings())


""" github """
OAUTH_TOKEN = '9870518e9fde970e38c9ccba3eb5cbedf650b19c'

def getUserProjects(user):
    resp = requests.get('https://api.github.com/users/{}/repos'.format(user), headers={'Authorization': 'token {}'.format(OAUTH_TOKEN)})
    if resp.status_code != 200:
        return []
    resp = resp.json()
    projects = [project['name'] for project in resp]
    return projects

def getProjectLastCommit(user, project):
    resp = requests.get('https://api.github.com/repos/{}/{}/commits'.format(user, project), headers={'Authorization': 'token {}'.format(OAUTH_TOKEN)})
    if resp.status_code != 200:
        return []
    resp = resp.json()
    commit = resp[0]['sha']
    return commit

def getProjectFilenames(user, project, limit):
    sha = getProjectLastCommit(user, project)
    files = []
    getProjectFilenamesRecursively(user, project, sha, files, limit)
    return files

def getProjectFilenamesRecursively(user, project, sha, files, limit):
    if len(files) == limit:
        return
    resp = requests.get('https://api.github.com/repos/{}/{}/git/trees/{}'.format(user, project, sha), headers={'Authorization': 'token {}'.format(OAUTH_TOKEN)})
    if resp.status_code == 200:
        resp = resp.json()
        tree = resp['tree']
        for content in tree:
            if len(files) == limit:
                    return
            if content['type'] == 'blob':
                files.append(content['path'])
            elif content['type'] == 'tree':
                dir_sha = content['sha']
                getProjectFilenamesRecursively(user, project, dir_sha, files, limit)

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

def getProjectFiles(user, project, limit):
    sha = getProjectLastCommit(user, project)
    files = []
    getProjectFilesRecursively(user, project, sha, files, limit)
    for i in range(len(files)):
        content = getFileContent(files[i]['url'])
        files[i]['content'] = content
    return files

def getProjectFilesRecursively(user, project, sha, files, limit):
    resp = requests.get('https://api.github.com/repos/{}/{}/git/trees/{}'.format(user, project, sha), headers={'Authorization': 'token {}'.format(OAUTH_TOKEN)})
    if resp.status_code == 200:
        resp = resp.json()
        tree = resp['tree']
        for content in tree:
            if len(files) == limit:
                    return
            if content['type'] == 'blob':
                files.append({'path': content['path'], 'url': content['url'], 'size': content['size'], 'sha': content['sha']})
            elif content['type'] == 'tree':
                dir_sha = content['sha']
                getProjectFilesRecursively(user, project, dir_sha, files, limit)

#print(getUserProjects('amandaghassaei'))
#print(getProjectFilenames('amandaghassaei', 'OrigamiSimulator', 6))
#print(getProjectFiles('amandaghassaei', 'OrigamiSimulator', 3))



apiKey = '811a31748544dd8d3a2d8a13785c2e78ffb2c351b5d56b37168ab6ff6315dc1f'

def saveProjectFilesToAzure(user, project, limit):
    def saveProjectFilesRecursively(user, project, sha, path, files, dirName, limit):
        #print('https://api.github.com/repos/{}/{}/git/trees/{}'.format(user, project, sha))
        resp = requests.get('https://api.github.com/repos/{}/{}/git/trees/{}'.format(user, project, sha), headers={'Authorization': 'token {}'.format(OAUTH_TOKEN)})  
        print(resp.status_code)
        if resp.status_code == 200:
            resp = resp.json()
            trees = []
            blobs = []
            for t in resp['tree']:
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
                print("here" + newPath)
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
    print('sha: ', sha)
    files = []
    dirName = '{}-{}'.format(user, project)
    t = threading.Thread(target=createDir, args=[ dirName])
    t.setDaemon(False)
    t.start()
    saveProjectFilesRecursively(user, project, sha, '', files, dirName, limit)
    return files

def saveProjectFilesToAzure2(user, project, limit):
    def saveProjectFilesRecursively2(user, project, path, files, dirName, limit):
        url = 'https://api.github.com/repos/{}/{}/contents/{}'.format(user, project, path)
        resp = requests.get(url, headers={'Authorization': 'token {}'.format(OAUTH_TOKEN)})  
        print(resp.status_code, resp.text)
        if resp.status_code == 200:
            resp = resp.json()
            dirs = []
            blobs = []
            for t in resp:
                if t['type'] == 'file':
                    blobs.append(t)
                elif t['type'] == 'dir':
                    dirs.append(t)
                else:
                    continue
            for content in blobs:
                if len(files) == limit:
                    return 1
                if content['name'] in [".gitignore", "LICENSE", "README.md"]:
                    continue
                files.append(content['path'])
                t = threading.Thread(target=getAzureFileReport, args=[user, project, content['path']])
                t.setDaemon(False)
                t.start()
                t = threading.Thread(target=saveFile, args=[content['path'].replace('/', '-'), getFileContent(content['_links']['git']), dirName])
                t.setDaemon(False)
                t.start()
            for content in dirs:
                if len(files) == limit:
                        return 1
                if saveProjectFilesRecursively2(user, project, content['path'], files, dirName, limit) == 1:
                    return 1
            return 0
    #print('sha: ', sha)
    files = []
    dirName = '{}-{}'.format(user, project)
    t = threading.Thread(target=createDir, args=[ dirName])
    t.setDaemon(False)
    t.start()
    saveProjectFilesRecursively2(user, project, '', files, dirName, limit)
    return files


class DoGithubRetrieve(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse(saveProjectFilesToAzure())

    def post(self, request, *args, **kwargs):
        user = request.POST.get("user", "nada")
        project = request.POST.get("project", "nada")
        files_limit = request.POST.get("files_limit", "nada")
        answer = saveProjectFilesToAzure2(user, project, int(files_limit))
      
        print(answer)
        return render(request, 'table_body.html', {'response':answer})

        
        
        
   


