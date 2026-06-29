import streamlit as st
st.set_page_config(page_title="Painel Digital Planner", layout="wide")

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
    ("Reunião",           ["reunião", "reuniao", "encontro"],                        "#4A90D9"),
    ("Mobilização",       ["mobilização", "mobilizacao"],                            "#E67E22"),
    ("Publicação/Story",  ["publicar", "publicação", "publicacao", "story", "post"], "#9B59B6"),
    ("Gravação",          ["gravação", "gravacao", "vídeo", "video"],                "#1ABC9C"),
    ("Faturamento",       ["faturamento", "leitura", "hidrômetro"],                  "#27AE60"),
    ("Instrumentação",    ["instrumentação", "instrumentacao", "piezômetro"],        "#16A085"),
    ("Monitoramento",     ["monitoramento", "captação", "captacao"],                 "#2980B9"),
    ("Vistoria/Fiscaliz.",["vistoria", "fiscalização", "fiscalizacao"],              "#C0392B"),
    ("Coleta/Água",       ["coleta", "análise", "analise", "sonda"],                 "#3498DB"),
    ("Diárias/Admin.",    ["diária", "diaria", "protheus", "estoque", "frota"],      "#7F8C8D"),
    ("Relatório/Ata",     ["relatório", "relatorio", "ata", "parecer"],              "#8E44AD"),
    ("Capacitação",       ["capacitação", "capacitacao", "curso", "treinamento"],    "#D35400"),
    ("Feriado/Data",      ["feriado", "ponto facultativo", "data magna"],            "#BDC3C7"),
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
    decoded_text = resp.content.decode("utf-8", errors="replace")
    df_raw = pd.read_csv(StringIO(decoded_text), header=None)
    if df_raw.shape[1] < 5:
        raise ValueError(
            f"Planilha retornou apenas {df_raw.shape[1]} coluna(s). "
            "Verifique se o GID e o layout da aba estão corretos."
        )
    df = df_raw.iloc[6:, [0, 4]].copy()
    df.columns = ["data_raw", "atividade"]
    df = df.dropna(subset=["data_raw"])
    df["data"] = pd.to_datetime(df["data_raw"], format="%d/%m/%Y", errors="coerce")
    df = df.dropna(subset=["data"])
    df["data"] = df["data"].dt.date
    df["atividade"] = df["atividade"].fillna("").astype(str).str.strip()
    df = df[df["atividade"] != ""]
    cat_df = pd.DataFrame(
        df["atividade"].apply(categorizar).tolist(),
        columns=["categoria", "cor"],
        index=df.index
    )
    df = pd.concat([df, cat_df], axis=1)
    return df.sort_values("data").reset_index(drop=True)


# ---------------- ESTADO ----------------
hoje = date.today()
if "ano" not in st.session_state:
    st.session_state.ano = hoje.year
if "mes" not in st.session_state:
    st.session_state.mes = hoje.month

try:
    df = carregar_dados()
except Exception as e:
    st.error(f"Erro ao carregar a planilha: {e}")
    st.stop()

# Índice por data — O(1) lookup
_idx_por_data: dict = {}
for _, row in df.iterrows():
    _idx_por_data.setdefault(row["data"], []).append(row.to_dict())


def atividades_do_dia(dia: date) -> list:
    return _idx_por_data.get(dia, [])


# ====================================================================
# CSS  — grid puro, sem depender do layout de colunas do Streamlit
# ====================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Playfair+Display:wght@700;800&display=swap');

* { font-family: 'Inter', sans-serif !important; box-sizing: border-box; }

/* Remove padding extra que o Streamlit injeta nos st.markdown */
[data-testid="stMarkdownContainer"] > div { width: 100% !important; }

/* ---- Container geral ---- */
.planner-wrap {
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    padding: 24px;
    border-radius: 20px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.1);
}

/* ---- Cabeçalho do mês ---- */
.planner-title {
    font-family: 'Playfair Display', serif !important;
    font-size: 2.4rem;
    font-weight: 800;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin: 0;
    text-align: center;
}

/* ---- Grid 7 colunas (header + semanas) ---- */
.cal-grid {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 8px;
    margin-top: 12px;
}

/* ---- Label do dia da semana ---- */
.dow-label {
    text-align: center;
    font-weight: 700;
    font-size: 0.95rem;
    padding: 10px 4px;
    background: white;
    border-radius: 10px;
    box-shadow: 0 3px 10px rgba(0,0,0,0.06);
    letter-spacing: 0.5px;
}

/* ---- Card de cada dia ---- */
.day-card {
    background: white;
    border-radius: 14px;
    box-shadow: 0 6px 20px rgba(0,0,0,0.06);
    padding: 10px;
    min-height: 180px;
    max-height: 220px;
    overflow-y: auto;
    transition: transform 0.25s ease, box-shadow 0.25s ease;
    display: flex;
    flex-direction: column;
}

.day-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 14px 32px rgba(0,0,0,0.12);
}

.day-card.fora-mes {
    opacity: 0.38;
    background: #f4f5f7;
}

/* ---- Número do dia ---- */
.day-num-wrap {
    display: flex;
    justify-content: flex-end;
    padding-bottom: 6px;
    margin-bottom: 6px;
    border-bottom: 2px solid #f0f0f0;
    flex-shrink: 0;
}

.day-num {
    font-weight: 800;
    font-size: 1rem;
    color: #333;
    background: #f8f9fa;
    padding: 3px 10px;
    border-radius: 20px;
}

/* ---- Tarefa ---- */
.task-item {
    display: flex;
    align-items: flex-start;
    font-size: 0.75rem;
    margin-bottom: 6px;
    padding: 5px 6px;
    border-radius: 7px;
    background: #f8f9fa;
    transition: background 0.15s, transform 0.15s;
    flex-shrink: 0;
}

.task-item:hover {
    background: #e9ecef;
    transform: translateX(2px);
}

.task-box {
    border: 2px solid #dee2e6;
    width: 11px;
    height: 11px;
    min-width: 11px;
    margin-right: 7px;
    margin-top: 2px;
    border-radius: 3px;
}

.task-text {
    word-break: break-word;
    font-weight: 600;
    line-height: 1.35;
}

.mais-itens {
    font-size: 0.68rem;
    color: #6c757d;
    text-align: center;
    margin-top: 6px;
    font-weight: 600;
}

/* scrollbar fina */
.day-card::-webkit-scrollbar { width: 4px; }
.day-card::-webkit-scrollbar-track { background: #f1f3f5; border-radius: 4px; }
.day-card::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #667eea, #764ba2);
    border-radius: 4px;
}

/* botões de navegação */
.stButton button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white !important;
    border: none !important;
    padding: 10px 22px;
    border-radius: 25px;
    font-weight: 600;
    font-size: 0.95rem;
    transition: all 0.25s ease;
    box-shadow: 0 4px 14px rgba(102,126,234,0.4);
}
.stButton button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 22px rgba(102,126,234,0.55);
}
</style>
""", unsafe_allow_html=True)


# ====================================================================
# RENDERIZAÇÃO
# ====================================================================
ano, mes = st.session_state.ano, st.session_state.mes

# --- Navegação (usa st.columns apenas para os botões — não interfere no grid) ---
c1, c2, c3 = st.columns([1, 4, 1])
with c1:
    if st.button("◀ Mês Anterior"):
        if mes == 1:
            st.session_state.mes, st.session_state.ano = 12, ano - 1
        else:
            st.session_state.mes -= 1
        st.rerun()
with c2:
    st.markdown(f'<p class="planner-title">{MESES_PT[mes]} {ano}</p>', unsafe_allow_html=True)
with c3:
    if st.button("Próximo Mês ▶"):
        if mes == 12:
            st.session_state.mes, st.session_state.ano = 1, ano + 1
        else:
            st.session_state.mes += 1
        st.rerun()

# ----------------------------------------------------------------
# Grid do calendário — HTML puro, um único st.markdown por semana
# ----------------------------------------------------------------
cal_obj = calendar.Calendar(firstweekday=0)
semanas = cal_obj.monthdatescalendar(ano, mes)

# Cabeçalho dos dias da semana
header_html = '<div class="cal-grid">'
for i, nome in enumerate(DIAS_SEMANA):
    header_html += (
        f'<div class="dow-label" style="color:{CORES_SEMANA[i]};">{nome}</div>'
    )
header_html += "</div>"

st.markdown(f'<div class="planner-wrap">{header_html}', unsafe_allow_html=True)

for semana in semanas:
    row_html = '<div class="cal-grid">'
    for i, dia in enumerate(semana):
        no_mes = dia.month == mes
        ativs  = atividades_do_dia(dia)
        borda  = f"border-top: 4px solid {CORES_SEMANA[i]};" if no_mes else f"border-top: 4px solid #E9ECEF;"
        classe = "day-card" if no_mes else "day-card fora-mes"

        tasks_html = ""
        for a in ativs[:MAX_ATIVIDADES_DIA]:
            tasks_html += (
                f'<div class="task-item">'
                f'<div class="task-box"></div>'
                f'<div class="task-text" style="color:{a["cor"]};">{a["atividade"]}</div>'
                f'</div>'
            )
        if len(ativs) > MAX_ATIVIDADES_DIA:
            tasks_html += (
                f'<div class="mais-itens">+{len(ativs) - MAX_ATIVIDADES_DIA} itens</div>'
            )

        row_html += (
            f'<div class="{classe}" style="{borda}">'
            f'  <div class="day-num-wrap"><span class="day-num">{dia.day}</span></div>'
            f'  {tasks_html}'
            f'</div>'
        )
    row_html += "</div>"
    st.markdown(row_html, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)   # fecha planner-wrap
