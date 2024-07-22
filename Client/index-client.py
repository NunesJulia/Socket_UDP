import random
import threading
import socket
from datetime import datetime
import os
import math
from zlib import crc32
import struct

# Configuração do Cliente 
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client.bind(("localhost", random.randint(8000, 9000)))

# Armazenamento de fragmentos recebidos
frags_received_list = []
frags_received_count = 0

def calcula_checksum(data):
    checksum = 0
    for byte in data:
        checksum = (checksum + byte) & 0xFF
    return checksum

# Verificação da Integridade dos dados recebidos por meio de desempacotamento e reagrupação 
def unpack_and_reassemble(data):
    global frags_received_count, frags_received_list

    header = data[:20] 
    message_in_bytes = data[20:] 
    frag_size, frag_index, frags_numb, crc, checksum = struct.unpack('!IIIII', header) 

    # Verifica CRC
    if crc != crc32(message_in_bytes): # ----------------> Essa função calcula o CRC32 da mensagem e cerifica se possui o mesmo valor do informado pelo cabeçalho
        print("Fragmento com CRC inválido, ignorando.")
        return

    # Verifica Checksum
    if checksum != calcula_checksum(message_in_bytes):
        print("Fragmento com checksum inválido, ignorando.")
        return

    if len(frags_received_list) < frags_numb: 
        add = frags_numb - len(frags_received_list)
        frags_received_list.extend([None] * add)

    frags_received_list[frag_index] = message_in_bytes # Armazena o fragmento na lista na posição correta
    frags_received_count += 1

    #Seta o ack agora no cliente
    ack_packet = struct.pack('!I', frag_index)
    client.sendto(ack_packet)
    print("Ack enviado")

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

#Lê o arquivo txt e printa a mensagem
def print_received_message():
    with open('received_message.txt', 'r') as file:
        file_content = file.read()
    os.remove('received_message.txt')
    print(file_content)

#Função que trata o recebimento da mensagem
def receive():
    while True:
        data, addr = client.recvfrom(1024)
        unpack_and_reassemble(data) 


thread1 = threading.Thread(target=receive)
thread1.start()

#Cria um Fragmento
def create_fragment(payload, frag_size, frag_index, frags_numb):
    data = payload[:frag_size]
    crc = crc32(data)
    checksum = calcula_checksum(data)
    header = struct.pack('!IIIII', frag_size, frag_index, frags_numb, crc, checksum)
    return header + data


def main():
    username = ''
    print("Para conectar a sala digite 'hi, meu nome eh' e digite seu username")
    #Loop principal
    while True:
        message = input("")
        #Trata o login ideal do usuario
        if message.startswith("hi, meu nome eh") or message.startswith("Hi, meu nome eh"):
            username = message[len("hi, meu nome eh") + 1:].strip()
            sent_msg = f"SIGNUP_TAG:{username}"
            with open('message_client.txt', 'w') as file:
                file.write(sent_msg)
            send_txt()
            print(f"Usuario {username}, você está conectado.")
        
        #Trata a saida do usuario
        elif username and message == "bye":
            sent_msg = f"SIGNOUT_TAG:{username}"
            with open('message_client.txt', 'w') as file:
                file.write(sent_msg)
            send_txt()
            print("Conexão encerrada, Até logo!")
            exit() #Encerra a conexão

        #Trata a mensagem do usuario
        else:
            if username:
                timestamp = datetime.now().strftime('%H:%M:%S - %d/%m/%Y')
                formatted_message = f"{client.getsockname()[0]}:{client.getsockname()[1]}/~{username}: {message} {timestamp}"
                with open('message_client.txt', 'w') as file:
                    file.write(formatted_message)
                send_txt()
            else:
                print("Para conectar a sala digite 'hi, meu nome eh' e digite seu username")

#Função que manda a mensagem
def send_txt():
    frag_index = 0
    frag_size = 1008

    with open('message_client.txt', 'rb') as file:
        payload = file.read()
        frags_numb = math.ceil(len(payload) / frag_size) #Calcula o numero de fragmentos

        while payload:
            fragment = create_fragment(payload, frag_size, frag_index, frags_numb)
            while True:
                client.sendto(fragment, ('localhost', 7777))
                try:
                    client.settimeout(1)
                    ack, _ = client.recvfrom(1024)
                    print("TESTE: MENSAGEM DO SERVIDOR, ACK RECEBIDO")
                    ack_index = struct.unpack('!I', ack)[0]
                    if ack_index == frag_index:
                        break
                except socket.timeout:
                    print(f"MENSGEM DO SERVIDOR: Desculpe! parece que ocorreu um erro enviando sua mensagem! Reenviando... Timeout: reenviando fragmento {frag_index}")
            
            payload = payload[frag_size:]
            frag_index += 1
    os.remove('message_client.txt')


main()