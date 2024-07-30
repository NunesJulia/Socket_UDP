## Socket_UDP

Este é um projeto da disciplina Redes de Computadores, realizado pelos alunos do curso de Sistemas de Informação da Universidade Federal de Pernambuco.

## Integrantes do projeto

- Ismael Henrique - ihxcs

- José Leandro - jlsf

- Júlia Nunes - jnas2

- Mateus Ribeiro - mra4

- Rafael Mourato - rmdv

- Sara Simone - sseap

## Especificações do projeto

Neste projeto, cada equipe desenvolverá um servidor de chat de sala única, onde os clientes se conectam à sala e recebem todas as mensagens dos outros usuários, além de também poderem enviar mensagens. Entretanto, essas mensagens não são strings como o convencional, mas, a fim de haver transferência de arquivos e segmentação dos mesmos, serão arquivos .txt que sendo lidos pelo servidor deverão ser impressos no terminal como mensagens.

1. Primeira Etapa: Transmissão de arquivos com UDP

- Implementação de comunicação UDP utilizando a biblioteca Socket na linguagem Python, com troca de arquivos em formato de texto (.txt) em pacotes de até 1024 bytes (buffer_size) em um chat de sala única, ou seja, apesar da troca inicial entre os usuários ser em arquivos .txt, elas devem ser exibidas em linha de comando no terminal de cada um dos clientes conectados à sala.

2. Segunda Etapa: Implementando chat com transferência confiável RDT 3.0
- Implementação de um sistema de chat básico com transferência confiável, segundo o canal de transmissão confiável rdt3.0, apresentado na disciplina e presente no Kurose, utilizando-se do código resultado da etapa anterior. A cada passo executado do algoritmo, em tempo de execução, deve ser printado na linha de comando do servidor as etapas do processo, de modo a se ter compreensão do que está acontecendo e demonstrar a coerência do rdt3.0 implementado.

## Modo de utilização

Baixe o arquivo zip e certifique-se de possuir todas as bibliotecas instaladas. Após isso, inicialize o servidor e o(s) Cliente(s) e converse! 

## Link para o repositório git

- https://github.com/NunesJulia/Socket_UDP
