import socket
<<<<<<< HEAD
import queue
=======
import os
>>>>>>> origin/jlsf1

clients = []
messages = queue.Queue()
server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind(('localhost', 7777))

<<<<<<< HEAD

def receive():
    while True:
        try:
            message, addr = server.recvfrom(1024)
            print(f"Received message from {addr}: {message.decode()}")
            messages.put((message, addr))
        except Exception as e:
            print(f"Error receiving message: {e}")
=======
def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        server.bind(('localhost', 7777))
        print("Servidor iniciado na porta 7777")
    except Exception as e:
        print(f'\nNão foi possível iniciar o servidor! Erro: {e}\n')
        return

    while True:
        data, addr = server.recvfrom(1024)
        if not data:
            continue

        with open('received_message.txt', 'ab') as file:
            file.write(data)

        with open('received_message.txt', 'r') as file:
            file_content = file.readlines()
>>>>>>> origin/jlsf1

        os.remove('received_message.txt')

<<<<<<< HEAD
def broadcast():
    while True:
        while not messages.empty():
            message, addr = messages.get()
            if addr not in clients:
                clients.append(addr)

            for client in clients:
                try:
                    if message.decode().startswith("SIGNUP_TAG:"):
                        name = message.decode().split(":")[1]
                        server.sendto(f"{name} entrou".encode(), client)
                    else:
                        server.sendto(message, client)
                except Exception as e:
                    print(f"Error sending message to client {client}: {e}")
                    clients.remove(client)
=======
        for line in file_content:
            line = line.strip()  # Remove espaços em branco no início e no final da linha
            if "SIGNUP_TAG:" in line:
                name = line.split(":")[1]
                sent_msg = f"{name} entrou na sala"
                if addr not in clients:
                    clients.append(addr)
                send_txt(server, clients, addr, sent_msg)
            elif "SIGNOUT_TAG:" in line:
                name = line.split(":")[1]
                sent_msg = f"{name} saiu da sala"
                if addr in clients:
                    clients.remove(addr)
                send_txt(server, clients, addr, sent_msg)
            else:
                send_txt(server, clients, addr, line)
>>>>>>> origin/jlsf1

def send_txt(server, clients, addr, message):
    for client in clients:
        if client != addr:  # Não envia a mensagem para o próprio emissor
            with open('sent_message.txt', 'w') as file:
                file.write(message)
            with open('sent_message.txt', 'rb') as file:
                while (chunk := file.read(1024)):
                    server.sendto(chunk, client)
            os.remove('sent_message.txt')

<<<<<<< HEAD
thread_1 = threading.Thread(target=receive)
thread_2 = threading.Thread(target=broadcast)
thread_1.start()
thread_2.start()
=======
main()
>>>>>>> origin/jlsf1
