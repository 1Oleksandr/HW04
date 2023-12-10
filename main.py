import json
import logging
import mimetypes
import pathlib
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import socket
import urllib.parse

BASE_DIR = pathlib.Path()
BUFFER = 1024
OK = 200
SERVER_SOCKET_IP = '127.0.0.1'
SERVER_SOCKET_PORT = 5000
SERVER_PORT = 3000


def send_data_to_server(body):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.sendto(body, (SERVER_SOCKET_IP, SERVER_SOCKET_PORT))
    client_socket.close()


class HTTPHandler(BaseHTTPRequestHandler):

    def do_POST(self):

        body = self.rfile.read(int(self.headers['Content-Length']))

        # print(self.headers)
        send_data_to_server(body)

        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        print('Route:', route)
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

    def send_html(self, filename, status_code=OK):
        self.send_response(status_code)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as f:
            self.wfile.write(f.read())

    def send_static(self, filename):
        self.send_response(OK)
        mime_type, *rest = mimetypes.guess_type(filename)
        if mime_type:
            self.send_header('Content-Type', mime_type)
        else:
            self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        with open(filename, 'rb') as f:
            self.wfile.write(f.read())


def run(server=HTTPServer, handler=HTTPHandler):
    address = ('0.0.0.0', SERVER_PORT)
    http_server = server(address, handler)
    try:
        http_server.serve_forever()
    except BrokenPipeError:
        ...
    except KeyboardInterrupt:
        http_server.server_close()


namefield = 'message'


def sanitize_data(s: str) -> str:

    symbols_to_remove = "=&"
    ind = s.find(namefield+'=')
    s1 = s[:ind+len(namefield)+1]
    data = s[ind+len(namefield)+1:]
    for symbol in symbols_to_remove:
        data_new = data.replace(symbol, " ")
    s_sanitize = s1 + data_new
    return s_sanitize, data


def save_data(data):
    try:
        body = urllib.parse.unquote_plus(data.decode())
        # print(body)
        # body, message_sanitize = sanitize_data(body)
        # print(body, message_sanitize)
        payload = {key: value for key, value in [
            el.split('=') for el in body.split('&')]}
        # payload[namefield] = message_sanitize
        with open(BASE_DIR.joinpath('storage/data.json'), 'r', encoding='utf-8') as fd:
            data_json = json.load(fd)
        rec = {}
        key = datetime.now().strftime('%Y/%m/%d/, %H:%M:%S.%f')
        rec[key] = payload
        data_json.update(rec)
        with open(BASE_DIR.joinpath('storage/data.json'), 'w', encoding='utf-8') as fd:
            json.dump(data_json, fd, indent=4, ensure_ascii=False)
    except ValueError as err:
        logging.error(f'Field parse data {body} with error {err}')
    except OSError as err:
        logging.error(f'Field write data {body} with error {err}')


def run_socket_server(ip, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    server_socket.bind(server)

    try:
        while True:
            data, address = server_socket.recvfrom(BUFFER)
            save_data(data)
    except KeyboardInterrupt:
        logging.info('Socket server has been stopped.')
    finally:
        server_socket.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(threadName)s %(message)s')
    STORAGE_DIR = pathlib.Path().joinpath('storage')
    STORAGE_FILE = STORAGE_DIR / 'data.json'
    if not STORAGE_FILE.exists():
        STORAGE_DIR.mkdir(exist_ok=True, parents=True)
        with open(STORAGE_FILE, 'w', encoding='utf-8') as fd:
            json.dump({}, fd, ensure_ascii=False)

    thread_server = Thread(target=run)
    thread_server.start()

    thread_socket = Thread(target=run_socket_server(
        SERVER_SOCKET_IP, SERVER_SOCKET_PORT))
    thread_socket.start()
