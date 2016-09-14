# settings.py (for sharing global variables between files)

import socket

def init():
    global dialogState
    global nluSocket
    global nluPort
    dialogState = 0
    nluPort = 9034
    nluSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address=('localhost',nluPort)
    nluSocket.connect(server_address)                              
                              
