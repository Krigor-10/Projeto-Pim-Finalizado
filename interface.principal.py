import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
import os
import io
import pandas as pd

# --- Constantes ---
CAMINHO_ARQUIVO = r"C:/Users/Krigor/OneDrive - UNIP/Área de Trabalho/ULTIMO PIM/output/SistemaAcademico.csv"
SECAO_ALVO = "[USUARIOS]"

# --- 1. CONSTANTES E FUNÇÕES LGPD (Baseado no seu modelo) ---
CONSENT_FILE = "lgpd_consent.txt"

def check_lgpd_consent():
    """Verifica se o usuário já aceitou os termos da LGPD."""
    return os.path.exists(CONSENT_FILE)

def set_lgpd_consent():
    """Registra o consentimento do usuário em um arquivo."""
    try:
        with open(CONSENT_FILE, "w") as f:
            f.write("accepted")
    except Exception as e:
        print(f"Erro ao salvar consentimento: {e}")

# =============================================================================
# === 2. CLASSE POP-UP LGPD (Baseado no seu modelo)
# =============================================================================
class LGPDPopup(ctk.CTkToplevel):
    def __init__(self, master, on_accept_callback):
        super().__init__(master)
        self.title("Aviso de Privacidade (LGPD)")
        
        self.on_accept_callback = on_accept_callback
        
        # Geometria e Centralização
        popup_width = 500
        popup_height = 350
        
        # --- CORREÇÃO: CENTRALIZAÇÃO NA TELA ---
        # Usa as dimensões da tela para garantir centralização absoluta,
        # independentemente do estado da janela principal (oculta ou não).
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        pos_x = (screen_width // 2) - (popup_width // 2)
        pos_y = (screen_height // 2) - (popup_height // 2)
        
        self.geometry(f"{popup_width}x{popup_height}+{pos_x}+{pos_y}")
        self.resizable(False, False)
        # --- FIM DA CORREÇÃO ---

        # Bloqueia interações com a janela principal
        self.transient(master)  
        self.grab_set()         

        # Se o usuário fechar no "X", o app principal fecha
        self.protocol("WM_DELETE_WINDOW", master.quit)

        msg = (
            "De acordo com a Lei Geral de Proteção de Dados (LGPD), "
            "precisamos do seu consentimento para processar seus dados. "
            "Ao clicar em 'Aceitar', você concorda com o uso de seus dados "
            "(como login, senha e notas) para o funcionamento deste aplicativo."
        )
        self.label = ctk.CTkLabel(self, text=msg, wraplength=380, font=("Arial", 14))
        self.label.pack(pady=30, padx=20, fill="x")

        self.accept_button = ctk.CTkButton(
            self, 
            text="Aceitar e Continuar", 
            command=self.accept, 
            fg_color="green", 
            font=("Arial", 12, "bold")
        )
        self.accept_button.pack(pady=20, padx=20, ipady=5)

    def accept(self):
        """Processa a aceitação, armazena o consentimento e fecha a janela."""
        set_lgpd_consent()
        
        # Remove a trava de fechar o app
        self.protocol("WM_DELETE_WINDOW", lambda: None)
        
        self.grab_release()
        self.destroy()
        self.on_accept_callback()


# =============================================================================
# === FUNÇÃO DE CARREGAMENTO (Sem alterações)
# =============================================================================
def carregar_tabela(caminho_arquivo):
    if not os.path.exists(caminho_arquivo):
        messagebox.showerror(
            "Erro de Leitura",
            f"Arquivo CSV não encontrado no caminho: {caminho_arquivo}",
        )
        return pd.DataFrame()
    try:
        with open(caminho_arquivo, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        start_index = -1
        end_index = -1
        for i, line in enumerate(lines):
            if line.strip().upper() == SECAO_ALVO:
                start_index = i + 1
                break
        if start_index == -1:
            messagebox.showerror(
                "Erro de Formato",
                f"Não foi possível encontrar a seção {SECAO_ALVO} no arquivo {caminho_arquivo}.",
            )
            return pd.DataFrame()
        
        for i in range(start_index, len(lines)):
            if lines[i].strip().startswith("["):
                end_index = i
                break
        if end_index == -1:
            end_index = len(lines)
            
        usuarios_lines = lines[start_index:end_index]
        usuarios_lines_clean = [line for line in usuarios_lines if line.strip()]

        header_default = "id;nome;email;senha;nivel;curso;turma;idade;np1;np2;pim;media;atividade"

        if len(usuarios_lines_clean) <= 1:
            header_line = (
                usuarios_lines_clean[0]
                if usuarios_lines_clean
                else header_default
            )
            colunas = [col.strip() for col in header_line.split(";")]
            return pd.DataFrame(columns=colunas)

        header_line = usuarios_lines_clean[0]
        colunas = [col.strip() for col in header_line.split(";")]
        data_lines = "".join(usuarios_lines_clean[1:])
        csv_file_like = io.StringIO(data_lines)
        df = pd.read_csv(csv_file_like, sep=";", header=None, names=colunas)

        df.columns = df.columns.str.strip().str.upper()

        column_map = {
            "TURMA": "ID_TURMAS",       
            "ATIVIDADE": "STATUS DO ALUNO", 
        }
        df.rename(columns=column_map, inplace=True)
        
        cols_numericas = ["NP1", "NP2", "PIM", "MEDIA"]
        for col in cols_numericas:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(",", ".", regex=False)
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        
        cols_inteiras = ["ID", "IDADE"]
        for col in cols_inteiras:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

        if "NOME" in df.columns:
            df["NOME"] = df["NOME"].astype(str).str.upper()
        if "EMAIL" in df.columns:
            df["EMAIL"] = df["EMAIL"].astype(str).str.lower()
        if "SENHA" in df.columns:
            df["SENHA"] = df["SENHA"].astype(str)
        if "NIVEL" in df.columns:
            df["NIVEL"] = df["NIVEL"].astype(str).str.upper()

        if all(col in df.columns for col in ["NP1", "NP2", "PIM"]):
            df["MEDIA"] = (df["NP1"] * 4 + df["NP2"] * 4 + df["PIM"] * 2) / 10
            df["MEDIA"] = df["MEDIA"].round(2)

        return df
    except Exception as e:
        messagebox.showerror(
            "Erro de Leitura", f"Não foi possível ler o arquivo CSV.\nErro: {e}"
        )
        return pd.DataFrame()


# =============================================================================
# === CLASSE 3: CHATBOT (Alterado) ===
# =============================================================================
respostas = {
    "Quais cursos posso me matrícular?": "As aulas disponibilizadas para esse semestre são Educação Ambiental, Redes de Computadores, Banco de Dados, Inteligência Artificial, Ciberssegurança, Programação Orientada a Objetos, Python, Java, C / C++ e Análise e Projeto de Sistemas.",
    "Como calcular a média final?": "A média é calculada com média ponderada, onde cada prova tem peso 4 e o trabalho final tem peso 2. A fórmula é: (NP1 * 4 + NP2 * 4 + PIM * 2) / 10.",
    "Quais os horários que posso fazer as aulas?": "A partir do momento em que você se matricula em uma disciplina, tem um período de 6 meses para completar o curso.",
    "Quem é o coordenador geral?": "O coordenador geral é o Prof. Cordeiro, escolhido dentro da sua instituição.",
    "Qual é o prazo para entrega dos trabalhos?": "A data de entrega dos trabalhos é até o final do semestre.",
    "Qual é o conteúdo da aula de segunda-feira?": "Na segunda-feira, estudamos Programação Orientada a Objetos e Java.",
    "Qual é o conteúdo da aula de terça-feira?": "Na terça-feira, estudamos Educação Ambiental e C / C++.",
    "Qual é o conteúdo da aula de quarta-feira?": "Na quarta-feira, estudamos Redes de Computadores e Análise e Projeto de Sistemas.",
    "Qual é o conteúdo da aula de quinta-feira?": "Na quarta-feira, estudamos Banco de Dados e Ciberssegurança.",
    "Qual é o conteúdo da aula de sexta-feira?": "Na sexta-feira, estudamos Inteligência Artificial e Python.",
    "Como funciona a avaliação do curso?": "A avaliação são duas provas de 12 questões, sendo 10 alternativas e 2 dissertativas e um trabalho final.",
    "Quais são os horários de atendimento do coordenador?": "O Prof. Cordeiro atende às quartas, das 14h às 16h.",
}


class Chatbot(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(
            self, text="Assistente Acadêmico", font=("Arial", 18, "bold")
        ).pack(pady=10)

        self.area_chat = tk.Text(
            self, height=12, state=tk.DISABLED, wrap=tk.WORD, font=("Arial", 10)
        )
        self.area_chat.pack(padx=10, pady=5, fill="both", expand=True)

        frame_botoes = ctk.CTkFrame(self)
        frame_botoes.pack(padx=10, pady=10, fill="x")
        ctk.CTkLabel(
            frame_botoes, text="Perguntas Frequentes:", font=("Arial", 12, "bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        canvas = tk.Canvas(
            frame_botoes,
            height=200,
            bg=self._apply_appearance_mode(
                ctk.ThemeManager.theme["CTkFrame"]["fg_color"]
            ),
            highlightthickness=0,
        )
        v_scrollbar = ctk.CTkScrollbar(
            frame_botoes, orientation="vertical", command=canvas.yview
        )

        scrollable_frame = ctk.CTkFrame(canvas)

        # 1. Cria a janela dentro do canvas e armazena o ID
        scrollable_window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=v_scrollbar.set)
        
        def on_canvas_configure(event):
            """
            Função para garantir que o frame de rolagem (scrollable_frame)
            preencha a largura total do canvas.
            """
            # Define a região de rolagem verticalmente
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Força a largura da janela de rolagem (scrollable_window_id) a ser
            # igual à largura visível do canvas, permitindo a expansão horizontal
            # dos botões internos (sticky="ew").
            canvas.itemconfig(scrollable_window_id, width=event.width)

        # Liga o evento de redimensionamento do canvas para ajustar a largura do conteúdo
        canvas.bind("<Configure>", on_canvas_configure)
        
        # Liga o evento de configuração do frame interno para recalcular o scroll region verticalmente
        scrollable_frame.bind(
             "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        v_scrollbar.grid(row=1, column=2, sticky="ns")
        canvas.grid(row=1, column=0, columnspan=2, sticky="nsew")
        frame_botoes.grid_columnconfigure(0, weight=1)
        frame_botoes.grid_rowconfigure(1, weight=1)
        
        # ----------------------------------------------------
        # --- MODIFICAÇÃO PARA BOTÕES LADO A LADO E CENTRALIZADOS ---
        # ----------------------------------------------------
        
        # Divide as perguntas em duas colunas.
        perguntas = list(respostas.keys())
        num_perguntas = len(perguntas)
        num_colunas = 2
        
        # Configura as colunas 0 e 1 do scrollable_frame para terem o mesmo peso
        scrollable_frame.grid_columnconfigure(0, weight=1)
        scrollable_frame.grid_columnconfigure(1, weight=1)

        for i in range(num_perguntas):
            pergunta = perguntas[i]
            
            # Calcula a linha e coluna (0 ou 1)
            row = i // num_colunas
            col = i % num_colunas
            
            btn = ctk.CTkButton(
                scrollable_frame,
                text=pergunta,
                command=lambda p=pergunta: self.fazer_pergunta(p),
                corner_radius=8,
                height=40, # Aumenta a altura para melhor visualização
                # sticky="ew" garante que o botão preencha a largura da sua célula
            )
            btn.grid(row=row, column=col, padx=10, pady=5, sticky="ew")

        # ----------------------------------------------------
        # --- FIM DA MODIFICAÇÃO ---
        # ----------------------------------------------------

        self.mostrar_mensagem_boas_vindas()

    def mostrar_mensagem_boas_vindas(self):
        self.adicionar_mensagem(
            "Assistente",
            "Olá! Sou seu assistente acadêmico. Clique em uma pergunta para começar.",
        )

    def adicionar_mensagem(self, remetente, mensagem):
        self.area_chat.config(state=tk.NORMAL)

        tag_color = "blue" if remetente == "Assistente" else "green"
        self.area_chat.tag_config(
            remetente, foreground=tag_color, font=("Arial", 10, "bold")
        )

        self.area_chat.insert(tk.END, f"{remetente}: ", remetente)
        self.area_chat.insert(tk.END, f"{mensagem}\n\n")

        self.area_chat.config(state=tk.DISABLED)
        self.area_chat.see(tk.END)

    def fazer_pergunta(self, pergunta):
        self.adicionar_mensagem("Você", pergunta)
        self.adicionar_mensagem("Assistente", respostas[pergunta])


# =============================================================================
# === CLASSE 1: TELA DE LOGIN (Sem alterações) ===
# =============================================================================
class LoginFrame(ctk.CTkFrame):
    def __init__(self, master, login_callback):
        super().__init__(master)
        self.login_callback = login_callback

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(
            self, text="Acesso ao Sistema Acadêmico", font=("Arial", 18, "bold")
        ).grid(row=1, column=1, padx=20, pady=(20, 10))

        self.username_entry = ctk.CTkEntry(
            self, placeholder_text="Usuário (Nome/Email)", width=250
        )
        self.username_entry.grid(row=2, column=1, padx=20, pady=10, sticky="ew")

        self.password_entry = ctk.CTkEntry(
            self, placeholder_text="Senha", show="*", width=250
        )
        self.password_entry.grid(row=3, column=1, padx=20, pady=10, sticky="ew")

        self.login_button = ctk.CTkButton(
            self,
            text="Entrar",
            command=self.attempt_login,
            width=250,
            fg_color="#3C66E0",
        )
        self.login_button.grid(
            row=4, column=1, padx=20, pady=(10, 20), sticky="ew"
        ) 

        self.password_entry.bind("<Return>", lambda event: self.attempt_login())
        self.username_entry.bind("<Return>", lambda event: self.attempt_login())

    def attempt_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if username and password:
            self.login_callback(username, password)
        else:
            messagebox.showwarning("Aviso", "Por favor, insira o usuário e a senha.")


# =============================================================================
# === CLASSE 2: APLICAÇÃO PRINCIPAL (Com lógica LGPD) ===
# =============================================================================
class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistema Acadêmico Integrado")
        self.geometry("1100x700")

        # Variáveis de Estado
        self.data_frame_full = None # Carregado DEPOIS do LGPD
        self.data_frame = pd.DataFrame()
        self.tabela_widget = None
        self.frame_tabela_dados = None
        self.current_user = None

        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)

        # --- MODIFICAÇÃO ---
        # A tela de login NÃO é mais mostrada aqui.
        # O início será tratado pela função 'start_app_with_lgpd_check'
        # self.show_login() # <- REMOVIDO
        # --- FIM DA MODIFICAÇÃO ---


    # --- 3. MÉTODOS DE INICIALIZAÇÃO E LGPD (RESTAURADOS) ---

    def start_app_with_lgpd_check(self):
        """Verifica o consentimento LGPD antes de iniciar o app."""
        
        # --- CORREÇÃO: Removida a centralização desnecessária da janela principal ---
        # Mantemos o withdraw() APENAS se o popup for necessário.
        if not check_lgpd_consent():
            # Esconde a janela principal (que está na geometria padrão 1100x700)
            self.withdraw() 
            # Mostra o pop-up de consentimento
            LGPDPopup(self, self.on_lgpd_accepted)
        else:
            # Se já aceitou, inicia o app normalmente
            self.on_lgpd_accepted()

    def on_lgpd_accepted(self):
        """Chamado após o usuário aceitar a LGPD. Inicia a tela de login."""
        
        # 1. Mostra a janela principal (só tem efeito se estava oculta)
        self.deiconify() 

        # 2. Usa 'self.after' para garantir que a janela reapareça
        #    ANTES de tentar desenhar a tela de login, evitando travamentos.
        self.after(50, self.show_login)

        # O carregamento de dados (carregar_tabela) permanece
        # corretamente dentro da função authenticate_user() para evitar outro travamento.

    # --- FUNÇÃO REMOVIDA ---
    # def on_lgpd_accepted_after_login(selfd):
    #     """Callback para o popup LGPD exibido APÓS o login."""
    #     self.deiconify() 
    #     self.show_main_content() 

    def center_window(self, width=1100, height=700):
        """Função auxiliar para centralizar a janela principal."""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        
    # --- Métodos de Transição de Tela ---

    def show_login(self):
        """Mostra a tela de Login."""
        for widget in self.container.winfo_children():
            widget.destroy()

        login_frame = LoginFrame(self.container, self.authenticate_user)
        login_frame.pack(fill="both", expand=True)
        
        # Centraliza a janela de login
        self.center_window(400, 300) 
        self.title("Login - Sistema Acadêmico")
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

    def show_main_content(self):
        """Mostra a tela principal após o login."""
        for widget in self.container.winfo_children():
            widget.destroy()

        # Centraliza a janela principal
        self.center_window(1100, 700) 
        self.title(
            f"Sistema Acadêmico Integrado - Logado como {self.current_user.get('NOME', 'N/A')} ({self.current_user.get('NIVEL', 'N/A')})"
        )

        self.create_user_info_banner(self.container)
        self.create_main_tabs(self.container)

        self.atualizar_tabela(reload_csv=False)
        
    # --- O restante do seu código MainApp (sem alterações) ---

    def create_user_info_banner(self, master):
        user_name = self.current_user.get("NOME", "N/A")
        user_id = self.current_user.get("ID", "N/A")
        user_level = self.current_user.get("NIVEL", "N/A")

        banner_frame = ctk.CTkFrame(master, height=40)
        banner_frame.pack(fill="x", padx=10, pady=(10, 5))

        banner_frame.grid_columnconfigure(0, weight=1)
        banner_frame.grid_columnconfigure(1, weight=0)

        info_text = f"👤 Logado como: {user_name} (ID: {user_id}) | Nível: {user_level}"
        info_label = ctk.CTkLabel(
            banner_frame,
            text=info_text,
            font=("Arial", 14, "bold"),
            text_color="#1E90FF",
        )
        info_label.grid(row=0, column=0, padx=20, pady=5, sticky="w")

        logout_button = ctk.CTkButton(
            banner_frame, text="Sair", command=self.show_login, width=80, fg_color="red"
        )
        logout_button.grid(row=0, column=1, padx=(0, 10), pady=5, sticky="e")

    def authenticate_user(self, username_or_email, password):
        
        # --- CORREÇÃO ROBUSTA APLICADA ---
        # 1. Verifica se os dados já foram carregados
        if self.data_frame_full is None:
            # 2. Se não, carrega AGORA (ao clicar em "Entrar")
            #    Neste ponto, a tela de login está visível e estável.
            #    Qualquer erro de 'carregar_tabela' mostrará o messagebox
            #    corretamente sobre a tela de login.
            self.data_frame_full = carregar_tabela(CAMINHO_ARQUIVO)
        # --- FIM DA CORREÇÃO ---

        df_auth = self.data_frame_full

        if df_auth is None or df_auth.empty:
            messagebox.showerror(
                "Erro de Login",
                "Não foi possível carregar os dados de usuários. Verifique o arquivo CSV.",
            )
            return False

        if not all(
            col in df_auth.columns for col in ["NOME", "EMAIL", "SENHA", "NIVEL"]
        ):
            messagebox.showerror(
                "Erro de Configuração",
                "O arquivo CSV deve conter as colunas 'nome', 'email', 'senha' e 'nivel'.",
            )
            return False

        input_lower = username_or_email.strip().lower()

        user_row = df_auth[
            (df_auth["EMAIL"] == input_lower)
            | (df_auth["NOME"] == username_or_email.strip().upper())
        ]

        if user_row.empty:
            messagebox.showerror("Login Falhou", "Usuário não encontrado.")
            return False

        user = user_row.iloc[0]

        if str(user["SENHA"]) == str(password):
            self.current_user = user
            messagebox.showinfo("Sucesso", f"Bem-vindo(a), {user['NOME']}!")
            
            # --- MODIFICAÇÃO: LÓGICA LGPD REMOVIDA DESTE PONTO ---
            # A verificação agora é feita antes do login
            self.show_main_content()
            # --- FIM DA MODIFICAÇÃO ---
            
            return True
        else:
            messagebox.showerror("Login Falhou", "Senha incorreta.")
            return False

    def _gerar_novo_id(self):
        if self.data_frame_full is None or self.data_frame_full.empty:
            return 1
        
        if "ID" in self.data_frame_full.columns:
            max_id = self.data_frame_full["ID"].max()
            return int(max_id) + 1
        
        return 1

    def create_main_tabs(self, master):
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("Treeview", font=("Arial", 10), rowheight=25)
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))
        style.map("Treeview", background=[("selected", "blue")])

        self.abas = ttk.Notebook(master)
        frame_tabela = ctk.CTkFrame(self.abas)

        user_level = self.current_user.get("NIVEL", "ALUNO")
        is_student = user_level == "ALUNO"

        if is_student:
            frame_chatbot = ctk.CTkFrame(self.abas)
            self.abas.add(frame_chatbot, text="Assistente Acadêmico")
            Chatbot(frame_chatbot)

        self.abas.add(frame_tabela, text="Tabela de Usuários")
        self.abas.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.create_tabela_frame(frame_tabela)

    def create_tabela_frame(self, frame_tabela):
        frame_controles = ctk.CTkFrame(frame_tabela)
        frame_controles.pack(fill="x", padx=10, pady=10)

        user_level = (
            self.current_user["NIVEL"]
            if self.current_user is not None
            else "NÃO AUTORIZADO"
        )
        user_is_admin = user_level == "ADMINISTRADOR"
        user_is_student = user_level == "ALUNO"
        user_is_coordinator = user_level == "COORDENADOR"


        titulo = ctk.CTkLabel(
            frame_controles,
            text=f"Gerenciamento de Usuários (Nível: {user_level})",
            font=("Arial", 16, "bold"),
        )
        titulo.pack(pady=5)

        # --- Interface do Aluno ---
        if user_is_student:
            student_button_frame = ctk.CTkFrame(frame_controles)
            student_button_frame.pack(pady=(10, 15), fill="x", padx=20)
            
            student_button_frame.grid_columnconfigure(0, weight=1)
            student_button_frame.grid_columnconfigure(1, weight=1)
            student_button_frame.grid_columnconfigure(2, weight=1) 

            botao_enviar_atividade = ctk.CTkButton(
                student_button_frame,
                text="🚀 Enviar Atividades",
                command=self.open_activity_submission_window,
                fg_color="#4CAF50",
                font=("Arial", 14, "bold"),
            )
            botao_enviar_atividade.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

            botao_ver_dados = ctk.CTkButton(
                student_button_frame,
                text="👤 Ver Meus Dados",
                command=self.abrir_janela_meus_dados, 
                fg_color="#007BFF",
                font=("Arial", 12),
            )
            botao_ver_dados.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

            botao_atualizar_aluno = ctk.CTkButton(
                student_button_frame,
                text="🔄 Recarregar Tabela", 
                command=lambda: self.atualizar_tabela(reload_csv=True),
                font=("Arial", 12),
            )
            botao_atualizar_aluno.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        # --- Interface do Admin ---
        elif user_is_admin:
            frame_botoes = ctk.CTkFrame(frame_controles)
            frame_botoes.pack(fill="x", padx=10, pady=10)

            botao_ativar = ctk.CTkButton(
                frame_botoes,
                text="🟢 Ativar Aluno",
                command=self.ativar_aluno,
                fg_color="#3A8A3A",
            )
            botao_ativar.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

            botao_desativar = ctk.CTkButton(
                frame_botoes,
                text="🔴 Desativar Aluno",
                command=self.desativar_aluno,
                fg_color="#E03C31",
            )
            botao_desativar.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

            botao_editar = ctk.CTkButton(
                frame_botoes, text="✏️ Editar Usuário", command=self.abrir_janela_edicao
            )
            botao_editar.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

            botao_excluir = ctk.CTkButton(
                frame_botoes,
                text="❌ Excluir Usuário",
                command=self.excluir_usuario,
                fg_color="#CC0000",
            )
            botao_excluir.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

            botao_adicionar = ctk.CTkButton(
                frame_botoes,
                text="➕ Adicionar Usuário",
                command=self.abrir_janela_novo_usuario, 
                fg_color="#007BFF", 
            )
            botao_adicionar.grid(row=0, column=4, padx=5, pady=5, sticky="ew")

            botao_salvar = ctk.CTkButton(
                frame_botoes,
                text="💾 Salvar Alterações",
                command=self.salvar_dados,
                fg_color="#3C66E0",
            )
            botao_salvar.grid(row=0, column=5, padx=5, pady=5, sticky="ew")

            ctk.CTkLabel(
                frame_botoes, text="| Filtros Rápidos:", font=("Arial", 12, "bold")
            ).grid(row=0, column=6, padx=10) 

            botao_filtrar_ativos = ctk.CTkButton(
                frame_botoes,
                text="Mostrar Ativos",
                command=lambda: self.filtrar_por_status("ATIVO"),
                fg_color="#4CAF50",
            )
            botao_filtrar_ativos.grid(row=0, column=7, padx=5, pady=5, sticky="ew") 

            botao_filtrar_inativos = ctk.CTkButton(
                frame_botoes,
                text="Mostrar Inativos",
                command=lambda: self.filtrar_por_status("INATIVO"),
                fg_color="#FF9800",
            )
            botao_filtrar_inativos.grid(row=0, column=8, padx=5, pady=5, sticky="ew") 

            botao_atualizar = ctk.CTkButton(
                frame_botoes,
                text="🔄 Recarregar CSV",
                command=lambda: self.atualizar_tabela(reload_csv=True),
            )
            botao_atualizar.grid(row=0, column=9, padx=5, pady=5, sticky="ew") 

            for i in range(10):
                frame_botoes.grid_columnconfigure(i, weight=1)

            filtros_container = ctk.CTkFrame(frame_controles)
            filtros_container.pack(fill="x", padx=10, pady=5)
            self.criar_widgets_filtro(filtros_container) 

        # --- Interface do Coordenador ---
        elif user_is_coordinator:
            frame_botoes_coord = ctk.CTkFrame(frame_controles)
            frame_botoes_coord.pack(fill="x", padx=10, pady=10)

            botao_ativar = ctk.CTkButton(
                frame_botoes_coord,
                text="🟢 Ativar Aluno",
                command=self.ativar_aluno,
                fg_color="#3A8A3A",
            )
            botao_ativar.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

            botao_desativar = ctk.CTkButton(
                frame_botoes_coord,
                text="🔴 Desativar Aluno",
                command=self.desativar_aluno,
                fg_color="#E03C31",
            )
            botao_desativar.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

            botao_adicionar = ctk.CTkButton(
                frame_botoes_coord,
                text="➕ Adicionar Usuário",
                command=self.abrir_janela_novo_usuario, 
                fg_color="#007BFF", 
            )
            botao_adicionar.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

            botao_salvar = ctk.CTkButton(
                frame_botoes_coord,
                text="💾 Salvar Alterações",
                command=self.salvar_dados,
                fg_color="#3C66E0",
            )
            botao_salvar.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
            
            botao_atualizar = ctk.CTkButton(
                frame_botoes_coord,
                text="🔄 Recarregar CSV",
                command=lambda: self.atualizar_tabela(reload_csv=True),
            )
            botao_atualizar.grid(row=0, column=4, padx=5, pady=5, sticky="ew")

            for i in range(5):
                frame_botoes_coord.grid_columnconfigure(i, weight=1)

            filtros_container_coord = ctk.CTkFrame(frame_controles)
            filtros_container_coord.pack(fill="x", padx=10, pady=5)
            self.criar_widgets_filtro(filtros_container_coord) 
        
        # --- Interface do Professor ---
        elif user_level == "PROFESSOR":
            frame_botoes_prof = ctk.CTkFrame(frame_controles)
            frame_botoes_prof.pack(fill="x", padx=10, pady=10)

            botao_editar_notas = ctk.CTkButton(
                frame_botoes_prof,
                text="✏️ Lançar/Editar Notas de Aluno",
                command=self.abrir_janela_edicao_notas, 
                fg_color="#007BFF",
            )
            botao_editar_notas.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

            botao_atualizar = ctk.CTkButton(
                frame_botoes_prof,
                text="🔄 Recarregar Dados",
                command=lambda: self.atualizar_tabela(reload_csv=True),
            )
            botao_atualizar.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

            frame_botoes_prof.grid_columnconfigure(0, weight=1)
            frame_botoes_prof.grid_columnconfigure(1, weight=1)

            filtros_container_prof = ctk.CTkFrame(frame_controles)
            filtros_container_prof.pack(fill="x", padx=10, pady=5)
            self.criar_widgets_filtro(filtros_container_prof) 

        self.frame_tabela_dados = ctk.CTkFrame(frame_tabela)
        self.frame_tabela_dados.pack(fill="both", expand=True, padx=10, pady=10)

    def criar_widgets_filtro(self, master_frame):
        ctk.CTkLabel(master_frame, text="Filtrar por:").grid(
            row=0, column=0, padx=(10, 5), pady=10, sticky="w"
        )

        colunas_filtro = ["Filtrar por Coluna..."]
        
        # Adiciona uma verificação 'if self.data_frame_full is not None'
        if self.data_frame_full is not None and not self.data_frame_full.empty:
            lista_completa_colunas = self.data_frame_full.columns.tolist()
            colunas_filtradas = [coluna for coluna in lista_completa_colunas if coluna != "SENHA"]
            colunas_filtro.extend(colunas_filtradas)

        self.combo_filtro_coluna = ctk.CTkComboBox(
            master_frame, values=colunas_filtro, width=180
        )
        self.combo_filtro_coluna.grid(row=0, column=1, padx=5, pady=10, sticky="w")

        self.entrada_filtro_geral = ctk.CTkEntry(
            master_frame, placeholder_text="Digite o valor...", width=180
        )
        self.entrada_filtro_geral.grid(row=0, column=2, padx=5, pady=10, sticky="w")
        
        botao_filtrar_geral = ctk.CTkButton(
            master_frame, text="Buscar", command=self.filtrar_geral, width=80
        )
        botao_filtrar_geral.grid(row=0, column=3, padx=5, pady=10, sticky="w")

        botao_limpar_filtros = ctk.CTkButton(
            master_frame, text="Limpar Filtros", command=self.limpar_filtros
        )
        botao_limpar_filtros.grid(
            row=0, column=4, padx=(20, 10), pady=10, sticky="w"
        )
        
    def excluir_usuario(self):
        if self.current_user["NIVEL"] != "ADMINISTRADOR":
            messagebox.showwarning(
                "Permissão Negada", "Somente usuários ADMIN podem excluir usuários."
            )
            return
        if self.tabela_widget is None:
            return
        selecionado = self.tabela_widget.focus()
        if not selecionado:
            messagebox.showwarning("Seleção", "Selecione uma linha para excluir.")
            return
        
        try:
            idx_visible = int(selecionado)
            user_id = self.data_frame.loc[idx_visible, "ID"]
            user_nome = self.data_frame.loc[idx_visible, "NOME"]

            if not messagebox.askyesno(
                "Confirmação de Exclusão",
                f"Tem certeza que deseja EXCLUIR o usuário ID {user_id} ({user_nome})? Esta ação é permanente.",
            ):
                return
            
            idx_full_list = self.data_frame_full[
                self.data_frame_full["ID"] == user_id
            ].index
            
            if not idx_full_list.empty:
                self.data_frame_full.drop(idx_full_list, inplace=True)
                self.salvar_dados() 
                messagebox.showinfo("Sucesso", f"Usuário ID {user_id} excluído e arquivo CSV salvo.")
            else:
                messagebox.showwarning(
                    "Erro",
                    f"Usuário ID {user_id} não encontrado no banco de dados completo.",
                )
        except Exception as e:
            messagebox.showerror(
                "Erro de Exclusão", f"Ocorreu um erro ao excluir o usuário: {e}"
            )

    def filtrar_por_status(self, status):
        if self.current_user["NIVEL"] in ["ADMINISTRADOR", "COORDENADOR", "PROFESSOR"]:
            self.atualizar_tabela(reload_csv=False, filter_status=status)
        else:
            messagebox.showwarning(
                "Permissão Negada", "Filtros rápidos são exclusivos para Admin, Coordenador ou Professor."
            )

    def filtrar_geral(self):
        if self.current_user["NIVEL"] not in ["ADMINISTRADOR", "COORDENADOR", "PROFESSOR"]:
            messagebox.showwarning(
                "Permissão Negada", "Filtros são exclusivos para Admin, Coordenador ou Professor."
            )
            return
        coluna = self.combo_filtro_coluna.get()
        texto = self.entrada_filtro_geral.get().strip()
        if coluna == "Filtrar por Coluna..." or not texto:
            messagebox.showwarning(
                "Filtro", "Selecione uma coluna e digite um valor de busca."
            )
            return
        self.atualizar_tabela(
            reload_csv=False, general_filter_text=texto, filter_column=coluna
        )

    def limpar_filtros(self):
        if self.current_user["NIVEL"] in ["ADMINISTRADOR", "COORDENADOR", "PROFESSOR"]:
            self.combo_filtro_coluna.set("Filtrar por Coluna...")
            self.entrada_filtro_geral.delete(0, tk.END)
            self.atualizar_tabela(reload_csv=False)
        else:
            messagebox.showwarning(
                "Permissão Negada", "Limpar filtros é exclusivo para Admin, Coordenador ou Professor."
            )

    def atualizar_tabela(
        self,
        reload_csv=True,
        filter_status=None,
        general_filter_text=None,
        filter_column=None,
    ):
        if reload_csv:
            # Se 'Recarregar CSV' for clicado, recarregamos os dados
            self.data_frame_full = carregar_tabela(CAMINHO_ARQUIVO)
            if self.data_frame_full.empty:
                self.data_frame = pd.DataFrame()
                self.mostrar_tabela(self.data_frame)
                return

        if self.data_frame_full is None or self.data_frame_full.empty:
             # Isso pode acontecer se o login foi feito, mas o arquivo falhou
             # e o usuário está tentando fazer algo (ex: recarregar)
            self.data_frame = pd.DataFrame()
            self.mostrar_tabela(self.data_frame)
            return

        df_display = self.data_frame_full.copy()

        if self.current_user is None:
            self.mostrar_tabela(pd.DataFrame())
            return

        user_level = self.current_user["NIVEL"]
        columns_to_drop = []
        rows_filter = None

        if user_level == "ALUNO":
            user_id = self.current_user["ID"]
            rows_filter = df_display["ID"] == user_id
            columns_to_drop.extend([
                "STATUS DO ALUNO", 
                "SENHA", 
                "ID_TURMAS",
                "EMAIL",      
                "IDADE",      
                "NIVEL"       
            ])

        elif user_level == "PROFESSOR":
            rows_filter = df_display["NIVEL"] == "ALUNO"
            columns_to_drop.append("SENHA")
            columns_to_drop.append("ID_TURMAS") 

        elif user_level == "COORDENADOR":
            rows_filter = df_display["NIVEL"].isin(
                ["ALUNO", "PROFESSOR", "COORDENADOR"]
            )
            columns_to_drop.append("SENHA")
            columns_to_drop.extend(["NP1", "NP2", "PIM"])
            columns_to_drop.append("ID_TURMAS") 

        elif user_level == "ADMINISTRADOR":
            columns_to_drop.append("SENHA")

        if rows_filter is not None:
            df_display = df_display[rows_filter].copy()

        cols_to_drop_final = [
            col for col in columns_to_drop if col in df_display.columns
        ]
        if cols_to_drop_final:
            df_display = df_display.drop(columns=cols_to_drop_final)

        if user_level in ["ADMINISTRADOR", "COORDENADOR", "PROFESSOR"]:
            if filter_status:
                df_display = df_display[
                    df_display["STATUS DO ALUNO"] == filter_status.upper()
                ]

            if (
                general_filter_text
                and filter_column
                and filter_column in df_display.columns
            ):
                search_term = general_filter_text.lower()
                df_display = df_display[
                    df_display[filter_column]
                    .astype(str)
                    .str.lower()
                    .str.contains(search_term, na=False)
                ]

        self.data_frame = df_display.reset_index(drop=True)
        self.mostrar_tabela(self.data_frame)

        if reload_csv and user_level in ["ADMINISTRADOR", "COORDENADOR", "PROFESSOR"]:
            messagebox.showinfo(
                "Atualização", "Tabela recarregada a partir do arquivo CSV."
            )

    def mostrar_tabela(self, df):
        for widget in self.frame_tabela_dados.winfo_children():
            widget.destroy()

        if df.empty:
            ctk.CTkLabel(
                self.frame_tabela_dados,
                text="Nenhum dado encontrado para o filtro aplicado ou seu nível de acesso.",
                text_color="red",
            ).pack(pady=20)
            self.tabela_widget = None
            return

        colunas = list(df.columns)
        self.tabela_widget = ttk.Treeview(
            self.frame_tabela_dados, columns=colunas, show="headings"
        )

        vsb = ttk.Scrollbar(
            self.frame_tabela_dados, orient="vertical", command=self.tabela_widget.yview
        )
        hsb = ttk.Scrollbar(
            self.frame_tabela_dados,
            orient="horizontal",
            command=self.tabela_widget.xview,
        )
        self.tabela_widget.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")

        self.tabela_widget.column("#0", width=0, stretch=tk.NO)

        user_level = self.current_user.get("NIVEL", "N/A")
        
        self.tabela_widget.tag_configure('aprovado', foreground='#00B050', font=('Arial', 10, 'bold'))
        self.tabela_widget.tag_configure('reprovado', foreground='#E03C31', font=('Arial', 10, 'bold'))

        for col in colunas:
            col_display = col.replace("_", " ")
            if col == "ID_TURMAS":
                col_display = "TURMA"
            
            self.tabela_widget.heading(col, text=col_display)

            col_width = 100
            if col in ["NOME", "EMAIL", "CURSO"]:
                col_width = 180
            elif col in ["ID_TURMAS"]: 
                col_width = 150
            elif col in ["NP1", "NP2", "PIM", "MEDIA", "ID", "IDADE"]:
                col_width = 80

            self.tabela_widget.column(
                col, anchor="center", width=col_width, minwidth=50
            )

        for i, row in df.iterrows():
            row_list = list(row)
            
            tag_para_aplicar = () 
            
            if "MEDIA" in colunas:
                media_index = colunas.index("MEDIA")
                
                try:
                    media_valor = float(row_list[media_index])
                    row_list[media_index] = f"{media_valor:.2f}"
                    
                    if user_level == "ALUNO":
                        if media_valor >= 7.0:
                            tag_para_aplicar = ('aprovado',)
                        else:
                            tag_para_aplicar = ('reprovado',)

                except (ValueError, TypeError):
                    pass 

            self.tabela_widget.insert("", "end", iid=i, values=row_list, tags=tag_para_aplicar)

        self.tabela_widget.pack(fill="both", expand=True)

    def ativar_aluno(self):
        if self.current_user["NIVEL"] not in ["ADMINISTRADOR", "COORDENADOR"]:
            messagebox.showwarning("Permissão Negada", "Acesso negado.")
            return
        if self.tabela_widget is None: return
        selecionado = self.tabela_widget.focus()
        
        if selecionado:
            try:
                idx_visible = int(selecionado)
                user_id = self.data_frame.loc[idx_visible, "ID"]
                idx_full_list = self.data_frame_full[self.data_frame_full["ID"] == user_id].index
                
                if not idx_full_list.empty:
                    idx_full = idx_full_list[0]
                    self.data_frame_full.loc[idx_full, "STATUS DO ALUNO"] = "ATIVO"
                    
                    if "STATUS DO ALUNO" in self.data_frame.columns:
                        self.data_frame.loc[idx_visible, "STATUS DO ALUNO"] = "ATIVO"
                    
                    current_values = list(self.data_frame.loc[idx_visible].values)
                    if "MEDIA" in self.data_frame.columns:
                        media_index = self.data_frame.columns.tolist().index("MEDIA")
                        current_values[media_index] = (
                            f"{float(current_values[media_index]):.2f}"
                        )
                    self.tabela_widget.item(selecionado, values=current_values)
                    
                    messagebox.showinfo("Status", f"Aluno ID {user_id} ativado. Lembre-se de SALVAR as alterações.")
                else:
                    messagebox.showwarning("Erro", f"Não foi possível encontrar o usuário ID {user_id} no banco de dados completo.")
            
            except Exception as e:
                messagebox.showerror("Erro", f"Ocorreu um erro ao ativar: {e}")
        else:
            messagebox.showwarning("Seleção", "Selecione uma linha para ativar.")
            
    def desativar_aluno(self):
        if self.current_user["NIVEL"] not in ["ADMINISTRADOR", "COORDENADOR"]:
            messagebox.showwarning("Permissão Negada", "Acesso negado.")
            return
        if self.tabela_widget is None: return
        selecionado = self.tabela_widget.focus()
        
        if selecionado:
            try:
                idx_visible = int(selecionado)
                user_id = self.data_frame.loc[idx_visible, "ID"]
                idx_full_list = self.data_frame_full[self.data_frame_full["ID"] == user_id].index
                
                if not idx_full_list.empty:
                    idx_full = idx_full_list[0]
                    self.data_frame_full.loc[idx_full, "STATUS DO ALUNO"] = "INATIVO"
                    
                    if "STATUS DO ALUNO" in self.data_frame.columns:
                        self.data_frame.loc[idx_visible, "STATUS DO ALUNO"] = "INATIVO"
                    
                    current_values = list(self.data_frame.loc[idx_visible].values)
                    if "MEDIA" in self.data_frame.columns:
                        media_index = self.data_frame.columns.tolist().index("MEDIA")
                        current_values[media_index] = (
                            f"{float(current_values[media_index]):.2f}"
                        )
                    self.tabela_widget.item(selecionado, values=current_values)
                    
                    messagebox.showinfo("Status", f"Aluno ID {user_id} desativado. Lembre-se de SALVAR as alterações.")
                else:
                    messagebox.showwarning("Erro", f"Não foi possível encontrar o usuário ID {user_id} no banco de dados completo.")
            
            except Exception as e:
                messagebox.showerror("Erro", f"Ocorreu um erro ao desativar: {e}")
        else:
            messagebox.showwarning("Seleção", "Selecione uma linha para desativar.")

    def abrir_janela_meus_dados(self):
        if self.current_user["NIVEL"] != "ALUNO":
            messagebox.showwarning("Aviso", "Esta função é apenas para alunos.")
            return

        user_data = self.current_user

        dados_window = ctk.CTkToplevel(self)
        dados_window.title("Meus Dados Cadastrais")
        dados_window.geometry("450x300")
        dados_window.transient(self)
        dados_window.grab_set()

        form_frame = ctk.CTkFrame(dados_window)
        form_frame.pack(padx=20, pady=20, fill="both", expand=True)

        dados_para_exibir = [
            ("ID", "ID"),
            ("NOME", "Nome Completo"),
            ("EMAIL", "Email"),
            ("IDADE", "Idade"),
            ("NIVEL", "Nível de Acesso"),
            ("CURSO", "Curso"),
            ("ID_TURMAS", "Turma"),
            ("STATUS DO ALUNO", "Status da Matrícula"),
        ]

        for i, (key, label_text) in enumerate(dados_para_exibir):
            
            label = ctk.CTkLabel(form_frame, text=f"{label_text}:", font=("Arial", 12, "bold"))
            label.grid(row=i, column=0, padx=10, pady=8, sticky="e")
            
            valor = str(user_data.get(key, "N/A")) 
            
            if key == "STATUS DO ALUNO":
                valor = "ATIVO" if valor == "ATIVO" else "INATIVO"
                
            value_label = ctk.CTkLabel(form_frame, text=valor, text_color="cyan")
            value_label.grid(row=i, column=1, padx=10, pady=8, sticky="w")

        form_frame.grid_columnconfigure(0, weight=1)
        form_frame.grid_columnconfigure(1, weight=2)

    def abrir_janela_novo_usuario(self):
        if self.current_user["NIVEL"] not in ["ADMINISTRADOR", "COORDENADOR"]:
            messagebox.showwarning("Permissão Negada", "Acesso negado.")
            return

        add_window = ctk.CTkToplevel(self)
        add_window.title("Adicionar Novo Usuário")
        add_window.geometry("400x600")
        add_window.transient(self)
        add_window.grab_set()

        form_frame = ctk.CTkFrame(add_window)
        form_frame.pack(padx=20, pady=20, fill="both", expand=True)

        entries = {}
        editaveis = [
            "NOME", "EMAIL", "SENHA", "IDADE", "CURSO",
            "ID_TURMAS", 
            "NIVEL", "NP1", "NP2", "PIM",
        ]

        for i, col in enumerate(editaveis):
            label_text = col.replace("_", " ")
            if col == "ID_TURMAS":
                label_text = "TURMA"
                
            ctk.CTkLabel(form_frame, text=f"{label_text}:").grid(
                row=i, column=0, padx=10, pady=5, sticky="w"
            )
            entry = ctk.CTkEntry(form_frame, width=250)
            
            if col in ["NP1", "NP2", "PIM", "IDADE"]:
                entry.insert(0, "0")
            elif col == "NIVEL":
                entry.insert(0, "ALUNO")
                
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
            entries[col] = entry

        save_button = ctk.CTkButton(
            form_frame,
            text="Adicionar e Salvar Usuário",
            command=lambda: self.salvar_novo_usuario(entries, add_window),
            fg_color="green"
        )
        save_button.grid(
            row=len(editaveis), column=0, columnspan=2, padx=10, pady=20, sticky="ew"
        )

    def salvar_novo_usuario(self, entries, window):
        try:
            new_user_data = {}
            
            for col, entry_widget in entries.items():
                new_value = entry_widget.get().strip()
                
                if not new_value and col not in ["NP1", "NP2", "PIM", "IDADE"]:
                     messagebox.showerror("Erro de Validação", f"O campo '{col}' não pode estar vazio.")
                     return

                if col in ["IDADE", "NP1", "NP2", "PIM"]:
                    try:
                        new_value_converted = (0 if not new_value else float(new_value))
                        if col in ["NP1", "NP2", "PIM"] and not (0 <= new_value_converted <= 10):
                            messagebox.showerror("Erro", f"Notas devem estar entre 0 e 10.")
                            return
                        new_user_data[col] = new_value_converted
                    except ValueError:
                        messagebox.showerror("Erro", f"O campo '{col}' deve ser um número.")
                        return
                elif col in ["NOME", "NIVEL", "CURSO"]:
                    new_user_data[col] = new_value.upper()
                elif col == "EMAIL":
                    new_user_data[col] = new_value.lower()
                elif col == "ID_TURMAS":
                    new_user_data[col] = new_value
                elif col == "SENHA":
                    new_user_data[col] = new_value
            
            new_user_data["ID"] = self._gerar_novo_id()
            new_user_data["STATUS DO ALUNO"] = "ATIVO" 
            
            np1 = new_user_data.get("NP1", 0)
            np2 = new_user_data.get("NP2", 0)
            pim = new_user_data.get("PIM", 0)
            media = (np1 * 4 + np2 * 4 + pim * 2) / 10
            new_user_data["MEDIA"] = round(media, 2)
            
            colunas_completas = self.data_frame_full.columns
            for col in colunas_completas:
                if col not in new_user_data:
                    new_user_data[col] = 0 if col in ["IDADE", "NP1", "NP2", "PIM", "MEDIA"] else ""
            
            new_user_df = pd.DataFrame([new_user_data])
            new_user_df = new_user_df[colunas_completas] 

            self.data_frame_full = pd.concat([self.data_frame_full, new_user_df], ignore_index=True)

            self.salvar_dados()

            messagebox.showinfo("Sucesso", f"Novo usuário '{new_user_data['NOME']}' (ID: {new_user_data['ID']}) adicionado com sucesso!")
            window.destroy()

        except Exception as e:
            messagebox.showerror(
                "Erro ao Salvar Novo Usuário", f"Ocorreu um erro: {e}"
            )

    def abrir_janela_edicao(self):
        if self.current_user["NIVEL"] != "ADMINISTRADOR":
            messagebox.showwarning("Permissão Negada", "Acesso negado.")
            return
        if not isinstance(self.tabela_widget, ttk.Treeview):
            messagebox.showwarning("Aviso", "A tabela não está carregada.")
            return
        selecionado = self.tabela_widget.focus()
        if not selecionado:
            messagebox.showwarning("Seleção", "Selecione um usuário para editar.")
            return
        
        idx = int(selecionado)
        user_data_series = self.data_frame.loc[idx]
        user_id = user_data_series["ID"]
        full_user_data_row = self.data_frame_full[self.data_frame_full["ID"] == user_id]
        if full_user_data_row.empty:
            messagebox.showerror("Erro", "Dados completos do usuário não encontrados.")
            return
        full_user_data = full_user_data_row.iloc[0]

        edit_window = ctk.CTkToplevel(self)
        edit_window.title(f"Editar Usuário ID: {user_id}")
        edit_window.geometry("400x600") 
        edit_window.transient(self)
        edit_window.grab_set()

        form_frame = ctk.CTkFrame(edit_window)
        form_frame.pack(padx=20, pady=20, fill="both", expand=True)

        entries = {}
        editaveis = [
            "NOME", "EMAIL", "IDADE", "CURSO",
            "ID_TURMAS", 
            "NIVEL", "SENHA", "NP1", "NP2", "PIM",
        ]

        for i, col in enumerate(editaveis):
            if col in full_user_data.index:
                label_text = col.replace("_", " ")
                if col == "ID_TURMAS":
                    label_text = "TURMA"
                    
                ctk.CTkLabel(form_frame, text=f"{label_text}:").grid(
                    row=i, column=0, padx=10, pady=5, sticky="w"
                )
                entry = ctk.CTkEntry(form_frame, width=250)
                entry.insert(0, str(full_user_data[col]))
                entry.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
                entries[col] = entry

        save_button = ctk.CTkButton(
            form_frame,
            text="Salvar Alterações",
            command=lambda: self.salvar_edicao_usuario(user_id, entries, edit_window),
        )
        save_button.grid(
            row=len(editaveis), column=0, columnspan=2, padx=10, pady=20, sticky="ew"
        )

    def salvar_edicao_usuario(self, user_id, entries, window):
        try:
            user_index = self.data_frame_full[
                self.data_frame_full["ID"] == user_id
            ].index[0]
            
            for col, entry_widget in entries.items():
                new_value = entry_widget.get().strip()
                if col in ["IDADE", "NP1", "NP2", "PIM"]:
                    try:
                        new_value_converted = (
                            0 if not new_value else float(new_value)
                        ) 
                        if col in ["NP1", "NP2", "PIM"] and not (
                            0 <= new_value_converted <= 10
                        ):
                            messagebox.showerror("Erro", f"Notas devem estar entre 0 e 10.")
                            return
                        self.data_frame_full.loc[user_index, col] = new_value_converted
                    except ValueError:
                        messagebox.showerror("Erro", f"O campo '{col}' deve ser um número.")
                        return
                elif col in ["NOME", "NIVEL", "CURSO"]:
                    new_value = new_value.upper()
                    self.data_frame_full.loc[user_index, col] = new_value
                elif col == "EMAIL":
                    new_value = new_value.lower()
                    self.data_frame_full.loc[user_index, col] = new_value
                elif col == "ID_TURMAS": 
                    self.data_frame_full.loc[user_index, col] = new_value
                elif col == "SENHA":
                    self.data_frame_full.loc[user_index, col] = new_value

            if all(
                col in self.data_frame_full.columns for col in ["NP1", "NP2", "PIM"]
            ):
                row = self.data_frame_full.loc[user_index]
                media = (row["NP1"] * 4 + row["NP2"] * 4 + row["PIM"] * 2) / 10
                self.data_frame_full.loc[user_index, "MEDIA"] = media

            self.salvar_dados()

            messagebox.showinfo("Sucesso", "Usuário atualizado com sucesso!")
            window.destroy()

        except Exception as e:
            messagebox.showerror(
                "Erro ao Salvar", f"Ocorreu um erro ao salvar as alterações: {e}"
            )

    def abrir_janela_edicao_notas(self):
        if self.current_user["NIVEL"] != "PROFESSOR":
            messagebox.showwarning("Permissão Negada", "Acesso negado.")
            return
        if not isinstance(self.tabela_widget, ttk.Treeview):
            messagebox.showwarning("Aviso", "A tabela não está carregada.")
            return
        
        selecionado = self.tabela_widget.focus()
        if not selecionado:
            messagebox.showwarning("Seleção", "Selecione um ALUNO para editar as notas.")
            return
        
        idx = int(selecionado)
        user_data_series = self.data_frame.loc[idx]
        
        if user_data_series["NIVEL"] != "ALUNO":
            messagebox.showwarning("Ação Inválida", "Você só pode editar as notas de usuários do nível ALUNO.")
            return
            
        user_id = user_data_series["ID"]
        full_user_data_row = self.data_frame_full[self.data_frame_full["ID"] == user_id]
        if full_user_data_row.empty:
            messagebox.showerror("Erro", "Dados completos do usuário não encontrados.")
            return
        full_user_data = full_user_data_row.iloc[0]

        edit_window = ctk.CTkToplevel(self)
        edit_window.title(f"Lançar Notas - Aluno ID: {user_id}")
        edit_window.geometry("400x300")
        edit_window.transient(self)
        edit_window.grab_set()

        form_frame = ctk.CTkFrame(edit_window)
        form_frame.pack(padx=20, pady=20, fill="both", expand=True)

        ctk.CTkLabel(form_frame, text="Aluno:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        ctk.CTkLabel(form_frame, text=f"{full_user_data['NOME']}", font=("Arial", 12, "bold")).grid(row=0, column=1, padx=10, pady=5, sticky="w")

        entries = {}
        editaveis = ["NP1", "NP2", "PIM"]

        for i, col in enumerate(editaveis):
            ctk.CTkLabel(form_frame, text=f"{col}:").grid(
                row=i+1, column=0, padx=10, pady=5, sticky="w"
            )
            entry = ctk.CTkEntry(form_frame, width=250)
            entry.insert(0, str(full_user_data[col]))
            entry.grid(row=i+1, column=1, padx=10, pady=5, sticky="ew")
            entries[col] = entry

        save_button = ctk.CTkButton(
            form_frame,
            text="Salvar Notas",
            command=lambda: self.salvar_edicao_notas(user_id, entries, edit_window),
            fg_color="green"
        )
        save_button.grid(
            row=len(editaveis)+1, column=0, columnspan=2, padx=10, pady=20, sticky="ew"
        )

    def salvar_edicao_notas(self, user_id, entries, window):
        try:
            user_index = self.data_frame_full[
                self.data_frame_full["ID"] == user_id
            ].index[0]
            
            for col, entry_widget in entries.items():
                new_value = entry_widget.get().strip()
                try:
                    new_value_converted = (0 if not new_value else float(new_value))
                    
                    if not (0 <= new_value_converted <= 10):
                        messagebox.showerror("Erro de Validação", f"A nota {col} deve estar entre 0 e 10.")
                        return
                        
                    self.data_frame_full.loc[user_index, col] = new_value_converted
                except ValueError:
                    messagebox.showerror("Erro de Validação", f"O campo '{col}' deve ser um número (use . para decimais).")
                    return

            row = self.data_frame_full.loc[user_index]
            media = (row["NP1"] * 4 + row["NP2"] * 4 + row["PIM"] * 2) / 10
            self.data_frame_full.loc[user_index, "MEDIA"] = round(media, 2)

            self.salvar_dados()

            messagebox.showinfo("Sucesso", "Notas do aluno atualizadas com sucesso!")
            window.destroy()

        except Exception as e:
            messagebox.showerror(
                "Erro ao Salvar", f"Ocorreu um erro ao salvar as notas: {e}"
            )

    def open_activity_submission_window(self):
        user_name = self.current_user.get("NOME", "N/A")
        user_id = self.current_user.get("ID", "N/A")

        submission_window = ctk.CTkToplevel(self)
        submission_window.title("Envio de Atividades do Aluno")
        submission_window.geometry("500x350")
        submission_window.transient(self)
        submission_window.grab_set()

        frame = ctk.CTkFrame(submission_window)
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        ctk.CTkLabel(
            frame, text="Portal de Envio de Atividades", font=("Roboto", 18, "bold")
        ).pack(pady=10)
        ctk.CTkLabel(
            frame, text=f"Aluno: {user_name} (ID: {user_id})", text_color="#4CAF50"
        ).pack(pady=(5, 10))

        ctk.CTkLabel(frame, text="Disciplina:").pack(pady=(10, 0))
        self.discipline_entry = ctk.CTkEntry(frame, width=300)
        self.discipline_entry.pack(pady=(0, 10))

        self.current_file_path = None
        self.filepath_label = ctk.CTkLabel(
            frame, text="Nenhum arquivo selecionado.", text_color="gray"
        )
        self.filepath_label.pack(pady=(5, 0))

        btn_anexar = ctk.CTkButton(
            frame, text="Anexar Arquivo...", command=self._anexar_arquivo_dialog
        )
        btn_anexar.pack(pady=10)

        btn_enviar = ctk.CTkButton(
            frame,
            text="Enviar Atividade",
            command=lambda: self._enviar_atividade_action(submission_window),
            fg_color="green",
        )
        btn_enviar.pack(pady=20)

    def _anexar_arquivo_dialog(self):
        from tkinter import filedialog

        filepath = filedialog.askopenfilename(
            title="Selecione o arquivo da atividade",
            filetypes=(
                ("Todos os Arquivos", "*.*"),
                ("Documentos", "*.pdf;*.docx;*.txt"),
            ),
        )
        if filepath:
            self.filepath_label.configure(
                text=f"Arquivo: {os.path.basename(filepath)}", text_color="yellow"
            )
            self.current_file_path = filepath
        else:
            self.filepath_label.configure(
                text="Nenhum arquivo selecionado.", text_color="gray"
            )
            self.current_file_path = None

    def _enviar_atividade_action(self, window):
        disciplina = self.discipline_entry.get().strip()
        if not disciplina:
            messagebox.showwarning("Aviso", "Por favor, digite o nome da disciplina.")
            return
        if not hasattr(self, "current_file_path") or not self.current_file_path:
            messagebox.showwarning("Aviso", "Por favor, anexe o arquivo da atividade.")
            return

        messagebox.showinfo(
            "Envio Concluído",
            f"Atividade de '{disciplina}' enviada com sucesso (Simulação) pelo aluno ID: {self.current_user['ID']}!",
        )
        window.destroy()

    def salvar_dados(self):
        if self.current_user["NIVEL"] not in ["ADMINISTRADOR", "COORDENADOR", "PROFESSOR"]:
            messagebox.showwarning(
                "Permissão Negada",
                "Somente Admin, Coordenador ou Professor (para salvar notas) podem salvar alterações.",
            )
            return

        if self.data_frame_full is None or self.data_frame_full.empty:
            messagebox.showwarning(
                "Salvar",
                "Não foi possível salvar, o banco de dados está vazio ou não foi carregado.",
            )
            return

        try:
            df_to_save = self.data_frame_full.copy()

            column_map_save = {
                "ID": "id",
                "NOME": "nome",
                "EMAIL": "email",
                "SENHA": "senha",
                "IDADE": "idade",
                "NIVEL": "nivel",
                "CURSO": "curso",
                "ID_TURMAS": "turma",           
                "NP1": "np1",
                "NP2": "np2",
                "PIM": "pim",
                "MEDIA": "media",
                "STATUS DO ALUNO": "atividade", 
            }
            df_to_save.rename(columns=column_map_save, inplace=True)

            final_csv_cols = [
                "id", "nome", "email", "senha", "nivel", "curso", "turma", 
                "idade", "np1", "np2", "pim", "media", "atividade"
            ]
            
            df_to_save = df_to_save.reindex(columns=final_csv_cols)

            for col in ["np1", "np2", "pim", "media"]:
                if col in df_to_save.columns:
                    df_to_save[col] = df_to_save[col].apply(
                        lambda x: f"{x:.2f}".replace(".", ",") if pd.notna(x) and pd.notnull(x) else ""
                    )
            
            with open(CAMINHO_ARQUIVO, "w", encoding="utf-8", newline="") as f:
                f.write("[USUARIOS]\n")
                df_to_save.to_csv(
                    f, sep=";", index=False, header=True, lineterminator="\r\n"
                )

            messagebox.showinfo(
                "Salvo",
                "Todas as alterações (Status e Edições) foram salvas com sucesso no arquivo CSV.",
            )

            self.atualizar_tabela(reload_csv=True)

        except Exception as e:
            messagebox.showerror(
                "Erro ao Salvar", f"Ocorreu um erro ao salvar os dados: {e}"
            )


# =============================================================================
# === 4. PONTO DE PARTIDA DO PROGRAMA (Com lógica LGPD) ===
# =============================================================================

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    
    app = MainApp()
    
    # --- MODIFICAÇÃO ---
    # Chama o verificador LGPD ANTES do mainloop
    app.start_app_with_lgpd_check()
    # --- FIM DA MODIFICAÇÃO ---
    
    app.mainloop()


#PRINCIPAL ATUALIZADO // 03/11 ÁS 23:16