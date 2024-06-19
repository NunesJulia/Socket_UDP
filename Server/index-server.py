import socket
import os

clients = []

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Inicializa o socket udp do servidor

    try:
        server.bind(('localhost', 7777))  #Define o endereço de porta do server
        print("Servidor iniciado na porta 7777")
    except Exception as e:
        print(f'\nNão foi possível iniciar o servidor! Erro: {e}\n')
        return

    while True:
        data, addr = server.recvfrom(1024) # recebe do cliente
        if not data:
            continue

        # trata a leitura de arquivos
        with open('received_message.txt', 'ab') as file:
            file.write(data)

        with open('received_message.txt', 'r') as file:
            file_content = file.readlines()

        os.remove('received_message.txt')

        for line in file_content:
            line = line.strip()  # Remove espaços em branco no início e no final da linha
            
            # Detecta se é uma mensagem de login e recebe o nome do cliente, adiciona a lista de clientes ou remove da mesma.
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

# Função que trata o envio de mensagens para os clientes
def send_txt(server, clients, addr, message):
    for client in clients:
        if client != addr:  # Não envia a mensagem para o próprio emissor
            with open('sent_message.txt', 'w') as file:
                file.write(message)
            with open('sent_message.txt', 'rb') as file:
                while (chunk := file.read(1024)):
                    server.sendto(chunk, client)
            os.remove('sent_message.txt')

main()