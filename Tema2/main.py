import http.server
import socketserver
import sqlite3
from http import HTTPStatus
import html
from sqlite3 import Error
import json
import urllib.parse

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

    def send_error(self, code, message=None, explain=None):
        content = ({
            'code': str(code.value),
            'message': html.escape(message, quote=False),
            'explain': ''
        })
        body = str(content).replace("'", '"').encode('UTF-8')
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self.end_headers()

        self.wfile.write(body)

    def send_result(self, query, should_respond=True):
        try:
            db_result = db_conn.execute(query)
            db_conn.commit()
            if should_respond:
                db_result = db_result.fetchall()
                result = dict()
                result['results'] = list()
                if len(db_result) == 1:
                    if len(db_result[0]) > 1:
                        result['results'] = [[j for j in i if str(j) != ''] for i in db_result]
                    else:
                        result['results'] = [str(db_result[0])]
                else:
                    for item in db_result:
                        if len(item) > 1:
                            result['results'] += [[i for i in item]]
                        else:
                            result['results'] += [str(item[0])]

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
            return
        except sqlite3.IntegrityError as e:
            print(e)
            self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR, e.__str__())
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, e.__str__())
            return
        except Exception as e:
            print(e.__cause__, e)
            self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR, e.__str__())
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, e.__str__())
            return

    def do_GET(self):
        parts = urllib.parse.urlsplit(self.path)
        if parts[2] != '/':
            self.send_response(HTTPStatus.NOT_FOUND, 'Path not found!')
            self.send_error(HTTPStatus.NOT_FOUND, 'Path not found!')
            return
        url_params = urllib.parse.parse_qs(parts[3])

        for key in url_params:
            if len(url_params[key]) > 1:
                self.send_response(HTTPStatus.BAD_REQUEST)
                self.send_error(HTTPStatus.BAD_REQUEST)
                return
            else:
                url_params[key] = url_params[key][0]
        if ['table'] == sorted(list(url_params.keys())):
            query = '''select id from %s''' % (url_params['table'])
            self.send_result(query)

        elif ['id', 'table'] == sorted(list(url_params.keys())):
            query = '''select * from %s where id like "%s"''' \
                    % (url_params['table'], url_params['id'])
            self.send_result(query)
        elif ['rating', 'table'] == sorted(list(url_params.keys())):
            query = '''select id, rating from %s where rating >= %f''' \
                    % (url_params['table'], float(url_params['rating']))
            self.send_result(query)
        elif ['id', 'rating', 'table'] == sorted(list(url_params.keys())):
            query = '''select * from %s where id like "%s" and rating = %f''' \
                    % (url_params['table'], url_params['id'],
                       float(url_params['rating']))
            self.send_result(query)
        elif ['date', 'table'] == sorted(list(url_params.keys())):
            query = '''select * from %s where date >= "%s"''' \
                    % (url_params['table'], url_params['date'])
            self.send_result(query)
        elif ['date', 'rating', 'table'] == sorted(list(url_params.keys())):
            query = '''select * from %s where date >= "%s" and rating >= %f''' \
                    % (url_params['table'], url_params['date'], float(url_params['rating']))
            self.send_result(query)
        elif ['date', 'id', 'table'] == sorted(list(url_params.keys())):
            query = '''select * from %s where date = "%s" and id = "%s"''' \
                    % (url_params['table'], url_params['date'], url_params['id'])
            self.send_result(query)
        elif ['date', 'id', 'rating', 'table'] == sorted(list(url_params.keys())):
            query = '''select * from %s where date = "%s" and rating = %f and id = "%s"''' \
                    % (url_params['table'], url_params['date'], float(url_params['rating']),
                       url_params['id'])
            self.send_result(query)
        else:
            self.send_response(HTTPStatus.BAD_REQUEST)
            self.send_error(HTTPStatus.BAD_REQUEST)
            return

    def do_POST(self):
        parts = urllib.parse.urlsplit(self.path)
        if parts[2] != '/':
            self.send_response(HTTPStatus.NOT_FOUND, 'Path not found!')
            self.send_error(HTTPStatus.NOT_FOUND, 'Path not found!')
            return
        url_params = urllib.parse.parse_qs(parts[3])

        for key in url_params:
            if len(url_params[key]) > 1:
                self.send_response(HTTPStatus.BAD_REQUEST)
                self.send_error(HTTPStatus.BAD_REQUEST)
                return
            else:
                url_params[key] = url_params[key][0]

        if ['table'] == sorted(list(url_params.keys())):
            query = '''select id from %s''' % (url_params['table'])
            self.send_result(query)
        elif ['id', 'table'] == sorted(list(url_params.keys())):
            query = '''select * from %s where id like "%s"''' \
                    % (url_params['table'], url_params['id'])
            self.send_result(query)
        elif ['rating', 'table'] == sorted(list(url_params.keys())):
            query = '''select id, rating from %s where rating >= %f''' \
                    % (url_params['table'], float(url_params['rating']))
            self.send_result(query)
        elif ['id', 'rating', 'table'] == sorted(list(url_params.keys())):
            query = '''select * from %s where id like "%s" and rating = %f''' \
                    % (url_params['table'], url_params['id'],
                       float(url_params['rating']))
            self.send_result(query)
        elif ['date', 'table'] == sorted(list(url_params.keys())):
            query = '''select * from %s where date >= "%s"''' \
                    % (url_params['table'], url_params['date'])
            self.send_result(query)
        elif ['date', 'rating', 'table'] == sorted(list(url_params.keys())):
            query = '''select * from %s where date >= "%s" and rating >= %f''' \
                    % (url_params['table'], url_params['date'], float(url_params['rating']))
            self.send_result(query)
        elif ['date', 'id', 'table'] == sorted(list(url_params.keys())):
            query = '''select * from %s where date = "%s" and id = "%s"''' \
                    % (url_params['table'], url_params['date'], url_params['id'])
            self.send_result(query)
        elif ['date', 'id', 'rating', 'table'] == sorted(list(url_params.keys())):
            query = '''insert into %s values("%s", "%s", %f) '''\
                    % (url_params['table'], url_params['id'], url_params['date'],
                       float(url_params['rating']))
            self.send_result(query, should_respond=False)
            query = '''select * from %s where date = "%s" and rating = %f and id = "%s"''' \
                    % (url_params['table'], url_params['date'], float(url_params['rating']),
                       url_params['id'])
            self.send_result(query)
        else:
            self.send_response(HTTPStatus.BAD_REQUEST)
            self.send_error(HTTPStatus.BAD_REQUEST)
            return

    def do_PUT(self):
        parts = urllib.parse.urlsplit(self.path)
        if parts[2] != '/':
            self.send_response(HTTPStatus.NOT_FOUND, 'Path not found!')
            self.send_error(HTTPStatus.NOT_FOUND, 'Path not found!')
            return
        url_params = urllib.parse.parse_qs(parts[3])

    def do_DELETE(self):
        parts = urllib.parse.urlsplit(self.path)
        if parts[2] != '/':
            self.send_response(HTTPStatus.NOT_FOUND, 'Path not found!')
            self.send_error(HTTPStatus.NOT_FOUND, 'Path not found!')
            return
        url_params = urllib.parse.parse_qs(parts[3])


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
    db_conn.execute('''insert into music values ('Song 2', '13-12-2017', 1)''')
    db_conn.commit()


if __name__ == '__main__':
    db_conn = create_database_connection(CONFIG['db_path'])
    populate_db()
    httpd = open_server()
