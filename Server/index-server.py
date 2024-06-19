import socket
import os
import queue
import math
import threading
import struct
from zlib import crc32

#Configurações do servidor e Variaveis de fragmento
clients = []
messages = queue.Queue()

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind(('localhost', 7777))

frags_received_list = []
frags_received_count = 0

#Função que cria fragmentos
def create_fragment(payload, frag_size, frag_index, frags_numb):
    data = payload[:frag_size]
    crc = crc32(data)
    header = struct.pack('!IIII', frag_size, frag_index, frags_numb, crc)
    return header + data

# Verificação da Integridade dos dados recebidos por meio de desempacotamento e reagrupação
def unpack_and_reassemble(data, addr):
    global frags_received_count, frags_received_list

    header = data[:16]
    message_in_bytes = data[16:]
    frag_size, frag_index, frags_numb, crc = struct.unpack('!IIII', header)

    # Verificar CRC
    if crc != crc32(message_in_bytes):
        print("Fragmento com CRC inválido, ignorando.")
        return

    if len(frags_received_list) < frags_numb:
        add = frags_numb - len(frags_received_list)
        frags_received_list.extend([None] * add)

    frags_received_list[frag_index] = message_in_bytes
    frags_received_count += 1

    if frags_received_count == frags_numb:
        with open('received_message.txt', 'wb') as file:
            for fragment in frags_received_list:
                file.write(fragment)
        frags_received_count = 0
        frags_received_list = []
        process_received_message(addr) #Aqui há uma diferença da versão do cliente e servidor

    elif (frags_received_count < frags_numb) and (frag_index == frags_numb - 1):
        print("Provavelmente houve perda de pacotes")
        frags_received_count = 0
        frags_received_list = []

#Processa a mensagem e a trata caso seja uma confirmação de Login, Log out ou apenas uma mensagem qualquer.
def process_received_message(addr):
    with open('received_message.txt', 'r') as file:
        file_content = file.read()
    os.remove('received_message.txt')
    for line in file_content.strip().split('\n'):
        line = line.strip()
        if "SIGNUP_TAG:" in line:
            name = line.split(":")[1]
            sent_msg = f"{name} entrou na sala"
            messages.put(sent_msg)
        elif "SIGNOUT_TAG:" in line:
            name = line.split(":")[1]
            sent_msg = f"{name} saiu da sala"
            messages.put(sent_msg)
        else:
            messages.put(line)
    send_to_all_clients(addr)

# Faz o broadcast da mensagem para os clientes
def send_to_all_clients(sender_addr):
    frag_index = 0
    frag_size = 1024
    while not messages.empty():
        message = messages.get()
        with open('message_client.txt', 'w') as file:
            file.write(message)

        with open('message_client.txt', 'rb') as file:
            payload = file.read()
            frags_numb = math.ceil(len(payload) / frag_size)

            for client in clients:
                if client != sender_addr:  # Evitar enviar para o remetente original
                    fragment_payload = payload
                    fragment_index = 0
                    while fragment_payload:
                        fragment = create_fragment(fragment_payload, frag_size, fragment_index, frags_numb)
                        server.sendto(fragment, client)
                        fragment_payload = fragment_payload[frag_size:]
                        fragment_index += 1
        os.remove('message_client.txt')

# Função de receber dados
def receive():
    while True:
        data, addr = server.recvfrom(1024)
        if addr not in clients:
            clients.append(addr)
        unpack_and_reassemble(data, addr)


thread = threading.Thread(target=receive)
thread.start()