import random
import threading
import socket
from datetime import datetime
import os

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Inicialização do Cliente
client.bind(("localhost", random.randint(8000, 9000)))

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #Inicialização do Cliente
client.bind(("localhost", random.randint(8000, 9000))) 
porta = 7777
username = ""

<<<<<<< HEAD
#Função que Recebe as mensagens
def receive():
    while True:
        try:
            message, addr = client.recvfrom(1024)
            print(message.decode())
=======
# Função que Recebe as mensagens
def receive():
    while True:
        try:
            data, addr = client.recvfrom(1024)
            if data:
                with open('received_message_client.txt', 'ab') as file:
                    file.write(data)
                with open('received_message_client.txt', 'rb') as file:
                    file_content = file.readlines()
                for lines in file_content:
                    print(lines.decode('utf-8').strip())
                os.remove('received_message_client.txt')
>>>>>>> origin/jlsf1
        except Exception as e:
            print(f"Error receiving message: {e}")

thread1 = threading.Thread(target=receive)
thread1.start()

<<<<<<< HEAD
#Codigo que envia Mensagens
while True:
    message = input("") 

    #Inicializa o usuario e sai caso o usuario digite "bye"
    if message.startswith("hi, meu nome eh") or message.startswith("Hi, meu nome eh"):
        username = message[len("hi meu nome eh") + 1:].strip()                                           #Função que separa o "hi meu nome eh do nome de usuario escrito"
        client.sendto(f"<{client.getsockname()[0]}>:<{client.getsockname()[1]}>/~{username}: hi, meu nome eh: {username}".encode(), ("localhost", 7777))                      #Envia ao servidor a mensagem de conexão inicial
    elif username and message == "bye":
        client.sendto(f"<{client.getsockname()[0]}>:<{client.getsockname()[1]}>/~{username}:{message}".encode(), ("localhost", 7777))
        print("Conexão encerrada, Até logo!")
        exit()
    
    #Envia a mensagem caso o usuario já esteja conectado    
    else:
        if username:
            client.sendto(f"<{client.getsockname()[0]}>:<{client.getsockname()[1]}>/~{username}:{message}".encode(), ("localhost", 7777))            #Envia a mensagem ao servidor
        else:
            print("Para conectar a sala digite 'hi, meu nome eh' e digite seu username")
=======
thread1 = threading.Thread(target=receive)
thread1.start()

# Codigo que envia Mensagens
def broadcast_txt():
    username = ''
    while True:
        message = input("")

        if message.startswith("hi, meu nome eh") or message.startswith("Hi, meu nome eh"):
            username = message[len("hi meu nome eh") + 1:].strip()  # Função que separa o "hi meu nome eh do nome de usuario escrito"
            sent_msg = f"SIGNUP_TAG:{username}"
            send_txt(sent_msg)

        elif username and message == "bye":
            sent_msg = f"SIGNOUT_TAG:{username}"
            send_txt(sent_msg)
            print("Conexão encerrada, Até logo!")
            exit()

        # Envia a mensagem caso o usuario já esteja conectado
        else:
            if username:
                timestamp = datetime.now().strftime('%H:%M:%S - %d/%m/%Y')
                formatted_message = f"{client.getsockname()[0]}:{client.getsockname()[1]}/~{username}: {message} {timestamp}"
                send_txt(formatted_message)

            else:
                print("Para conectar a sala digite 'hi, meu nome eh' e digite seu username")

def send_txt(message):
    with open('message_client.txt', 'w') as file:
        file.write(message)
    with open('message_client.txt', 'rb') as file:
        while (chunk := file.read(1024)):
            client.sendto(chunk, ('localhost',7777))
    os.remove('message_client.txt')

broadcast_txt()
>>>>>>> origin/jlsf1
