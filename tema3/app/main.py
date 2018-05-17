# import os
# import json
# from flask import Flask, request, session, redirect, url_for
# import storage
# import datastore
# import google.cloud.logging
# import google.oauth2.credentials
# from flask_oauth import OAuth
# import json
# 
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'app.json'
# CONFIG = json.load(open('client_json.json'))
# CLOUD_STORAGE_BUCKET = 'tema-cloud3.appspot.com'
# GOOGLE_CLIENT_ID = CONFIG['web']['client_id']
# GOOGLE_CLIENT_SECRET = CONFIG['web']['client_secret']
# REDIRECT_URI = '/auth'
# SECRET_KEY = 'AIzaSyAcgsLVd26JLnZW3SyvszXgZ3WJJbI8OxA'
# DEBUG = True
# 
# storage_client = None
# datastore_client = None
# logger = None
# project_id = 'tema-cloud3'
# 
# app = Flask(__name__)
# app.debug = DEBUG
# app.secret_key = SECRET_KEY
# oauth = OAuth()
# 
# google_auth = oauth.remote_app('tema-cloud3',
#                                base_url='https://www.google.com/accounts/',
#                                authorize_url='https://accounts.google.com/o/oauth2/auth',
#                                request_token_url=None,
#                                request_token_params={'scope': 'https://www.googleapis.com/auth/cloud-platform',
#                                                      'response_type': 'code'},
#                                access_token_url='https://accounts.google.com/o/oauth2/token',
#                                access_token_method='POST',
#                                access_token_params={'grant_type': 'authorization_code'},
#                                consumer_key=GOOGLE_CLIENT_ID,
#                                consumer_secret=GOOGLE_CLIENT_SECRET)
# 
# 
# @app.route('/upload', methods=['POST'])
# def upload():
#     logger.log_text('Request for /upload')
#     uploaded_file = request.files.get('file')
#     datastore.insert(datastore_client, uploaded_file)
#     if not uploaded_file:
#         return 'No file uploaded.', 400
#     return storage.upload_file(storage_client, uploaded_file)
# 
# 
# @app.route('/list', methods=['GET'])
# def list_files():
#     logger.log_text('Request for /list')
#     access_token = session.get('access_token')
#     logger.log_text('Request for /home')
#     if access_token is None:
#         return redirect(url_for('login'))
# 
#     files = []
#     creds = google.oauth2.credentials.Credentials(session.get('access_token')[0])
#     datastore_client = datastore.get_client(creds)
#     print creds
#     for file in datastore.list_files(datastore_client):
#         file_ = {}
#         items = file.items()
#         for item in items:
#             if item[0] == 'added':
#                 file_[item[0]] = str(item[1])
#             else:
#                 file_[item[0]] = str(item[1])
#         files.append(file_)
#     # storage_files = storage.list_blobs(storage_client)
#     # print 'in storage: ', storage_files
#     print 'in datastore: ', files
#     return json.dumps(files)
# 
# 
# @app.route('/delete', methods=['DELETE'])
# def delete_files():
#     return datastore.delete_files(datastore_client)
# 
# 
# @app.route('/login')
# def login():
#     callback = url_for('authorized', _external=True)
#     return google_auth.authorize(callback=callback)
# 
# 
# @app.route(REDIRECT_URI)
# @google_auth.authorized_handler
# def authorized(resp):
#     print 'resp', resp
#     access_token = resp['access_token']
#     print 'access_token', access_token
#     session['access_token'] = access_token, ''
#     return redirect(url_for('hello'))
# 
# 
# @google_auth.tokengetter
# def get_access_token():
#     return session.get('access_token')
# 
# 
# @app.route('/')
# def redirect_home():
#     return redirect(url_for('hello'))
# 
# 
# @app.route('/home')
# def hello():
#     access_token = session.get('access_token')
#     logger.log_text('Request for /home')
#     if access_token is None:
#         return redirect(url_for('login'))
# 
#     # access_token = access_token[0]
#     # from urllib2 import Request, urlopen, URLError
#     #
#     # headers = {'Authorization': 'OAuth ' + access_token}
#     # req = Request('https://www.googleapis.com/oauth2/v1/userinfo',
#     #               None, headers)
#     # try:
#     #     res = urlopen(req)
#     # except URLError as e:
#     #     if e.code == 401:
#     #         # Unauthorized - bad token
#     #         session.pop('access_token', None)
#     #         return redirect(url_for('login'))
#     #     return 'Error'
# 
#     return 'Hello World!', 200
# 
# 
# @app.errorhandler(500)
# def server_error(e):
#     logger.log_text('An error occurred during a request.')
#     return "An internal error occurred: <pre>{}</pre>See logs for full stacktrace.".format(e), 500
# 
# 
# @app.before_first_request
# def execute_this():
#     global logger, storage_client, datastore_client
#     logging_client = google.cloud.logging.Client(project_id)
#     log_name = 'my-log'
#     logger = logging_client.logger(log_name)
#     storage_client = storage.get_client()
#     # datastore_client = datastore.get_client()
#     if 'access_token' in session:
#         del session['access_token']
# 
# 
# '''
# def main(environ, start_response):
# 	app.run(host='127.0.0.1', port=8000, debug=True)
# '''
# if __name__ == '__main__':
#     app.run(host='127.0.0.1', port=8000, debug=True)
import os
import json
from flask import Flask, request
import storage
import datastore
import google.cloud.logging
import flask
import requests
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'app.json'
CLOUD_STORAGE_BUCKET = 'tema-cloud3.appspot.com'
storage_client = None
datastore_client = None
logger = None
project_id = 'tema-cloud3'
os.environ['DEBUG'] = '1'
CLIENT_SECRETS_FILE = "client_json.json"
SCOPES = ['https://www.googleapis.com/auth/drive']
API_SERVICE_NAME = 'drive'
API_VERSION = 'v3'
app = flask.Flask(__name__)
app.debug = True
app.secret_key = 'secret_key'


@app.route('/')
def index():
    return print_index()


@app.route('/list_drive')
def list_files_drive():
    if 'credentials' not in flask.session:
        return flask.redirect('authorize')
    credentials = google.oauth2.credentials.Credentials(
        **flask.session['credentials'])
    drive = googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials)
    files = drive.files().list(pageSize=10, fields="nextPageToken, files(id, name)").execute()
    flask.session['credentials'] = credentials_to_dict(credentials)
    return flask.jsonify(**files)


@app.route('/metadata/<fileID>')
def print_file_metadata(fileID):
    if 'credentials' not in flask.session:
        return flask.redirect('authorize')
    credentials = google.oauth2.credentials.Credentials(
        **flask.session['credentials'])
    drive = googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials)
    file = drive.files().get(fileId=fileID).execute()
    flask.session['credentials'] = credentials_to_dict(credentials)
    return flask.jsonify(**file)


@app.route('/content/<fileID>')
def print_file_content(fileID):
    if 'credentials' not in flask.session:
        return flask.redirect('authorize')
    credentials = google.oauth2.credentials.Credentials(
        **flask.session['credentials'])
    drive = googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials)
    file = drive.files().get_media(fileId=fileID).execute()
    flask.session['credentials'] = credentials_to_dict(credentials)
    return file


@app.route('/import/<fileID>')
def import_file(fileID):
    if 'credentials' not in flask.session:
        return flask.redirect('authorize')
    credentials = google.oauth2.credentials.Credentials(
        **flask.session['credentials'])
    drive = googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials)
    file = drive.files().get_media(fileId=fileID).execute()
    flask.session['credentials'] = credentials_to_dict(credentials)
    return file


@app.route('/authorize')
def authorize():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES)
    flow.redirect_uri = flask.url_for('auth', _external=True)
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true')
    flask.session['state'] = state
    print authorization_url
    return flask.redirect(authorization_url)


@app.route('/auth')
def auth():
    state = flask.session['state']
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = flask.url_for('auth', _external=True)
    authorization_response = flask.request.url  # .replace('http', 'https')
    print authorization_response
    flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials
    flask.session['credentials'] = credentials_to_dict(credentials)
    return flask.redirect(flask.url_for('list_files_drive'))


@app.route('/clear')
def clear_credentials():
    if 'credentials' in flask.session:
        del flask.session['credentials']
    return ('Credentials have been cleared.<br><br>' + print_index())


@app.route('/upload', methods=['POST'])
def upload():
    logger.log_text('Request for /upload')
    uploaded_file = request.files.get('file')
    datastore.insert(datastore_client, uploaded_file)
    if not uploaded_file:
        return 'No file uploaded.', 400
    return storage.upload_file(storage_client, uploaded_file)


@app.route('/list', methods=['GET'])
def list_files():
    logger.log_text('Request for /list')
    files = []
    for file in datastore.list_files(datastore_client):
        file_ = {}
        items = file.items()
        for item in items:
            if item[0] == 'added':
                file_[item[0]] = str(item[1])
            else:
                file_[item[0]] = item[1]
        files.append(file_)
    storage_files = storage.list_blobs(storage_client)
    print 'in storage: ', storage_files
    print 'in datastore: ', files
    return json.dumps(files, indent=4, sort_keys=True, default=str)


@app.route('/delete', methods=['DELETE'])
def delete_files():
    return datastore.delete(datastore_client)


'''
@app.route('/')
def hello():
    logger.log_text('Request for /')
    return 'Hello World!', 200
'''


@app.errorhandler(500)
def server_error(e):
    logger.log_text('An error occurred during a request.')
    return "An internal error occurred: <pre>{}</pre>See logs for full stacktrace.".format(e), 500


@app.before_first_request
def execute_this():
    global logger, storage_client, datastore_client
    logging_client = google.cloud.logging.Client(project_id)
    log_name = 'my-log'
    logger = logging_client.logger(log_name)
    storage_client = storage.get_client()
    datastore_client = datastore.get_client()
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


def credentials_to_dict(credentials):
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}


def print_index():
    return ('<table>' +
            '<tr><td><a href="/list_drive">List</a></td>' +
            '<td>&nbsp;&nbsp;&nbsp;&nbsp;Listeaza toate fisierele din Drive ' +
            '    </td></tr>' +
            '<tr><td>/import/fileID</td>' +
            '<td>&nbsp;&nbsp;&nbsp;&nbsp;Importa un fisier din drive' +
            '    </td></tr>' +
            '<tr><td>/metadata/fileID</td>' +
            '<td>&nbsp;&nbsp;&nbsp;&nbsp;Afiseaza metadatele unui fisier din drive' +
            '    </td></tr>' +
            '<tr><td>/content/fileID</td>' +
            '<td>&nbsp;&nbsp;&nbsp;&nbsp;Afiseaza continutul unui fisier din drive' +
            '    </td></tr>')


'''
def main(environ, start_response):
    app.run(host='127.0.0.1', port=8000, debug=True)
'''
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)
