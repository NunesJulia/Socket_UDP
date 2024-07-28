import random
import threading
import socket
from datetime import datetime
import os
import math
import struct
import time

# Configuração do Cliente
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client.bind(("localhost", random.randint(8000, 9000)))

# Armazenamento de fragmentos recebidos
frags_received_list = []
frags_received_count = 0

# Variáveis de controle de ACK
ack_received = {}
ack_lock = threading.Lock()
ack_timeout = 2  # Tempo de espera para o ACK em segundos

# Calculo Checksum
def calcula_checksum(data):
    checksum = 0
    for byte in data:
        checksum = (checksum + byte) & 0xFF
    return checksum

# Verificação da Integridade dos dados recebidos por meio de desempacotamento e reagrupação
def unpack_and_reassemble(data):
    global frags_received_count, frags_received_list

    header = data[:24]
    message_in_bytes = data[24:]
    frag_size, frag_index, frags_numb, checksum, message_id, frag_index = struct.unpack('!IIIIII', header)

    # Verifica Checksum
    if checksum != calcula_checksum(message_in_bytes):
        print("Fragmento com checksum inválido, ignorando.")
        return

    if len(frags_received_list) < frags_numb:
        add = frags_numb - len(frags_received_list)
        frags_received_list.extend([None] * add)

    frags_received_list[frag_index] = message_in_bytes  # Armazena o fragmento na lista na posição correta
    frags_received_count += 1

    # Verifica se todos os fragmentos foram recebidos e reseta a lista para o próximo pacote ou se houve perda de pacote
    if frags_received_count == frags_numb:
        with open('received_message.txt', 'wb') as file:
            for fragment in frags_received_list:
                file.write(fragment)
        frags_received_count = 0
        frags_received_list = []
        print_received_message()  # Aqui há uma diferença da versão do cliente e servidor
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
    global ack_received, ack_lock
    while True:
        data, addr = client.recvfrom(1024)
        if data.startswith(b'ACK'):
            _, message_id = struct.unpack('!II', data[3:11])
            with ack_lock:
                ack_received[message_id] = True
        else:
            _, message_id, frag_index = struct.unpack('!III', data[:12])
            ack_data = struct.pack('!II', len(data), message_id)
            client.sendto(b'ACK' + ack_data, addr)
            unpack_and_reassemble(data)

thread1 = threading.Thread(target=receive)
thread1.start()

# Cria um Fragmento
def create_fragment(payload, frag_size, frag_index, frags_numb, message_id):
    data = payload[:frag_size]
    checksum = calcula_checksum(data)
    header = struct.pack('!IIIIII', frag_size, frag_index, frags_numb, checksum, message_id, frag_index)
    return header + data

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
            print(f"Usuario {username}, você está conectado.")
        # Trata a saída do usuário
        elif username and message == "bye":
            sent_msg = f"SIGNOUT_TAG:{username}"
            with open('message_client.txt', 'w') as file:
                file.write(sent_msg)
            send_txt()
            print("Conexão encerrada, Até logo!")
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
                print("Para conectar a sala digite 'hi, meu nome eh' e digite seu username")

# Função que manda a mensagem
def send_txt():
    global ack_received, ack_lock
    frag_index = 0
    frag_size = 1008

    with open('message_client.txt', 'rb') as file:
        payload = file.read()
        frags_numb = math.ceil(len(payload) / frag_size)  # Calcula o número de fragmentos
        message_id = int(time.time() * 1000) & 0xFFFFFFFF  # ID único baseado no timestamp

        while payload:
            fragment = create_fragment(payload, frag_size, frag_index, frags_numb, message_id)
            send_with_ack(fragment, message_id)
            payload = payload[frag_size:]
            frag_index += 1
    os.remove('message_client.txt')

# Função de enviar dados com ACK
def send_with_ack(data, message_id):
    global ack_received, ack_lock
    retries = 3
    while retries > 0:
        with ack_lock:
            ack_received[message_id] = False
        client.sendto(data, ('localhost', 7777))
        print("Fragmento enviado, aguardando ACK...")
        start_time = time.time()
        while time.time() - start_time < ack_timeout:
            with ack_lock:
                if ack_received.get(message_id, False):
                    print("ACK recebido.")
                    return
            time.sleep(0.1)
        print("Tempo de espera do ACK esgotado, reenviando fragmento...")
        retries -= 1
    if not ack_received.get(message_id, False):
        print(f"Não foi possível obter ACK após {3 - retries} tentativas.")

main()
