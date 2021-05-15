import socket
import select
import errno
import sys
import threading
import tkinter
import tkinter.scrolledtext
from tkinter import simpledialog

HEADER_LENGTH = 10

# Variaveis de conexão
IP = "127.0.0.1" 
PORTA = 65432
# Variavel para manter track da sessao
timeout_id = None
# Dicionario de emojis
DICT_EMOJI = {
    ':)' : '\U0001F642',
    ':D' : '\U0001F601',
    ':-D': '\U0001F601',
    ':(' : '\U0001F641',
    ';(' : '\U0001F622',
    ':O' : '\U0001F631',
    ':o' : '\U0001F62F',
    ':P' : '\U0001F61B'
}

class Client:

    def __init__(self, ip, porta):

        # Cria um objeto socket, IPv4 (AF_INET) e TCP(SOCK_STREAM)
        self.cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Conecta no servidor
        self.cliente_socket.connect((ip, porta))
        self.cliente_socket.setblocking(False)

        # MessageBox que pedira pelo nome do usuario
        msg_box = tkinter.Tk()
        msg_box.withdraw()
        nome_usuario = simpledialog.askstring("Nome de usuario", "Por favor escolha um apelido", parent=msg_box)

        # Faz a primeira conexao com o servidor
        nome_usuario.strip()
        self.usuario = nome_usuario.encode('utf-8')
        self.usuario_header = f"{len(nome_usuario):<{HEADER_LENGTH}}".encode('utf-8')
        self.cliente_socket.send(self.usuario_header + self.usuario)

        # Essa variavel é para saber quando devemos inicializar a GUI
        self.gui_pronta = False
        # Essa variavel determina se o programa estara rodando ou nao.
        self.rodando = True

        gui_thread = threading.Thread(target=self.gui_loop)
        recebe_thread = threading.Thread(target=self.recebe_mensagem)

        gui_thread.start()
        recebe_thread.start()

    def gui_loop(self):
        """
        Função responsável pelos elementos visuais do programa que serão rodados na gui_thread
        """
        self.janela = tkinter.Tk()
        self.janela.configure(bg="lightgray")
        self.janela.title(f"Chat (logado como {self.usuario.decode('utf-8')})")

        self.chat_label = tkinter.Label(self.janela, text="Chat:", bg="lightgray")
        self.chat_label.config(font=("Arial", 12))
        self.chat_label.pack(padx=20, pady=5)

        self.area_texto = tkinter.scrolledtext.ScrolledText(self.janela)
        self.area_texto.pack(padx=20, pady=5)
        self.area_texto.config(state='disable') # Impossibilita o usuario alterar o historico do chat

        self.mensagem_label = tkinter.Label(self.janela, text="Mensagem:", bg="lightgray")
        self.mensagem_label.config(font=("Arial", 12))
        self.mensagem_label.pack(padx=20, pady=5)

        self.area_input = tkinter.Text(self.janela, height=5)
        self.area_input.pack(padx=20, pady=5)

        self.botao_enviar = tkinter.Button(self.janela, text="Enviar", command=self.envia_mensagem)
        self.botao_enviar.config(font=("Arial", 12))
        self.botao_enviar.pack(padx=20, pady=5)

        self.gui_done = True # A GUI esta pronta

        # Toda vez que o usuario pressionar uma tecla ou botao reiniciamos o timeout timer
        self.janela.bind_all("<Any-KeyPress>", self.resetar_timer)
        self.janela.bind_all("<Any-ButtonPress>", self.resetar_timer)

        self.janela.protocol("WM_DELETE_WINDOW", self.parar) # Quando a janela é fechada o programa deverá para a execução

        self.janela.mainloop()

    def envia_mensagem(self):
        """
        Função responsável por enviar mensagens para servidor 
        """
        mensagem = self.area_input.get('1.0', 'end')
        if mensagem:
            mensagem = mensagem.encode('utf-8')
            mensagem_header = f"{len(mensagem):<{HEADER_LENGTH}}".encode('utf-8')
            self.cliente_socket.send(mensagem_header + mensagem)
        self.area_input.delete('1.0', 'end')

    def recebe_mensagem(self):
        """
        Função responsável por receber e mostrar as mensagens recebidas pelo servidor 
        """
        while self.rodando:
            # Tentamos ler as mensagem recebidas
            try:
                # Recebe o "header" com o tamanho do nome do usuario
                usuario_header = self.cliente_socket.recv(HEADER_LENGTH)

                # Caso vazio o servidor fechou a conexao
                if not len(usuario_header):
                    print('Conexão fechada pelo servidor')
                    sys.exit()

                tamanho_usuario = int(usuario_header.decode('utf-8').strip())
                usuario = self.cliente_socket.recv(tamanho_usuario).decode('utf-8')

                # Com as informações do usuario conseguimos pegar a mensagem
                mensagem_header = self.cliente_socket.recv(HEADER_LENGTH)
                tamanho_mensagem = int(mensagem_header.decode('utf-8').strip())
                mensagem = self.cliente_socket.recv(tamanho_mensagem).decode('utf-8')
                
                if self.gui_done:
                    # Detecta emojis e mostra a figura para o usuario
                    for emoji, valor_unicode in DICT_EMOJI.items():
                        if emoji in mensagem:
                            mensagem = mensagem.replace(emoji, valor_unicode)
                    texto = f'{usuario} > {mensagem}'
                    self.area_texto.config(state='normal')
                    self.area_texto.insert('end', texto)
                    self.area_texto.yview('end')
                    self.area_texto.config(state='disable')

            except IOError as e:
                # Caso recebamos algum erro vamos validar se ele nao é nenhum dos abaixos e vamos alertar
                # Os erros EAGAIN e EWOULDBLOCK acontecem em alguns sistemas operacionais quando reutilizamos o mesmo socket e podemos ignora-los
                if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                    print('Erro de Leitura: {}'.format(str(e)))
                    self.cliente_socket.close()
                    sys.exit()
                continue

            except Exception as e:
                print('Reading error: {}'.format(str(e)))
                self.cliente_socket.close()
                sys.exit()
    
    def parar(self, inatividade=None):
        """
        Função responsável por parar a execução do programa
        """
        self.rodando = False
        self.janela.destroy()
        self.cliente_socket.close()
        if inatividade:
            print("Sessão expirada por inatividade!")
        exit(0)

    def resetar_timer(self, event=None):
        """
        Função responsável por redefinir o timeout timer quando o usuario tomar uma ação
        """
        global timeout_id
        if timeout_id is not None:
            self.janela.after_cancel(timeout_id)
        timeout_id = self.janela.after(86400000, self.encerrar_sessao) # Faz o timeout depois de 10 minutos
    
    def encerrar_sessao(self):
        """
        Função responsável por encerrar program por inatividade
        """
        self.parar(inatividade=True)    
        

client = Client(IP, PORTA)
