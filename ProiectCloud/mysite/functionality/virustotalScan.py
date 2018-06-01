import requests
import hashlib
import time
import os

apiKey = '811a31748544dd8d3a2d8a13785c2e78ffb2c351b5d56b37168ab6ff6315dc1f'

def getReportWait(filePath, fileSha=None):
    if not fileSha:
        h = hashlib.sha1()
        with open(filePath, 'rb', buffering=0) as f:
            for b in iter(lambda : f.read(128*1024), b''):
                h.update(b)
        fileSha = h.hexdigest()
    resp = requests.post('https://www.virustotal.com/vtapi/v2/file/report?apikey={}&resource={}'.format(apiKey, fileSha))
    if resp.status_code == 204:
        time.sleep(30)
        return getReportWait(filePath, fileSha)
    if resp.status_code != 200:
        return None
    resp = resp.json()
    if resp['response_code'] == 1:
        return resp
    elif resp['response_code'] == -2:
        time.sleep(20)
        return getReportWait(filePath, fileSha)
    else:
        return scan(filePath, True)

def scan(filePath, wait=False):
    resp = requests.post('https://www.virustotal.com/vtapi/v2/file/scan?apikey={}'.format(apiKey), files={'file': (os.path.basename(filePath), open(filePath, 'rb'))})
    if resp.status_code == 204:
        return 'api limit'
    if resp.status_code != 200:
        return None
    resp = resp.json()
    if resp['response_code'] != 1:
        return None
    fileSha = resp['sha1']
    if wait == True:
        return getReportWait(filePath)
    return 'loading'
    
def getReportNoWait(filePath):
    h = hashlib.sha1()
    with open(filePath, 'rb', buffering=0) as f:
        for b in iter(lambda : f.read(128*1024), b''):
            h.update(b)
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
        return scan(filePath, False)

def getFileReport(filePath):
    f = True
    while f:
        report = getReportNoWait(filePath)
        if report in ['api limit', 'loading']:
            time.sleep(20)
            continue
        f = False
    if report['positives'] > report['total'] // 2:
        return 'infected'
    return 'clean'
        

filePath = ''
print(getFileReport(filePath))
