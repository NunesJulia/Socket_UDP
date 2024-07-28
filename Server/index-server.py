import socket
import os
import queue
import math
import threading
import struct
import time

# Configuração do Cliente
clients = []
messages = queue.Queue()

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind(('localhost', 7777))

# Armazenamento de fragmentos recebidos
frags_received_list = []
frags_received_count = 0

# Variáveis de controle de ACK
acks_received = {}
acks_locks = {}
ack_timeout = 2  # Tempo de espera para o ACK em segundos

# Função que faz o cálculo do Checksum (não o CRC)
def calcula_checksum(data):
    checksum = 0
    for byte in data:
        checksum = (checksum + byte) & 0xFF
    return checksum

# Função que cria fragmentos
def create_fragment(payload, frag_size, frag_index, frags_numb, message_id):
    data = payload[:frag_size]
    checksum = calcula_checksum(data)
    header = struct.pack('!IIIIII', frag_size, frag_index, frags_numb, checksum, message_id, frag_index)
    return header + data

# Verificação da Integridade dos dados recebidos por meio de desempacotamento e reagrupação
def unpack_and_reassemble(data, addr):
    global frags_received_count, frags_received_list

    header = data[:24]
    message_in_bytes = data[24:]
    frag_size, frag_index, frags_numb, checksum, message_id, frag_index = struct.unpack('!IIIIII', header)

    # Verificar o Checksum
    checksum_calculado = calcula_checksum(message_in_bytes)
    if checksum != checksum_calculado:
        print(f"Fragmento com checksum inválido, ignorando.\nEsperado: {checksum},\nCalculado: {checksum_calculado}")
        return

    print(f"Recebido fragmento: Tamanho={frag_size}, Índice={frag_index}, Total Fragmentos={frags_numb}, Checksum={checksum}, Message ID={message_id}")

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
        process_received_message(addr)  # Aqui há uma diferença da versão do cliente e servidor
    elif (frags_received_count < frags_numb) and (frag_index == frags_numb - 1):
        print("Provavelmente houve perda de pacotes")
        frags_received_count = 0
        frags_received_list = []

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
            print(f"Nova lista de Clientes: {clients}")
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
            message_id = int(time.time() * 1000) & 0xFFFFFFFF  # ID único baseado no timestamp

            for client in clients:
                if client != sender_addr:  # Evitar enviar para o remetente original
                    fragment_payload = payload
                    fragment_index = 0
                    while fragment_payload:
                        fragment = create_fragment(fragment_payload, frag_size, fragment_index, frags_numb, message_id)
                        send_with_ack(fragment, client, message_id)
                        fragment_payload = fragment_payload[frag_size:]
                        fragment_index += 1
                    print(f"Mensagem enviada para {client}")
        os.remove('message_server.txt')

# Função de enviar dados com ACK
def send_with_ack(data, addr, message_id):
    global acks_received, acks_locks
    if addr not in acks_received:
        acks_received[addr] = {}
        acks_locks[addr] = threading.Lock()
    retries = 3
    while retries > 0:
        with acks_locks[addr]:
            acks_received[addr][message_id] = False
        server.sendto(data, addr)
        print(f"Fragmento enviado para {addr}, aguardando ACK...")
        start_time = time.time()
        while time.time() - start_time < ack_timeout:
            with acks_locks[addr]:
                if acks_received[addr].get(message_id, False):
                    print("ACK recebido.")
                    return
            time.sleep(0.1)
        print("Tempo de espera do ACK esgotado, reenviando fragmento...")
        retries -= 1
    if not acks_received[addr].get(message_id, False):
        print(f"Não foi possível obter ACK de {addr} após {3 - retries} tentativas.")

# Função de receber dados
def receive():
    global acks_received, acks_locks
    while True:
        data, addr = server.recvfrom(1024)
        if data.startswith(b'ACK'):
            _, message_id = struct.unpack('!II', data[3:11])
            with acks_locks[addr]:
                acks_received[addr][message_id] = True
        else:
            print("Mensagem recebida")
            if addr not in clients:
                clients.append(addr)
                print(f"Lista de Clientes: {clients}")
            unpack_and_reassemble(data, addr)
            _, message_id, frag_index = struct.unpack('!III', data[:12])
            ack_data = struct.pack('!II', len(data), message_id)
            server.sendto(b'ACK' + ack_data, addr)

thread = threading.Thread(target=receive)
thread.start()
