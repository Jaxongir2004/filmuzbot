from http.server import BaseHTTPRequestHandler, HTTPServer

class KeepAliveHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        self.wfile.write(b"Bot is running.")

def run():
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, KeepAliveHandler)
    httpd.serve_forever()