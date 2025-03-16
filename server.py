import socket     # Importa a biblioteca para comunicação via sockets
import threading  # Importa threading para permitir múltiplas conexões simultâneas
import os         # Importa os para manipulação de diretórios e arquivos
import time

# ==================/ Variaveis de escopo global /==================

# Dicionário de usuários cadastrados no servidor (login: senha)
USERS = {"1": "1", "user2": "pass2"}

# Configurações do servidor FTP
HOST = "0.0.0.0"  # Aceita conexões de qualquer IP
PORT = 2121  # Porta que o servidor irá escutar

# Diretório base onde os arquivos do servidor serão armazenados
BASE_DIR = os.path.abspath("server_files")
os.makedirs(BASE_DIR, exist_ok=True)  # Cria a pasta se ela não existir


server = None           # Variável global para armazenar o socket do servidor
server_thread = None    # Variável para armazenar a thread do servidor
running = False         # Flag para indicar se o servidor está rodando
client_threads = []     # Lista de threads dos clientes

# Flag de debug
DEBUG = 0 

# ==================/ Funcoes auxiliares /==================

# Funcao de remover os diretorios recursivamente
def remove_dir_safe(directory):
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isdir(item_path):
            remove_dir_safe(item_path)  
        else:
            # Remove arquivos
            os.remove(item_path)  
    # Agora a pasta está vazia e pode ser removida
    os.rmdir(directory)  


# ==================/ Funcoes de interacao com cliente /==================

# Função para tratar a conexão de um cliente
def handle_client(connected_client, addr):
    global running
    print(f"Nova conexão de {addr}")  # Exibe no terminal o IP do cliente conectado

    try:
        # ================/ Conexao do servidor com cliente /================
        connected_client.sendall("Bem-vindo ao MyFTP!\n".encode())  # Envia mensagem de boas-vindas

        # Processo de autenticação do usuário
        
        connected_client.sendall("<Servidor>| Pedido de Login\n".encode())  # Solicita o login do usuário
        
        username = connected_client.recv(1024).decode().strip() # Recebe o login

        if DEBUG:
            print("Usuário recebido: ", username)                   

        connected_client.sendall("<Servidor>| Pedido de Senha\n".encode())  # Solicita a senha do usuário
        password = connected_client.recv(1024).decode().strip()             # Recebe a senha

        if DEBUG:
            print("Senha recebida: ", password)                               
            print("USERS.GET = ", USERS.get(username))  

        # ================/ Verificacao se o usuário e senha são válidos /================
        if USERS.get(username) != password:
            print(f"Conexão encerrada com {addr}")
            connected_client.sendall("<Servidor>| Login falhou. Conexão encerrada.\n".encode())  # Mensagem de erro
            connected_client.close()  # Fecha a conexão
            return  # Encerra a função

        # Se o login for bem-sucedido, envia a confirmação ao cliente
        connected_client.sendall("<Servidor>| Login bem-sucedido!\n".encode())
        current_dir = BASE_DIR  # Define o diretório inicial do usuário

        # ================/ Loop para receber comandos do cliente /================
        while running:
            # connected_client.sendall("Servidor MyFTP>\n".encode()) # Envia o prompt para o cliente
            command = connected_client.recv(1024).decode().strip() # Recebe o comando e divide em duas partes

            # Se o comando for vazio, aguarda o próximo
            if not command:
                continue  

            # Comando para sair da sessão
            if command.lower() == "exit":
                connected_client.sendall("Encerrando conexão...\n".encode())
                break  # Encerra o loop e a conexão com o cliente

            # Comando para listar arquivos do diretório atual
            elif command.lower() == "ls":
                # Lista os arquivos e diretórios
                items = os.listdir(current_dir)  
                files = []

                for item in items:
                    # Se o item é um diretório, concatena o caracter '/'
                    if os.path.isdir(os.path.join(current_dir, item)):  
                        files.append(item + "/") 
                    # Caso contrário, apenas adiciona o arquivo na lista
                    else:
                        files.append(item)  

                # Validação da lista está vazia
                if not files:
                    connected_client.sendall("O diretório está vazio.\n".encode())
                # Envia a lista formatada
                else:
                    response = "\n".join(files)
                    connected_client.sendall(b"\n" + response.encode() + b"\n")  

            # Comando para voltar um diretório
            elif command.lower().split() == ["cd", ".."]: 
                # Se não estiver no diretório raiz, volta um nível
                if current_dir != BASE_DIR:  
                    current_dir = os.path.dirname(current_dir)
                    connected_client.sendall(f"Voltou um diretório. Atualmente em {os.path.basename(current_dir)}\n".encode())
                # Caso contrário, valida a entrada
                else:
                    connected_client.sendall("Já está no diretório raiz!\n".encode())  # Mensagem de erro

            # Comando para mudar de diretório
            elif command.startswith("cd "):
                # Obtndo o nome do diretório
                new_dir = command[3:].strip()  
                # Cria o caminho absoluto
                path = os.path.join(current_dir, new_dir)  
                # Se o diretório existe, atualiza o diretorio atual
                if os.path.isdir(path):  
                    current_dir = path 
                    connected_client.sendall(f"Diretório alterado. Atualmente em {new_dir}\n".encode())
                # Caso contrario, o diretorio não existe
                else:
                    connected_client.sendall("Diretório não encontrado.\n".encode())

            # Comando para criar um novo diretório no servidor
            elif command.startswith("mkdir "):
                # Obtendo o nome do diretorio
                new_dir = command[6:].strip()
                new_dir_path = os.path.join(current_dir, new_dir)

                # Se o diretório ainda não existe, o sistema operacional o cria
                if not os.path.exists(new_dir_path):
                    os.mkdir(new_dir_path)
                    # Mensagem formatada corretamente
                    connected_client.sendall(f'Diretório "{new_dir}" criado.\n'.encode())  
                # Caso contrário, valida se o diretório já existe
                else:
                    connected_client.sendall("Este diretório já existe no sistema!\n".encode()) 
                
            # Comando para remover um diretório no servidor
            elif command.startswith("rmdir "):
                # Obtem o nome do diretorio
                old_dir = command[6:].strip()
                old_dir_path = os.path.join(current_dir, old_dir)

                # Se o diretório ainda existe, o sistema operacional o deleta
                if os.path.isdir(old_dir_path):
                    remove_dir_safe(old_dir_path)
                    # Mensagem formatada corretamente
                    connected_client.sendall(f"Diretório '{old_dir}' deletado.\n".encode())  
                # Caso contrário, valida se o diretório não existe
                else:                    
                    connected_client.sendall("Este arquivo não é um diretório ou não existe no sistema!\n".encode())  # Mensagem de erro

            # Comando para receber um arquivo do cliente para o servidor
            elif command.startswith("put "):
                # Obtendo o arquivo e o diretorio destino
                file_put = command[4:].strip()
                put_dir_name = os.path.join(current_dir, file_put)
                # Envia confirmação ao cliente
                connected_client.sendall(f"put {file_put}".encode())  
                
                with open(put_dir_name, "wb") as f:
                    while True:
                        # Usa o cliente correto para receber os dados
                        data = connected_client.recv(1024)
                        if b"FIM_TRANSMISSAO" in data:
                            if DEBUG:
                                print("fim dos pacotes no servidor")
                            break
                        f.write(data)
            
            # Comando para enviar um arquivo do servidor para o cliente
            elif command.startswith("get "):
                # Obtendo o arquivo e o diretorio destino
                file_get = command[4:].strip()
                get_dir_name = os.path.join(current_dir, file_get)
                
                # Validação caso o diretório não exista
                if not os.path.exists(get_dir_name):  
                    connected_client.sendall("ERRO: Arquivo ou pasta não encontrada\n".encode())
                    continue
                # Validação caso o arquivo seja uma pasta
                elif os.path.isdir(get_dir_name):  
                    connected_client.sendall("ERRO: Não é possível enviar pastas\n".encode())
                    continue
                # Envio do arquivo 
                else:
                    connected_client.sendall(f"get {file_get}".encode())  # Envia confirmação ao cliente
                    if DEBUG:
                        print("confirmação") 
                # Se a mensagem de recebimento foi entregue, começa o envio dos pacotes
                if connected_client.recv(1024).decode().strip() == "READY":
                    if DEBUG:
                        print("ready recebido")
                    
                    with open(get_dir_name, "rb") as f:
                        data = f.read(1024)
                        while data:
                            connected_client.sendall(data)
                            if DEBUG:
                                print("pacote enviado")
                            
                            data = f.read(1024)
                            # Pequena pausa para evitar sobrecarregar o buffer
                            time.sleep(0.001)
                    
                    # Pequena pausa antes de enviar fim de transmissão
                    time.sleep(0.1)
                    
                    # Envia fim de transmissão
                    connected_client.sendall(b"FIM_TRANSMISSAO")  
                    if DEBUG:
                        print("Fim da transmissão no servidor")
                    #connected_client.sendall(f"Arquivo '{file_get}' enviado com sucesso!\n".encode())
                else:
                    print("O cliente não ficou pronto!")

            # Tratamento de qualquer outro comando
            else:
                connected_client.sendall("Comando desconhecido\n".encode())

    # Tratamento de exceções
    except Exception as e:
        # Exibe erros no terminal
        print(f"Erro com {addr}: {e}")
          
    # Mensagem de desconexão e fechamento da conexão com o cliente
    print(f"Conexão encerrada com {addr}")  
    connected_client.close()  


# ================/ Função de controle do servidor FTP /================
# Função de abertura do servidor
def start_server():
    # Cria o socket do servidor
    global server, running, client_threads
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))  # Associa o socket ao IP e porta especificados
    server.listen(5)           # Permite até 5 conexões simultâneas
    running = True
    print(f"Servidor MyFTP rodando em {HOST}:{PORT}")  # Exibe no terminal que o servidor está rodando

    # Loop infinito para aceitar conexões de clientes
    try:
        while running:
            # server.settimeout(5)  # Timeout de 1 segundo para evitar bloqueio
            try:
                connected_client, addr = server.accept()
                print(f"Conexão recebida de {addr}")
                
                thread = threading.Thread(target=handle_client, args=(connected_client, addr))
                if thread.start():
                    client_threads.append(thread)  # Armazena a thread na lista
                    # running = False  # Para o loop do servidor até reinício manual
                    # break  # Sai do loop para voltar ao terminal principal
            except OSError:  # Exceção gerada quando o servidor é fechado
                if not running:  # Verifica se o servidor foi fechado
                    print("Servidor fechado, saindo da thread.")
                    break
                else:
                    raise  # Caso contrário, levanta novamente a exceção
    # Interrupção de teclado
    except KeyboardInterrupt:
        print("Usuário deu ctrl+C")
        server.close()


# Função de fechamento do servidor
def stop_server():
    global server, running, client_threads
    running = False

    # Fecha todas as threads de clientes ativas
    for thread in client_threads:
        if thread.is_alive():
            thread.join()
    
    if server:
        try:
            server.close()  # Fecha o socket
        except OSError:
            pass
        server = None

    print("Servidor fechado.")


# Execução principal do programa
if __name__ == "__main__":
    # Laço infinito
    while True:
        # Comandos do servidor
        server_state = input("Digite um comando (start/exit):\n").strip().lower()
        # Se o usuario digita start e não existe nenhuma thread ativa, o servidor é aberto 
        if server_state == "start":
            if server_thread and server_thread.is_alive():
                print("O servidor já está rodando.")
            else:
                server_thread = threading.Thread(target=start_server, daemon=True)
                server_thread.start()
                print("Servidor iniciado.")
        # Se o usuário digita exit, encerra o servidor
        elif server_state == "exit":
            if server and running:
                stop_server()
            # Aguarda a thread do servidor antes de sair
            if server_thread and server_thread.is_alive():
                server_thread.join()
            print("Encerrando o programa...")
            break  # Sai do loop e finaliza o programa
        else:
            print("Comando inválido! Use 'start' ou 'exit'.")