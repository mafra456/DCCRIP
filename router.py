# coding=utf-8

import socket
import time
import sys
import os
import numpy as np
import json
import threading
import math
import argparse
import pdb
from collections import defaultdict


class Path(object):
    def __init__(self, cost, nextStep, updatedAt = ""):
        self.cost = cost
        self.nextStep = nextStep
        self.updatedAt = int(round(time.time()))
        self.LastUsedAt = 0
        self.updated = True
    
    def refresh(self):
        self.updatedAt = int(round(time.time()))

lock = threading.Lock()

ips = defaultdict()
imediateNeighbors = defaultdict()
global myIP
global TOUT


def refresh_path(dest, cost, nextStep):
    for idx, path in enumerate(ips[dest]):
        if path.nextStep == nextStep and path.cost == cost:
            ips[dest][idx].refresh()



def updateMessage(source,dest,distances):
    message = {'type':'update', 'source':source, 'destination':dest, 'distances':distances}
    update_message = json.dumps(message)
    return update_message.encode('latin1')

def dataMessage(source, dest, traceMessage):

    message = {'type':'data', 'source':source, 'destination':dest, 'payload': json.dumps(traceMessage)}
    data_message = json.dumps(message)
    return data_message.encode('latin1')


def errorMessage(source, dest, errorFoundAtRouter, hops):

    message = {'type':'error', 'source':source, 'destination':dest, 'hops': hops, 'payload': "ERROR: A path from {} to {} was not found. Error found @ router: {}".format(source, dest, errorFoundAtRouter)}
    data_message = json.dumps(message)
    return data_message.encode('latin1')

def encodeTraceMessage(source, dest, hops):
    message = {'type':'trace', 'source':source, 'destination':dest, 'hops': hops}
    trace_message = json.dumps(message)
    #LOG print("\ntrace_message: {}".format(trace_message))
    return trace_message.encode('latin1')

def decodeTraceMessage(message):
    jsonMessage = json.loads(message.decode('latin1'))
    _type = jsonMessage["type"]
    _source = jsonMessage["source"]
    _destination = jsonMessage["destination"]
    _hops = jsonMessage["hops"]

    return _type, _source, _destination, _hops

# Recebemos um comando de adicionar enlace
def _add(cost, dest, nextStep):
    global ips

    # Se é um destino novo no nosso dicionario de ips, criamos nossa lista
    if dest not in ips:
        ips[dest] = []

    # Se pra esse destino já existe uma rota com o mesmo nextStep, simplesmente a atualizamos.
    for idx, path in enumerate(ips[dest]):
        if path.nextStep == nextStep:
            ips[dest][idx].cost = cost
            ips[dest][idx].updated = True
            ips[dest][idx].updatedAt = int(round(time.time()))
            #LOG print("Atualizando caminho redudante para {} via {}".format(dest, path.nextStep))
            return 


    ips[dest].insert(0, Path(int(cost), nextStep))

    #LOG print("Inserindo caminho para {} via {}".format(dest, nextStep))
def dumpIps():
    print('\n\n\n–––––––– {}'.format(int(round(time.time()))))

    global ips
    for ip in ips:
        print(ip)
        for path in ips[ip]:
            print("    Cost: {} Next Step: {} UpdatedAt: {} LastUsedAt: {}".format(path.cost, path.nextStep, path.updatedAt, path.LastUsedAt))

# Recebemos um comando de deletar enlace do CLI
def _del(dest):
    global ips
    # Deletamos todos os enlaces virtuais (ou seja, o nextStep é o próprio destino)
    for idx, path in enumerate(ips[dest]):
        if(path.nextStep == dest):
            del ips[dest][idx]

# Recebemos um comando de trace do CLI
def _trace(dest):
    global ips, myIP
    _message = encodeTraceMessage(myIP, dest, [myIP])
    
    if(dest not in ips):
        print("\nERRO PATH_NOT_FOUND: Caminho não encontrado para {}".format(dest))
    else:
        nextStep = findNextStep(dest)

        # Se encontramos um nextStep para encaminhar nosso trace, podemos prosseguir
        if(nextStep != math.inf):
            #LOG print("\nMensagem de Trace enviada para {} com destino a {}".format(nextStep, dest))
            _socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
            _socket.sendto(_message, (nextStep, 55151))
            _socket.close()
        else:
            #LOG EXTRA: Se não, enviamos uma mensagem para a origem (nós mesmos) dizendo que não existe caminho
            print("\nERRO PATH_NOT_FOUND: Caminho não encontrado para {}".format(dest))



def _validTime(path):
    global TOUT
    _currentTime = int(round(time.time()))
    return (_currentTime - path.updatedAt < (TOUT * 4))



# Aqui implementamos o balanceamento de carga
def findNextStep(dest):
    possiblePaths = []
    nextStep = math.inf
    nextStepPathIdx = math.inf
    minLastUsedAt = math.inf

    minCost = math.inf
    #pdb.set_trace()


    # Nesses dois fors, pegamos as rotas com o menor custo.
    for pathIdx, path in enumerate(ips[dest]): 
        if path.cost < minCost:
            minCost = path.cost

    for pathIdx, path in enumerate(ips[dest]): 
        if path.cost <= minCost:
            possiblePaths.append([pathIdx, path])

   
    # Agora temos todos os nextSteps possíveis e válidos. 
    # Vamos agora pegar o que não foi usado por mais tempo, garantindo assim nosso balanceamento de carga.
    for pathIdx, possiblePath in possiblePaths:
        if possiblePath.LastUsedAt < minLastUsedAt:
            minLastUsedAt = possiblePath.LastUsedAt
            nextStep = possiblePath.nextStep
            nextStepPathIdx = pathIdx

    # Se foi encontrado um caminho, atualizamos seu LastUsedAt para garantir o balacenamento
    if nextStep != math.inf:
        ips[dest][nextStepPathIdx].LastUsedAt = int(round(time.time()))
    return nextStep




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
        #LOG print("\nMensagem de Data enviada para {}".format(nextDestination))


    else:
    # Se não somos, enviamos o trace para o próximo passo
        nextDestination = findNextStep(_destination)

        # EXTRA: Caso não seja encontrado um próximo caminho, enviamos uma mensagem do tipo error para a origem do trace.
        if(nextDestination == math.inf):
            print("\nMensagem de ERRO: PATH_NOT_FOUND")
            nextMessage = errorMessage(_source, _destination, myIP, _hops)
            nextDestination = _source
        else:
            # Se achamos um próximo passo, encaminhamos a mensagem de trace.
            nextMessage = _traceMessage
            nextMessage = json.dumps(nextMessage)
            nextMessage = nextMessage.encode('latin1')
            print("\nMensagem de Trace re-enviada para {}".format(nextDestination))


    
    _socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    _socket.sendto(nextMessage, (nextDestination, 55151))
    _socket.close()




def executeCommand(line):
    commands = line.split(" ")
    args = commands[1:]
    command = commands[0].strip()
    if(command == "add"):
        # Source, custo, destino, next step.
        dest, cost = args[0], args[1]
        # Salvamos o vizinho imediato com o tempo de atualização
        imediateNeighbors[dest] = int(round(time.time()))
        _add(cost, dest, dest)
    elif(command == "del"):
        dest = args[0]
        _del(dest)
    elif(command == "trace"):
        dest = args[0]
        _trace(dest)
    elif(command == "dump"):
        dumpIps()
    #else:
    #    print("\n{}: Comando nao reconhecido, tente novamente com [add, del, trace]".format(command))





def sendDistances(TOUT, PORT): #Envia mensagem do tipo update de tempos em tempos
    global ips, myIP, imediateNeighbors

    _socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    lock.acquire()

    for _imediateNeighbor, _neighborUpdatedAt in imediateNeighbors.items():

        _currentTime = int(round(time.time()))

        distances = []

        # Split Horizon: Criamos a lista de distancias excluindo os caminhos para nosso destinatário
        # e os caminhos que tem ele como next step.
        for destino, paths in ips.items():
            # Se não temos caminho para esse destino, não enviamos nada
            if len(paths) == 0:
                continue

            # Não enviamos caminhos para nosso destinatário
            if destino == _imediateNeighbor:
                continue

            if destino == myIP:
                continue

            # Não enviamos rotas aprendidas do nosso destinatário
            if paths[0].nextStep == _imediateNeighbor:
                continue

            distances.append({destino:paths[0].cost}) 

        _socket.sendto(updateMessage(myIP, _imediateNeighbor, distances), (_imediateNeighbor, PORT))
        
    threading.Timer(int(TOUT),sendDistances, args=(int(TOUT),PORT)).start()
    lock.release()
    _socket.close()



# Marcamos os caminhos como não atualizados
def mark_paths_as_non_updated(neighbor):
    global ips

    for ip, paths in ips.items():
        for idx_path, path in enumerate(paths):
            if(path.nextStep == neighbor):
                ips[ip][idx_path].updated = False


def delete_non_updated_paths(neighbor):
    global ips

    for ip, paths in ips.items():
        for idx_path, path in enumerate(paths):
            # Não deletamos um caminho direto, por isso a 3a condicao do if
            if(path.nextStep == neighbor and path.updated == False and ip != neighbor):
                #print("Deletando caminho para {} via {}".format(ip, path.nextStep))
                del ips[ip][idx_path]


# Não recebemos distancias de roteadores que temos ligação direta, portanto usamos essa função pra atualizar essas ligações sempre que recebmos uma mensagem de distancia.
def update_direct_path(neighbor):
    global ips
    for idx_path, path in enumerate(ips[neighbor]):
        if(path.nextStep == neighbor):
            ips[neighbor][idx_path].updatedAt = int(round(time.time()))

# Recebemos o anuncio             
def receive_update(js):
    global ips, imediateNeighbors

    _anunciante = js["source"]
    _receiver = js["destination"]
    _distances = js["distances"]
    _custoVizinhoAnunciante = ips[_anunciante][0].cost

    imediateNeighbors[_anunciante] = int(round(time.time()))
    # Atualizamos o updatedAt do caminho direto para o anunciante
    update_direct_path(_anunciante)

    # Marcamos todos os caminhos como não atualizados. Assim conseguiremos manter um registro de quais foram recebidos agora.
    mark_paths_as_non_updated(_anunciante)

    # Para cada vizinho no anuncio recebido
    for _distance in _distances:
        for destinoAnunciado, custoAnunciado in _distance.items():
            if(destinoAnunciado not in ips):
                # Destino não está na tabela
                _add(_custoVizinhoAnunciante + custoAnunciado, destinoAnunciado, _anunciante)
            else:
                _pathsCount = len(ips[destinoAnunciado])
                # Talvez o ip esteja na tabela, mas sem nenhum caminho. Nesse caso simplesmente adicionamos ele.
                if(_pathsCount == 0):
                    _add(_custoVizinhoAnunciante + custoAnunciado, destinoAnunciado, _anunciante)
                else:
                    # Já existe um link para este destino anunciado
                    _linkAtual = ips[destinoAnunciado][0]
            
                    # O novo caminho é melhor do que o atual?
                    if(_custoVizinhoAnunciante + custoAnunciado  < _linkAtual.cost):
                        _add(_custoVizinhoAnunciante + custoAnunciado, destinoAnunciado, _anunciante)
                    else:
                        # Se o próximo passo para o destino já é o anunciante, atualizamos para o valor recebido
                        if(_linkAtual.nextStep == _anunciante):
                            _add(_custoVizinhoAnunciante + custoAnunciado, destinoAnunciado, _anunciante)
                        elif(_custoVizinhoAnunciante + custoAnunciado  == _linkAtual.cost):
                            # Neste caso temos uma rota alternativa. Matemos isso pelo reroteamento imediato.
                            _add(_custoVizinhoAnunciante + custoAnunciado, destinoAnunciado, _anunciante)
                   
    
    # Deletamos todos os caminhos que não foram atualizados, ou seja, não existem mais
    delete_non_updated_paths(_anunciante)

def listen(HOST,PORT):

    listenSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    listenSocket.bind((HOST,PORT))
    while True:
        message, address = listenSocket.recvfrom(2048)
        decoded_message = message.decode('latin1')  
        js = json.loads(decoded_message)
        #print("\n Message Listened: {}".format(js))
        
        _type = js["type"]
        if(_type == 'update'):
            receive_update(js)
            
        elif(_type == 'data'):
            #print("\n Received {} From {}".format(js["type"], js["source"]))
            print(js)
            pass
        elif(_type == 'trace'):
            #print("\n Received {} From {}".format(js["type"], js["source"]))
            handleTrace(message)
        elif(_type == 'error'):
            #print("\n{} \n Hops: {}".format(js["payload"], js["hops"]))
            handleTrace(message)
         

def CLI():
    line = ""
    try:
        while(True):
            line = input()
            if(line == "quit"):
                print("\nTermino da Execucao")
                os._exit(1)
            else:
                executeCommand(line)
    except KeyboardInterrupt:
        print("\nTermino da Execucao")
        os._exit(1)


def removeRotasDesatualizadas(TOUT):
    global ips, myIP, imediateNeighbors

    while True:
        oldNeighbors = []
        _currentTime = int(round(time.time()))

        # Checa pela última vez que recebemos uma atualização de um vizinho imediato
        for _imediateNeighbor, _neighborUpdatedAt in imediateNeighbors.items():
            if _currentTime - _neighborUpdatedAt >= (TOUT * 4):
                oldNeighbors.append(_imediateNeighbor)
        
        # Apagamos todas as rotas que tem esse vizinho como próximo passo
        for ip in ips.copy():
            for idxPath, path in enumerate(ips[ip]):
                if path.nextStep in oldNeighbors:
                    del ips[ip][idxPath]




def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--addr", help = "Endereço do roteador", required = False)
    parser.add_argument("--update-period", help = "Período de atualização", required = False)
    parser.add_argument("--startup-commands", help = "Comandos de inicialização", required = False)

    argument, unknown = parser.parse_known_args()


    if argument.addr:
        HOST = argument.addr
    else:
        HOST = sys.argv[1]


    if argument.update_period:
        period = argument.update_period
    else:
        period = sys.argv[2]

    if argument.startup_commands:
        filename = argument.startup_commands
    elif len(sys.argv) > 3:
        filename = sys.argv[3]
    else:
        filename = ""

    return HOST, int(period), filename

def main():
    global ips, myIP, TOUT, imediateNeighbors
    t_start = time.time()


    HOST, TOUT, filename = parse_args()
    print(HOST)
    PORT = 55151
    myIP = HOST

    _add(0, HOST, HOST)

    # Se foi informado um arquivo de startup, lemos ele.
    if filename:
        file = open(filename,"r")
        for line in file:
            executeCommand(line)
    threading.Thread(target=CLI, args=()).start()
    threading.Timer(int(TOUT),sendDistances, args=(TOUT, PORT)).start()
    threading.Thread(target=listen, args=(HOST,PORT)).start()
    threading.Thread(target=removeRotasDesatualizadas, args=(TOUT,)).start()

    
#python3 router.py 127.0.1.1 5 input.txt
if __name__ == "__main__":
    main()
