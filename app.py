import streamlit as st
import pandas as pd
from datetime import datetime
import logging

# Importa as funções do seu db_config.py
from db_config import consultar_dados, executar_query

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="APTUS - Gestão Ocupacional",
    page_icon="🚀",
    layout="wide"
)

# --- ESTILO VISUAL (CSS) ---
st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #007bff;
        color: white;
        font-weight: bold;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR / NAVEGAÇÃO ---
st.sidebar.title("🚀 APTUS SYSTEM")
st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "Menu Principal",
    ["📋 Recepção", "💰 Caixa", "🧪 Toxicológico", "📊 Faturamento", "🏢 Empresas"]
)

# =============================================================================
# ABA: RECEPÇÃO
# =============================================================================
if menu == "📋 Recepção":
    st.header("📋 Recepção e Atendimento")
    
    with st.expander("Novo Registo de Entrada", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            nome = st.text_input("Nome do Paciente").upper()
            cpf = st.text_input("CPF (Apenas números)")
        with col2:
            # Busca empresas do banco Aiven
            res_empresas = consultar_dados("SELECT nome FROM empresas ORDER BY nome")
            lista_empresas = [r[0] for r in res_empresas] if res_empresas else ["PARTICULAR"]
            empresa = st.selectbox("Empresa", lista_empresas)
        with col3:
            procedimento = st.selectbox("Procedimento", ["ASO Admissional", "Toxicológico", "Periódico", "Demissional"])

        if st.button("Registrar Atendimento"):
            if nome and cpf:
                sql = "INSERT INTO recepcao (paciente, cpf, empresa, procedimento, status, data_ts) VALUES (%s, %s, %s, %s, %s, %s)"
                executar_query(sql, (nome, cpf, empresa, procedimento, "AGUARDANDO", datetime.now()))
                st.success(f"✅ {nome} adicionado à fila!")
                st.rerun()
            else:
                st.error("⚠️ Por favor, preencha o Nome e o CPF.")

    st.subheader("Fila de Atendimento do Dia")
    # Busca dados em tempo real do banco
    query_fila = "SELECT data_ts, paciente, empresa, procedimento, status FROM recepcao WHERE status != 'FINALIZADO' ORDER BY data_ts DESC"
    dados = consultar_dados(query_fila)
    
    if dados:
        df = pd.DataFrame(dados, columns=["Data/Hora", "Paciente", "Empresa", "Procedimento", "Status"])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum paciente aguardando no momento.")

# =============================================================================
# ABA: TOXICOLÓGICO (Lógica de Prazos)
# =============================================================================
elif menu == "🧪 Toxicológico":
    st.header("🧪 Controlo de Exames Toxicológicos")
    
    col_b, _ = st.columns([2, 2])
    busca = col_b.text_input("🔍 Procurar Paciente (Nome ou CPF)")

    sql_tox = "SELECT paciente, data_coleta, dias_restantes, status FROM toxicologico"
    if busca:
        sql_tox += f" WHERE paciente ILIKE '%{busca}%' OR cpf ILIKE '%{busca}%'"
    
    dados_tox = consultar_dados(sql_tox)
    
    if dados_tox:
        df_tox = pd.DataFrame(dados_tox, columns=["Paciente", "Data Coleta", "Dias Restantes", "Status"])
        
        # Função para destacar prazos críticos (estilo que usavas no Tkinter)
        def highlight_prazos(row):
            if row['Dias Restantes'] <= 2:
                return ['background-color: #ffcccc'] * len(row) # Vermelho claro
            elif row['Dias Restantes'] <= 5:
                return ['background-color: #fff4cc'] * len(row) # Amarelo/Laranja
            return [''] * len(row)

        st.dataframe(df_tox.style.apply(highlight_prazos, axis=1), use_container_width=True)

# =============================================================================
# ABA: CAIXA
# =============================================================================
elif menu == "💰 Caixa":
    st.header("💰 Fluxo de Caixa")
    
    # KPIs rápidos
    res_soma = consultar_dados("SELECT SUM(valor_num) FROM recepcao WHERE tipo = 'DIN' AND excluido = FALSE")
    total_recebido = res_soma[0][0] if res_soma and res_soma[0][0] else 0.0
    
    st.metric("Total em Caixa (Dinheiro)", f"R$ {total_recebido:,.2f}")

    st.subheader("Últimos Lançamentos")
    dados_caixa = consultar_dados("SELECT data_ts, paciente, valor_num, empresa FROM recepcao ORDER BY data_ts DESC LIMIT 50")
    if dados_caixa:
        df_c = pd.DataFrame(dados_caixa, columns=["Data", "Paciente", "Valor", "Empresa"])
        st.table(df_c)

# --- RODAPÉ ---
st.sidebar.markdown("---")
st.sidebar.caption("APTUS v4.0 | Cloud Edition")
st.sidebar.caption("Developed by Sara Sales")