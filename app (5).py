import streamlit as st
import pandas as pd
import calendar
from datetime import date
import requests
from io import StringIO

# ---------------- CONFIG ----------------
SHEET_ID = "1kte6Ys9vgzw7a0Z1PDXkxf6VOX9KHWlRCXp7P-7RSi4"
GID = "507430155"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

DIAS_SEMANA = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
MESES_PT = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
MAX_ATIVIDADES_DIA = 8

CORES_SEMANA = ["#5AB0A2", "#EB8C87", "#A6CA76", "#EB8DB5", "#F4BA5E", "#A0AAB2", "#848E96"]

CATEGORIAS = [
    ("Reunião",          ["reunião", "reuniao", "encontro"],                       "#4A90D9"),
    ("Mobilização",      ["mobilização", "mobilizacao"],                           "#E67E22"),
    ("Publicação/Story", ["publicar", "publicação", "publicacao", "story", "post"], "#9B59B6"),
    ("Gravação",         ["gravação", "gravacao", "vídeo", "video"],                "#1ABC9C"),
    ("Faturamento",      ["faturamento", "leitura", "hidrômetro"],                  "#27AE60"),
    ("Instrumentação",   ["instrumentação", "instrumentacao", "piezômetro"],        "#16A085"),
    ("Monitoramento",    ["monitoramento", "captação", "captacao"],                 "#2980B9"),
    ("Vistoria/Fiscaliz.", ["vistoria", "fiscalização", "fiscalizacao"],            "#C0392B"),
    ("Coleta/Água",      ["coleta", "análise", "analise", "sonda"],                 "#3498DB"),
    ("Diárias/Admin.",   ["diária", "diaria", "protheus", "estoque", "frota"],      "#7F8C8D"),
    ("Relatório/Ata",    ["relatório", "relatorio", "ata", "parecer"],              "#8E44AD"),
    ("Capacitação",      ["capacitação", "capacitacao", "curso", "treinamento"],    "#D35400"),
    ("Feriado/Data",     ["feriado", "ponto facultativo", "data magna"],            "#BDC3C7"),
]
COR_PADRAO = "#95A5A6"

def categorizar(texto: str):
    if not isinstance(texto, str) or not texto.strip():
        return "Outros", COR_PADRAO
    t = texto.lower()
    for nome, palavras, cor in CATEGORIAS:
        if any(p in t for p in palavras):
            return nome, cor
    return "Outros", COR_PADRAO

@st.cache_data(ttl=600)
def carregar_dados():
    resp = requests.get(CSV_URL, timeout=15)
    resp.raise_for_status()
    df_raw = pd.read_csv(StringIO(resp.text), header=None)

    df = df_raw.iloc[6:, [0, 4]].copy()
    df.columns = ["data_raw", "atividade"]
    df = df.dropna(subset=["data_raw"])

    df["data"] = pd.to_datetime(df["data_raw"], format="%d/%m/%Y", errors="coerce")
    df = df.dropna(subset=["data"])
    df["data"] = df["data"].dt.date
    df["atividade"] = df["atividade"].fillna("").astype(str).str.strip()
    df = df[df["atividade"] != ""]

    cat_cor = df["atividade"].apply(categorizar)
    df["categoria"] = cat_cor.apply(lambda x: x[0])
    df["cor"] = cat_cor.apply(lambda x: x[1])

    return df.sort_values("data").reset_index(drop=True)

# ---------------- ESTADO ----------------
st.set_page_config(page_title="Painel Digital Planner", layout="wide")

hoje = date.today()
if "ano" not in st.session_state: st.session_state.ano = hoje.year
if "mes" not in st.session_state: st.session_state.mes = hoje.month

try:
    df = carregar_dados()
except Exception as e:
    st.error(f"Erro ao carregar a planilha: {e}")
    st.stop()

def atividades_do_dia(dia: date):
    return df[df["data"] == dia].to_dict("records")

# ---------------- ESTILO MODERNO CORRIGIDO ----------------
st.markdown("""
<style>
/* Importação de fontes modernas */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Playfair+Display:wght@700;800&display=swap');

/* Reset e estilos base */
* {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
}

/* Container principal */
.planner-container {
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    padding: 30px;
    border-radius: 20px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.1);
    backdrop-filter: blur(10px);
}

/* Header do planner */
.planner-header {
    background: white;
    border: none;
    border-radius: 15px;
    padding: 15px 30px;
    display: inline-block;
    margin-bottom: 30px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.08);
    transform: translateY(0);
    transition: all 0.3s ease;
}

.planner-header:hover {
    transform: translateY(-2px);
    box-shadow: 0 15px 40px rgba(0,0,0,0.12);
}

.planner-title {
    font-family: 'Playfair Display', Georgia, serif !important;
    font-size: 2.8rem;
    font-weight: 800;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin: 0;
}

/* Labels dos dias da semana */
.dia-semana-label {
    text-align: center;
    font-weight: 700;
    padding: 15px 5px;
    font-size: 1.2rem;
    background: white;
    border-radius: 10px;
    margin-bottom: 10px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    font-family: 'Inter', sans-serif !important;
    letter-spacing: 1px;
}

/* Cards dos dias */
.day-card {
    border: none;
    background: white;
    height: 200px;
    overflow-y: auto;
    padding: 15px;
    box-sizing: border-box;
    border-radius: 15px;
    box-shadow: 0 8px 25px rgba(0,0,0,0.06);
    transition: all 0.3s ease;
    position: relative;
}

.day-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 15px 35px rgba(0,0,0,0.12);
}

.day-card-header {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 10px;
    padding-bottom: 8px;
    border-bottom: 2px solid #f0f0f0;
}

.day-num {
    font-weight: 800;
    font-size: 1.1rem;
    color: #333;
    background: #f8f9fa;
    padding: 5px 12px;
    border-radius: 20px;
}

/* Itens de tarefa */
.task-item {
    display: flex;
    align-items: flex-start;
    font-size: 0.8rem;
    margin-bottom: 8px;
    padding: 6px;
    border-radius: 8px;
    background: #f8f9fa;
    transition: all 0.2s ease;
}

.task-item:hover {
    background: #e9ecef;
    transform: translateX(3px);
}

.task-box {
    border: 2px solid #dee2e6;
    width: 12px;
    height: 12px;
    margin-right: 8px;
    margin-top: 2px;
    border-radius: 4px;
    flex-shrink: 0;
    transition: all 0.2s ease;
}

.task-item:hover .task-box {
    border-color: #667eea;
}

.task-text {
    word-break: break-word;
    font-weight: 500;
    line-height: 1.4;
}

/* Scrollbar personalizada */
::-webkit-scrollbar {
    width: 6px;
}

::-webkit-scrollbar-track {
    background: #f1f3f5;
    border-radius: 10px;
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
}

/* Botões de navegação */
.stButton button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 25px;
    font-weight: 600;
    font-size: 1rem;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.stButton button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
    background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
}
</style>
""", unsafe_allow_html=True)


# ====================================================================
# RENDERIZAÇÃO
# ====================================================================
ano, mes = st.session_state.ano, st.session_state.mes

st.markdown('<div class="planner-container">', unsafe_allow_html=True)

col_nav1, col_nav2, col_nav3 = st.columns([1, 4, 1])
with col_nav1:
    if st.button("◀ Mês Anterior"):
        if mes == 1:
            st.session_state.mes, st.session_state.ano = 12, ano - 1
        else:
            st.session_state.mes -= 1
        st.rerun()
with col_nav2:
    st.markdown(f"""
    <div style="text-align: center;">
        <div class="planner-header">
            <h1 class="planner-title">{MESES_PT[mes]} {ano}</h1>
        </div>
    </div>
    """, unsafe_allow_html=True)
with col_nav3:
    if st.button("Próximo Mês ▶"):
        if mes == 12:
            st.session_state.mes, st.session_state.ano = 1, ano + 1
        else:
            st.session_state.mes += 1
        st.rerun()

cols = st.columns(7)
for i, dia_nome in enumerate(DIAS_SEMANA):
    cols[i].markdown(
        f'<div class="dia-semana-label" style="color:{CORES_SEMANA[i]};">{dia_nome}</div>',
        unsafe_allow_html=True)

cal = calendar.Calendar(firstweekday=0)
semanas = cal.monthdatescalendar(ano, mes)

for semana in semanas:
    cols = st.columns(7)
    for i, dia in enumerate(semana):
        with cols[i]:
            no_mes = dia.month == mes
            ativs = atividades_do_dia(dia)
            opacidade = "1" if no_mes else "0.4"
            bg_color = "#F8F9FA" if not no_mes else "#FFFFFF"
            borda_topo = f"border-top: 5px solid {CORES_SEMANA[i]};" if no_mes else "border-top: 5px solid #E9ECEF;"

            html_tasks = ""
            for a in ativs[:MAX_ATIVIDADES_DIA]:
                texto = a["atividade"]
                html_tasks += f'<div class="task-item"><div class="task-box"></div><div class="task-text" style="color:{a["cor"]}; font-weight:600;">{texto}</div></div>'
            
            if len(ativs) > MAX_ATIVIDADES_DIA:
                html_tasks += f'<div style="font-size:0.7rem; color:#6c757d; text-align:center; margin-top:8px; font-weight:600;">+{len(ativs)-MAX_ATIVIDADES_DIA} itens</div>'

            card_html = f'<div class="day-card" style="opacity:{opacidade}; background:{bg_color}; {borda_topo}"><div class="day-card-header"><span class="day-num">{dia.day}</span></div>{html_tasks}</div>'
            
            st.markdown(card_html, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
