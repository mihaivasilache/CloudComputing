import requests
import base64

#OAUTH_TOKEN = '2ace99f502776f620ddc23fae9cc3b2b42dd3631'
OAUTH_TOKEN = '47ca9f7f3de3f39b1055c8a37fb3bf7b95d3ebe8'

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
