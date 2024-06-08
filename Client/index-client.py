import random
import threading
import socket
from datetime import datetime

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Inicialização do Cliente
client.bind(("localhost", random.randint(8000, 9000)))

username = ""


# Função que Recebe as mensagens
def receive():
    while True:
        try:
            message, addr = client.recvfrom(1024)
            print(message.decode())
        except Exception as e:
            print(f"Error receiving message: {e}")


thread1 = threading.Thread(target=receive)
thread1.start()

# Codigo que envia Mensagens
while True:
    message = input("")

    # Inicializa o usuario e sai caso o usuario digite "bye"
    if message.startswith("hi, meu nome eh") or message.startswith("Hi, meu nome eh"):
        username = message[
                   len("hi meu nome eh") + 1:].strip()  # Função que separa o "hi meu nome eh do nome de usuario escrito"
        client.sendto(f"SIGNUP_TAG:{username}".encode(), ("localhost", 7777))

    elif username and message == "bye":
        client.sendto(f"SIGNOUT_TAG:{username}".encode(), ("localhost", 7777))
        print("Conexão encerrada, Até logo!")
        exit()

    # Envia a mensagem caso o usuario já esteja conectado
    else:
        if username:
            timestamp = datetime.now().strftime('%H:%M:%S - %d/%m/%Y')
            formatted_message = f"{client.getsockname()[0]}:{client.getsockname()[1]}/~{username}: {message} {timestamp}"

            client.sendto(formatted_message.encode(), ("localhost", 7777))  # Envia a mensagem ao servidor
        else:
            print("Para conectar a sala digite 'hi, meu nome eh' e digite seu username")