import http.server
import socketserver


def open_server():
    port = 8000
    handler = http.server.SimpleHTTPRequestHandler

    httpd = socketserver.TCPServer(("", port), handler)
    print("serving at port", port)
    httpd.serve_forever()
    return httpd


if __name__ == '__main__':
    httpd = open_server()
