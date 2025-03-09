import socket     # Importa a biblioteca para comunicação via sockets
import threading  # Importa threading para permitir múltiplas conexões simultâneas
import os         # Importa os para manipulação de diretórios e arquivos

# ==================/ Variaveis de escopo global /==================

# Dicionário de usuários cadastrados no servidor (login: senha)
USERS = {"1": "1", "user2": "pass2"}

# Configurações do servidor FTP
HOST = "0.0.0.0"  # Aceita conexões de qualquer IP
PORT = 2121  # Porta que o servidor irá escutar

# Diretório base onde os arquivos do servidor serão armazenados
BASE_DIR = os.path.abspath("server_files")
os.makedirs(BASE_DIR, exist_ok=True)  # Cria a pasta se ela não existir


server = None  # Variável global para armazenar o socket do servidor
server_thread = None  # Variável para armazenar a thread do servidor
running = False  # Flag para indicar se o servidor está rodando
client_threads = []

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
        print("Usuário recebido: ", username)                   # Mensagem de depuração

        connected_client.sendall("<Servidor>| Pedido de Senha\n".encode())  # Solicita a senha do usuário
        password = connected_client.recv(1024).decode().strip()             # Recebe a senha
        print("Senha recebida: ", password)                               # Mensagem de depuração

        print("USERS.GET = ", USERS.get(username))  # Exibe a senha armazenada para depuração

        # ================/ Verificacao se o usuário e senha são válidos /================
        if USERS.get(username) != password:
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
                files = "\n".join(os.listdir(current_dir))  # Lista os arquivos
                if not files:
                    connected_client.sendall("O diretório está vazio.\n".encode())
                else:
                    connected_client.sendall(b"\n" + files.encode() + b"\n")  # Envia a lista para o cliente

            # Comando para voltar um diretório
            elif command.lower().split() == ["cd", ".."]: # Consegue verificar se possui espaços
                if current_dir != BASE_DIR:  # Se não estiver no diretório raiz
                    current_dir = os.path.dirname(current_dir)  # Volta um nível
                    connected_client.sendall(f"Voltou um diretório. Atualmente em {os.path.basename(current_dir)}\n".encode())
                else:
                    connected_client.sendall("Já está no diretório raiz!\n".encode())  # Mensagem de erro

            # Comando para mudar de diretório
            elif command.startswith("cd "):
                new_dir = command[3:].strip()  # Obtém o nome do diretório
                path = os.path.join(current_dir, new_dir)  # Cria o caminho absoluto
                if os.path.isdir(path):  # Verifica se o diretório existe
                    current_dir = path  # Atualiza o diretório atual
                    connected_client.sendall(f"Diretório alterado. Atualmente em {new_dir}\n".encode())
                else:
                    connected_client.sendall("Diretório não encontrado.\n".encode())


            # Comandos não implementados
            elif command.startswith("mkdir "):
                new_dir = command[6:].strip()
                mkdir_name = os.path.join(BASE_DIR, new_dir)

                # print(mkdir_name)  # Depuração

                if not os.path.exists(mkdir_name):
                    os.mkdir(mkdir_name)
                    connected_client.sendall(f'Diretório "{new_dir}" criado.\n'.encode())  # Mensagem formatada corretamente
                else:
                    connected_client.sendall("Este diretório já existe no sistema!\n".encode())  # Mensagem de erro
                

            elif command.startswith("rmdir "):
                old_dir = command[6:].strip()
                rmdir_name = os.path.join(BASE_DIR, old_dir)

                # print(rmdir_name)  # Depuração

                if os.path.exists(rmdir_name):
                    os.rmdir(rmdir_name)
                    connected_client.sendall(f'Diretório "{old_dir}" deletado.\n'.encode())  # Mensagem formatada corretamente
                else:
                    connected_client.sendall("Este diretório não existe no sistema!\n".encode())  # Mensagem de erro

            elif command.startswith("put "):
                file_put = command[4:].strip()
                put_dir_name = os.path.join(BASE_DIR, file_put)
                connected_client.sendall(f"put {file_put}".encode())  # Envia confirmação ao cliente
                
                with open(put_dir_name, "wb") as f:
                    while True:
                        # Usa o cliente correto para receber os dados
                        data = connected_client.recv(1024)
                        print("pacote recevido")
                        if data == b"FIM_TRANSMISSAO":
                            print("cabou aq tb")
                            break
                        f.write(data)
            

            elif command.startswith("get "):
                file_get = command[4:].strip()
                get_dir_name = os.path.join(BASE_DIR, file_get)
                
                if not os.path.exists(get_dir_name):  # Verifica se o arquivo existe
                    connected_client.sendall("ERRO: Arquivo ou pasta não encontrada\n".encode())
                    continue
                elif os.path.isdir(get_dir_name):  # Impede envio de pastas
                    connected_client.sendall("ERRO: Não é possível enviar pastas\n".encode())
                    continue
                else:
                    connected_client.sendall(f"get {file_get}".encode())  # Envia confirmação ao cliente
                    print("confirmação")
                
                if connected_client.recv(1024).decode().strip() == "READY":
                    print("ready recebido")
                    with open(get_dir_name, "rb") as f:
                        data = f.read(1024)
                        while data:
                            connected_client.sendall(data)
                            print("pacote enviado")
                            data = f.read(1024)
                    
                    connected_client.sendall(b"FIM_TRANSMISSAO")  # Envia fim de transmissão
                    print("cabou")
                    #connected_client.sendall(f"Arquivo '{file_get}' enviado com sucesso!\n".encode())
                else:
                    print("Cliente não ficou pronto!")

            # Comando desconhecido
            else:
                connected_client.sendall("Comando desconhecido\n".encode())

    except Exception as e:
        print(f"Erro com {addr}: {e}")  # Exibe erros no terminal
    # finally:
    print(f"Conexão encerrada com {addr}")  # Mensagem de desconexão
    connected_client.close()  # Fecha a conexão com o cliente


# ================/ Função de controle do servidor FTP /================
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
            # except socket.timeout:
            #     if not running:  # Verifica se o servidor foi encerrado enquanto esperava
            #         break
            #     # Apenas imprime uma mensagem e continua aguardando novas conexões
            #     print("Nenhuma conexão recebida. Timeout expirado.")
            #     continue
    except KeyboardInterrupt:
        print("Usuário deu ctrl+C")
        server.close()
    # finally:
    #     server.close()  # Assegura que o socket seja fechado quando a thread terminar
    #     print("Servidor finalizado.")



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
    while True:
        
        server_state = input("Digite um comando (start/exit):\n").strip().lower()

        if server_state == "start":
            if server_thread and server_thread.is_alive():
                print("O servidor já está rodando.")
            else:
                server_thread = threading.Thread(target=start_server, daemon=True)
                server_thread.start()
                print("Servidor iniciado.")

        elif server_state == "exit":
            if server and running:
                stop_server()
            # Aguarda a thread do servidor antes de sair
            if server_thread and server_thread.is_alive():
                server_thread.join()
            print("Encerrando o programa...")
            break  # Sai do loop e finaliza o programa
        else:
            print("Comando inválido! Use 'start', 'close' ou 'exit'.")