import time

from flask import Flask, flash, redirect, render_template, request, session, abort, url_for, send_file, \
    after_this_request, Markup

import os
import pyodbc
from hashlib import md5
from azure.storage.file import FileService, ContentSettings
import urllib2
import json

file_service = FileService(account_name='cs7b04dc31e3552x4267x9c3',
                           account_key='ihwu6KLKRkUv3/dF3ELyhqbsB34jUJGyyVexD3gr2PUhcL3X5XFg/aFumVEHZCUHqqfP+m2UBM1Lni3uw26WcA==')

file_service.create_share('fileshare')
app = Flask(__name__)

app.secret_key = os.urandom(12)


def http_post(url, data):
    req = urllib2.Request(url)
    req.add_header('Content-Type', 'application/json')
    response = urllib2.urlopen(req, json.dumps(data))
    return response.read().replace('\\r', '').replace('\\n', '').replace('"', "")


def connect_to_db():
    print 'Connecting to db...'
    conn = pyodbc.connect(
        'Driver={ODBC Driver 13 for SQL Server};Server=tcp:tema4.database.windows.net,1433;'
        'Database=tema4;Uid=tema4@tema4;Pwd={parola1234!};Encrypt=yes;'
        'TrustServerCertificate=no;Connection Timeout=30;')
    print 'Connected!'
    return conn


def create_table_users():
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("Create table Users (id INT IDENTITY PRIMARY KEY, username NVARCHAR(128) NOT NULL, "
                   "password NVARCHAR(32) NOT NULL)")
    conn.close()


@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        files = get_files(session['user'])
        # print files
        return render_template('home.html', files=files)


@app.route('/login', methods=['POST'])
def login():
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute('Select password from Users where username = ?', request.form['username'])
    result = cursor.fetchone()
    if result is None or result is '':
        flash('Invalid username')
        return home()
    else:
        result = result[0]
    cursor.close()
    conn.close()
    password_md5 = md5(request.form['password']).hexdigest()
    if password_md5 == result:
        session['logged_in'] = True
        session['user'] = request.form['username']
    else:
        flash('wrong password!')
    return home()


@app.route('/signup')
def sign_up_render():
    return render_template('signup.html')


@app.route('/signupadd', methods=['POST'])
def sign_up():
    conn = connect_to_db()
    cursor = conn.cursor()
    print request.form['password'], request.form['username']
    password_md5 = md5(request.form['password']).hexdigest()
    if request.form['password'] == '' or request.form['username'] == '':
        flash('Password and username cannot be empty!')
        cursor.close()
        conn.close()
        return redirect('/signup')
    try:
        cursor.execute('Insert into Users (username, password) values (?,?)', request.form['username'], password_md5)
    except:
        flash('User already exists')
        cursor.close()
        conn.close()
        return redirect('/signup')
    cursor.commit()
    cursor.close()
    conn.close()
    flash("Account created!")
    return redirect('/')


@app.route("/logout")
def logout():
    session['logged_in'] = False
    session['user'] = None
    return home()


@app.route("/upload", methods=['POST'])
def upload():
    if not session['user']:
        return render_template('login.html')
    file_service.create_directory('fileshare', session['user'])
    uploaded_file = request.files.get('file')
    file_service.create_file_from_text('fileshare', session['user'],
                                       uploaded_file.filename + str(int(time.time())),
                                       unicode(uploaded_file.read(), errors='ignore'),
                                       content_settings=ContentSettings(content_type=uploaded_file.content_type))
    return redirect(url_for('home'))


def get_files(user):
    files = []
    try:
        generator = file_service.list_directories_and_files('fileshare', user)
        for file_or_dir in generator:
            files.append(file_or_dir.name)
    except:
        files = []
    return files


@app.route("/download", methods=['POST'])
def download():
    file = file_service.get_file_to_text('fileshare', session['user'], request.form['file_to_download'])
    temp_path = file.name
    with open(temp_path, 'w') as f:
        f.write(file.content)
    file_handle = open(temp_path, 'r')
    return send_file(file_handle, as_attachment=True, attachment_filename=temp_path)


@app.route("/delete", methods=['POST'])
def delete():
    file_service.delete_file('fileshare', session['user'], request.form['file_to_delete'])
    return redirect('/')


@app.route("/execute_python", methods=['POST'])
def execute_python():
    to_run_file = file_service.get_file_to_text('fileshare', session['user'], request.form['file_to_execute'])
    print {"script": to_run_file.content}
    r = http_post(
        "https://functiontema4.azurewebsites.net/api/HttpTriggerPython31?code=eylPtyCqCAGGDSdx9tALdC2ws8LnLMc3zErCjLcausFY1lCTbdXQMQ==",
        {"script": to_run_file.content})
    flash(Markup(r))
    return redirect('/')


if __name__ == '__main__':
    app.run()
