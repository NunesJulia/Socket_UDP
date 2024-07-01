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
numeroSequenciaEsperado = 0
TIMEOUT = 2

# Verificação da Integridade dos dados recebidos por meio de desempacotamento e reagrupação 
def unpack_and_reassemble(data):
    global frags_received_count, frags_received_list, numeroSequenciaEsperado

    if len(data) < 16:
        print("Pacote recebido com tamanho insuficiente, ignorando.")
        return

    header = data[:16]
    message_in_bytes = data[16:]
    frag_size, frag_index, frags_numb, crc = struct.unpack('!IIII', header)

    # Verifica CRC
    if crc != crc32(message_in_bytes):
        print("Fragmento com CRC inválido, ignorando.")
        mandaAck(numeroSequenciaEsperado - 1)
        return
    
    if frag_index != numeroSequenciaEsperado:
        print(f"Fragmento fora de sequência, ignorando. Esperado: {numeroSequenciaEsperado}, Recebido: {frag_index}")
        mandaAck(numeroSequenciaEsperado - 1)  # Enviar ACK do último pacote recebido com sucesso
        return

    if len(frags_received_list) < frags_numb: 
        add = frags_numb - len(frags_received_list)
        frags_received_list.extend([None] * add)

    frags_received_list[frag_index] = message_in_bytes # Armazena o fragmento na lista na posição correta
    frags_received_count += 1
    numeroSequenciaEsperado += 1

    mandaAck(frag_index)

    # Verifica se todos os fragmentos foram recebidos e reseta a lista para o próximo pacote ou se houve perda de pacote
    if frags_received_count == frags_numb:
        with open('received_message.txt', 'wb') as file:
            for fragment in frags_received_list:
                file.write(fragment)
        frags_received_count = 0 
        frags_received_list = []
        numeroSequenciaEsperado = 0
        print_received_message()

    elif (frags_received_count < frags_numb) and (frag_index == frags_numb - 1):
        print("Provavelmente houve perda de pacotes")
        frags_received_count = 0
        frags_received_list = []
        numeroSequenciaEsperado = 0

def mandaAck(frag_index):
    ack = struct.pack('!I', frag_index)
    client.sendto(ack, ('localhost', 7777))
    print(f"ACK do pacote {frag_index} enviado")

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
        unpack_and_reassemble(data)

thread1 = threading.Thread(target=receive)
thread1.start()

# Cria um Fragmento
def create_fragment(payload, frag_size, frag_index, frags_numb):
    data = payload[:frag_size]
    crc = crc32(data)
    header = struct.pack('!IIII', frag_size, frag_index, frags_numb, crc)
    return header + data

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
        
        # Trata a saída do usuário
        elif username and message == "bye":
            sent_msg = f"SIGNOUT_TAG:{username}"
            with open('message_client.txt', 'w') as file:
                file.write(sent_msg)
            send_txt()
            print("Conexão encerrada, Até logo!")
            exit()

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
    frag_index = 0
    frag_size = 1024

    with open('message_client.txt', 'rb') as file:
        payload = file.read()
        frags_numb = math.ceil(len(payload) / frag_size) # Calcula o número de fragmentos

        while payload:
            mandaFragmento(payload[:frag_size], frag_index, frags_numb)
            payload = payload[frag_size:]
            frag_index += 1
    os.remove('message_client.txt')

def mandaFragmento(fragment, frag_index, frags_numb):
    while True:
        frag = create_fragment(fragment, len(fragment), frag_index, frags_numb)
        client.sendto(frag, ('localhost', 7777))
        print(f"Fragmento {frag_index} enviado, aguardando ACK")

        client.settimeout(TIMEOUT)
        try:
            ack_data, _ = client.recvfrom(1024)
            ack_frag_index = struct.unpack('!I', ack_data)[0]
            if ack_frag_index == frag_index:
                print(f"ACK {ack_frag_index} recebido")
                break
            else:
                print(f"ACK {ack_frag_index} errado, esperando {frag_index}")
        except socket.timeout:
            print(f"Timeout ao esperar ACK {frag_index}, retransmitindo")

main()