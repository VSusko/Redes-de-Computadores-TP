import socket  # Importa a biblioteca para comunicação via sockets
import threading  # Importa threading para permitir múltiplas conexões simultâneas
import os  # Importa os para manipulação de diretórios e arquivos

# Dicionário de usuários cadastrados no servidor (login: senha)
USERS = {"1": "1", "user2": "pass2"}

# Configurações do servidor FTP
HOST = "0.0.0.0"  # Aceita conexões de qualquer IP
PORT = 2121  # Porta que o servidor irá escutar

# Diretório base onde os arquivos do servidor serão armazenados
BASE_DIR = os.path.abspath("server_files")
os.makedirs(BASE_DIR, exist_ok=True)  # Cria a pasta se ela não existir


# Função para tratar a conexão de um cliente
def handle_client(connected_client, addr):
    print(f"Nova conexão de {addr}")  # Exibe no terminal o IP do cliente conectado
    connected_client.sendall("Bem-vindo ao MyFTP!\n".encode())  # Envia mensagem de boas-vindas

    try:
        # Processo de autenticação do usuário
        connected_client.sendall("Login: ".encode())  # Solicita o login do usuário
        username = connected_client.recv(1024).decode().strip()  # Recebe o login
        print(f"Usuário recebido: '{repr(username)}'")  # Mensagem de depuração

        connected_client.sendall("Senha: ".encode())  # Solicita a senha do usuário
        password = connected_client.recv(1024).decode().strip()  # Recebe a senha
        print(f"Senha recebida: '{repr(password)}'")  # Mensagem de depuração

        print(USERS.get(username))  # Exibe a senha armazenada para depuração

        # Verifica se o usuário e senha são válidos
        if USERS.get(username) != password:
            connected_client.sendall("Login falhou. Conexão encerrada.\n".encode())  # Mensagem de erro
            connected_client.close()  # Fecha a conexão
            return  # Encerra a função

        # Se o login for bem-sucedido, envia a confirmação ao cliente
        connected_client.sendall("Login bem-sucedido!\n".encode())
        current_dir = BASE_DIR  # Define o diretório inicial do usuário

        # Loop para receber comandos do cliente
        while True:
            connected_client.sendall("MyFTP> ".encode())  # Envia o prompt para o cliente
            command = connected_client.recv(1024).decode().strip()  # Recebe o comando

            if not command:
                continue  # Se o comando for vazio, aguarda o próximo

            # Comando para sair da sessão
            if command.lower() == "exit":
                break  # Encerra o loop e a conexão com o cliente

            # Comando para listar arquivos do diretório atual
            elif command.lower() == "ls":
                files = "\n".join(os.listdir(current_dir)) or "Diretório vazio"  # Lista os arquivos
                connected_client.sendall(files.encode() + b"\n")  # Envia a lista para o cliente

            # Comando para mudar de diretório
            elif command.startswith("cd "):
                new_dir = command[3:].strip()  # Obtém o nome do diretório
                path = os.path.join(current_dir, new_dir)  # Cria o caminho absoluto
                if os.path.isdir(path):  # Verifica se o diretório existe
                    current_dir = path  # Atualiza o diretório atual
                    connected_client.sendall("Diretório alterado\n".encode())
                else:
                    connected_client.sendall("Diretório não encontrado\n".encode())

            # Comando para voltar um diretório
            elif command.lower() == "cd..":
                if current_dir != "./":  # Se não estiver no diretório raiz
                    current_dir = os.path.dirname(current_dir)  # Volta um nível
                    connected_client.sendall("Voltou um diretório\n".encode())
                else:
                    connected_client.sendall("Já está na raiz\n".encode())  # Mensagem de erro

            # Comandos não implementados
            elif command.lower() == "mkdir":
                connected_client.sendall("Ainda não implementado\n".encode())

            elif command.lower() == "rmdir":
                connected_client.sendall("Ainda não implementado\n".encode())

            elif command.lower() == "put":
                connected_client.sendall("Ainda não implementado\n".encode())

            elif command.lower() == "get":
                connected_client.sendall("Ainda não implementado\n".encode())

            # Comando desconhecido
            else:
                connected_client.sendall("Comando desconhecido\n".encode())

    except Exception as e:
        print(f"Erro com {addr}: {e}")  # Exibe erros no terminal
    finally:
        print(f"Conexão encerrada com {addr}")  # Mensagem de desconexão
        connected_client.close()  # Fecha a conexão com o cliente


# Função para iniciar o servidor FTP
def start_server():
    # Cria o socket do servidor
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))  # Associa o socket ao IP e porta especificados
    server.listen(5)  # Permite até 5 conexões simultâneas
    print(f"Servidor MyFTP rodando em {HOST}:{PORT}")  # Exibe no terminal que o servidor está rodando

    # Loop infinito para aceitar conexões de clientes
    while True:
        connected_client, addr = server.accept()  # Aguarda conexões
        thread = threading.Thread(target=handle_client, args=(connected_client, addr), daemon=True)  
        thread.start()  # Inicia uma thread para tratar o cliente


# Execução principal do programa
if __name__ == "__main__":
    start_server()  # Inicia o servidor
