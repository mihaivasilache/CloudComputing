import http.server
import socketserver
import sqlite3
from http import HTTPStatus
import html
from sqlite3 import Error
import json
import urllib.parse
import datetime

CONFIG = json.load(open('config'))
db_conn = None


def create_database_connection(db_file):
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)


class MyHttpRequestHandler(http.server.BaseHTTPRequestHandler):
    global db_conn

    def send_error(self, code, message='', explain=''):
        message = message.replace("'", '').replace('"', '')
        content = ({
            'status': str(code.value),
            'message': html.escape(message, quote=False),
            'explain': explain
        })
        body = str(content).replace("'", '"').encode('UTF-8')
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self.end_headers()

        self.wfile.write(body)

    def send_result(self, query, should_respond=True, commit=True, is_get=False):
        try:
            db_result = db_conn.execute(query)
            if commit:
                db_conn.commit()
            if should_respond:
                db_result = db_result.fetchall()
                result = dict()
                result['results'] = list()
                if len(db_result) == 1:
                    if len(db_result[0]) > 1:
                        result['results'] = [[j for j in i if str(j) != ''] for i in db_result]
                    else:
                        result['results'] = [str(db_result[0][0])]
                else:
                    for item in db_result:
                        if len(item) > 1:
                            result['results'] += [[i for i in item]]
                        else:
                            result['results'] += [str(item[0])]

                result['status'] = str(HTTPStatus.OK.value)
                if is_get:
                    if len(result['results']) == 0:
                        self.send_response(HTTPStatus.NOT_FOUND)
                        self.send_error(HTTPStatus.NOT_FOUND)
                        return
                body = html.escape(str(result).replace("'", '"'), quote=False)
                body = body.encode('UTF-8')
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-type", 'application/json')
                self.send_header("Content-Length", len(body))
                self.end_headers()
                self.wfile.write(body)
        except sqlite3.OperationalError as e:
            print(e)
            self.send_response(HTTPStatus.NOT_FOUND, e.__str__())
            self.send_error(HTTPStatus.NOT_FOUND, e.__str__())
            raise Exception
        except sqlite3.IntegrityError as e:
            print(e)
            self.send_response(HTTPStatus.UNPROCESSABLE_ENTITY, e.__str__())
            self.send_error(HTTPStatus.UNPROCESSABLE_ENTITY, e.__str__())
            raise Exception
        except Exception as e:
            print(e.__cause__, e)
            self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR, e.__str__())
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, e.__str__())
            raise Exception

    def parse_url(self, url):
        parts = urllib.parse.urlsplit(url)
        url_params = dict()
        if parts[2] == '/':
            url_params = urllib.parse.parse_qs(parts[3])
        else:
            url_items = parts[2].split('/')
            if len(url_items) > 4:
                self.send_response(HTTPStatus.BAD_REQUEST)
                self.send_error(HTTPStatus.BAD_REQUEST)
                raise Exception
            url_params['table'] = [url_items[1]]
            if len(url_items) > 2 and url_items[2] != '':
                url_params['id'] = [url_items[2].replace('%20', ' ')]
            temp_url_params = urllib.parse.parse_qs(parts[3])
            for i in temp_url_params:
                if i in list(url_params.keys()):
                    self.send_response(HTTPStatus.BAD_REQUEST)
                    self.send_error(HTTPStatus.BAD_REQUEST)
                    raise Exception
                else:
                    url_params[i] = temp_url_params[i]
        for key in url_params:
            if len(url_params[key]) > 1:
                self.send_response(HTTPStatus.BAD_REQUEST)
                self.send_error(HTTPStatus.BAD_REQUEST)
                raise Exception
            else:
                url_params[key] = url_params[key][0]
        if 'date' in url_params.keys():
            try:
                datetime.datetime.strptime(url_params['date'], '%d-%m-%Y')
            except Exception as e:
                self.send_response(HTTPStatus.BAD_REQUEST, e.__str__().replace("'", '').replace('"', ''))
                self.send_error(HTTPStatus.BAD_REQUEST, e.__str__().replace("'", '').replace('"', ''))
                raise Exception
        return url_params

    def load_rfile_json_post(self, must_contain):
        if self.headers['Content-Type'] != 'application/json':
            self.send_response(HTTPStatus.BAD_REQUEST, 'body is not json')
            self.send_error(HTTPStatus.BAD_REQUEST, 'body is not json')
            raise Exception
        try:
            content_json = json.loads(self.rfile.read(int(self.headers['content-length'])))
        except Exception:
            self.send_response(HTTPStatus.BAD_REQUEST)
            self.send_error(HTTPStatus.BAD_REQUEST)
            raise Exception
        for key in must_contain:
            if key not in content_json.keys():
                self.send_response(HTTPStatus.BAD_REQUEST, '%s not in json' % key)
                self.send_error(HTTPStatus.BAD_REQUEST, '%s not in json' % key)
                raise Exception
        if 'date' in content_json.keys():
            try:
                datetime.datetime.strptime(content_json['date'], '%d-%m-%Y')
            except Exception as e:
                self.send_response(HTTPStatus.BAD_REQUEST, e.__str__().replace("'", '').replace('"', ''))
                self.send_error(HTTPStatus.BAD_REQUEST, e.__str__().replace("'", '').replace('"', ''))
                raise Exception
        return content_json

    def load_rfile_json_put(self, dict_must_contain, items_must_contain):
        if self.headers['Content-Type'] != 'application/json':
            self.send_response(HTTPStatus.BAD_REQUEST, 'body is not json')
            self.send_error(HTTPStatus.BAD_REQUEST, 'body is not json')
            raise Exception
        try:
            content_json = json.loads(self.rfile.read(int(self.headers['content-length'])))
        except Exception:
            self.send_response(HTTPStatus.BAD_REQUEST)
            self.send_error(HTTPStatus.BAD_REQUEST)
            raise Exception
        for key in dict_must_contain:
            if key not in content_json.keys():
                self.send_response(HTTPStatus.BAD_REQUEST, '%s not in json' % key)
                self.send_error(HTTPStatus.BAD_REQUEST, '%s not in json' % key)
                raise Exception
        for item in content_json['items']:
            for must_item in items_must_contain:
                if must_item not in item.keys():
                    self.send_response(HTTPStatus.BAD_REQUEST, '%s not in json' % must_item)
                    self.send_error(HTTPStatus.BAD_REQUEST, '%s not in json' % must_item)
                    raise Exception
            if 'date' in item.keys():
                try:
                    datetime.datetime.strptime(item['date'], '%d-%m-%Y')
                except Exception as e:
                    self.send_response(HTTPStatus.BAD_REQUEST, e.__str__().replace("'", '').replace('"', ''))
                    self.send_error(HTTPStatus.BAD_REQUEST, e.__str__().replace("'", '').replace('"', ''))
                    raise Exception
        return content_json

    def do_GET(self):
        try:
            try:
                url_params = self.parse_url(self.path)
            except Exception as e:
                print('Error', e)
                if e.__str__() != '':
                    raise
                return

            if ['table'] == sorted(list(url_params.keys())):
                query = '''select id from %s''' % (url_params['table'])
                try:
                    self.send_result(query)
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return

            elif ['id', 'table'] == sorted(list(url_params.keys())):
                query = '''select * from %s where id like "%s"''' \
                        % (url_params['table'], url_params['id'])
                try:
                    self.send_result(query, is_get=True)
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
            elif ['rating', 'table'] == sorted(list(url_params.keys())):
                query = '''select * from %s where rating >= %f''' \
                        % (url_params['table'], float(url_params['rating']))
                try:
                    self.send_result(query, is_get=True)
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
            elif ['id', 'rating', 'table'] == sorted(list(url_params.keys())):
                query = '''select * from %s where id like "%s" and rating = %f''' \
                        % (url_params['table'], url_params['id'],
                           float(url_params['rating']))
                try:
                    self.send_result(query, is_get=True)
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
            elif ['date', 'table'] == sorted(list(url_params.keys())):
                query = '''select * from %s where date >= "%s"''' \
                        % (url_params['table'], url_params['date'])
                try:
                    self.send_result(query, is_get=True)
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
            elif ['date', 'rating', 'table'] == sorted(list(url_params.keys())):
                query = '''select * from %s where date >= "%s" and rating >= %f''' \
                        % (url_params['table'], url_params['date'], float(url_params['rating']))
                try:
                    self.send_result(query, is_get=True)
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
            elif ['date', 'id', 'table'] == sorted(list(url_params.keys())):
                query = '''select * from %s where date = "%s" and id = "%s"''' \
                        % (url_params['table'], url_params['date'], url_params['id'])
                try:
                    self.send_result(query, is_get=True)
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
            elif ['date', 'id', 'rating', 'table'] == sorted(list(url_params.keys())):
                query = '''select * from %s where date = "%s" and rating = %f and id = "%s"''' \
                        % (url_params['table'], url_params['date'], float(url_params['rating']),
                           url_params['id'])
                try:
                    self.send_result(query, is_get=True)
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
            else:
                self.send_response(HTTPStatus.BAD_REQUEST, 'Incorrect parameters!')
                self.send_error(HTTPStatus.BAD_REQUEST, 'Incorrect parameters!')
                return
        except Exception as e:
            print(e)
            self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR)
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR)
            return

    def do_POST(self):
        try:
            try:
                url_params = self.parse_url(self.path)
            except Exception as e:
                print('Error', e)
                if e.__str__() != '':
                    raise
                return
            if ['table'] == sorted(list(url_params.keys())):
                try:
                    content_json = self.load_rfile_json_post(['id', 'date', 'rating'])
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
                query = '''insert into %s values("%s", "%s", %f) ''' \
                        % (url_params['table'], content_json['id'], content_json['date'],
                           float(content_json['rating']))
                try:
                    self.send_result(query, should_respond=False)
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
                query = '''select * from %s where date = "%s" and rating = %f and id = "%s"''' \
                        % (url_params['table'], content_json['date'], float(content_json['rating']),
                           content_json['id'])
                try:
                    self.send_result(query)
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
            elif ['id', 'table'] == sorted(list(url_params.keys())):
                try:
                    content_json = self.load_rfile_json_post(['date', 'rating'])
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
                query = '''insert into %s values("%s", "%s", %f) ''' \
                        % (url_params['table'], url_params['id'], content_json['date'],
                           float(content_json['rating']))
                try:
                    self.send_result(query, should_respond=False)
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
                query = '''select * from %s where date = "%s" and rating = %f and id = "%s"''' \
                        % (url_params['table'], content_json['date'], float(content_json['rating']),
                           url_params['id'])
                try:
                    self.send_result(query)
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
            elif ['rating', 'table'] == sorted(list(url_params.keys())):
                query = '''select * from %s where rating >= %f''' \
                        % (url_params['table'], float(url_params['rating']))
                try:
                    self.send_result(query)
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
            elif ['id', 'rating', 'table'] == sorted(list(url_params.keys())):
                query = '''select * from %s where id like "%s" and rating = %f''' \
                        % (url_params['table'], url_params['id'],
                           float(url_params['rating']))
                try:
                    self.send_result(query)
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
            elif ['date', 'table'] == sorted(list(url_params.keys())):
                query = '''select * from %s where date >= "%s"''' \
                        % (url_params['table'], url_params['date'])
                try:
                    self.send_result(query)
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
            elif ['date', 'rating', 'table'] == sorted(list(url_params.keys())):
                query = '''select * from %s where date >= "%s" and rating >= %f''' \
                        % (url_params['table'], url_params['date'], float(url_params['rating']))
                try:
                    self.send_result(query)
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
            elif ['date', 'id', 'table'] == sorted(list(url_params.keys())):
                query = '''select * from %s where date = "%s" and id = "%s"''' \
                        % (url_params['table'], url_params['date'], url_params['id'])
                try:
                    self.send_result(query)
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
            elif ['date', 'id', 'rating', 'table'] == sorted(list(url_params.keys())):
                query = '''select * from %s where date = "%s" and rating = %f and id = "%s"''' \
                        % (url_params['table'], url_params['date'], float(url_params['rating']),
                           url_params['id'])
                try:
                    self.send_result(query)
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
            else:
                self.send_response(HTTPStatus.BAD_REQUEST, 'Incorrect parameters!')
                self.send_error(HTTPStatus.BAD_REQUEST, 'Incorrect parameters!')
                return
        except Exception as e:
            print(e)
            self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR)
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR)
            return

    def do_PUT(self):
        try:
            try:
                url_params = self.parse_url(self.path)
            except Exception as e:
                print('Error', e)
                if e.__str__() != '':
                    raise
                return
            if len(list(url_params.keys())) == 0:
                try:
                    content_json = self.load_rfile_json_put(['replace_table_name', 'items'], ['id', 'date', 'rating'])
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return

                query = '''create table %s (id text unique, date date, rating integer)''' % \
                        content_json['replace_table_name']
                try:
                    self.send_result(query, should_respond=False)
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return

                for item in content_json['items']:
                    query = '''insert into %s values("%s", "%s", %f) ''' \
                            % (content_json['replace_table_name'], item['id'], item['date'],
                               float(item['rating']))
                    try:
                        self.send_result(query, should_respond=False)
                    except Exception as e:
                        print('Error', e)
                        if e.__str__() != '':
                            raise
                        return

                query = '''select id from %s ''' % (content_json['replace_table_name'])
                try:
                    self.send_result(query)
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
            elif ['table'] == sorted(list(url_params.keys())):
                try:
                    content_json = self.load_rfile_json_put(['replace_table_name', 'items'], ['id', 'date', 'rating'])
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
                query = '''drop table %s''' % url_params['table']
                try:
                    self.send_result(query, should_respond=False)
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
                query = '''create table %s (id text unique, date date, rating integer)''' % \
                        content_json['replace_table_name']
                try:
                    self.send_result(query, should_respond=False)
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return

                for item in content_json['items']:
                    query = '''insert into %s values("%s", "%s", %f) ''' \
                            % (content_json['replace_table_name'], item['id'], item['date'],
                               float(item['rating']))
                    try:
                        self.send_result(query, should_respond=False)
                    except Exception as e:
                        print('Error', e)
                        if e.__str__() != '':
                            raise
                        return

                query = '''select id from %s ''' % (content_json['replace_table_name'])
                try:
                    self.send_result(query)
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
            elif ['id', 'table'] == sorted(list(url_params.keys())):
                try:
                    content_json = self.load_rfile_json_put(['items'], ['date', 'rating'])
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
                query = '''replace into %s(id, date, rating) values("%s" ,"%s", %f)''' \
                        % (url_params['table'], url_params['id'], content_json['items'][0]['date'],
                           float(content_json['items'][0]['rating']))
                try:
                    self.send_result(query)
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
            elif ['rating', 'table'] == sorted(list(url_params.keys())):
                try:
                    content_json = self.load_rfile_json_put(['items'], ['date', 'id'])
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
                query = '''replace into %s(id, date, rating) values("%s" ,"%s", %f)''' \
                        % (url_params['table'], content_json['items'][0]['id'], content_json['items'][0]['date'],
                           float(url_params['rating']))
                try:
                    self.send_result(query)
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
            elif ['id', 'rating', 'table'] == sorted(list(url_params.keys())):
                try:
                    content_json = self.load_rfile_json_put(['items'], ['date'])
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
                query = '''replace into %s(id, date, rating) values("%s" ,"%s", %f)''' \
                        % (url_params['table'], url_params['id'], content_json['items'][0]['date'],
                           float(url_params['rating']))
                try:
                    self.send_result(query)
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
            elif ['date', 'table'] == sorted(list(url_params.keys())):
                try:
                    content_json = self.load_rfile_json_put(['items'], ['rating', 'id'])
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
                query = '''replace into %s(id, date, rating) values("%s" ,"%s", %f)''' \
                        % (url_params['table'], content_json['items'][0]['id'], url_params['date'],
                           float(content_json['items'][0]['rating']))
                try:
                    self.send_result(query)
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
            elif ['date', 'rating', 'table'] == sorted(list(url_params.keys())):
                try:
                    content_json = self.load_rfile_json_put(['items'], ['id'])
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
                query = '''replace into %s(id, date, rating) values("%s" ,"%s", %f)''' \
                        % (url_params['table'], content_json['items'][0]['id'], url_params['date'],
                           float(url_params['rating']))
                try:
                    self.send_result(query)
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
            elif ['date', 'id', 'table'] == sorted(list(url_params.keys())):
                try:
                    content_json = self.load_rfile_json_put(['items'], ['rating'])
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
                query = '''replace into %s(id, date, rating) values("%s" ,"%s", %f)''' \
                        % (url_params['table'], url_params['id'], url_params['date'],
                           float(content_json['items'][0]['rating']))
                try:
                    self.send_result(query)
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
            elif ['date', 'id', 'rating', 'table'] == sorted(list(url_params.keys())):
                query = '''replace into %s(id, date, rating) values("%s" ,"%s", %f)''' \
                        % (url_params['table'], url_params['id'], url_params['date'],
                           float(url_params['rating']))
                try:
                    self.send_result(query)
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
            else:
                self.send_response(HTTPStatus.BAD_REQUEST, 'Incorrect parameters!')
                self.send_error(HTTPStatus.BAD_REQUEST, 'Incorrect parameters!')
                return
        except:
            self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR)
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR)
            return

    def do_DELETE(self):
        try:
            try:
                url_params = self.parse_url(self.path)
            except Exception as e:
                print('Error', e)
                if e.__str__() != '':
                    raise
                return

            if ['table'] == sorted(list(url_params.keys())):
                query = '''drop table %s''' % (url_params['table'])
                try:
                    self.send_result(query)
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
            elif ['id', 'table'] == sorted(list(url_params.keys())):
                query = '''delete from %s where id like "%s"''' \
                        % (url_params['table'], url_params['id'])
                try:
                    self.send_result(query)
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
            elif ['rating', 'table'] == sorted(list(url_params.keys())):
                query = '''delete from %s where rating >= %f''' \
                        % (url_params['table'], float(url_params['rating']))
                try:
                    self.send_result(query)
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
            elif ['id', 'rating', 'table'] == sorted(list(url_params.keys())):
                query = '''delete from %s where id like "%s" and rating = %f''' \
                        % (url_params['table'], url_params['id'],
                           float(url_params['rating']))
                try:
                    self.send_result(query)
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
            elif ['date', 'table'] == sorted(list(url_params.keys())):
                query = '''delete from %s where date >= "%s"''' \
                        % (url_params['table'], url_params['date'])
                try:
                    self.send_result(query)
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
            elif ['date', 'rating', 'table'] == sorted(list(url_params.keys())):
                query = '''delete from %s where date >= "%s" and rating >= %f''' \
                        % (url_params['table'], url_params['date'], float(url_params['rating']))
                try:
                    self.send_result(query)
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
            elif ['date', 'id', 'table'] == sorted(list(url_params.keys())):
                query = '''delete from %s where date = "%s" and id = "%s"''' \
                        % (url_params['table'], url_params['date'], url_params['id'])
                try:
                    self.send_result(query)
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
            elif ['date', 'id', 'rating', 'table'] == sorted(list(url_params.keys())):
                query = '''delete from %s where date = "%s" and rating = %f and id = "%s"''' \
                        % (url_params['table'], url_params['date'], float(url_params['rating']),
                           url_params['id'])
                try:
                    self.send_result(query)
                except Exception as e:
                    print('Error', e)
                    if e.__str__() != '':
                        raise
                    return
            else:
                self.send_response(HTTPStatus.BAD_REQUEST, 'Incorrect parameters!')
                self.send_error(HTTPStatus.BAD_REQUEST, 'Incorrect parameters!')
                return
        except Exception as e:
            print(e)
            self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR)
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR)
            return


def open_server():
    port = 8000
    handler = MyHttpRequestHandler
    httpd = socketserver.TCPServer(("", port), handler)
    httpd.serve_forever()
    return httpd


def populate_db():
    global db_conn
    db_conn.execute('''drop table movie''')
    db_conn.execute('''create table movie (id text unique, date date, rating integer)''')
    db_conn.execute('''insert into movie values ('Movie 1', '12-12-2017', 3)''')
    db_conn.execute('''insert into movie values ('Movie 2', '11-12-2017', 2)''')

    db_conn.execute('''drop table music''')
    db_conn.execute('''create table music (id text unique, date date, rating integer)''')
    db_conn.execute('''insert into music values ('Song 1', '10-12-2017', 5)''')
    # db_conn.execute('''insert into music values ('Song 2', '13-12-2017', 1)''')
    db_conn.commit()


if __name__ == '__main__':
    db_conn = create_database_connection(CONFIG['db_path'])
    populate_db()
    httpd = open_server()
