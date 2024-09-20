from threading import Thread
from http_server import run_server

def start_http_server():
    from http_server import run_server
    run_server()


def start_ws_server():
    from ws_server import run_server
    run_server()


# start_http_server()
start_ws_server()
