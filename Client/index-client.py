import random
import threading
import socket

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client.bind(("localhost", random.randint(8000, 9000)))
porta = 7777
name = ""

def receive():
    while True:
        try:
            message, addr = client.recvfrom(1024)
            print(message.decode())
        except Exception as e:
            print(f"Error receiving message: {e}")

thread1 = threading.Thread(target=receive)
thread1.start()

while True:
    message = input("")
    if "toctoc" in message:
        name = input("Usuário: ")
        client.sendto(f"SIGNUP_TAG:{name}".encode(), ("localhost", 7777))
    elif message == "bye":
        exit()
    else:
        if name:
            client.sendto(f"<{client.getsockname()[0]}>:<{client.getsockname()[1]}>/~{name}:{message}".encode(), ("localhost", 7777))
        else:
            print("Você precisa fazer login com 'toctoc' antes de enviar mensagens.")
