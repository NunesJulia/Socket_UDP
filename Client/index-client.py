import random
import threading
import socket
from datetime import datetime
import os

#Inicialização do socket do Cliente 
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
client.bind(("localhost", random.randint(8000, 9000)))


# Função que Recebe as mensagens
def receive():
    while True:
        try:
            data, addr = client.recvfrom(1024) # Recebe do servidor
            if data:
                with open('received_message_client.txt', 'ab') as file: 
                    file.write(data) # escreve os dados recebidos no arquivo
                with open('received_message_client.txt', 'rb') as file:
                    file_content = file.readlines()   #Lê o arquivo txt 
                for line in file_content:
                    print(line.decode('utf-8').strip()) # Imprime o txt
                os.remove('received_message_client.txt')
        except Exception as e:
            print(f"Error receiving message: {e}")


thread1 = threading.Thread(target=receive)
thread1.start()

# Função que gerencia o envio de mensagens
def broadcast_txt():
    username = ''
    while True:
        message = input("")
        
        # Caso o usuario não esteja conectado
        if message.startswith("hi, meu nome eh") or message.startswith("Hi, meu nome eh"):
            username = message[len("hi meu nome eh") + 1:].strip()  # separação o "hi meu nome eh do nome de usuario escrito"
            sent_msg = f"SIGNUP_TAG:{username}"
            send_txt(sent_msg)
        
        # Caso o usuario esteja conectado e queira sair
        elif username and message == "bye":
            sent_msg = f"SIGNOUT_TAG:{username}"
            send_txt(sent_msg)
            print("Conexão encerrada, até logo!")
            exit()

        # Envia a mensagem caso o usuario já esteja conectado e formata a mesma
        else:
            if username:
                timestamp = datetime.now().strftime('%H:%M:%S - %d/%m/%Y')
                formatted_message = f"{client.getsockname()[0]}:{client.getsockname()[1]}/~{username}: {message} {timestamp}"
                send_txt(formatted_message)

            else:
                print("Para conectar a sala digite 'hi, meu nome eh' e digite seu username")

# Função que trata o envio de mensagens propriamente dito
def send_txt(message):
    with open('message_client.txt', 'w') as file:
        file.write(message)
    with open('message_client.txt', 'rb') as file:
        while (chunk := file.read(1024)): # Define o chunk como o valor de 'file.read(1024)' e lê o arquivo em pedaços de 1024 bytes
            client.sendto(chunk, ('localhost',7777))
    os.remove('message_client.txt')

broadcast_txt()