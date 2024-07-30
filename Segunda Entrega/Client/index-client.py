import random
import threading
import socket
import struct
import time
import os
import math
from datetime import datetime

# Configuração do Cliente 
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client.bind(("localhost", random.randint(8000, 9000)))

# Armazenamento de fragmentos recebidos
frags_received_list = []
frags_received_count = 0

# Variáveis relacionadas ao RDT 3.0
timeout = 2  # Timeout de 2 segundos
ack_received_flag = False
lock = threading.Lock()

# Função que faz o cálculo do Checksum
def calcula_checksum(data):
    checksum = 0
    for byte in data:
        checksum = (checksum + byte) & 0xFF
    return checksum

# Função para verificar se recebeu ACK
def ack_received():
    global ack_received_flag
    ack_received_flag = True

# Verificação da integridade dos dados recebidos por meio de desempacotamento e reagrupação
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
    frags_received_list[frag_index] = message_in_bytes  # Armazena o fragmento na lista na posição correta
    frags_received_count += 1

    # Envia ACK após receber o fragmento
    send_ack()

    # Verifica se todos os fragmentos foram recebidos e reseta a lista para o próximo pacote ou se houve perda de pacote
    if frags_received_count == frags_numb:
        with open('received_message.txt', 'wb') as file:
            for fragment in frags_received_list:
                file.write(fragment)
        frags_received_count = 0
        frags_received_list = []
        print_received_message()
    elif (frags_received_count < frags_numb) and (frag_index == frags_numb - 1):
        print("Provavelmente houve perda de pacotes")
        frags_received_count = 0
        frags_received_list = []

# Lê o arquivo txt e printa a mensagem
def print_received_message():
    with open('received_message.txt', 'r') as file:
        file_content = file.read()
    print(file_content)

# Função para enviar ACK
def send_ack():
    ack_packet = struct.pack('!I', 1)
    client.sendto(ack_packet, ('localhost', 7777))


# Função que trata o recebimento da mensagem
def receive():
    global ack_received_flag
    while True:
        data, addr = client.recvfrom(1024)
        header = data[:16]
        message_type = struct.unpack('!I', header[:4])[0]

        # Se a mensagem recebida for um ACK, altera a flag de ACK para True
        if message_type == 1:  # ACK
            ack_received_flag = True
        # Se a mensagem recebida NÃO for um ACK: Trata a mensagem
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
    # Loop de ACK
    while not ack_received_flag:  # Enquanto a função "ACK Received" não transformar a flag em True, reenvia a mensagem
        client.sendto(fragment, addr)
        start = time.time()
        while time.time() - start < timeout:
            if ack_received_flag:
                break

def main():
    username = ''
    # Loop principal
    while True:
        message = input("")
        # Trata o login ideal do usuário
        if message.startswith("hi, meu nome eh") or message.startswith("Hi, meu nome eh"):
            username = message[len("hi, meu nome eh") + 1:].strip()
            sent_msg = f"SIGNUP_TAG:{username}"
            with open('message_client.txt', 'w') as file:
                file.write(sent_msg)
            send_txt()
            print(f"Usuário {username}, você está conectado.")
        # Trata a saída do usuário
        elif username and message == "bye":
            sent_msg = f"SIGNOUT_TAG:{username}"
            with open('message_client.txt', 'w') as file:
                file.write(sent_msg)
            send_txt()
            print("Conexão encerrada, até logo!")
            exit()  # Encerra a conexão
        # Trata a mensagem do usuário
        else:
            if username:
                timestamp = datetime.now().strftime('%H:%M:%S - %d/%m/%Y')
                formatted_message = f"{client.getsockname()[0]}:{client.getsockname()[1]}/~{username}: {message} {timestamp}"
                with open('message_client.txt', 'w') as file:
                    file.write(formatted_message)
                send_txt()
            else:
                print("Para conectar à sala digite 'hi, meu nome eh' e digite seu username")

# Função que manda a mensagem
def send_txt():
    frag_index = 0
    frag_size = 1008
    with open('message_client.txt', 'rb') as file:
        payload = file.read()
        frags_numb = math.ceil(len(payload) / frag_size)  # Calcula o número de fragmentos
        while payload:
            fragment = create_fragment(payload, frag_size, frag_index, frags_numb)
            send_fragment(fragment, ('localhost', 7777))
            payload = payload[frag_size:]
            frag_index += 1
    os.remove('message_client.txt')

main()
