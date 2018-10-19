import socket
import time
import sys
import os
import numpy as np
import json
import threading
import math
import argparse

from collections import defaultdict

lock = threading.Lock()

ips = defaultdict()
global myIP

class Path:
    def __init__(self, cost, nextStep, updatedAt):
        self.cost = cost
        self.nextStep = nextStep
        self.updatedAt = int(round(time.time()))


 def updateMessage(source,dest,distances):
    message = {'type':'update', 'source':source, 'destination':dest, 'distances':distances}
    update_message = json.dumps(message)
    print(update_message)
    return update_message.encode('latin1')

def dataMessage(source, dest, traceMessage):

    message = {'type':'data', 'source':source, 'destination':dest, 'payload': json.dumps(traceMessage)}
    data_message = json.dumps(message)
    #print(data_message)
    return data_message.encode('latin1')

def encodeTraceMessage(source, dest, hops):
    message = {'type':'trace', 'source':source, 'destination':dest, 'hops': hops}
    trace_message = json.dumps(message)
    print("trace_message: {}".format(trace_message))
    return trace_message.encode('latin1')

def decodeTraceMessage(message):
    jsonMessage = json.loads(message.decode('latin1'))
    _type = jsonMessage["type"]
    _source = jsonMessage["source"]
    _destination = jsonMessage["destination"]
    _hops = jsonMessage["hops"]

    return _type, _source, _destination, _hops

# Recebemos um comando de adicionar enlace do CLI
def _add(cost, dest, nextStep):
    global ips

    # Se é um destino novo no nosso dicionario de ips, criamos nossa lista
    if dest not in ips:
        ips[dest] = []

    # Deletamos os caminhos redundantes do nosso histórico, afinal eles não existem mais.
    for idx, path in enumerate(ips[dest]):
        if path.nextStep == nextStep:
            del ips[dest][idx]


    ips[dest].insert(0, new Path(int(cost), nextStep))

# Recebemos um comando de deletar enlace do CLI
def _del(dest):
    global ips
    # Deletamos todos os enlaces virtuais (ou seja, o nextStep é o próprio destino)
    for idx, path in enumerate(ips[dest]):
        if(path.nextStep == dest):
            del ips[dest][idx]

# Recebemos um comando de trace do CLI
def _trace(sourceIP, dest):
    global ips
    _message = encodeTraceMessage(sourceIP, dest, [sourceIP])

    _socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    _socket.sendto(_message, (dest, 55151))
    _socket.close()

def handleTrace(message):
    global myIP

    _type, _source, _destination, _hops = decodeTraceMessage(message)

    # Adicionamos nosso IP ao final do hops
    _hops.append(myIP)
    _traceMessage = {'type':'trace', 'source':_source, 'destination': _destination, 'hops': _hops}

    # Verificamos se somos o destino do trace
    if _destination == myIP:
        _traceSource = _source
        _dataMessage = dataMessage(myIP, _traceSource, _traceMessage)

        nextDestination = _traceSource
        nextMessage = _dataMessage

    else:
    # Se não somos, enviamos o trace para o próximo passo
    #todo balanceamento de carga
        nextDestination = ips[_destination][0].nextStep
        nextMessage = _traceMessage

    _socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    _socket.sendto(nextMessage, (nextDestination, 55151))
    _socket.close()




def executeCommand(line, sourceIP):
    commands = line.split(" ")
    args = commands[1:]
    if(commands[0] == "add"):
        # Source, custo, destino, next step.
        dest, cost = args[0], args[1]
        _add(cost, dest, dest)
    elif(commands[0] == "del"):
        dest = args[0]
        _del(dest)
    elif(commands[0] == "trace"):
        dest = args[0]
        _trace(sourceIP, dest)
    else:
        print("Comando nao reconhecido, tente novamente com [add, del, trace]")



def broadcastDV(HOST, TOUT, PORT): #Envia mensagem do tipo update de tempos em tempos
    global ips
    broadcast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    lock.acquire()

    for _broadcastDestination in ips:
        _currentTime = int(round(time.time()))

        # Split Horizon: Criamos a lista de distancias excluindo os caminhos para nosso destinatário
        # e os caminhos que tem ele como next step.
        distances = [{destino:paths[0].cost} 
        for destino, paths in ips.items() 
        if path[0].nextStep != _broadcastDestination 
        and destino != _broadcastDestination 
        and _currentTime - path[0].updatedAt < TOUT*4]


        print("Distances: {}".format(distances))
        broadcast.sendto(updateMessage(host, _broadcastDestination, distances), (_broadcastDestination, PORT))
        
    threading.Timer(int(TOUT),broadcastDV, args=(HOST, int(TOUT),PORT)).start()
    lock.release()
    broadcast.close()

# Recebemos o anuncio             
def receive_update(js):
    global ips

    # Anunciante
    _anunciante = js["source"]

    # Eu
    _receiver = js["destination"]

    # Endereços conectados no anunciante
    _distances = js["distances"]

    _custoVizinhoAnunciante = ips[_anunciante][0].cost

    print("Receiver: {} Anunciante: {} Custo Vizinho Anunciante: {}".format(_receiver, _anunciante, _custoVizinhoAnunciante))
    # Para cada vizinho no anuncio recebido
    for destinoAnunciado, custoAnunciado in _distances.items():
        if(destinoAnunciado not in ips):
            # Destino não está na tabela
            _add(_custoVizinhoAnunciante + custo, destinoAnunciado, _anunciante)
        else:
            _linkAtual = ips[dest][0]
    
            # O novo caminho é melhor do que o atual?
            if(_custoVizinhoAnunciante + custoAnunciado  < _linkAtual.cost):
                _add(_custoVizinhoAnunciante + custo, destinoAnunciado, _anunciante)
            else:
                # Se o próximo passo para o destino já é o anunciante, atualizamos para o valor recebido
                if(_linkAtual.nextStep == _anunciante):
                    _add(_custoVizinhoAnunciante + custo, destinoAnunciado, _anunciante)

def listen(HOST,PORT):

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
            handleTrace()
         

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
    global ips

    while True:
        for idxIp, ip in enumerate(ips):
            for idxPath, path in enumerate(ip):
                _currentTime = int(round(time.time()))
                if path.updatedAt - _currentTime > (period * 4):
                    del ips[idxIp][idxPath]



def parse_args():
    parser = argparse.ArgumentParser(description = "Parser de argumentos")

    parser.add_argument("--addr", help = "Endereço do roteador", required = False, default = "")
    parser.add_argument("--update-period", help = "Período de atualização", required = False, default = "")
    parser.add_argument("--startup-commands", help = "Comandos de inicialização", required = False, default = "")
    argument = parser.parse_args()
 
    if argument.addr:
        HOST = argument.addr
    else
        sys.argv[1]


     if argument.update_period:
        period = argument.update_period
    else
        sys.argv[2]

    if argument.startup_commands:
        filename = argument.startup_commands
    else if sys.argv[3]:
        filename = sys.argv[3]
    else:
        filename = ""

    return host, int(period), filename

def main():
    global ips, myIP
    t_start = time.time()



    HOST, period, filename = parse_args()
    PORT = 55151
    myIP = HOST

    _add(0, HOST, HOST)

    # Se foi informado um arquivo de startup, lemos ele.
    if filename:
        file = open(filename,"r")
        for line in file:
            executeCommand(line, sourceIP)

    threading.Thread(target=CLI, args=(HOST,)).start()
    threading.Timer(int(period),broadcastDV, args=(HOST, period, PORT)).start()
    threading.Thread(target=listen, args=(HOST,PORT)).start()
    threading.Thread(target=remove_rotas_desatualizadas, args=(period,)).start()

    
#python3 router.py 127.0.0.1 5 file.txt
if __name__ == "__main__":
    main()
