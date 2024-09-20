import io
import os
import asyncio
import subprocess
from io import BytesIO
import time
import cv2
import imageio_ffmpeg as ffmpeg
import numpy as np
import NDIlib as ndi
import websockets
import threading
from PIL import Image

# buffer = BytesIO()
video_frame = ndi.VideoFrameV2()
ndi_send = ndi.send_create()
# ffmpeg command to read from stdin and decode video
ffmpeg_cmd = [
    ffmpeg.get_ffmpeg_exe(), '-i', 'pipe:0',  # Input from pipe
    '-f', 'image2pipe',  # Output format
    '-pix_fmt', 'bgr24',  # Pixel format (24-bit RGB)
    '-vcodec', 'rawvideo', '-'  # Output to stdout
]
process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           bufsize=10 ** 8)


def send_frame_to_ndi(ndi_send, frame):
    if frame is None:
        return
    print("sending frame")
    frame_bgrx = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
    video_frame.data = frame_bgrx
    video_frame.FourCC = ndi.FOURCC_VIDEO_TYPE_BGRX
    ndi.send_send_video_v2(ndi_send, video_frame)


async def send_ndi_stream():
    if not ndi.initialize():
        return 0

    ndi_send = ndi.send_create()
    if ndi_send is None:
        return 0
    img = np.zeros((1080, 1920, 4), dtype=np.uint8)
    video_frame = ndi.VideoFrameV2()

    video_frame.data = img
    video_frame.FourCC = ndi.FOURCC_VIDEO_TYPE_BGRX

    start = time.time()

    while time.time() - start < 60 * 5:
        start_send = time.time()
        for idx in reversed(range(200)):
            img.fill(255 if idx % 2 else 0)
            print(img)
            ndi.send_send_video_v2(ndi_send, video_frame)

        print('200 frames sent, at %1.2ffps' % (200.0 / (time.time() - start_send)))

    ndi.send_destroy(ndi_send)

    ndi.destroy()


async def parse_ppt_slide(websocket, ppt_slide):
    await websocket.send("ppt_slide")


async def observe_live_media_stream(websocket, stream):
    count = 0
    # print("new stream coming\n")
    # print(stream[:50])
    # img = np.fromstring(stream, dtype=np.uint8)
    # print(img)

    # video_frame.data = img
    # ndi.send_send_video_v2(ndi_send, video_frame)

    # with open("received_stream.webm", "wb") as file:
    #     print(f"received binary data of size: {len(stream)} bytes")
    #     file.write(stream)
    #     # file.flush()
    #     await websocket.send("video frame received")

    # process.stdin.write(stream)  # Feed binary data into FFmpeg
    # print("reading stream")
    #
    # # Read frames from FFmpeg output
    # frame_size = 1920 * 1080 * 3  # Assuming 1080p resolution (adjust accordingly)
    # frame_data = process.stdout.read(frame_size)
    # print("read out stream")
    #
    # # Convert raw frame data to numpy array
    # frame = np.frombuffer(frame_data, dtype=np.uint8).reshape((1080, 1920, 3))

    # Send the frame to NDI
    # send_frame_to_ndi(ndi_send, img)


def video_capture_loop(video_path):
    # Function to continuously capture and display the most recent frame
    video_capture = cv2.VideoCapture(video_path)

    while True:
        # Reopen the video file to get the latest data
        video_capture.open(video_path)

        if video_capture.isOpened():
            ret, frame = None, None
            while True:
                # Read the frames continuously until we reach the last available one
                ret, frame = video_capture.read()
                if not ret:
                    break  # No more frames available, so break the loop

            if ret:
                print("Captured latest frame")
                cv2.imshow('Latest Frame', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                print("No frame captured, retrying...")

            # Small delay to avoid too frequent reading
            time.sleep(0.1 * 1000)
        else:
            print("Video stream is not yet open.")
            time.sleep(0.1 * 1000)  # Wait before retrying

    video_capture.release()
    cv2.destroyAllWindows()


async def controller(websocket, path):
    buffer = b""
    with open("received_stream.webm", "wb") as file:
        async for message in websocket:
            if path == "/slides":
                await parse_ppt_slide(websocket, message)
                continue
            elif path == "/ndi-livestream":

                # Receive binary data and write it to the file
                # print(f"received binary data of size: {len(message)} bytes")
                # file.write(message)
                #
                # # Start a thread to capture frames while receiving binary data
                # capture_thread = threading.Thread(target=video_capture_loop, args=("received_stream.webm",))
                # capture_thread.start()

                while True:
                    try:
                        # Receive data from websocket (this should be inside your main async loop)
                        buffer += message

                        # Decode the frame from the buffer using OpenCV
                        nparr = np.frombuffer(buffer, np.uint8)
                        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                        print('frame', nparr)

                        if frame is not None:
                            # Display the frame
                            cv2.imshow("Live Stream", frame)
                            if cv2.waitKey(1) & 0xFF == ord('q'):
                                break

                        # Clear buffer for the next frame (optional)
                        buffer = b""

                    except Exception as e:
                        print(f"Error receiving stream data: {e}")
                        break

                continue
            else:
                await websocket.send(f"Echo: {message}")


# async def controller(websocket, path):
#     with open("received_stream.webm", "wb") as file:
#         async for message in websocket:
#             if path == "/slides":
#                 await parse_ppt_slide(websocket, message)
#                 continue
#             elif path == "/ndi-livestream":
#                 # await send_ndi_stream()
#                 # await observe_live_media_stream(websocket, message)
#                 print(f"received binary data of size: {len(message)} bytes")
#                 file.write(message)
#
#                 # Creating frames
#                 video_capture = cv2.VideoCapture("received_stream.webm")
#                 while True:
#                     ret, frame = video_capture.read()
#                     if ret is True:
#                         print(frame)
#                     #     cv2.imshow('first-frame', frame)
#                     # if cv2.waitKey(1) & 0xFF == ord('q'):
#                     #     break
#                     # np = np.frombuffer(frame_data, dtype=np.uint8)
#
#                 # continue
#             else:
#                 await websocket.send(f"Echo: {message}")
#         # file.write(stream)
#         # file.flush()
#         # await websocket.send("video frame received")


# async def controller(websocket, path):
#     async for message in websocket:
#         if path == "/slides":
#             await parse_ppt_slide(websocket, message)
#             continue
#         elif path == "/ndi-livestream":
#             # await send_ndi_stream()
#             await observe_live_media_stream(websocket, message)
#             continue
#         else:
#             await websocket.send(f"Echo: {message}")


async def start_server():
    server = await websockets.serve(controller, "localhost", 6787)  # CW - ASCII code
    print("WS Server now running")
    await server.wait_closed()


def run_server():
    asyncio.run(start_server())
