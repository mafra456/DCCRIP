import socket
import time
import sys
import os
import numpy as np
import json
import threading
import math
from collections import defaultdict

lock = threading.Lock()
global DVTable
global graph

def _add(args, sourceIP):
    global DVTable,graph
    dest = args[0]
    cost = int(args[1])
    DVTable.append([sourceIP, cost, dest])
    DVTable.append([dest, cost, sourceIP])
    graph[sourceIP].update({dest: cost})
    graph[dest].update({sourceIP: cost})
    print(DVTable)
    print(graph)

def _del(args, sourceIP):
    global DVTable,graph
    dest = args[0]
    for i in range(len(DVTable)):
        if(DVTable[i][2] == dest):
            DVTable.remove([sourceIP,DVTable[i][1],dest])
            graph[sourceIP][dest] = math.inf

def _trace(args):#Enviam mensagem to tipo data e trace
    global DVTable,graph
    print('')

def executeCommand(line, sourceIP):
    commands = line.split(" ")
    args = commands[1:]
    if(commands[0] == "add"):
        _add(args,sourceIP)
    elif(commands[0] == "del"):
        _del(args,sourceIP)
    elif(commands[0] == "trace"):
        _trace(args)
    else:
        print("Comando nao reconhecido, tente novamente com [add, del, trace]")

def updateMessage(source,dest,distances):
    message = {'type':'update', 'source':source, 'destination':dest, 'distances':distances}
    update_message = json.dumps(message)
    #print(update_message)
    return update_message.encode('latin1')

def dataMessage(source,dest):
    message = {'type':'data', 'source':source, 'destination':dest, 'payload':'data'+'\'+ source + '\' + dest}
    data_message = json.dumps(message)
    #print(data_message)
    return data_message.encode('latin1')

def traceMessage():
    #Falta implementar o hops
    hops = []
    message = {'type':'trace', 'source':source, 'destination':dest, 'hops':hops}
    trace_message = json.dumps(message)
    #print(trace_message)
    return trace_message.encode('latin1')

def broadcastDV(TOUT,PORT): #Envia mensagem do tipo update de tempos em tempos
    global DVTable,graph
    broadcast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    lock.acquire()
    distances = {dist[2]:dist[1] for dist in DVTable}
    for dist in DVTable:  #Enviando msg a todos os vizinhos
        broadcast.sendto(updateMessage(dist[0],dist[2], distances), (dist[2], PORT))
    threading.Timer(int(TOUT),broadcastDV, args=(int(TOUT),PORT)).start()
    lock.release()
    broadcast.close()

def createDVTable(HOST):
    global DVTable,graph
    DVTable = []
    return DVTable, HOST

def pathCost(sourceIP, dest):
    global graph
    #bellmanFord algorithm

def bellmanFord():
    print('')


def listen(HOST,PORT):
    global DVTable,graph
    listenSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    listenSocket.bind((HOST,PORT))
    while True:
        message, address = listenSocket.recvfrom(2048)
        message = message.decode('latin1')  
        print(message)
        js = json.loads(message)
        matrixDV = np.array(DVTable)
        if(js['type'] == 'update'):
            for key,val in js['distances'].items():
                if(key not in matrixDV[:,2]):
                    #graph.update({js['source']:{d:js['destination'][d]}})
                    _add([key,js['destination'][key]], js['source'])
                else:
                    for t in DVTable:
                        for key,val in js['distances'].items():
                            if(t[2] == key):
                                pass
                                #Comparo para ver se o novo caminho é melhor (pathCost é o bellmanFord - caminho minimo no grafo)
                                #if(t[1] > js['distances'][d] + pathCost(HOST,js['source']))

        elif(js['type'] == 'data'):
            pass
        elif(js['type'] == 'trace'):
            pass
         

def CLI(sourceIP):
    line = ""
    try:
        while(True):
            line = input()
            if(line == "quit"):
                print("Termino da Execucao")
                os._exit(1)
            else:
                executeCommand(line, sourceIP)
    except KeyboardInterrupt:
        print("Termino da Execucao")
        os._exit(1)

def main():
    global DVTable
    global graph
    t_start = time.time()
    param = sys.argv[1:] 
    PORT = 55151
    HOST = param[0]
    period = param[1]
    DVTable = [[HOST,0,HOST]]
    graph = defaultdict(dict)

    if(len(param) > 2):#Startup
        filename = param[2]
        file = open(filename,"r")
        for line in file:
            executeCommand(line, sourceIP)
    #starting threads
    threading.Thread(target=CLI, args=(HOST,)).start()
    threading.Timer(int(period),broadcastDV, args=(int(period),PORT)).start()
    threading.Thread(target=listen, args=(HOST,PORT)).start()

    
#python3 router.py 127.0.0.1 5 file.txt
if __name__ == "__main__":
    main()
