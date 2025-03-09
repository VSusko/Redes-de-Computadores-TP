import socket                   # Importa socket para comunicação com o servidor FTP

class MyFTPClient:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client = None

    # ================/ Método de login no servidor FTP /================
    def login(self, user, password):
        
        # ================/ Conexao do cliente com servidor /================
        # Cria o socket para comunicação com o servidor
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((self.host, self.port))  # Conecta ao servidor FTP

        # Processo de autenticação
        boas_vindas = self.client.recv(1024).decode().strip()  # Recebe a mensagem de boas-vindas
        print("Mensagem de boas vindas: ", boas_vindas)
        
        pedido_login = self.client.recv(1024).decode().strip()  # Recebe o pedido de login
        print("Pedido de login: ", pedido_login)
        self.client.sendall((user + "\n").encode())     # Envia o nome de usuário
        
        self.client.recv(1024)                          # Recebe o pedido de senha
        self.client.sendall((password + "\n").encode())  # Envia a senha

        response = self.client.recv(1024).decode().strip() # Recebe a resposta do servidor sobre o login

        if "Login bem-sucedido" in response:
            return True
        else:
            return False

    # ================/ Métodos de comunicacao com o servidor FTP /================
    def send_command(self, new_command: str) -> str:
        if self.client:
            try:
                # Envia o comando para o servidor
                self.client.sendall((new_command + "\n").encode())
                return True
            except Exception as e:
                self.disconnect()  # Fecha a conexão se houver erro
                return f"Erro ao enviar comando: {e}"
        return "Erro: Cliente não conectado"
                
    def server_response(self):
        if  self.client:
            response = self.client.recv(4096).decode()
            return response

    def disconnect(self):
        if self.client:  # Verifica se a conexão existe
            self.client.close() # Encerra a conexao de rede
            self.client = None 