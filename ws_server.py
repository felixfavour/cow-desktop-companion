import io
import os
import asyncio
import socket
import subprocess
from io import BytesIO
import time
import cv2
import imageio_ffmpeg as ffmpeg
import numpy as np
import NDIlib as ndi
import websockets
import platform
import threading
from PIL import Image

async def parse_ppt_slide(websocket, ppt_slide):
    await websocket.send("ppt_slide")

clients = set()
private_ip = ""


# Function to allow the WebSocket port through the firewall
def allow_port(port):
    os_name = platform.system()
    if os_name == "Windows":
        command = f"netsh advfirewall firewall add rule name=\"AllowPort{port}\" protocol=TCP dir=in localport={port} action=allow"
    elif os_name == "Linux":
        command = f"sudo ufw allow {port}/tcp"
    else:
        command = None

    if command:
        subprocess.run(command, shell=True)
        print(f"Allowed port {port} on {os_name}")


async def controller(websocket, path):
    global clients
    clients.add(websocket)
    try:
        async for message in websocket:
            if path == "/slides":
                await parse_ppt_slide(websocket, message)
                continue
            elif path == "/livestream":
                # Broadcast message to all connected clients except the sender
                if len(clients) > 1:
                    await asyncio.wait([client.send(message) for client in clients if client != websocket])
                continue
            else:
                await websocket.send(f"Echo: {message}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Remove the client from the set when it disconnects
        clients.remove(websocket)


async def start_server():
    port = 6787  # CW - ASCII code
    allow_port(port)
    server = await websockets.serve(controller, '0.0.0.0', port)
    print("WS Server now running")
    await server.wait_closed()


def run_server():
    asyncio.run(start_server())
