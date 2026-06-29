import streamlit as st
import pandas as pd
import calendar
from datetime import date, datetime, timedelta
import requests
from io import StringIO

# ---------------- CONFIG ----------------
SHEET_ID = "1kte6Ys9vgzw7a0Z1PDXkxf6VOX9KHWlRCXp7P-7RSi4"
GID = "507430155"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

DIAS_SEMANA = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MESES_PT = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
MAX_ATIVIDADES_DIA = 8

# Cores pastéis inspiradas na imagem para os dias da semana
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

# ---------------- ESTILO (INSPIRADO NO PLANNER) ----------------
FONTE = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif"

st.markdown(f"""
<style>
* {{ font-family: {FONTE} !important; }}

.planner-container {{
    background-color: #FDFDFD;
    padding: 20px;
    border-radius: 12px;
    border: 2px solid #EBEBEB;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.02);
}}

/* Header com fonte Serifada estilo clássico */
.planner-header {{
    border: 2px solid #3B3C43;
    border-radius: 8px;
    padding: 10px 20px;
    display: inline-block;
    margin-bottom: 20px;
}}
.planner-title {{
    font-family: 'Times New Roman', Times, serif !important;
    font-size: 2.5rem;
    font-weight: 800;
    color: #3B3C43;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin: 0;
}}

.dia-semana-label {{
    text-align: center; font-weight: 700; padding: 10px 5px; 
    font-size: 1.1rem; border-bottom: 2px solid #EBEBEB;
    font-family: 'Georgia', serif !important; font-style: italic;
}}

/* Grid do Calendário */
.day-card {{
    border: 1px solid #EBEBEB; background: #FFFFFF;
    height: 180px; overflow-y: auto; padding: 8px;
    box-sizing: border-box; position: relative;
}}
.day-card-header {{
    display: flex; justify-content: flex-end;
    border-bottom: 1px solid #F0F0F0; margin-bottom: 6px; padding-bottom: 2px;
}}
.day-num {{
    font-weight: 700; font-size: 0.9rem; color: #555;
}}

/* Estilo Checklist */
.task-item {{
    display: flex; align-items: flex-start;
    font-size: 0.75rem; margin-bottom: 6px; color: #444;
    line-height: 1.3;
}}
.task-box {{
    border: 1px solid #CCC; width: 10px; height: 10px;
    margin-right: 6px; margin-top: 3px; border-radius: 2px;
    flex-shrink: 0;
}}
.task-text {{
    word-break: break-word;
}}
</style>
""", unsafe_allow_html=True)


# ====================================================================
# RENDERIZAÇÃO
# ====================================================================
ano, mes = st.session_state.ano, st.session_state.mes

st.markdown('<div class="planner-container">', unsafe_allow_html=True)

# Controles e Cabeçalho
col_nav1, col_nav2, col_nav3 = st.columns([1, 4, 1])
with col_nav1:
    if st.button("◀ Anterior"):
        if mes == 1: st.session_state.mes, st.session_state.ano = 12, ano - 1
        else: st.session_state.mes -= 1
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
    if st.button("Próximo ▶"):
        if mes == 12: st.session_state.mes, st.session_state.ano = 1, ano + 1
        else: st.session_state.mes += 1
        st.rerun()

# Dias da Semana
cols = st.columns(7)
for i, dia_nome in enumerate(DIAS_SEMANA):
    cols[i].markdown(
        f'<div class="dia-semana-label" style="color:{CORES_SEMANA[i]};">{dia_nome}</div>',
        unsafe_allow_html=True)

# Grid Mensal
cal = calendar.Calendar(firstweekday=0)
semanas = cal.monthdatescalendar(ano, mes)

for semana in semanas:
    cols = st.columns(7)
    for i, dia in enumerate(semana):
        with cols[i]:
            no_mes = dia.month == mes
            ativs = atividades_do_dia(dia)
            opacidade = "1" if no_mes else "0.4"
            bg_color = "#FAFAFA" if not no_mes else "#FFFFFF"

            # Borda do topo com a cor do dia da semana (detalhe do planner)
            borda_topo = f"border-top: 4px solid {CORES_SEMANA[i]};" if no_mes else "border-top: 4px solid #EBEBEB;"

            html_tasks = ""
            for a in ativs[:MAX_ATIVIDADES_DIA]:
                texto = a["atividade"]
                # A cor da categoria agora pinta apenas o texto ou um leve background para ficar sutil
                html_tasks += f'''
                <div class="task-item">
                    <div class="task-box"></div>
                    <div class="task-text" style="color: {a["cor"]}; font-weight: 600;">{texto}</div>
                </div>'''
            
            if len(ativs) > MAX_ATIVIDADES_DIA:
                html_tasks += f'<div style="font-size: 0.65rem; color: #999; text-align: center;">+{len(ativs)-MAX_ATIVIDADES_DIA} itens</div>'

            card_html = f'''
            <div class="day-card" style="opacity:{opacidade}; background:{bg_color}; {borda_topo}">
                <div class="day-card-header">
                    <span class="day-num">{dia.day}</span>
                </div>
                {html_tasks}
            </div>
            '''
            st.markdown(card_html, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
