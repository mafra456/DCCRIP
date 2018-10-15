import socket
import time
import sys
import numpy as np
import json
import threading

def _add(args, sourceIP, DVTable):
    dest = args[0]
    cost = args[1]
    DVTable.append([sourceIP, cost, dest])

def _del(args, DVTable):
    dest = args[]
    for i in DVTable:
        if(DVTable[i][2] == dest):
            DVTable.remove([sourceIP,DVTable[i][1],dest])

def _trace(args, DVTable):#Enviam mensagem to tipo data e trace
    print('')

def executeCommand(commands, sourceIP,DVTable):
    commands = line.split(" ")
    args = commands[1:]
    if(commands[0] == "add"):
        _add(args,sourceIP,DVTable)
    elif(commands[0] == "del"):
        _del(args)
    elif(commands[0] == "trace"):
        _trace(args)
    else:
        print("Comando nao reconhecido, tente novamente com [add, del, trace]")

def bellmanFord():
    print('')

def updateMessage(dest):
    message = {'type':'update', 'source':dest, 'destination':True, 'distances':}
    update_message = json.dumps(message)
    return update_message

def dataMessage():
    print('')

def traceMessage():
    print('')

def broadcastDV(PORT):#Envia mensagem do tipo update de tempos em tempos
    broadcast = socket(AF_INET, SOCK_DGRAM)
    lock.acquire()
    for id, neighbour in r_neighbours.items():  #sending to every neigbor
        broadcast.sendto(updateMessage(id, sendLinkCost), (dest, PORT))
    lock.release()
    broadcast.close()

def createDVTable(HOST):
    DVTable = []
    return DVTable, HOST

def main():
    t_start = time.time()
    param = sys.argv[1:] 
    PORT = 55151
    HOST = param[0]
    period = param[1]
    DVTable, sourceIP = createDVTable(HOST)

    if(len(param) > 2):
        filename = param[2]
        file = open(filename,"r")
        for line in file:
            executeCommand(line, DVTable)

    dest = (HOST, PORT)
   # socket.bind((HOST,PORT))
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    udp.connect(dest)
    line = ""
    try:
        while(line != "quit"):
            line = input()
            executeCommand(line)
    except KeyboardInterrupt:
        pass
    udp.close()
    
#python3 router.py 127.0.0.1 5 file.txt
if __name__ == "__main__":
    main()
    print ("Termino da execucao")