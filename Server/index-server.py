import os
import queue
import math
import threading
import struct
from zlib import crc32
import time
import socket

# Configuração do Cliente
clients = []
messages = queue.Queue()
ack_wait_time = 2  # Tempo de espera para ACK em segundos
server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind(('localhost', 7777))
server.settimeout(ack_wait_time)  # Define um timeout para operações de socket

# Armazenamento de fragmentos recebidos
frags_received_list = []
frags_received_count = 0

# Estrutura para gerenciar pacotes enviados
sent_packets = {}  # {address: [(fragment, timestamp)]}
lock = threading.Lock()  # Para sincronização
ack_received = {}  # {address: set of acked fragment indices}

# Função que cria fragmentos
def create_fragment(payload, frag_size, frag_index, frags_numb):
    data = payload[:frag_size]
    crc = crc32(data)
    header = struct.pack('!IIII', frag_size, frag_index, frags_numb, crc)
    return header + data

# Verificação da integridade dos dados recebidos
def unpack_and_reassemble(data, addr):
    global frags_received_count, frags_received_list

    header = data[:16]  # Assumindo que o cabeçalho tem 16 bytes
    message_in_bytes = data[16:]  # Mensagem após o cabeçalho

    frag_size, frag_index, frags_numb, crc = struct.unpack('!IIII', header)

    # Verifica CRC
    if crc != crc32(message_in_bytes):
        print("Fragmento com CRC inválido, ignorando.")
        return

    # Garantir que a lista de fragmentos tenha o tamanho correto
    if len(frags_received_list) < frags_numb:
        add = frags_numb - len(frags_received_list)
        frags_received_list.extend([None] * add)

    # Verificar se o índice do fragmento é válido
    if frag_index < frags_numb:
        frags_received_list[frag_index] = message_in_bytes
        frags_received_count += 1

    # Verificar se todos os fragmentos foram recebidos
    if frags_received_count == frags_numb:
        # Juntar os fragmentos e processar a mensagem
        complete_message = b''.join(frags_received_list)
        print (f"Recebido mensagem completa de {addr}: {complete_message}")
        process_received_message( addr)

        # Enviar ACK após receber todos os fragmentos
        send_ack(addr)

def process_received_message(addr):
    with open('received_message.txt', 'r') as file:
        file_content = file.read()
    os.remove('received_message.txt')

    for line in file_content.strip().split('\n'):
        line = line.strip()
        if "SIGNUP_TAG:" in line:
            name = line.split(":")[1].strip()
            sent_msg = f"{name} entrou na sala"
            messages.put(sent_msg)
        elif "SIGNOUT_TAG:" in line:
            name = line.split(":")[1].strip()
            sent_msg = f"{name} saiu da sala"
            messages.put(sent_msg)
        else:
            messages.put(line)
    send_to_all_clients(addr)

# Faz o broadcast da mensagem para os clientes
def send_to_all_clients(sender_addr):
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
                    with lock:
                        sent_packets[client] = []  # Inicializa a lista de pacotes enviados para o cliente
                    while fragment_payload:
                        fragment = create_fragment(fragment_payload, frag_size, fragment_index, frags_numb)
                        server.sendto(fragment, client)
                        with lock:
                            sent_packets[client].append((fragment, time.time()))  # Armazena o pacote e o timestamp
                        fragment_payload = fragment_payload[frag_size:]
                        fragment_index += 1

        os.remove('message_server.txt')

# Função de reenviar pacotes
def resend_packets():
    while True:
        time.sleep(1)  # Espera antes de verificar pacotes
        with lock:
            for client, packets in list(sent_packets.items()):
                packets_to_remove = []
                for fragment, timestamp in packets:
                    if time.time() - timestamp > ack_wait_time:  # Verifica se o tempo limite foi atingido
                        print(f"Reenviando pacote para {client}")
                        server.sendto(fragment, client)  # Reenvia o pacote
                        packets_to_remove.append((fragment, timestamp))
                for packet in packets_to_remove:
                    packets.remove(packet)

def send_ack(addr):
    ack_message = f"ACK"
    server.sendto(ack_message.encode('utf-8'), addr)
    print(f"ACK enviado para o cliente {addr}")

def receive():
    while True:
        try:
            data, addr = server.recvfrom(1024)
            print(f"Dados recebidos de {addr}: {data}")

            if addr not in clients:
                clients.append(addr)
                print(f"Novo cliente conectado: {addr}")

            # Tente decodificar os dados
            # A decodificação deve ser feita apenas após verificar o cabeçalho
            unpack_and_reassemble(data, addr)

        except socket.timeout:
            print("Timeout: Nenhum pacote recebido. Verificando clientes...")

# Threads para receber e reenviar pacotes
thread = threading.Thread(target=receive)
thread.start()
thread_resend = threading.Thread(target=resend_packets)
thread_resend.start()
