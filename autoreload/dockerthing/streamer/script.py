#!/usr/bin/env python3
import sys
import os
import time
import datetime
from random import randrange
import socketserver
import threading

import numpy as np
from PIL import Image, ImageDraw

FPS = 30
FRAMETIME = 1/FPS

SPS = 24000


def call_const_rate(fn, interval):
    tnext = time.perf_counter()
    while True:
        tnow = time.perf_counter()
        if (tnow - tnext) > interval * 10:
            tnext = tnow
            print("WARNING: lagging behind")

        if tnow >= tnext:
            tnext += interval
            fn()


class VideoServer(socketserver.BaseRequestHandler):
    def handle(self):
        frame = Image.new("RGB", (1920, 1080), (0, 0, 0))
        def send_frame():
            frame.putpixel((randrange(0, 1920), randrange(0, 1080)), (randrange(0, 256), randrange(0, 256), randrange(0, 256)))
            draw = ImageDraw.Draw(frame)
            draw.rectangle([(0, 0), (400, 40)], fill=(0, 0, 0))
            draw.text((0, 0), str(datetime.datetime.now()), fill=(255, 255, 255), font_size=30)
            self.request.sendall(frame.tobytes())
        call_const_rate(send_frame, FRAMETIME)


class AudioServer(socketserver.BaseRequestHandler):
    def handle(self):
        def send_frame():
            #self.request.sendall(np.random.bytes(SPS * 2))
            freq = datetime.datetime.now().second * 100
            self.request.sendall(
                (np.sin(2*np.pi*np.arange(SPS)*freq/SPS)*32767).astype(np.int16).tobytes()
            )
        call_const_rate(send_frame, 1)


def unix_serve(handler, name):
    server = socketserver.UnixStreamServer(name, handler)
    server.serve_forever()

t1 = threading.Thread(target=unix_serve, args=[VideoServer, "video.socket"], daemon=True)
t1.start()

t2 = threading.Thread(target=unix_serve, args=[AudioServer, "audio.socket"], daemon=True)
t2.start()

t1.join()
t2.join()
