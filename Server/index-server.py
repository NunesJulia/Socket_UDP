import socket
import os
import queue
import math
import threading
import struct
from zlib import crc32

# Configuração do Cliente
clients = []
messages = queue.Queue()

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind(('localhost', 7777))

# Armazenamento de fragmentos recebidos
frags_received_list = []
frags_received_count = 0

#Função que faz o calculo do Checksum (não o CRC)
def calcula_checksum(data):
    checksum = 0
    for byte in data:
        checksum = (checksum + byte) & 0xFF #Serve para manter o checksum no intervalo de 1 byte, essa operação "& 0xFF" se a soma de checksum e byte resultar em um valor que excede 8 bits, a operação & 0xFF descarta todos os bits acima do oitavo bit. Isso mantém o checksum dentro do intervalo de 0 a 255 (8 bits).
    return checksum

#Função que cria fragmentos
def create_fragment(payload, frag_size, frag_index, frags_numb):
    data = payload[:frag_size]
    
    crc = crc32(data)
    checksum = calcula_checksum(data)

    print(f"Criando fragmento: Tamanho={frag_size}, Índice={frag_index}, Total Fragmentos={frags_numb}, CRC={crc}, Checksum={checksum}") #Verificação de fragmento

    header = struct.pack('!IIIII', frag_size, frag_index, frags_numb, crc, checksum)
    return header + data

# Verificação da Integridade dos dados recebidos por meio de desempacotamento e reagrupação
def unpack_and_reassemble(data, addr):
    global frags_received_count, frags_received_list

    header = data[:20]
    message_in_bytes = data[20:]
    frag_size, frag_index, frags_numb, crc, checksum = struct.unpack('!IIIII', header)

    # Verificar CRC
    crc_calculado = crc32(message_in_bytes)
    if crc != crc_calculado:
        print(f"Fragmento com CRC inválido, ignorando.\nEsperado: {crc},\nCalculado: {crc_calculado}")
        return

    # Verificar o Checksum
    checksum_calculado = calcula_checksum(message_in_bytes)
    if checksum != checksum_calculado:
        print(f"Fragmento com checksum clássico inválido, ignorando.\nEsperado: {checksum},\nCalculado: {checksum_calculado}")
        return

    print(f"\nRecebido fragmento: Tamanho={frag_size}, Índice={frag_index}, Total Fragmentos={frags_numb}, CRC={crc}, Checksum={checksum}\n")

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
            print(f"{addr} entrou na sala")
            messages.put(sent_msg)
        elif "SIGNOUT_TAG:" in line:
            name = line.split(":")[1]
            sent_msg = f"{name} saiu da sala"
            print(f"{addr} saiu da sala")
            clients.remove(addr) #Remove o cliente da lista de clientes
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

            for client in clients:
                if client != sender_addr:  # Evitar enviar para o remetente original
                    fragment_payload = payload
                    fragment_index = 0
                    while fragment_payload:
                        fragment = create_fragment(fragment_payload, frag_size, fragment_index, frags_numb)
                        server.sendto(fragment, client)
                        fragment_payload = fragment_payload[frag_size:]
                        fragment_index += 1
                    print(f"Mensagem enviada para {client}\n") 
        os.remove('message_server.txt')

# Função de receber dados
def receive():
    while True:
        data, addr = server.recvfrom(1024)
        print("Mensagem recebida")
        if addr not in clients:
            clients.append(addr)
            print(f"Lista de Clientes: {clients}")
        unpack_and_reassemble(data, addr)


thread = threading.Thread(target=receive)
thread.start()