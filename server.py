import socket
import select

HEADER_LENGTH = 10

IP = "127.0.0.1" # IP de LoopBack, pois estamos fazendo uma aplicação local
PORTA = 65432

# Cria um objeto socket, IPv4 (AF_INET) e TCP(SOCK_STREAM)
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Permite reutilizar o socket
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# Binda o servidor a um IP e porta
server_socket.bind((IP, PORTA))
# Garante que o server esta escutando novas conexoes
server_socket.listen()

# Lista de sockets para select.select()
lista_sockets = [server_socket]
# Lista de usuarios
clientes = {}

print(f'Esperando por conexoes em {IP}:{PORTA}...')

def recebe_mensagem(cliente_socket):
    """
    Essa função lida com o recebimento de mensagens, 
    """
    try:
        # O "header" da mensagem
        messagem_header = cliente_socket.recv(HEADER_LENGTH)

        # Se nao recebermos o header, isso significa que o cliente fechou a conexão.
        if not len(messagem_header):
            return False

        messagem_tamanho = int(messagem_header.decode('utf-8').strip())

        return {'header': messagem_header, 'data': cliente_socket.recv(messagem_tamanho)}

    except:
        # Lida com qualquer interrupção brusca na comunicação
        return False

def broadcast(mensagem, socket):
    """
    Função responsavel por transmitir as mensagens de um usuario para os demais usuarios
    """
    # Se nao tiver mensagem, entao a conexão foi fechada e precisamo limpar as coisas
    if mensagem is False:
        print('Conexão fechada por: {}'.format(clientes[socket]['data'].decode('utf-8')))
        # Remove da lista de sockets
        lista_sockets.remove(socket)
        #Remove da lista de usuarios
        del clientes[socket]
        return

    # Pega o usuario que enviou a mensagem
    usuario = clientes[socket]
    print(f'Messagem recebida de {usuario["data"].decode("utf-8")}: {mensagem["data"].decode("utf-8")}')
    # Manda a mensagem recebida para todos os demais clientes
    for cliente in clientes:
        cliente.send(usuario['header'] + usuario['data'] + mensagem['header'] + mensagem['data'])

def aceita_conexao():
    """
    Função responsavel por aceitar novas conexões
    """
    # Aceita a conexao
    cliente_socket, cliente_endereco = server_socket.accept()

    # O cliente deverá mandar seu nome de usuario como sua primeira mensagem
    nome_usuario = recebe_mensagem(cliente_socket)

    # Se a mensagem é nula entao continuamos em frente
    if nome_usuario is False:
        return

    # Adicionamos o novo cliente na lista de sockets do servidor
    lista_sockets.append(cliente_socket)

    # E salvamos as informações do usuario na lista de clientes
    clientes[cliente_socket] = nome_usuario

    print('Conexão aceita de {}:{}, usuario: {}'.format(*cliente_endereco, nome_usuario['data'].decode('utf-8')))


while True:
    sockets_lidos, _, excessao_sockets = select.select(lista_sockets, [], lista_sockets)

    # Para cada socket lido na nossa lista_sockets (que virou sockets_lidos)
    for socket in sockets_lidos:

        # Caso o socket notificado seja o socket usado para o servidor, isso significa que um novo cliente deseja conectar
        if socket == server_socket:
            aceita_conexao()

        # Caso contrario, o socket ja esta conectado e esta mandando uma mensagem
        else:
            mensagem = recebe_mensagem(socket)
            broadcast(mensagem, socket)

    # Caso tenhamos problemas com algum socket vamos se livrar dele
    for socket in excessao_sockets:
        lista_sockets.remove(socket)
        del clientes[socket]
