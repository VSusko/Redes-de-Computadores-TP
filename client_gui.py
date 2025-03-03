import tkinter as tk  # Importa o módulo Tkinter para criar a interface gráfica
from tkinter import messagebox  # Importa messagebox para exibir mensagens ao usuário
import socket  # Importa socket para comunicação com o servidor FTP
import os  # Importa os para manipulação de diretórios e arquivos


# Definição do endereço e porta do servidor FTP
HOST = "127.0.0.1"
PORT = 2121

# Diretório base onde os arquivos do cliente serão armazenados
BASE_DIR = os.path.abspath("client_files")
os.makedirs(BASE_DIR, exist_ok=True)  # Cria a pasta se ela não existir

# Função para receber todos os dados do servidor até que não haja mais nada a ser recebido
# (Atualmente não está sendo utilizada)
def recv_all(client):
    data = b""  # Inicializa a variável para armazenar os dados recebidos
    while True:
        part = client.recv(1024)  # Recebe os dados em blocos de 1024 bytes
        if not part:  # Se não houver mais dados, encerra o loop
            break
        data += part  # Acumula os dados recebidos

    return data.decode().strip()  # Retorna os dados decodificados e sem espaços extras

# Classe que representa o cliente FTP com interface gráfica
class MyFTPClient:
    def __init__(self, root):
        # Configuração da janela principal
        self.root = root
        self.root.title("MyFTP Client")  # Define o título da janela
        self.root.geometry("500x500")  # Define o tamanho da janela
        self.root.minsize(500, 500)  # Define o tamanho mínimo da janela
        self.root.maxsize(500, 500)  # Define o tamanho máximo da janela

        # Criação do frame de login (usando pack para organização)
        self.frame_login = tk.Frame(root)
        self.frame_login.pack(pady=50)  # Adiciona espaçamento vertical

        # Campo de entrada para o nome de usuário
        tk.Label(self.frame_login, text="Usuário:").pack(pady=20)
        self.entry_user = tk.Entry(self.frame_login)
        self.entry_user.pack()

        # Campo de entrada para a senha
        tk.Label(self.frame_login, text="Senha:").pack(pady=20)
        self.entry_pass = tk.Entry(self.frame_login, show="*")  # Oculta a senha digitada
        self.entry_pass.pack()

        # Botão para conectar ao servidor
        tk.Button(self.frame_login, text="Conectar", command=self.login).pack(pady=60)

        # Frame principal (será exibido após o login)
        self.frame_main = tk.Frame(root)

        # Área de saída de texto para exibir respostas do servidor
        self.text_output = tk.Text(self.frame_main, height=23, width=55)
        self.text_output.pack(padx=10, pady=10, fill="both", expand=True)

        # Campo de entrada para comandos FTP
        # Entrada de comando
        self.entry_command = tk.Entry(self.frame_main, width=40)
        self.entry_command.pack(side="left", padx=10, pady=10, expand=True, fill="x")

        # Associa a tecla "Enter" ao envio do comando
        self.entry_command.bind("<Return>", lambda event: self.send_command())
        
        
        # Botão para enviar comandos ao servidor
        self.btn_send = tk.Button(self.frame_main, text="Enviar", command=self.send_command, width=10)
        self.btn_send.pack(side="right", padx=10, pady=10)

    # Método de login no servidor FTP
    def login(self):
        user = self.entry_user.get().strip()  # Obtém o nome de usuário e remove espaços extras
        password = self.entry_pass.get().strip()  # Obtém a senha e remove espaços extras
        
        try:
            # Cria o socket para comunicação com o servidor
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((HOST, PORT))  # Conecta ao servidor FTP

            # Processo de autenticação
            self.client.recv(1024)  # Recebe a mensagem de boas-vindas
            self.client.recv(1024)  # Recebe o pedido de login
            self.client.sendall((user + "\n").encode())  # Envia o nome de usuário

            self.client.recv(1024)  # Recebe o pedido de senha
            self.client.sendall((password + "\n").encode())  # Envia a senha

            # Recebe a resposta do servidor sobre o login
            response = self.client.recv(1024).decode().strip()

            if "Login bem-sucedido" in response:
                # Se o login for bem-sucedido, exibe uma mensagem e troca para a tela principal
                messagebox.showinfo("Sucesso", "Login bem-sucedido!")
                self.frame_login.pack_forget()  # Oculta a tela de login
                self.frame_main.pack(pady=20)  # Exibe a tela principal
            else:
                # Se o login falhar, exibe uma mensagem de erro e fecha a conexão
                messagebox.showerror("Erro", "Login falhou!")
                self.client.close()
                self.client = None
        except Exception as e:
            # Se houver falha na conexão, exibe uma mensagem de erro
            messagebox.showerror("Erro", f"Falha na conexão: {e}")
            self.client = None

    # Método para enviar comandos ao servidor FTP
    def send_command(self):
        if self.client:
            # Lê e exibe a resposta anterior antes de enviar um novo comando
            response = self.client.recv(4096).decode()
            self.text_output.insert(tk.END, response)
            
            command = self.entry_command.get().strip()  # Obtém o comando digitado pelo usuário
            
            if not command:
                return  # Se o comando estiver vazio, não faz nada

            try:
                # Envia o comando para o servidor
                self.client.sendall((command + "\n").encode())

                # Recebe e exibe a resposta do servidor
                response = self.client.recv(4096).decode()
                self.text_output.insert(tk.END, response + "\n")
            except Exception as e:
                # Se houver erro no envio do comando, exibe uma mensagem de erro e fecha a conexão
                messagebox.showerror("Erro", f"Erro ao enviar comando: {e}")
                self.client.close()
                self.client = None

# Função para centralizar a janela no meio da tela do usuário
def center_window(window, width=500, height=500):
    # Obtém a largura e altura da tela do usuário
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    
    # Calcula a posição para centralizar a janela
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    
    # Define a geometria da janela
    window.geometry(f"{width}x{height}+{x}+{y}")

# Inicialização da interface gráfica
if __name__ == "__main__":
    root = tk.Tk()  # Cria a janela principal
    app = MyFTPClient(root)  # Instancia a classe do cliente FTP

    # Centraliza a janela
    center_window(root, 500, 500)

    root.mainloop()  # Inicia o loop da interface gráfica
