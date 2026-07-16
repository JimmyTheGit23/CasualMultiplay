"""No-cache preview server for E:\CasualMultiplay\docs
Run: python E:\CasualMultiplay\server.py
Open: http://localhost:8083/
"""
import http.server
import socketserver
import os
import sys

PORT = 8085
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'docs')


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()


if __name__ == '__main__':
    with socketserver.TCPServer(('127.0.0.1', PORT), NoCacheHandler) as httpd:
        print(f'Preview server on http://localhost:{PORT}/')
        print(f'Serving: {ROOT}')
        httpd.serve_forever()
