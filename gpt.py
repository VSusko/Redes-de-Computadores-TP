import os
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES
from PIL import Image, ImageTk

class FileTransferApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Arraste e Solte - Transferência de Arquivos")

        # Criando a interface do cliente e servidor
        self.client_frame = ttk.Frame(root)
        self.client_frame.pack(side="left", padx=20, pady=20)

        self.server_frame = ttk.Frame(root)
        self.server_frame.pack(side="right", padx=20, pady=20)

        # Criando o Treeview para cliente
        self.client_tree = ttk.Treeview(self.client_frame)
        self.client_tree.pack()

        # Criando o Treeview para servidor
        self.server_tree = ttk.Treeview(self.server_frame)
        self.server_tree.pack()

        # Carregar uma imagem de pasta (opcional, para visualização)
        image = Image.open("pasta.png")  # Substitua pelo caminho correto
        self.photo = ImageTk.PhotoImage(image.resize((30, 30)))

        # Populando as árvores com as pastas e arquivos fictícios
        self.populate_tree(self.client_tree, "Pasta Cliente 1", ["arquivo1.txt", "arquivo2.pdf"])
        self.populate_tree(self.server_tree, "Pasta Servidor", ["arquivoA.txt", "arquivoB.pdf"])

        # Adicionando botões para criar e remover pastas
        self.client_create_button = ttk.Button(self.client_frame, text="Criar Pasta Cliente", command=lambda: self.create_folder(self.client_tree, "cliente"))
        self.client_create_button.pack(pady=5)

        self.client_remove_button = ttk.Button(self.client_frame, text="Remover Pasta Cliente", command=lambda: self.remove_folder(self.client_tree, "cliente"))
        self.client_remove_button.pack(pady=5)

        self.server_create_button = ttk.Button(self.server_frame, text="Criar Pasta Servidor", command=lambda: self.create_folder(self.server_tree, "servidor"))
        self.server_create_button.pack(pady=5)

        self.server_remove_button = ttk.Button(self.server_frame, text="Remover Pasta Servidor", command=lambda: self.remove_folder(self.server_tree, "servidor"))
        self.server_remove_button.pack(pady=5)

        # Habilitar arraste de arquivos para a árvore
        self.enable_drag_and_drop(self.client_tree, "client")
        self.enable_drag_and_drop(self.server_tree, "server")

    def populate_tree(self, tree, folder_name, files):
        folder_id = tree.insert("", "end", folder_name, text=folder_name, image=self.photo)
        for file in files:
            tree.insert(folder_id, "end", text=file)

    def enable_drag_and_drop(self, tree, tree_type):
        tree.drop_target_register(DND_FILES)
        tree.dnd_bind('<<Drop>>', lambda e, tree=tree, tree_type=tree_type: self.on_drop(e, tree, tree_type))

    def on_drop(self, event, tree, tree_type):
        files = event.data.split()  # Obtém o caminho dos arquivos arrastados
        for file in files:
            if os.path.isfile(file):
                tree.insert("", "end", text=os.path.basename(file))  # Adiciona ao treeview
                print(f"Arquivo {file} transferido para o {tree_type}.")  # Simulação da transferência

    def create_folder(self, tree, tree_type):
        # Perguntar o nome da nova pasta
        folder_name = simpledialog.askstring("Criar Pasta", "Digite o nome da nova pasta:")
        if folder_name:
            if tree_type == "cliente":
                tree.insert("", "end", folder_name, text=folder_name, image=self.photo)
            else:
                tree.insert("", "end", folder_name, text=folder_name, image=self.photo)
            print(f"Pasta {folder_name} criada no {tree_type}.")

    def remove_folder(self, tree, tree_type):
        # Selecionar a pasta a ser removida
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("Erro", "Por favor, selecione uma pasta para remover.")
            return

        folder_name = tree.item(selected_item, "text")
        confirm = messagebox.askyesno("Confirmar", f"Tem certeza que deseja remover a pasta '{folder_name}'?")
        if confirm:
            tree.delete(selected_item)
            print(f"Pasta {folder_name} removida do {tree_type}.")

# Criar a janela principal
root = TkinterDnD.Tk()
app = FileTransferApp(root)

# Iniciar o loop do Tkinter
root.mainloop()
