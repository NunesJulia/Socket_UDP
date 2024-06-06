import threading
import socket
import queue

clients = []
messages = queue.Queue()
server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind(('localhost', 7777))


def receive():
    while True:
        try:
            message, addr = server.recvfrom(1024)
            print(f"Received message from {addr}: {message.decode()}")
            messages.put((message, addr))
        except Exception as e:
            print(f"Error receiving message: {e}")


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


thread_1 = threading.Thread(target=receive)
thread_2 = threading.Thread(target=broadcast)
thread_1.start()
thread_2.start()
