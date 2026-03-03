import psycopg2
import psycopg2.pool
import streamlit as st
import logging

# ── CONFIGURAÇÃO DE CONEXÃO SEGURA ──────────────────────────────────────────
try:
    # 1. Tenta ler do Streamlit Cloud (Segurança Máxima)
    # Se você configurou o "Secrets" no site, ele usará isso
    if "postgres" in st.secrets:
        DB_URI = st.secrets["postgres"]["uri"]
    else:
        raise Exception("Secrets não encontrados")
except Exception:
    # 2. Se você estiver no seu PC, ele não vai achar o "Secrets" e usará este link:
    DB_URI = "postgres://avnadmin:AVNS_cTcliIkcWH35zDJAviD@pg-195a48b8-controledecaixa015.g.aivencloud.com:11674/empresa_db?sslmode=require"

# Inicialização do Pool (Gerenciador de conexões)
try:
    pool = psycopg2.pool.ThreadedConnectionPool(1, 15, DB_URI)
except Exception as e:
    logging.error(f"Erro ao conectar ao Aiven: {e}")
    pool = None

def executar_query(sql, params=None, fetch=False):
    """Executa comandos e garante que a conexão volte para o pool."""
    if not pool: return None
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            if fetch:
                return cur.fetchall()
            conn.commit()
            return True
    except Exception as e:
        st.error(f"❌ Erro no Banco: {e}")
        return None
    finally:
        pool.putconn(conn)

def consultar_dados(sql, params=None):
    return executar_query(sql, params, fetch=True)
