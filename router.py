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

    # Mantemos essa variável p sermos capazes de identificar rotas desatualizadas.
    _record_updated_at = int(round(time.time()))

    cost = int(cost)
    DVTable.append([sourceIP, cost, dest, nextStep, _record_updated_at])
    # Só adicionamos na oposta caso o destino seja igual ao próximo passo.
    # Nesse caso, é uma ligação direta e sabemos q o caminho inverso é o melhor para o outro.
    if(nextStep == dest):
        DVTable.append([dest, cost, sourceIP, sourceIP, _record_updated_at])
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

    # Crio minha tabela de distancias
#    distances = {dist[2]:dist[1] for dist in DVTable}

    # Crio e envio tabela todos os meus vizinhos
    for _broadcastSource, _cost, _broadcastDestination, _nextStep in DVTable: 
        # Não incluímos rotas para _broadcastDestination nem rotas que tem ela como next step. Split Horizon.
        distances = [vizinho[2]:vizinho[1] for line in DVTable if vizinho[2] != _broadcastDestination && vizinho[3] != _broadcastDestination]
        # TODO TEST.
        print("Distances: {}".format(distances))
        broadcast.sendto(updateMessage(_broadcastSource, _broadcastDestination, distances), (_broadcastDestination, PORT))
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

# !!!  Essa função só deve ser utilizada entre nós vizinhos.
def getCustoVizinho(source, dest):
    global DVTable
    for _source, _cost, _dest, _nextStep in DVTable:
        if source == _source && dest == _dest:
            return _cost 

def getNextStep(source, dest):
    global DVTable
    for _source, _cost, _dest, _nextStep in DVTable:
        if source == _source && dest == _dest:
            return _nextStep 

def getTableLine(source, dest):
    global DVTable
    for idx, line in enumerate(DVTable):
        _source, _cost, _dest, _nextStep = line
        if(_source == source && _dest == dest):
            return DVTable[idx]

def updatePath(source, newCost, dest, newNextStep):
    global DVTable
    for idx, line in enumerate(DVTable):
        _source, _cost, _dest, _nextStep = line
        if(_source == source && _dest == dest):
            _current_time_in_seconds = int(round(time.time()))
            DVTable[idx] = [source, newCost, dest, newNextStep, _current_time_in_seconds]

def bellmanFord():
    print('')


# Recebemos o anuncio`1             
def receive_update(js):
    global DVTable

    # Os vizinhos deste roteador
    _meus_vizinhos = np.array(DVTable)[:,2]

    # Anunciante
    _anunciante = js["source"]

    # Eu
    _receiver = js["destination"]

    # Endereços conectados no anunciante
    _distances = js["distances"]

    _custo_vizinho_anunciante = getCustoVizinho(_receiver, _anunciante)
    

    print("Receiver: {} Anunciante: {} Custo Vizinho Anunciante: {}".format(_receiver, _anunciante, _custo_vizinho_anunciante))
    # Para cada vizinho no anuncio recebido
    for destino, custo in _distances.items():
        if(destino not in _meus_vizinhos):
            # Destino não está na tabela
            _add(_receiver, _custo_vizinho_anunciante + custo, destino, _anunciante)
        else:
            _linha_receiver_destino = getTableLine(_receiver, destino)
             _custo_atual = _linha_receiver_destino[1]
            _nextStep_destino = _linha_receiver_destino[3]

            # Vale a pena atualizar o destino?
            if(_custo_vizinho_anunciante + custo  < _custo_atual):
                updatePath(_receiver, _custo_vizinho_anunciante + custo, destino, _anunciante)
            else:
                # Se o próximo passo para o destino já é o anunciante, atualizamos para o valor recebido
                if(_nextStep_destino == _anunciante):
                    updatePath(_receiver, _custo_vizinho_anunciante + custo, destino, _anunciante)



def listen(HOST,PORT):
    #graph_comment global DVTable,graph

    listenSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    listenSocket.bind((HOST,PORT))
    while True:
        message, address = listenSocket.recvfrom(2048)
        message = message.decode('latin1')  
        print(message)
        js = json.loads(message)
        _type = js["type"]
        if(_type == 'update'):
            receive_update(js)
            
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


def remove_rotas_desatualizadas(period):
    while True:
        global DVTable
        for idx, line in enumerate(DVTable):
            _record_updated_at = line[4]
            _current_time_in_seconds = int(round(time.time()))
            if _record_updated_at - _current_time_in_seconds > (period * 4):
                del DVTable[idx]



def main():
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
    threading.Thread(target=remove_rotas_desatualizadas, args=(period,)).start()

    
#python3 router.py 127.0.0.1 5 file.txt
if __name__ == "__main__":
    main()
