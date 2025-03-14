import tkinter as tk                      # Importa o módulo Tkinter para criar a interface gráfica
from tkinter import messagebox, simpledialog            # Importa messagebox para exibir mensagens ao usuário
import os                                 # Importa os para manipulação de diretórios e arquivos
import threading                          # Importa threading para permitir múltiplas conexões simultâneas
from client_ftp import MyFTPClient        # Importa a lógica do FTP


# ==================/ Variaveis de escopo global /==================
# Definição do endereço e porta do servidor FTP
HOST = "127.0.0.1"
PORT = 2121

# Diretório base onde os arquivos do cliente serão armazenados
BASE_DIR = os.path.abspath("client_files")
os.makedirs(BASE_DIR, exist_ok=True)  # Cria a pasta se ela não existir

DEBUG = 1

# ==================/ Classe para a interface /==================

class MyFTPGUI:
    
    # ================/ Construcao das telas da classe /================
    def __init__(self, root_window):
        
        self.MyFTPClient = MyFTPClient(HOST,PORT)
        
        self.logged_in = False
        self.current_server_dir = ""
        # self.server_path_var = tk.StringVar(value="/")
        
        # ================/ Configuracao da janela /================
        self.root_window = root_window
        self.root_window.title("MyFTP Client")  # Define o título da janela
        self.root_window.geometry("500x500")    # Define o tamanho da janela
        self.root_window.minsize(950, 600)      # Define o tamanho mínimo da janela
        self.root_window.maxsize(950, 600)      # Define o tamanho máximo da janela             
        self.root_window.configure(bg = "lightgray")
        self.root_window.protocol("WM_DELETE_WINDOW", self.close_app) # Encerra a aplicação no botao
        self.center_window(950, 600)    # Centraliza a janela
        
        self.login_screen()
        self.create_frame_main()
        # self.main_screen()
        
    def login_screen(self):
        # ================/ Configuracao da janela de login /================

        self.frame_login = tk.Frame(root_window)                 # Criação do frame de login (usando pack para organização)
        self.frame_login.pack(pady=50, fill="both", expand=True) # Adiciona espaçamento vertical
        self.frame_login.config(bg = "lightgray")

        tk.Label(self.frame_login, text="Usuário:", bg = "lightgray").pack(pady=20) # Campo de entrada para o nome de usuário
        self.entry_user = tk.Entry(self.frame_login)
        self.entry_user.pack()                                    # Exibe o campo de usuario
        self.entry_user.bind("<Return>", lambda event: self.start_connection())
        
        tk.Label(self.frame_login, text="Senha:", bg = "lightgray").pack(pady=20) # Campo de entrada para a senha
        self.entry_pass = tk.Entry(self.frame_login, show="*")  # Oculta a senha digitada
        self.entry_pass.pack()                                  # Exibe o campo de senha
        self.entry_pass.bind("<Return>", lambda event: self.start_connection())
    
        tk.Button(self.frame_login, text="Conectar", command=self.start_connection).pack(pady=60) # Botão para conectar ao servidor
        
        
    
    def center_window(self, width, height):
        # Obtém a largura e altura da tela do usuário
        screen_width = self.root_window.winfo_screenwidth()
        screen_height = self.root_window.winfo_screenheight()
        
        # Calcula a posição para centralizar a janela
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        # Define a geometria da janela
        self.root_window.geometry(f"{width}x{height}+{x}+{y}")
    

    def create_frame_main(self):
        # ================/ Configuracao do frame principal de comandos /================
        self.frame_main = tk.Frame(self.root_window)
        
        
        # Top navigation bar
        top_frame = tk.Frame(self.frame_main, height=40)
        top_frame.pack(fill="x", side="top")
        
        # Server path display
        # self.server_path_var = tk.StringVar(value="/")
        # path_label = tk.Label(top_frame, text="Server Path:")
        # path_label.pack(side="left", padx=5, pady=5)
        
        # server_path_display = tk.Entry(top_frame, textvariable=self.server_path_var, 
        #                                width=40, state="readonly")
        # server_path_display.pack(side="left", padx=5, pady=5)
        
        # Buttons for common operations
        refresh_btn = tk.Button(top_frame, text="Atualizar", command=self.refresh_both)
        refresh_btn.pack(side="left", padx=10, pady=5)
        
        mkdir_btn = tk.Button(top_frame, text="Novo Diretório", command=self.show_mkdir_dialog)
        mkdir_btn.pack(side="right", padx=5, pady=5)
        
        rmdir_btn = tk.Button(top_frame, text="Remover Diretório", command=self.show_rmdir_dialog)
        rmdir_btn.pack(side="right", padx=5, pady=5)
        
        # Main content with status bar for messages
        content_frame = tk.Frame(self.frame_main)
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Painel esquerdo
        server_frame = tk.LabelFrame(content_frame, text="Arquivos do Servidor")
        server_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        # Frame pro botão "Up"
        server_toolbar = tk.Frame(server_frame)
        server_toolbar.pack(fill="x")
        
        up_btn = tk.Button(server_toolbar, text="↑ Diretório acima", command=self.go_up_directory)
        up_btn.pack(side="left", padx=5, pady=5)
        
        # Label de diretorio atual
        self.dir_label = tk.Label(server_toolbar, text=f"Diretório atual: 'server_files'")
        self.dir_label.pack(pady=20)  
              
        # Arquivos do servidor
        server_file_frame = tk.Frame(server_frame)
        server_file_frame.pack(fill="both", expand=True)
        
        self.server_files_list = tk.Listbox(server_file_frame, selectmode=tk.SINGLE)
        self.server_files_list.pack(side="left", fill="both", expand=True)
        self.server_files_list.bind("<Double-Button-1>", self.on_server_item_dblclick)
        
        server_scrollbar = tk.Scrollbar(server_file_frame)
        server_scrollbar.pack(side="right", fill="y")
        
        self.server_files_list.config(yscrollcommand=server_scrollbar.set)
        server_scrollbar.config(command=self.server_files_list.yview)
        
        # Painel central
        transfer_frame = tk.Frame(content_frame)
        transfer_frame.pack(side="left", fill="y", padx=10, pady=5)
        
        # Create transfer buttons
        to_server_btn = tk.Button(transfer_frame, text="←", font=("Arial", 16), width=2,
                                  command=self.upload_file)
        to_server_btn.pack(pady=10)
        
        to_client_btn = tk.Button(transfer_frame, text="→", font=("Arial", 16), width=2,
                                  command=self.download_file)
        to_client_btn.pack(pady=10)
        
        # Painel direito
        client_frame = tk.LabelFrame(content_frame , text="Arquivos do Cliente")
        client_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        # Arquivos do cliente
        client_file_frame = tk.Frame(client_frame)
        client_file_frame.pack(fill="both", expand=True)
        
        self.client_files_list = tk.Listbox(client_file_frame, selectmode=tk.SINGLE)
        self.client_files_list.pack(side="left", fill="both", expand=True)
        
        client_scrollbar = tk.Scrollbar(client_file_frame)
        client_scrollbar.pack(side="right", fill="y")
        
        self.client_files_list.config(yscrollcommand=client_scrollbar.set)
        client_scrollbar.config(command=self.client_files_list.yview)
        
        # Caixa de respostas
        bottom_frame = tk.Frame(self.frame_main, height=40)
        bottom_frame.pack(fill="x", side="bottom")
        
        # Área de saída de texto para exibir respostas do servidor
        self.text_output = tk.Text(bottom_frame, height=10, width=55)
        self.text_output.pack(padx=10, pady=5, fill="both", expand=True)
        
        
        if DEBUG:
            self.start_connection()

    # Métodos
    
    def update_dir_label(self, new_dirname):
        self.dir_label.config(text=f"Diretório atual: '{new_dirname}'")
    
    
    def refresh_client_files(self):
        """Refresh the client files list"""
        self.client_files_list.delete(0, tk.END)
        
        try:
            # Lista os arquivos do diretorio do cliente
            files = os.listdir(BASE_DIR)
            for file in sorted(files):
                # Diretórios são escritos com "/" no final
                path = os.path.join(BASE_DIR, file)
                if os.path.isdir(path):
                    self.client_files_list.insert(tk.END, f"{file}/")
                else:
                    self.client_files_list.insert(tk.END, file)
        except Exception as e:
            self.text_output.insert(tk.END, f"Erro ao carregar arquivos do cliente: {str(e)}\n")
            self.text_output.see(tk.END)
    
    def refresh_server_files(self):
        """Refresh the server files list"""
        self.server_files_list.delete(0, tk.END)
        
        if not self.logged_in:
            return
            
        try:
            # Send ls command to get server files
            self.MyFTPClient.send_command("ls")
            response = self.MyFTPClient.server_response()
            
            # Process the response
            if  "O diretório está vazio" in response:
                self.text_output.see(tk.END)
            else:
                # Split the response by newlines to get file list
                files = response.strip().split('\n')
                # Remove the prompt part if present
                files = [f for f in files if f and not f.startswith("Servidor MyFTP>")]
                
                for file in sorted(files):
                    self.server_files_list.insert(tk.END, file)
                
        except Exception as e:
           self.text_output.insert(tk.END, f"Erro ao carregar arquivos do servidor: {str(e)}\n")
           self.text_output.see(tk.END)
    
    def refresh_both(self):
        """Refresh both file lists"""
        self.refresh_client_files()
        self.refresh_server_files()
        
        self.text_output.delete("1.0", tk.END)  # Limpa toda a área de texto

    def show_mkdir_dialog(self):
        folder_name = tk.simpledialog.askstring("Novo Diretório", "Insira o nome do diretório:")
        if folder_name:
            self.MyFTPClient.send_command(f"mkdir {folder_name}")
            response = self.MyFTPClient.server_response()
            
            if "Este diretório já existe" in response:
                messagebox.showerror("ERRO","Este diretório já existe no sistema!")
                return
            
            self.text_output.insert(tk.END, f"Diretório '{folder_name}' criado com Sucesso!\n")
            self.text_output.see(tk.END)
            self.refresh_server_files()

    def show_rmdir_dialog(self):
        selection = self.server_files_list.curselection()
        
        if not selection:
            messagebox.showerror("ERRO","Por favor, selecione alguma pasta")
            return
        
        folder_name = self.server_files_list.get(selection[0])    
        
        if messagebox.askokcancel("Remover pasta", f"Tem certeza que deseja remover o diretório '{folder_name}'? Todos os arquivos contidos nele serão deletados"):
            if self.MyFTPClient.send_command(f"rmdir {folder_name}"):
                response = self.MyFTPClient.server_response()
                self.text_output.insert(tk.END, (response.strip() + "\n"))
                self.text_output.see(tk.END)
                self.refresh_server_files()

    def download_file(self):
        """Download selected file from client to server"""
        selection = self.server_files_list.curselection()
        
        if not selection:
            messagebox.showinfo("Selection Required", "Please select a file to download")
            return
            
        filename = self.server_files_list.get(selection[0])
        
        # Não baixar diretórios
        if filename.endswith("/"):
            messagebox.showinfo("Cannot Download", "Cannot download directories")
            return
        
        """Navigate to parent directory"""
        if not self.logged_in:
            return
            
        try:
            self.MyFTPClient.send_command(f"get {filename}")
            response = self.MyFTPClient.server_response()
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
                    if b"FIM_TRANSMISSAO" in data:
                        print("cabou aq tb")
                        break
                    f.write(data)
            
            self.text_output.insert(tk.END, f"Arquivo '{file_get}' recebido com sucesso!\n")
            self.text_output.see(tk.END)
            self.refresh_client_files()
        except Exception as e:
            self.text_output.insert(tk.END, f"Erro {str(e)}\n")
            self.text_output.see(tk.END)

    def upload_file(self):
        """Upload selected file from client to server"""
        selection = self.client_files_list.curselection()
        if not selection:
            messagebox.showinfo("Selection Required", "Please select a file to upload")
            return
            
        filename = self.client_files_list.get(selection[0])
        
        """Navigate to parent directory"""
        if not self.logged_in:
            return
            
        try:
            self.MyFTPClient.send_command(f"put {filename}")
            response = self.MyFTPClient.server_response()
            
            if response.startswith("put "):
                file_path = os.path.join(BASE_DIR, filename)
                
                with open(file_path, "rb") as f:
                    data = f.read(1024)
                    while data:
                        self.MyFTPClient.client.sendall(data)
                        data = f.read(1024)
                
                self.MyFTPClient.client.sendall(b"FIM_TRANSMISSAO")
            else:
                self.root_window.after(0, self.text_output.insert(tk.END, f"Upload falhou: {response}"))
                self.text_output.see(tk.END)
            
            print("cabou")
            
            self.text_output.insert(tk.END, f"Arquivo '{filename}' enviado com sucesso!\n")
            self.text_output.see(tk.END)
            self.refresh_server_files()
        except Exception as e:
            self.text_output.insert(tk.END, f"Erro {str(e)}\n")
            self.text_output.see(tk.END)

    def on_server_item_dblclick(self, event):
        """Handle double-click on server item (navigate folders)"""
        selection = self.server_files_list.curselection()
        directory_name = self.server_files_list.get(selection[0])
        
        self.change_directory(directory_name)
    
    def go_up_directory(self):
        """Navigate to parent directory"""
        if not self.logged_in:
            return
            
        try:
            self.MyFTPClient.send_command("cd ..")
            response = self.MyFTPClient.server_response()
            self.text_output.insert(tk.END, (response.strip() + "\n"))
            self.text_output.see(tk.END)
            self.refresh_server_files()
            if "diretório raiz" in response:
                self.update_dir_label("server_files")
            else:
                self.update_dir_label(response[35:].strip())
        except Exception as e:
            self.text_output.insert(tk.END, f"Erro {str(e)}\n")
            self.text_output.see(tk.END)

    def change_directory(self, folder_name):
        if not self.logged_in:
            return
            
        try:
            self.MyFTPClient.send_command(f"cd {folder_name}")
            response = self.MyFTPClient.server_response()
            
            if "Diretório alterado" in response:
                # Update display
                if self.current_server_dir:
                    self.current_server_dir += f"/{folder_name}"
                else:
                    self.current_server_dir = folder_name
                    
                self.refresh_server_files()
                self.text_output.insert(tk.END, f"Mudou para o diretório: '{folder_name}'\n")
                self.text_output.see(tk.END)
                self.update_dir_label(folder_name)
            else:
                self.text_output.insert(tk.END, "O arquivo não é um diretório!\n")
                self.text_output.see(tk.END)
        except Exception as e:
            self.text_output.insert(tk.END, f"Erro: {str(e)}\n")
            self.text_output.see(tk.END)

    def start_connection(self):
        if DEBUG:
            user = "1"
            password = "1"
        else:
            user     = self.entry_user.get().strip()  # Obtém o nome de usuário e remove espaços extras
            password = self.entry_pass.get().strip()  # Obtém a senha e remove espaços extras
        
        # Cria uma thread para conectar sem travar a GUI
        thread = threading.Thread(target=self.login_response, args=(user,password))
        thread.start()

    def login_response(self, user, password):
        try: 
            if DEBUG:
                self.MyFTPClient.login(user,password)
                self.frame_login.pack_forget()  # Oculta a tela de login
                self.frame_main.pack(fill="both", expand=True) 
                self.logged_in = True
                self.refresh_both()
                return
            
            if  self.MyFTPClient.login(user,password):
                # Se o login for bem-sucedido, exibe uma mensagem e troca para a tela principal
                messagebox.showinfo("Sucesso", "Login bem-sucedido!")
                self.frame_login.pack_forget()  # Oculta a tela de login
                self.frame_main.pack(fill="both", expand=True) 
                self.logged_in = True
                self.refresh_both()

            else:
                # Se o login falhar, exibe uma mensagem de erro e fecha a conexão
                messagebox.showerror("Erro", "Login falhou!")
                self.MyFTPClient.disconnect(self.MyFTPClient) 
    
        except Exception as e:
            # Se houver falha na conexão, exibe uma mensagem de erro
            messagebox.showerror("Erro", f"Falha na conexão: {e}")
            self.client = None
    
    def close_app(self):
        if self.logged_in: #Se o cliente ja fez o login, disconecta primeiro
            if DEBUG:
                self.MyFTPClient.send_command("exit")
                self.MyFTPClient.disconnect()
                self.root_window.destroy()
                return
            
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


    root_window.mainloop()  # Inicia o loop da interface gráfica
