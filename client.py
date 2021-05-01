import socket
import select
import errno
import sys

HEADER_LENGTH = 10

IP = "127.0.0.1" # IP de LoopBack, pois estamos fazendo uma aplicação local
PORTA = 65432
nome_usuario = input("Nome do usuario: ")

# Cria um objeto socket, IPv4 (AF_INET) e TCP(SOCK_STREAM)
cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Conecta no servidor
cliente_socket.connect((IP, PORTA))
cliente_socket.setblocking(False)

# Faz a primeira conexao com o servidor
usuario = nome_usuario.encode('utf-8')
usuario_header = f"{len(usuario):<{HEADER_LENGTH}}".encode('utf-8')
cliente_socket.send(usuario_header + usuario)

while True:

    messagem = input(f'{nome_usuario} > ')

    if messagem:
        messagem = messagem.encode('utf-8')
        messagem_header = f"{len(messagem):<{HEADER_LENGTH}}".encode('utf-8')
        cliente_socket.send(messagem_header + messagem)

    try:
        # Tentamos ler as mensagem recebidas
        while True:

            # Recebe o "header" com o tamanho do nome do usuario
            usuario_header = cliente_socket.recv(HEADER_LENGTH)

            # Caso vazio o servidor fechou a conexao
            if not len(usuario_header):
                print('Conexão fechada pelo servidor')
                sys.exit()

            tamanho_usuario = int(usuario_header.decode('utf-8').strip())
            usuario = cliente_socket.recv(tamanho_usuario).decode('utf-8')

            # Com as informações do usuario conseguimos pegar a
            messagem_header = cliente_socket.recv(HEADER_LENGTH)
            tamanho_mensagem = int(messagem_header.decode('utf-8').strip())
            messagem = cliente_socket.recv(tamanho_mensagem).decode('utf-8')

            print(f'{usuario} > {messagem}')

    except IOError as e:
        # Caso recebamos algum erro vamos validar se ele nao é nenhum dos abaixos e vamos alertar
        # Os erros EAGAIN e EWOULDBLOCK acontecem em alguns sistemas operacionais quando reutilizamos o mesmo socket e podemos ignora-los
        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
            print('Erro de Leitura: {}'.format(str(e)))
            sys.exit()

        continue

    except Exception as e:
        print('Reading error: {}'.format(str(e)))
        sys.exit()