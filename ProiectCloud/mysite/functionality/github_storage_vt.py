import requests
import base64
import hashlib
from getGithubFiles import getProjectLastCommit, getFileContent
from storageFunctionality import saveFile, createDir, getFile
import threading
import time

OAUTH_TOKEN = 'b7570a0f6b521d31d04368e7c35b0d5a105c12dd'
apiKey = '811a31748544dd8d3a2d8a13785c2e78ffb2c351b5d56b37168ab6ff6315dc1f'

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

def saveProjectFilesToAzure2(user, project, limit):
    def saveProjectFilesRecursively2(user, project, path, files, dirName, limit):
        url = 'https://api.github.com/repos/{}/{}/contents/{}'.format(user, project, path)
        resp = requests.get(url, headers={'Authorization': 'token {}'.format(OAUTH_TOKEN)})  
        #print(resp.status_code)
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

def getAzureFileReport(githubUser, githubProject, fileName):
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
    dirName = '{}-{}'.format(githubUser, githubProject)
    file_ = getFile(dirName, fileName.replace('\\', '-').replace('/', '-'))
    if file_ == None:
        return 'file not in azure'
    fileText = file_.content.encode('utf-8')
    f = True
    while f:
        report = getReportNoWait(fileName, fileText)
        if report in ['api limit', 'loading']:
            time.sleep(20)
            continue
        f = False
    if report['positives'] > report['total'] // 2:
        return 'infected'
    return 'clean'

if __name__ == '__main__':
    githubUser = 'amandaghassaei'
    githubProject = 'OrigamiSimulator'
    t = time.time()
    files = saveProjectFilesToAzure(githubUser, githubProject, 3)
    print(files)
    print(time.time() - t)
    t = time.time()
    files = saveProjectFilesToAzure2(githubUser, githubProject, 3)
    print(files)
    print(time.time() - t)
    #print(getAzureFileReport(githubUser, githubProject, files[5]))