import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date
import hashlib

# ----------------------------
# Usuários e Acesso
# ----------------------------
usuarios = {
    "admin": {"senha": "admin123", "secao": "todos"},
    "user01": {"senha": "senha01", "secao": "açougue"},
    "user02": {"senha": "senha02", "secao": "padaria"},
    "user03": {"senha": "senha03", "secao": "frios"},
    "user04": {"senha": "senha04", "secao": "laticínios"},
    "user05": {"senha": "senha05", "secao": "hortifrútis"},
    "user06": {"senha": "senha06", "secao": "enlatados"},
    "user07": {"senha": "senha07", "secao": "bebidas"},
    "user08": {"senha": "senha08", "secao": "matinal"},
    "user09": {"senha": "senha09", "secao": "cereais"},
    "user10": {"senha": "senha10", "secao": "perfumaria"},
    "user11": {"senha": "senha11", "secao": "biscoitos"},
    "user12": {"senha": "senha12", "secao": "bazar"},
    "user13": {"senha": "senha13", "secao": "limpeza"},
    "user14": {"senha": "senha14", "secao": "bom bom"},
    "user15": {"senha": "senha15", "secao": "massas"},
    "user16": {"senha": "senha16", "secao": "condimentos"},
    "user17": {"senha": "senha17", "secao": "integral"},
}

usuarios_hash = {
    u: {
        "senha": hashlib.sha256(d["senha"].encode()).hexdigest(),
        "secao": d["secao"]
    } for u, d in usuarios.items()
}

# ----------------------------
# Banco de Dados
# ----------------------------
DB_NAME = "validade.db"

def create_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            secao_id TEXT,
            ean TEXT,
            descricao TEXT,
            validade DATE,
            quantidade INTEGER,
            excluido INTEGER DEFAULT 0,
            data_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def insert_produto(secao_id, ean, descricao, validade, quantidade):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO produtos (secao_id, ean, descricao, validade, quantidade)
        VALUES (?, ?, ?, ?, ?)
    ''', (secao_id, ean, descricao, validade, quantidade))
    conn.commit()
    conn.close()

def get_produtos():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM produtos")
    rows = c.fetchall()
    conn.close()
    return rows

def marcar_como_excluido(id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE produtos SET excluido = 1 WHERE id = ?", (id,))
    conn.commit()
    conn.close()

def excluir_definitivo(ids):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.executemany("DELETE FROM produtos WHERE id = ?", [(i,) for i in ids])
    conn.commit()
    conn.close()

def classificar_validade(data_validade):
    hoje = date.today()
    dias_restantes = (data_validade - hoje).days
    if dias_restantes < 0:
        return 'Vencido'
    elif dias_restantes <= 5:
        return 'Remover'
    elif dias_restantes <= 30:
        return '30 dias'
    else:
        return 'Retido'

# ----------------------------
# Streamlit App
# ----------------------------
st.set_page_config(page_title="Controle de Validade", layout="wide")
create_db()

# ----------------------------
# Login
# ----------------------------
st.sidebar.title("🔐 Login")
usuario = st.sidebar.text_input("Usuário")
senha = st.sidebar.text_input("Senha", type="password")
logado = False
secao_usuario = None

if usuario in usuarios_hash:
    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
    if senha_hash == usuarios_hash[usuario]["senha"]:
        logado = True
        secao_usuario = usuarios_hash[usuario]["secao"]
        st.sidebar.success(f"Bem-vindo, {usuario} ({secao_usuario})")
    else:
        st.sidebar.error("Senha incorreta")
elif usuario:
    st.sidebar.error("Usuário não encontrado")

# ----------------------------
# Se logado, mostra app
# ----------------------------
if logado:
    secoes = [
        "açougue", "padaria", "frios", "laticínios", "hortifrútis", "enlatados",
        "bebidas", "matinal", "cereais", "perfumaria", "biscoitos", "bazar",
        "limpeza", "bom bom", "massas", "condimentos", "integral"
    ]

    abas = st.tabs(["📋 Coleta Produto", "📦 Mapa de Itens", "📊 Gráfico"])

    # -----------------------
    # Aba 1 - Coleta
    # -----------------------
    with abas[0]:
        st.header("📋 Coleta de Produto")
    with st.form("form_coleta", clear_on_submit=True):
        st.subheader("📥 Inserir novo item")
        col1, col2 = st.columns(2)

        secao_id = secao_usuario if secao_usuario != "todos" else st.selectbox("Seção", secoes, key="secao_input")

        with col1:
            ean = st.text_input("Código de Barras (EAN)", key="ean_input")
            descricao = st.text_input("Descrição do Item", key="descricao_input")
        with col2:
            validade = st.date_input("Data de Validade", format="DD/MM/YYYY", key="validade_input")
            quantidade = st.number_input("Quantidade", min_value=1, step=1, key="quantidade_input")

        submitted = st.form_submit_button("Salvar Produto")

        if submitted:
            validade_formatada = validade.strftime("%Y-%m-%d")
            insert_produto(secao_id, ean, descricao, validade_formatada, quantidade)
            st.success("✅ Produto salvo com sucesso!")


    # -----------------------
    # Aba 2 - Mapa de Itens
    # -----------------------
    with abas[1]:
        st.header("📦 Mapa de Itens")
        df = pd.DataFrame(get_produtos(), columns=[
            "ID", "Seção", "EAN", "Descrição", "Validade", "Quantidade", "Excluído", "Data Coleta"
        ])
        df["Validade"] = pd.to_datetime(df["Validade"]).dt.date
        df["Status"] = df["Validade"].apply(classificar_validade)
        df["Validade Formatada"] = df["Validade"].apply(lambda x: x.strftime("%d/%m/%Y"))

        # Filtro por seção
        if secao_usuario != "todos":
            df = df[df["Seção"] == secao_usuario]
        else:
            filtro_secao = st.selectbox("🔎 Filtro por seção", ["Todas"] + secoes)
            if filtro_secao != "Todas":
                df = df[df["Seção"] == filtro_secao]

        # Filtro por status
        filtro_status = st.multiselect("📌 Filtro por status", ["Vencido", "Remover", "30 dias", "Retido"])
        if filtro_status:
            df = df[df["Status"].isin(filtro_status)]

        # Filtro por EAN
        busca = st.text_input("🔍 Buscar por EAN")
        if busca:
            df = df[df["EAN"].str.contains(busca)]

        df["Dias Restantes"] = df["Validade"].apply(lambda x: (x - date.today()).days)
        mostrar = df[["ID", "Seção", "EAN", "Descrição", "Validade Formatada", "Dias Restantes", "Quantidade", "Status", "Excluído"]]

        st.dataframe(mostrar.sort_values(by="Validade Formatada"))

        if secao_usuario == "todos":
            st.markdown("### 🗑️ Exclusões (apenas admin)")
            id_excluir = st.number_input("ID para marcar como excluído", min_value=1, step=1)
            if st.button("Marcar como Excluído"):
                marcar_como_excluido(id_excluir)
                st.success("Item marcado como excluído")

            ids_excluir = st.multiselect("IDs para exclusão definitiva", df["ID"].tolist())
            if st.button("Excluir Definitivamente"):
                excluir_definitivo(ids_excluir)
                st.success("Itens excluídos permanentemente")

    # -----------------------
    # Aba 3 - Gráfico
    # -----------------------
    with abas[2]:
        st.header("📊 Gráfico de Validade")
        df = pd.DataFrame(get_produtos(), columns=[
            "ID", "Seção", "EAN", "Descrição", "Validade", "Quantidade", "Excluído", "Data Coleta"
        ])
        df["Validade"] = pd.to_datetime(df["Validade"]).dt.date
        df["Status"] = df["Validade"].apply(classificar_validade)

        if secao_usuario != "todos":
            df = df[df["Seção"] == secao_usuario]
        else:
            filtro_secao = st.selectbox("Filtro por seção", ["Todas"] + secoes)
            if filtro_secao != "Todas":
                df = df[df["Seção"] == filtro_secao]

        grafico = df.groupby("Status")["Quantidade"].sum().reset_index()
        st.bar_chart(grafico.set_index("Status"))

else:
    st.warning("Faça login para acessar o sistema.")
    
secao_usuario