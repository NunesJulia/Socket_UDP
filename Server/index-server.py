#
import socket
import os
import queue
import math
import threading
import struct
import time

# Configuração do Servidor
clients = []
messages = queue.Queue()
server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind(('localhost', 7777))

# Armazenamento de fragmentos recebidos
frags_received_list = []
frags_received_count = 0

# Variável relacionada ao RDT 3.0
timeout = 2  # Timeout de 2 segundos
ack_received_flag = False

# Função que faz o cálculo do Checksum
def calcula_checksum(data):
    checksum = 0
    for byte in data:
        checksum = (checksum + byte) & 0xFF
    return checksum

# Função que cria fragmentos
def create_fragment(payload, frag_size, frag_index, frags_numb):
    data = payload[:frag_size]
    checksum = calcula_checksum(data)
    header = struct.pack('!IIII', frag_size, frag_index, frags_numb, checksum)
    return header + data

# Função para enviar ACK
def send_ack(addr):
    ack_packet = struct.pack('!I', 1)
    server.sendto(ack_packet, addr)
    print(f'-------------> ACK enviado para {addr}')

# Verificação da integridade dos dados recebidos por meio de desempacotamento e reagrupação
def unpack_and_reassemble(data, addr):
    global frags_received_count, frags_received_list

    header = data[:16]
    message_in_bytes = data[16:]
    frag_size, frag_index, frags_numb, checksum = struct.unpack('!IIII', header)

    # Verificar o Checksum
    checksum_calculado = calcula_checksum(message_in_bytes)
    if checksum != checksum_calculado:
        print(f"Fragmento com checksum inválido, ignorando.\nEsperado: {checksum},\nCalculado: {checksum_calculado}")
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
        process_received_message(addr)
    elif (frags_received_count < frags_numb) and (frag_index == frags_numb - 1):
        print("Provavelmente houve perda de pacotes")
        frags_received_count = 0
        frags_received_list = []

    # Envia ACK após receber o fragmento
    send_ack(addr)

# Processa a mensagem e a trata caso seja uma confirmação de Login, Log out ou apenas uma mensagem qualquer.
def process_received_message(addr):
    with open('received_message.txt', 'r') as file:
        file_content = file.read()
    os.remove('received_message.txt')
    for line in file_content.strip().split('\n'):
        line = line.strip()
        if "SIGNUP_TAG:" in line:
            name = line.split(":")[1]
            sent_msg = f"{name} entrou na sala"
            print(f"{addr} entrou na sala")
            messages.put(sent_msg)
        elif "SIGNOUT_TAG:" in line:
            name = line.split(":")[1]
            sent_msg = f"{name} saiu da sala"
            print(f"{addr} saiu da sala")
            clients.remove(addr)  # Remove o cliente da lista de clientes
            messages.put(sent_msg)
        else:
            messages.put(line)
            print(f"Mensagem recebida de {addr} processada.")
    send_to_all_clients(addr)

# Faz o broadcast da mensagem para os clientes
def send_to_all_clients(sender_addr):
    frag_index = 0
    frag_size = 1008
    while not messages.empty():
        message = messages.get()
        with open('message_server.txt', 'w') as file:
            file.write(message)
        with open('message_server.txt', 'rb') as file:
            payload = file.read()
            frags_numb = math.ceil(len(payload) / frag_size)
            for client in clients:
                if client != sender_addr:  # Evitar enviar para o remetente original
                    fragment_payload = payload
                    fragment_index = 0
                    while fragment_payload:
                        fragment = create_fragment(fragment_payload, frag_size, fragment_index, frags_numb)
                        send_fragment(fragment, client)
                        fragment_payload = fragment_payload[frag_size:]
                        fragment_index += 1
                    print(f"Mensagem enviada para {client}\n")
        os.remove('message_server.txt')

def send_fragment(fragment, addr):
    global ack_received_flag
    ack_received_flag = False
    # Loop de ACK
    while not ack_received_flag:  # Enquanto a função "ACK Received" não transformar a flag em True, reenvia a mensagem
        server.sendto(fragment, addr)
        start = time.time()
        while time.time() - start < timeout:
            if ack_received_flag:
                break

# Função de receber dados
def receive():
    global ack_received_flag
    while True:
        data, addr = server.recvfrom(1024)
        print("Mensagem recebida")
        if addr not in clients:
            clients.append(addr)
            print(f"Lista de Clientes: {clients}")
        header = data[:16]
        message_type = struct.unpack('!I', header[:4])[0]

        # Se a mensagem recebida for um ACK, altera a flag de ACK para True
        if message_type == 1:  # ACK
            ack_received_flag = True
            print('ACK recebido')
        # Se a mensagem recebida NÃO for um ACK: Trata a mensagem
        else:
            unpack_and_reassemble(data, addr)

thread = threading.Thread(target=receive)
thread.start()
