import tkinter as tk                # Importa o módulo Tkinter para criar a interface gráfica
from tkinter import messagebox      # Importa messagebox para exibir mensagens ao usuário
import os                           # Importa os para manipulação de diretórios e arquivos
import threading                    # Importa threading para permitir múltiplas conexões simultâneas
from client_ftp import MyFTPClient  # Importa a lógica do FTP


# ==================/ Variaveis de escopo global /==================
# Definição do endereço e porta do servidor FTP
HOST = "127.0.0.1"
PORT = 2121

# Diretório base onde os arquivos do cliente serão armazenados
BASE_DIR = os.path.abspath("client_files")
os.makedirs(BASE_DIR, exist_ok=True)  # Cria a pasta se ela não existir

logged_in = False

# ==================/ Funcoes Auxiliares /==================

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


# ==================/ Classe para a interface /==================

class MyFTPGUI:
    
    # ================/ Construcao das telas da classe /================
    def __init__(self, root_window):
        
        self.MyFTPClient = MyFTPClient(HOST,PORT)
        
        # ================/ Configuracao da janela de login /================
        self.root_window = root_window
        self.root_window.title("MyFTP Client")  # Define o título da janela
        self.root_window.geometry("500x500")    # Define o tamanho da janela
        self.root_window.minsize(500, 500)      # Define o tamanho mínimo da janela
        self.root_window.maxsize(500, 500)      # Define o tamanho máximo da janela

        self.frame_login = tk.Frame(root_window)                 # Criação do frame de login (usando pack para organização)
        self.frame_login.pack(pady=50, fill="both", expand=True) # Adiciona espaçamento vertical
        
        tk.Label(self.frame_login, text="Usuário:").pack(pady=20) # Campo de entrada para o nome de usuário
        self.entry_user = tk.Entry(self.frame_login)
        self.entry_user.pack()                                    # Exibe o campo de usuario
        self.entry_user.bind("<Return>", lambda event: self.start_connection())
        
        tk.Label(self.frame_login, text="Senha:").pack(pady=20) # Campo de entrada para a senha
        self.entry_pass = tk.Entry(self.frame_login, show="*")  # Oculta a senha digitada
        self.entry_pass.pack()                                  # Exibe o campo de senha
        self.entry_pass.bind("<Return>", lambda event: self.start_connection())
    
        tk.Button(self.frame_login, text="Conectar", command=self.start_connection).pack(pady=60) # Botão para conectar ao servidor

        # ================/ Configuracao do frame principal de comandos /================
        self.frame_main = tk.Frame(root_window) # Frame principal (será exibido após o login)

        # Área de saída de texto para exibir respostas do servidor
        self.text_output = tk.Text(self.frame_main, height=23, width=55)
        self.text_output.pack(padx=10, pady=10, fill="both", expand=True)
        self.root_window.protocol("WM_DELETE_WINDOW", self.close_app) # Encerra a aplicação no botao

        # Campo de entrada para comandos FTP
        self.entry_command = tk.Entry(self.frame_main, width=40) 
        self.entry_command.pack(side="left", padx=10, pady=10, expand=True, fill="x")

        # Associa a tecla "Enter" ao envio do comando
        self.entry_command.bind("<Return>", lambda event: self.commands_output())
        
        # Botão para enviar comandos ao servidor
        self.btn_send = tk.Button(self.frame_main, text="Enviar", command=self.commands_output, width=10)
        self.btn_send.pack(side="right", padx=10, pady=10)
        
    def commands_output(self):
        new_command = self.entry_command.get().strip()  # Obtém o comando digitado pelo usuário
        self.entry_command.delete(0, tk.END)  # Limpa a caixa de comandos
        
        if not new_command:  # Se o comando estiver vazio, não faz nada
            return  

        # Se o comando for de saida
        if "exit" == new_command:
            self.close_app()
            return

        if "clear" == new_command:
            self.text_output.delete("1.0", tk.END)  # Limpa toda a área de texto
            self.text_output.insert(tk.END, ("Servidor MyFTP> "))
            return
            
        command_feedback = self.MyFTPClient.send_command(new_command)
        response = self.MyFTPClient.server_response()
        print("Resposta do servidor: ",response)

        # Se `send_command` retornou um erro, exibe na interface
        if command_feedback != True:
            self.text_output.insert(tk.END, command_feedback)
             
        if "Encerrando conexão" in response:
            self.MyFTPClient.disconnect()
            self.root_window.destroy()
            return
        
        elif response.startswith("ERRO"):
            self.text_output.insert(tk.END, f"Erro ao receber arquivo: {response}\n")
            
        # Quando a resposta começa com "put"
        elif response.startswith("put "):
            file_put = response[4:].strip()
            get_dir_name = os.path.join(BASE_DIR, file_put)
            
            with open(get_dir_name, "rb") as f:
                data = f.read(1024)
                while data:
                    self.MyFTPClient.client.sendall(data)
                    print("pacote enviado")
                    data = f.read(1024)
            
            self.MyFTPClient.client.sendall(b"FIM_TRANSMISSAO")  # Envia fim de transmissão
            print("cabou")
            
            self.text_output.insert(tk.END, f"Arquivo '{file_put}' recebido com sucesso!\n")
    
        # Quando a resposta começa com "get"
        elif response.startswith("get "):
            file_get = response[4:].strip()  # Extrai o nome do arquivo da resposta
            
            # Usa o cliente correto para enviar "READY"
            self.MyFTPClient.client.sendall("READY".encode())
            print("ready enviado")
            
            # Define o caminho completo para salvar o arquivo
            save_path = os.path.join(BASE_DIR, file_get)
            
            with open(save_path, "wb") as f:
                while True:
                    # Usa o cliente correto para receber os dados
                    data = self.MyFTPClient.client.recv(1024)
                    print("pacote recevido")
                    if data == b"FIM_TRANSMISSAO":
                        print("cabou aq tb")
                        break
                    f.write(data)
            
            self.text_output.insert(tk.END, f"Arquivo '{file_get}' recebido com sucesso!\n")
        
        # Caso contrario, mostra a resposta do servidor
        else:
            self.text_output.insert(tk.END, response)  # Exibe a resposta do servidor

        self.text_output.insert(tk.END, ("Servidor MyFTP> "))
        self.text_output.see(tk.END)


    def start_connection(self):
        user     = self.entry_user.get().strip()  # Obtém o nome de usuário e remove espaços extras
        password = self.entry_pass.get().strip()  # Obtém a senha e remove espaços extras
        
        # Cria uma thread para conectar sem travar a GUI
        thread = threading.Thread(target=self.login_response, args=(user,password))
        thread.start()

    def login_response(self, user, password):
        global logged_in
        try: 
            if  self.MyFTPClient.login(user,password):
                # Se o login for bem-sucedido, exibe uma mensagem e troca para a tela principal
                messagebox.showinfo("Sucesso", "Login bem-sucedido!")
                self.frame_login.pack_forget()  # Oculta a tela de login
                self.frame_main.pack(pady=20)   # Exibe a tela principal  
                logged_in = True
                self.text_output.insert(tk.END, ("Servidor MyFTP> "))

            else:
                # Se o login falhar, exibe uma mensagem de erro e fecha a conexão
                messagebox.showerror("Erro", "Login falhou!")
                self.MyFTPClient.disconnect(self.MyFTPClient) 
    
        except Exception as e:
            # Se houver falha na conexão, exibe uma mensagem de erro
            messagebox.showerror("Erro", f"Falha na conexão: {e}")
            self.client = None
    
    def close_app(self):
        global logged_in
        if logged_in: #Se o cliente ja fez o login, disconecta primeiro
            if messagebox.askokcancel("Sair", "Tem certeza que deseja fechar o programa?"):
                self.MyFTPClient.send_command("exit")
                self.MyFTPClient.disconnect()
            else:
                return
        self.root_window.destroy()
        
# ==================/ Função main /==================

if __name__ == "__main__":
    root_window = tk.Tk()
    app = MyFTPGUI(root_window)  # Instancia a classe do cliente FTP

     # Centraliza a janela
    center_window(root_window, 500, 500)

    root_window.mainloop()  # Inicia o loop da interface gráfica
