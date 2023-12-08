import json
import mimetypes
import pathlib
# from threading import Thread
from datetime import datetime
# from http import client
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib

BASE_DIR = pathlib.Path()


class HTTPHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        body = self.rfile.read(int(self.headers['Content-Length']))
        body = urllib.parse.unquote_plus(body.decode())
        # body.replace('=', '')
        # print(self.headers)
        payload = {key: value for key, value in [
            el.split('=') for el in body.split('&')]}
        with open(BASE_DIR.joinpath('storage/data.json'), 'a', encoding='utf-8') as fd:
            rec = {}
            key = datetime.now().strftime('%Y/%m/%d/, %H:%M:%S.%f')
            rec[key] = payload
            json.dump(rec, fd, ensure_ascii=False)
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        match route.path:
            case '/':
                self.send_html('index.html')
            case '/message.html':
                self.send_html('message.html')
            case _:
                file = BASE_DIR / route.path[1:]
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html('error.html', 404)

    def send_html(self, filename, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as f:
            self.wfile.write(f.read())

    def send_static(self, filename):
        self.send_response(200)
        mime_type, *rest = mimetypes.guess_type(filename)
        if mime_type:
            self.send_header('Content-Type', mime_type)
        else:
            self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        with open(filename, 'rb') as f:
            self.wfile.write(f.read())


def run(server=HTTPServer, handler=HTTPHandler):
    address = ('', 3000)
    http_server = server(address, handler)
    try:
        http_server.serve_forever()
    except BrokenPipeError:
        ...
    except KeyboardInterrupt:
        http_server.server_close()


if __name__ == '__main__':
    run()

# httpd = HTTPServer(('localhost', 3000), HTTPRequestHandler)
# server = Thread(target=httpd.serve_forever)
# server.start()
# sleep(0.5)

# h1 = client.HTTPConnection('localhost', 3000)
# h1.request("GET", "/")

# res = h1.getresponse()
# print(res.status, res.reason)
# data = res.read()
# print(data)

# httpd.shutdown()