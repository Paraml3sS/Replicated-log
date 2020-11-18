import argparse
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from threading import Thread

log_messages = []


class SecondaryPublic(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps({
            'log_messages': log_messages
        }).encode())
        return


class SecondaryInternal(BaseHTTPRequestHandler):

    def do_POST(self):
        content_len = int(self.headers.get('content-length'))
        post_body = self.rfile.read(content_len)
        print(f"Received POST request: {post_body}")
        data = json.loads(post_body)
        response_delay = data.get('response_delay', 1)
        time.sleep(response_delay)
        new_message = data.get('log')
        if not new_message:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(json.dumps({
                'request_data': data,
            }).encode())
            return
        log_messages.append(new_message)
        print(f"Append new message: {new_message}")
        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps({
            'request_data': data,
            'new_message': new_message,
            'log_messages': log_messages
        }).encode())
        return


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


def run(ip_address, port, handler):
    httpd = ThreadingHTTPServer((ip_address, port), handler)
    print(f'Staring {handler} on http://{ip_address}:{port}')
    try:
        httpd.serve_forever()
    finally:
        httpd.shutdown()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Starts secondary node')
    parser.add_argument("--ip_address", help="public ip address", default='0.0.0.0', type=str)
    parser.add_argument("--port", help="public port", default=8000, type=int)
    parser.add_argument("--internal_port", help="internal port", default=5000, type=int)
    args = parser.parse_args()
    Thread(target=run, args=[args.ip_address, args.port, SecondaryPublic]).start()
    run(ip_address=args.ip_address, port=int(args.internal_port), handler=SecondaryInternal)
