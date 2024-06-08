import threading
import socket
import queue
from datetime import datetime

clients = []

def main():

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        server.bind(('localhost', 7777))
        server.listen()
    except:
        return print('\nNão foi possível iniciar o servidor!\n')

    while True:
        client, addr = server.accept()
        clients.append(client)

        thread = threading.Thread(target=messagesTreatment, args=[client])
        thread.start()

def messagesTreatment(client):
    while True:
        try:
            msg = client.recv(2048)
            broadcast(msg, client)
        except:
            deleteClient(client)
            break

def broadcast(msg, client):
    for clientItem in clients:
        if clientItem != client:
            try:
                clientItem.send(msg)
            except:
                deleteClient(clientItem)

def broadcast():
    while True:
        while not messages.empty():
            message, addr = messages.get()
            message_decoded = message.decode()
            timetamp = datetime.now().strftime('%H:%M - %d/%m/%Y')

            for client in clients:
                try:
                    if message.decode().startswith("SIGNUP_TAG:"):
                        name = message.decode().split(":")[1]
                        server.sendto(f"{name} entrou na sala".encode(), client)
                    elif message.decode().startswith("SIGNOUT_TAG:"):
                        name = message.decode().split(":")[1]
                        server.sendto(f"{name} saiu da sala".encode(), client)
                    else:
                        server.sendto(f"{message_decoded} {timetamp}".encode(), client)
                except Exception as e:
                    print(f"Error sending message to client {client}: {e}")
                    clients.remove(client)
            if addr not in clients:
                clients.append(addr)
def deleteClient(client):
    clients.remove(client)

main()