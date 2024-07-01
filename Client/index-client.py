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

    header = data[:16] # Separa o cabeçalho dos Dados
    message_in_bytes = data[16:] # Separa o cabeçalho dos Dados
    frag_size, frag_index, frags_numb, crc = struct.unpack('!IIII', header) #Desempacota o cabeçalho
    #frag_size: Tamanho do fragmento
    #frag_index: Índice do fragmento (posição na sequência)
    #frags_numb: Número total de fragmentos
    #crc: Valor CRC32 dos dados, usado para verificar a integridade

    # Verifica CRC
    if crc != crc32(message_in_bytes): # ----------------> Essa função calcula o CRC32 da mensagem e cerifica se possui o mesmo valor do informado pelo cabeçalho
        print("Fragmento com CRC inválido, ignorando.")
        mandaAck(numeroSequenciaEsperado - 1)
        return
    
    if frag_index != numeroSequenciaEsperado:
        print(f"Fragmento fora de sequência, ignorando. Esperado: {numeroSequenciaEsperado}, Recebido: {frag_index}")
        mandaAck(numeroSequenciaEsperado - 1)  #Enviar ACK do último pacote recebido com sucesso
        return

    if len(frags_received_list) < frags_numb: # Verifica se a lista tem o tamanho certo e aplica o tamanho certo caso não
        add = frags_numb - len(frags_received_list)
        frags_received_list.extend([None] * add) # -------> Isso adiciona espaços "None" na lista para adequar seu tamanho ao tamanho necessário

    frags_received_list[frag_index] = message_in_bytes # Armazena o fragmento na lista na posição correta
    frags_received_count += 1
    numeroSequenciaEsperado += 1

    mandaAck(frag_index)

    # Verifica se todos os fragmentos foram recebidos e reseta a lista para o proximo pacote ou se houve perda de pacote
    if frags_received_count == frags_numb:
        with open('received_message.txt', 'wb') as file:
            for fragment in frags_received_list:
                file.write(fragment)
        frags_received_count = 0 
        frags_received_list = []
        numeroSequenciaEsperado #!
        print_received_message()  #Aqui há uma diferença da versão do cliente e servidor

    elif (frags_received_count < frags_numb) and (frag_index == frags_numb - 1):
        print("Provavelmente houve perda de pacotes")
        frags_received_count = 0
        frags_received_list = []
        numeroSequenciaEsperado = 0

def mandaAck(frag_index):
    ack = struct.pack('!I', frag_index)   #!OBS - Mateus: Não sei ao certo ainda se isso é totalmente válido ou seria melhor criar o ACK com a propria função de criar fragmentos. Acho que não devido ao Cliente
    client.sendto(ack,('localhost', 7777))
    print(f"ACK do pacote {frag_index} enviado") #!Momentaneo para ajudar em testes, terá que ser removido

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
        unpack_and_reassemble(data) # ----> Aqui a função unpack_and_reassemble tratará corretamente a mensagem e fará sua verificação, caso tudo esteja correto, printa a mensagem


thread1 = threading.Thread(target=receive)
thread1.start()

#Cria um Fragmento
def create_fragment(payload, frag_size, frag_index, frags_numb):
    data = payload[:frag_size]
    crc = crc32(data)
    header = struct.pack('!IIII', frag_size, frag_index, frags_numb, crc)
    return header + data


def main():
    username = ''
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
        
        #Trata a saida do usuario
        elif username and message == "bye":
            sent_msg = f"SIGNOUT_TAG:{username}"
            with open('message_client.txt', 'w') as file:
                file.write(sent_msg)
            send_txt()
            print("Conexão encerrada, Até logo!")
            exit()

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
    frag_size = 1024

    with open('message_client.txt', 'rb') as file:
        payload = file.read()
        frags_numb = math.ceil(len(payload) / frag_size) #Calcula o numero de fragmentos

        while payload:
            #fragment = create_fragment(payload, frag_size, frag_index, frags_numb)
            mandaFragmento(payload[:frag_size], frag_index, frags_numb)
            #client.sendto(fragment, ('localhost', 7777))
            payload = payload[frag_size:]
            frag_index += 1
    os.remove('message_client.txt')

def mandaFragmento(fragment, frag_index, frags_numb):
    while True:
        frag = create_fragment(fragment, len(fragment), frag_index, frags_numb)
        client.sendto(frag, ('localhost', 7777)) #garante o envio do fragmento no lugar de onde estava no codigo passado
        print(f"Fragmento {frag_index} enviado, aguardando ACK")

        client.settimeout(TIMEOUT)
        try:                       #!Detecta os erros envolvendo acks
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