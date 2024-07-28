import random
import threading
import socket
from datetime import datetime
import os
import math
import struct
from zlib import crc32
import time

# Configuração do Cliente 
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client.bind(("localhost", random.randint(8000, 9000)))

# Armazenamento de fragmentos recebidos
frags_received_list = []
frags_received_count = 0

#Variaveis relacionadas ao RDT 3.0
timeout = 2  # Timeout de 2 segundos
lock = threading.Lock()

# Função que faz o calculo do Checksum
def calcula_checksum(data):
    checksum = 0
    for byte in data:
        checksum = (checksum + byte) & 0xFF
    return checksum

# Função para verificar se recebeu ACK
def ack_received():
    global ack_received_flag
    ack_received_flag = True
    print("ack recebido")

# Verificação da Integridade dos dados recebidos por meio de desempacotamento e reagrupação 
def unpack_and_reassemble(data):
    global frags_received_count, frags_received_list

    header = data[:16]
    message_in_bytes = data[16:]
    frag_size, frag_index, frags_numb, checksum = struct.unpack('!IIII', header)

    # Verifica Checksum
    if checksum != calcula_checksum(message_in_bytes):
        print("Fragmento com checksum inválido, ignorando.")
        return

    if len(frags_received_list) < frags_numb: 
        add = frags_numb - len(frags_received_list)
        frags_received_list.extend([None] * add)
    frags_received_list[frag_index] = message_in_bytes # Armazena o fragmento na lista na posição correta
    frags_received_count += 1
    
    # Verifica se todos os fragmentos foram recebidos e reseta a lista para o proximo pacote ou se houve perda de pacote
    if frags_received_count == frags_numb:
        with open('received_message.txt', 'wb') as file:
            for fragment in frags_received_list:
                file.write(fragment)
        frags_received_count = 0 
        frags_received_list = []
        print_received_message()  #Aqui há uma diferença da versão do cliente e servidor
    elif (frags_received_count < frags_numb) and (frag_index == frags_numb - 1):
        print("Provavelmente houve perda de pacotes")
        frags_received_count = 0
        frags_received_list = []

# Lê o arquivo txt e printa a mensagem
def print_received_message():
    with open('received_message.txt', 'r') as file:
        file_content = file.read()
    os.remove('received_message.txt')
    print(file_content)

# Função que trata o recebimento da mensagem
def receive():
    while True:
        data, addr = client.recvfrom(1024)
        header = data[:16]
        message_type = struct.unpack('!I', header[:4])[0]
        
        #Se a mensagem recebida for um ack, altera a flag de Ack para True
        if message_type == 1:  # ACK
            ack_received()
        #Se a mensagem recebida NÃO for um ack: Trata a mensagem
        else:
            unpack_and_reassemble(data)

thread1 = threading.Thread(target=receive)
thread1.start()

# Cria um Fragmento
def create_fragment(payload, frag_size, frag_index, frags_numb):
    data = payload[:frag_size]
    checksum = calcula_checksum(data)
    header = struct.pack('!IIII', frag_size, frag_index, frags_numb, checksum)
    return header + data

def send_fragment(fragment, addr):
    global ack_received_flag
    ack_received_flag = False
    #Loop de ack
    while not ack_received_flag: #Enquanto a função "Ack Received" não transformar a flag em True, reenvia a mensagem"
        client.sendto(fragment, addr)

        start = time.time()
        while time.time() - start < timeout:
                if ack_received_flag:
                    print("Ack recebido! (send fragment) \n ---------------------------------")
                break

def main():
    username = ''
    # Loop principal
    while True:
        message = input("")
        # Trata o login ideal do usuario
        if message.startswith("hi, meu nome eh") or message.startswith("Hi, meu nome eh"):
            username = message[len("hi, meu nome eh") + 1:].strip()
            sent_msg = f"SIGNUP_TAG:{username}"
            with open('message_client.txt', 'w') as file:
                file.write(sent_msg)
            send_txt()
            print(f"Usuario {username}, você está conectado.")
        
        # Trata a saida do usuario
        elif username and message == "bye":
            sent_msg = f"SIGNOUT_TAG:{username}"
            with open('message_client.txt', 'w') as file:
                file.write(sent_msg)
            send_txt()
            print("Conexão encerrada, Até logo!")
            exit()  # Encerra a conexão
        # Trata a mensagem do usuario
        else:
            if username:
                timestamp = datetime.now().strftime('%H:%M:%S - %d/%m/%Y')
                formatted_message = f"{client.getsockname()[0]}:{client.getsockname()[1]}/~{username}: {message} {timestamp}"
                with open('message_client.txt', 'w') as file:
                    file.write(formatted_message)
                send_txt()
            else:
                print("Para conectar a sala digite 'hi, meu nome eh' e digite seu username")

# Função que manda a mensagem
def send_txt():
    frag_index = 0
    frag_size = 1008
    with open('message_client.txt', 'rb') as file:
        payload = file.read()
        frags_numb = math.ceil(len(payload) / frag_size)  # Calcula o numero de fragmentos
        while payload:
            fragment = create_fragment(payload, frag_size, frag_index, frags_numb)
            send_fragment(fragment, ('localhost', 7777))
            payload = payload[frag_size:]
            frag_index += 1
    os.remove('message_client.txt')

main()
