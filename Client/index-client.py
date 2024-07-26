import random
import threading
import socket
from datetime import datetime
import os
import math
from zlib import crc32
import struct
import time

# Configuração do Cliente 
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client.bind(("localhost", random.randint(8000, 9000)))

# Armazenamento de fragmentos recebidos
frags_received_list = []
frags_received_count = 0

# Armazenamento de pacotes enviados e timestamps
sent_packets = {}
ack_wait_time = 2  # Tempo de espera para ACK em segundos

# Verificação da integridade dos dados recebidos
def unpack_and_reassemble(data):
    global frags_received_count, frags_received_list

    print("Recebendo dados...")

    if len(data) < 16:
        print("Dados recebidos insuficientes para desempacotar. Ignorando.")
        return

    header = data[:16] 
    message_in_bytes = data[16:] 
    frag_size, frag_index, frags_numb, crc = struct.unpack('!IIII', header) 

    print(f"Fragmento recebido: size={frag_size}, index={frag_index}, total={frags_numb}, crc={crc}")

    if crc != crc32(message_in_bytes):
        print(f"Fragmento com CRC inválido, ignorando.")
        return

    if len(frags_received_list) < frags_numb: 
        frags_received_list.extend([None] * (frags_numb - len(frags_received_list)))

    frags_received_list[frag_index] = message_in_bytes 
    frags_received_count += 1

    print(f"Total de fragmentos recebidos: {frags_received_count}/{frags_numb}")

    if frags_received_count == frags_numb:
        print("Todos os fragmentos recebidos, criando o arquivo...")
        with open('received_message.txt', 'wb') as file:
            for fragment in frags_received_list:
                file.write(fragment)
        frags_received_count = 0 
        frags_received_list = []
        print_received_message()
        send_ack(frag_index)

# Lê o arquivo txt e imprime a mensagem
def print_received_message():
    if os.path.exists('received_message.txt'):
        with open('received_message.txt', 'r') as file:
            file_content = file.read()
        os.remove('received_message.txt')
        print(file_content)

# Função que trata o recebimento da mensagem
def receive():
    print("Aguardando dados...")
    while True:
        try:
            data, addr = client.recvfrom(1024)
            if data.decode().startswith("ACK:"):
                print("Recebendo ACK...")
                frag_index = int(data.decode().split(":")[1])
                print(f"ACK recebido para o fragmento {frag_index}.")
                if frag_index in sent_packets:
                    del sent_packets[frag_index]  # Remove o pacote enviado
                continue  # Ignora o processamento de fragmento

            unpack_and_reassemble(data)
        except Exception as e:
            print(f"Erro ao receber dados: {e}")

# Função para enviar ACK
def send_ack(frag_index):
    ack_message = f"ACK:{frag_index}"
    client.sendto(ack_message.encode(), ('localhost', 7777))
    print(f"ACK enviado para o servidor para o fragmento {frag_index}")

thread1 = threading.Thread(target=receive)
thread1.start()
print("Thread de recebimento iniciada.")


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
        if message.startswith("hi, meu nome eh") or message.startswith("Hi, meu nome eh"):
            username = message[len("hi, meu nome eh") + 1:].strip()
            sent_msg = f"SIGNUP_TAG:{username}"
            with open('message_client.txt', 'w') as file:
                file.write(sent_msg)

            print(f"Enviando mensagem de inscrição: {sent_msg}")
            send_txt()
        
        elif username and message == "bye":
            sent_msg = f"SIGNOUT_TAG:{username}"
            with open('message_client.txt', 'w') as file:
                file.write(sent_msg)

            print(f"Enviando mensagem de saída: {sent_msg}")
            send_txt()
            print("Conexão encerrada, até logo!")
            client.close()  # Fecha o socket antes de sair
            exit()

        else:
            if username:
                timestamp = datetime.now().strftime('%H:%M:%S - %d/%m/%Y')
                formatted_message = f"{client.getsockname()[0]}:{client.getsockname()[1]}/~{username}: {message} {timestamp}"
                with open('message_client.txt', 'w') as file:
                    file.write(formatted_message)

                print(f"Enviando mensagem: {formatted_message}")
                send_txt()
            else:
                print("Para conectar à sala, digite 'hi, meu nome eh' e insira seu username.")

# Função que manda a mensagem
def send_txt():
    frag_index = 0
    frag_size = 1008

    with open('message_client.txt', 'rb') as file:
        payload = file.read()
        if len(payload) == 0:
            print("Nenhum dado para enviar.")
            return
        frags_numb = math.ceil(len(payload) / frag_size)

        while payload:
            fragment = create_fragment(payload, frag_size, frag_index, frags_numb)
            client.sendto(fragment, ('localhost', 7777))
            sent_packets[frag_index] = (fragment, time.time())  # Armazena o fragmento e timestamp
            payload = payload[frag_size:]
            frag_index += 1
            print(f"Enviando fragmento {frag_index} para o servidor")

    os.remove('message_client.txt')
    check_ack()  # Verifica se os ACKs foram recebidos

# Função para verificar se os ACKs foram recebidos
def check_ack():
    while sent_packets:
        for frag_index in list(sent_packets.keys()):  # Itera sobre uma cópia das chaves
            fragment, timestamp = sent_packets[frag_index]
            if time.time() - timestamp > ack_wait_time:  # Se o tempo limite foi atingido
                print(f"Reenviando fragmento {frag_index}...")
                client.sendto(fragment, ('localhost', 7777))  # Reenvia o fragmento
                sent_packets[frag_index] = (fragment, time.time())  # Atualiza o timestamp

main()
