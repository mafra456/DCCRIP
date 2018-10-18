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
#graph_comment global DVTable,graph
global DVTable


def _add(sourceIP, cost, dest, nextStep):
    #graph_comment global DVTable,graph
    global DVTable
    
    cost = int(cost)
    DVTable.append([sourceIP, cost, dest, nextStep])
    # Só adicionamos na oposta caso o destino não seja igual ao próximo passo.
    # Nesse caso, não é uma ligação direta e não sabemos se o caminho inverso é o melhor para o outro.
    if(nextStep != dest):
        DVTable.append([dest, cost, sourceIP, sourceIP])
#graph_comment     graph[sourceIP].update({dest: cost})
#graph_comment     graph[dest].update({sourceIP: cost})
    print(DVTable)
    #graph_comment print(graph)

def _del(args, sourceIP):
    #graph_comment global DVTable,graph
    global DVTable
    dest = args[0]
    for i in range(len(DVTable)):
        if(DVTable[i][2] == dest):
            #DVTable.remove([sourceIP,DVTable[i][1],dest])
            del DVTable[i]
#graph_comment             graph[sourceIP][dest] = math.inf

def _trace(args):#Enviam mensagem to tipo data e trace
    #graph_comment global DVTable,graph
    global DVTable
    print('')

def executeCommand(line, sourceIP):
    commands = line.split(" ")
    args = commands[1:]
    if(commands[0] == "add"):
        # Source, custo, destino, next step.
        _add(sourceIP, args[1], args[0], args[0])
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
    message = {'type':'data', 'source':source, 'destination':dest, 'payload':'data'+'\\'+ source + '\\' + dest}
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
    #graph_comment global DVTable,graph
    global DVTable
    broadcast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    lock.acquire()
    distances = {dist[2]:dist[1] for dist in DVTable}
    for dist in DVTable:  #Enviando msg a todos os vizinhos
        broadcast.sendto(updateMessage(dist[0],dist[2], distances), (dist[2], PORT))
    threading.Timer(int(TOUT),broadcastDV, args=(int(TOUT),PORT)).start()
    lock.release()
    broadcast.close()

def createDVTable(HOST):
    #graph_comment global DVTable,graph
    global DVTable
    DVTable = []
    return DVTable, HOST

def pathCost(sourceIP, dest):
    #graph_comment global graph
    #bellmanFord algorithm

def bellmanFord():
    print('')


# Recebemos o anuncio`1             
def update_table(js):
    # Anunciante
    _source = js["source"]

    # Eu
    _destination = js["destination"]

    # Endereços conectados no anunciante
    _distances = js["distances"]

    # Para cada vizinho no anuncio recebido
    for destino, custo in _distances.items():
        # Se o destino não está na tabela
        if(destino not in matrixDV[:,2]):
            #graph_comment #graph.update({js['source']:{d:js['destination'][d]}})
            _add(key,_destination[key], _source)
        else:
            for t in DVTable:
                for key,val in _distances.items():
                    if(t[2] == key):
                        pass
                        #Comparo para ver se o novo caminho é melhor (pathCost é o bellmanFord - caminho minimo no grafo)
                        #if(t[1] > js['distances'][d] + pathCost(HOST,js['source']))





for destino, custo in _distances.items():
        if(key not in matrixDV[:,2]):
            #graph_comment #graph.update({js['source']:{d:js['destination'][d]}})
            _add(key,_destination[key], _source)
        else:
            for t in DVTable:
                for key,val in _distances.items():
                    if(t[2] == key):
                        pass
                        #Comparo para ver se o novo caminho é melhor (pathCost é o bellmanFord - caminho minimo no grafo)
                        #if(t[1] > js['distances'][d] + pathCost(HOST,js['source']))




def listen(HOST,PORT):
    #graph_comment global DVTable,graph
    global DVTable
    listenSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    listenSocket.bind((HOST,PORT))
    while True:
        message, address = listenSocket.recvfrom(2048)
        message = message.decode('latin1')  
        print(message)
        js = json.loads(message)
        _type = js["type"]
        matrixDV = np.array(DVTable)
        if(_type == 'update'):
            update_table(js)
            
        elif(_type == 'data'):
            pass
        elif(_type == 'trace'):
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
    global DVTable
    #graph_comment global graph
    t_start = time.time()
    param = sys.argv[1:] 
    PORT = 55151
    HOST = param[0]
    period = param[1]
    DVTable = [[HOST,0,HOST]]
#graph_comment     graph = defaultdict(dict)

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
