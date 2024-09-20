import asyncio
import http.server
import socketserver
import socket
import json

PORT = 6788


def get_private_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ethernet_ip = s.getsockname()[0]
    # hostname = socket.gethostname()
    # print('hostname', hostname)
    # private_ip = socket.gethostbyname(hostname)
    # print('ip', private_ip)
    return ethernet_ip


class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'X-Requested-With, Content-Type, Accept')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            response_data = {
                "ip": get_private_ip()
            }

            response = json.dumps(response_data, indent=2)
            self.wfile.write(response.encode())
        else:
            # For all other routes, use the default behavior
            super().do_GET()


async def start_server():
    with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
        print(f"Serving at http://localhost:{PORT}")
        print("To access from other devices, use your computer's IP address instead of localhost")
        httpd.serve_forever()


def run_server():
    asyncio.run(start_server())
