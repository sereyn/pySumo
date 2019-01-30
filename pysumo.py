from socket import *
import numpy as np
import json
import sys
import asyncio
import struct
from time import sleep

async_loop = asyncio.get_event_loop()

uint8 = np.dtype("uint8").newbyteorder(">")
uint16LE = np.dtype("uint16").newbyteorder("<")
uint32LE = np.dtype("uint32").newbyteorder("<")

class Drone:
    def __init__(self, **kwargs):
        # sockets vars
        self.ip = ("ip" in kwargs and kwargs["ip"] or "192.168.2.1")
        self.c2d_port = ("c2d_port" in kwargs and kwargs["c2d_port"] or 54321)
        self.d2c_port = ("d2c_port" in kwargs and kwargs["d2c_port"] or 43210)
        self.discovery_port = ("discovery_port" in kwargs and kwargs["discovery_port"] or 44444)

        # sockets
        self.c2d_sock = socket(AF_INET, SOCK_DGRAM)
        self.d2c_sock = socket(AF_INET, SOCK_DGRAM)
        self.discovery_sock = socket(AF_INET, SOCK_STREAM)

        self.pcmd = {}
        self.seq = 0

    def generate_pcmd(self):
        buff = bytearray([
            np.uint8(2), np.uint8(10), np.uint8(self.seq), np.uint32(21).newbyteorder("<"),
            np.uint8(3), np.uint8(0), np.uint16(0).newbyteorder("<"), np.uint8(1), np.uint8(0), np.uint8(0)
            ])
        self.seq += 1
        self.seq %= 255
        return buff

    async def start_pcmd(self):
        while True:
            self.c2d_sock.send(self.generate_pcmd())
            print("pcdm")
            sleep(0.025)

    async def socket_on(self, s, callback):
        while True:
            data = await async_loop.sock_recv(s, 1024)
            self.d2c_handler(data)

    def d2c_handler(self, data):
        frame = {}
        [frame["type"], frame["id"], frame["seq"]] = np.frombuffer(data, dtype=uint8, count=3)
        frame["size"] = np.frombuffer(data, dtype=uint32LE, count=1, offset=3)
        if frame["size"] > 7:
            frame["data"] = data[7:int(frame["size"])]
            print(np.frombuffer(frame["data"], dtype=uint8, count=2))
            print(np.frombuffer(frame["data"], dtype=uint16LE, count=1, offset=2))
    def connect(self):
        try:
            self.discovery_sock.connect((self.ip, self.discovery_port))
        except:
            print("PySumo> Connexion impossible, etes-vous connecte au drone ? (wifi)")
            sys.exit()
        self.discovery_sock.sendall("{'controller_type':'computer','controller_name':'pysumo','d2c_port':'43210'}".encode("utf_8").strip())
        discovery_data = self.discovery_sock.recv(1024)
        print("PySumo> Drone trouve")
        self.d2c_sock.bind(("", self.d2c_port))
        asyncio.gather(self.generate_pcmd(), self.socket_on(self.d2c_sock, self.d2c_handler))

s = Drone()

s.connect()
