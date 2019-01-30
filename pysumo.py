from time import *
from socket import *
import sys, threading, struct

_constants = {
    "ARCOMMANDS_ID_PROJECT_JUMPINGSUMO": 3,
    "ARCOMMANDS_ID_JUMPINGSUMO_CLASS_PILOTING": 0,
    "ARCOMMANDS_ID_JUMPINGSUMO_PILOTING_CMD_PCMD": 0,
    "ARNETWORKAL_FRAME_TYPE_DATA": 2,
    "BD_NET_CD_NONACK_ID": 10 
}

class Drone:
    def __init__(self, **kwargs):
        # sockets vars
        self._ip = ("ip" in kwargs and kwargs["ip"] or "192.168.2.1")
        self._c2d_port = ("c2d_port" in kwargs and kwargs["c2d_port"] or 54321)
        self._d2c_port = ("d2c_port" in kwargs and kwargs["d2c_port"] or 43210)
        self._discovery_port = ("discovery_port" in kwargs and kwargs["discovery_port"] or 44444)

        # sockets
        self._c2d_sock = socket(AF_INET, SOCK_DGRAM)
        self._d2c_sock = socket(AF_INET, SOCK_DGRAM)
        self._discovery_sock = socket(AF_INET, SOCK_STREAM)

        self._pcmd = 0

    def _on_d2c(self):
        def callback(data):
            print(data)
        def on_d2c_thread():
            while True:
                data = self._d2c_sock.recv(32768)
                print("Data> " + str(data))
                if data:
                    callback(data)
        d2c_sock_thread = threading.Thread(target=on_d2c_thread)
        d2c_sock_thread.start()
    
    def _startPCMD(self):
        def _startPCMD_thread():
            while True:
                time_start = time()
                buf = struct.pack(">BBBIBBHBbb", 
                    _constants["ARNETWORKAL_FRAME_TYPE_DATA"],
                    _constants["BD_NET_CD_NONACK_ID"],
                    self._pcmd,
                    4294967295-struct.calcsize(">BBBIBBHBbb"),
                    _constants["ARCOMMANDS_ID_PROJECT_JUMPINGSUMO"], 
                    _constants["ARCOMMANDS_ID_JUMPINGSUMO_CLASS_PILOTING"], 
                    255-_constants["ARCOMMANDS_ID_JUMPINGSUMO_PILOTING_CMD_PCMD"],
                    1,
                    0,
                    0 
                )
                self._c2d_sock.send(buf)
                self._pcmd += 1
                duration = time()-time_start
                print(duration)
                sleep(max(0, 0.025-duration))
        PCMD_thread = threading.Thread(target=_startPCMD_thread)
        PCMD_thread.start()
        
    def connect(self):
        try:
            self._discovery_sock.connect((self._ip, self._discovery_port))
        except:
            print("PySumo> Connexion impossible, etes-vous connecte au drone ? (wifi)")
            sys.exit()
        print("PySumo> Connecte")
        self._discovery_sock.sendall("{'controller_type':'computer','controller_name':'pysumo','d2c_port':'43210'}".encode("utf_8"))
        discovery_data = self._discovery_sock.recv(1024)
        print("DiscoveryData> " + discovery_data.decode("utf-8"))
        print("PySumo> Associe")
        self._d2c_sock.bind(("", self._d2c_port))
        self._c2d_sock.connect((self._ip, self._c2d_port))
        self._on_d2c()
        self._startPCMD()

s = Drone()

s.connect()

print("end of script")
