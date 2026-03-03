import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime
import hashlib

# --- 1. Configuração da Página (Para ficar largo como o Desktop) ---
st.set_page_config(page_title="Sistema APTUS - Web", layout="wide")

# Inicializar o estado da sessão
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = None
if 'page' not in st.session_state:
    st.session_state['page'] = "Recepção"

# --- 2. Conexão com o Banco de Dados (Usando Secrets do Aiven) ---
@st.cache_resource
def get_db_connection():
    """Conecta ao banco usando a URI salva nos Secrets do Streamlit Cloud."""
    try:
        # Puxa a 'uri' que você colou nas Advanced Settings do Streamlit
        conn = psycopg2.connect(st.secrets["postgres"]["uri"])
        return conn
    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        return None

def execute_query(query, params=None, fetch=None):
    conn = get_db_connection()
    if conn is None: return None
    with conn.cursor() as cur:
        try:
            cur.execute(query, params)
            if fetch == 'one': return cur.fetchone()
            elif fetch == 'all': return cur.fetchall()
            else:
                conn.commit()
                return None
        except Exception as e:
            conn.rollback()
            st.error(f"Erro SQL: {e}")
            return None

# --- 3. Funções de Segurança ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_login(username, password):
    query = "SELECT id, nome_usuario, hash_senha, nivel_acesso FROM usuarios WHERE nome_usuario = %s"
    user_data = execute_query(query, (username,), fetch='one')
    if user_data:
        stored_hash = user_data[2]
        if stored_hash == hash_password(password):
            return {"id": user_data[0], "username": user_data[1], "access_level": user_data[3]}
    return None

# --- 4. Funções de Busca de Dados ---
@st.cache_data(ttl=60)
def get_pacientes(search_term=""):
    if search_term:
        query = "SELECT id, nome, cpf, data_nascimento, telefone, email FROM pacientes WHERE nome ILIKE %s OR cpf ILIKE %s ORDER BY nome"
        params = (f'%{search_term}%', f'%{search_term}%')
    else:
        query = "SELECT id, nome, cpf, data_nascimento, telefone, email FROM pacientes ORDER BY nome"
        params = None
    rows = execute_query(query, params, fetch='all')
    return pd.DataFrame(rows, columns=['ID', 'Nome', 'CPF', 'Nascimento', 'Telefone', 'Email']) if rows else pd.DataFrame()

# --- 5. Páginas do Sistema ---

def render_recepcao():
    st.header("🏥 Recepção e Atendimento")
    
    tab1, tab2 = st.tabs(["🔍 Buscar Paciente", "➕ Novo Cadastro"])

    with tab1:
        search = st.text_input("Buscar por Nome ou CPF")
        df = get_pacientes(search)
        st.dataframe(df, use_container_width=True, hide_index=True)

    with tab2:
        with st.form("cadastro_paciente"):
            c1, c2 = st.columns(2)
            nome = c1.text_input("Nome Completo")
            cpf = c2.text_input("CPF")
            data_nascto = c1.date_input("Data de Nascimento", value=datetime(2000, 1, 1))
            tel = c2.text_input("Telefone")
            
            if st.form_submit_button("Salvar no Banco"):
                query = "INSERT INTO pacientes (nome, cpf, data_nascimento, telefone) VALUES (%s, %s, %s, %s)"
                execute_query(query, (nome, cpf, data_nascto, tel))
                st.success("Paciente cadastrado!")
                st.cache_data.clear()

def render_configuracoes():
    st.header("⚙️ Configurações do Sistema")
    if st.session_state.user_info['access_level'] != 'admin':
        st.error("Acesso restrito a administradores.")
        return
    st.write("Aqui você pode gerenciar usuários e procedimentos.")

# --- 6. Lógica de Navegação ---

def main():
    if not st.session_state['logged_in']:
        # Tela de Login Estilizada
        st.title("APTUS MEDICINA DO TRABALHO")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.subheader("Acesso ao Sistema")
            user = st.text_input("Usuário")
            pw = st.text_input("Senha", type="password")
            if st.button("Entrar"):
                u_info = check_login(user, pw)
                if u_info:
                    st.session_state['logged_in'] = True
                    st.session_state['user_info'] = u_info
                    st.rerun()
                else:
                    st.error("Login inválido!")
    else:
        # Menu Lateral
        st.sidebar.title("MENU APTUS")
        st.sidebar.info(f"Logado como: {st.session_state.user_info['username']}")
        
        paginas = ["Recepção", "Faturamento", "Toxicológico"]
        if st.session_state.user_info['access_level'] == 'admin':
            paginas.append("Configurações")
        
        escolha = st.sidebar.radio("Navegar para:", paginas)
        
        if st.sidebar.button("Sair"):
            st.session_state.clear()
            st.rerun()

        # Roteamento
        if escolha == "Recepção": render_recepcao()
        elif escolha == "Configurações": render_configuracoes()
        else: st.info(f"Página de {escolha} em desenvolvimento.")

if __name__ == "__main__":
    main()
