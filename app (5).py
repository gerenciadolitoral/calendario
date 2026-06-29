import streamlit as st
import pandas as pd
import calendar
from datetime import date, timedelta
import requests
from io import StringIO

# ---------------- CONFIG ----------------
SHEET_ID = "1kte6Ys9vgzw7a0Z1PDXkxf6VOX9KHWlRCXp7P-7RSi4"
GID = "507430155"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

DIAS_SEMANA = ["SEGUNDA", "TERÇA", "QUARTA", "QUINTA", "SEXTA", "SÁBADO", "DOMINGO"]
MESES_PT = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
MAX_ATIVIDADES_DIA = 5

CATEGORIAS = [
    ("Reunião",          ["reunião", "reuniao", "encontro"],                       "#4A90D9"),
    ("Mobilização",      ["mobilização", "mobilizacao"],                           "#E67E22"),
    ("Publicação/Story", ["publicar", "publicação", "publicacao", "story", "post"], "#9B59B6"),
    ("Gravação",         ["gravação", "gravacao", "vídeo", "video"],                "#1ABC9C"),
    ("Faturamento",      ["faturamento", "leitura", "hidrômetro", "hidrometro"],    "#27AE60"),
    ("Instrumentação",   ["instrumentação", "instrumentacao", "piezômetro"],        "#16A085"),
    ("Monitoramento",    ["monitoramento", "captação", "captacao", "perenização"],  "#2980B9"),
    ("Vistoria/Fiscaliz.", ["vistoria", "fiscalização", "fiscalizacao", "inspeção"], "#C0392B"),
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
st.set_page_config(page_title="Painel de Atividades", layout="wide", initial_sidebar_state="collapsed")

hoje = date.today()
for key in ["ano", "mes", "view", "semana_ref"]:
    if key not in st.session_state:
        st.session_state[key] = hoje.year if key == "ano" else (hoje.month if key == "mes" else ("mes" if key == "view" else hoje))

if "observacoes" not in st.session_state:
    st.session_state.observacoes = {}

try:
    df = carregar_dados()
except Exception as e:
    st.error(f"Erro ao carregar a base de dados: {e}")
    st.stop()

def atividades_do_dia(dia: date):
    return df[df["data"] == dia].to_dict("records")

# ---------------- ESTILO VISUAL (UI/UX) ----------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    * { font-family: 'Inter', sans-serif !important; }
    
    /* Cabeçalho */
    .cal-header {
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        color: white; padding: 20px 24px; border-radius: 12px;
        display: flex; justify-content: space-between; align-items: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); margin-bottom: 20px;
    }
    .cal-title { font-size: 1.4rem; font-weight: 700; letter-spacing: 0.5px; margin: 0; }
    .cal-badge { background: #3b82f6; font-size: 1.1rem; padding: 6px 16px; border-radius: 8px; font-weight: 600; }

    /* Dias da Semana */
    .dia-semana-label {
        text-align: center; font-weight: 600; padding: 10px; border-radius: 8px;
        margin-bottom: 8px; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    /* Cartões Mensais */
    .day-card {
        background: #ffffff; border: 1px solid #e5e7eb; border-radius: 10px; padding: 10px;
        height: 160px; overflow-y: auto; box-sizing: border-box;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05); transition: all 0.2s ease;
    }
    .day-card:hover { transform: translateY(-2px); box-shadow: 0 6px 12px rgba(0,0,0,0.1); border-color: #d1d5db; }
    .day-num { font-weight: 700; font-size: 1.1rem; color: #374151; margin-bottom: 8px; }

    /* Pílulas de Atividades */
    .atividade-pill {
        border-radius: 6px; padding: 6px 8px; margin-bottom: 6px;
        font-size: 0.75rem; font-weight: 500; line-height: 1.2; color: white;
        box-shadow: inset 0 -2px 0 rgba(0,0,0,0.15); transition: opacity 0.2s;
    }
    .atividade-pill:hover { opacity: 0.9; cursor: default; }
    
    .sem-atividade { font-size: 0.8rem; color: #9ca3af; font-style: italic; text-align: center; margin-top: 20px;}
    .mais-info { font-size: 0.7rem; color: #6b7280; font-weight: 600; text-align: center; margin-top: 4px; }
    
    /* Ocultar barra de rolagem (Estética) */
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# ====================================================================
# VISÃO MENSAL
# ====================================================================
def render_mes():
    ano, mes = st.session_state.ano, st.session_state.mes

    st.markdown(f"""
    <div class="cal-header">
        <div class="cal-title">📅 VISÃO GERAL</div>
        <div class="cal-badge">{MESES_PT[mes].upper()} / {ano}</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns([1, 1, 4, 1, 1])
    with c1:
        if st.button("⏪ Ano"): st.session_state.ano -= 1; st.rerun()
    with c2:
        if st.button("◀ Mês"):
            st.session_state.mes, st.session_state.ano = (12, ano - 1) if mes == 1 else (mes - 1, ano)
            st.rerun()
    with c4:
        if st.button("Mês ▶"):
            st.session_state.mes, st.session_state.ano = (1, ano + 1) if mes == 12 else (mes + 1, ano)
            st.rerun()
    with c5:
        if st.button("Ano ⏩"): st.session_state.ano += 1; st.rerun()

    st.write("") # Espaçamento

    # Paleta de cores mais suave para os cabeçalhos dos dias
    cores_semana = ["#cbd5e1", "#cbd5e1", "#cbd5e1", "#cbd5e1", "#cbd5e1", "#fca5a5", "#fca5a5"]
    
    cols = st.columns(7)
    for i, dia_nome in enumerate(DIAS_SEMANA):
        cor_texto = "#334155" if i < 5 else "#991b1b"
        cols[i].markdown(f'<div class="dia-semana-label" style="background:{cores_semana[i]};color:{cor_texto};">{dia_nome}</div>', unsafe_allow_html=True)

    cal = calendar.Calendar(firstweekday=0)
    for semana in cal.monthdatescalendar(ano, mes):
        cols = st.columns(7)
        for i, dia in enumerate(semana):
            with cols[i]:
                no_mes = dia.month == mes
                ativs = atividades_do_dia(dia)
                
                # Destaque para o dia de hoje
                is_today = (dia == hoje)
                borda = "border: 2px solid #3b82f6;" if is_today else ""
                bg_hoje = "background: #eff6ff;" if is_today else ""
                opacidade = "1" if no_mes else "0.4"

                pills_html = "".join([f'<div class="atividade-pill" style="background:{a["cor"]};" title="{a["atividade"]}">{a["atividade"][:45] + ("…" if len(a["atividade"])>45 else "")}</div>' for a in ativs[:MAX_ATIVIDADES_DIA]])
                if len(ativs) > MAX_ATIVIDADES_DIA:
                    pills_html += f'<div class="mais-info">+{len(ativs)-MAX_ATIVIDADES_DIA} mais</div>'

                st.markdown(f'<div class="day-card" style="{borda} {bg_hoje} opacity:{opacidade};"><div class="day-num">{dia.day}</div>{pills_html}</div>', unsafe_allow_html=True)

                if st.button("Expandir", key=f"btn_{dia}", use_container_width=True):
                    st.session_state.semana_ref = dia
                    st.session_state.view = "semana"
                    st.rerun()

# ====================================================================
# VISÃO SEMANAL
# ====================================================================
def render_semana():
    ref = st.session_state.semana_ref
    inicio = ref - timedelta(days=ref.weekday())
    dias = [inicio + timedelta(days=i) for i in range(7)]

    c1, c2, c3 = st.columns([1, 5, 1])
    with c1:
        if st.button("← Voltar ao Calendário"):
            st.session_state.view = "mes"
            st.rerun()
    with c2:
        st.markdown(f"""
        <div class="cal-header" style="justify-content: center; background: linear-gradient(135deg, #374151 0%, #1f2937 100%);">
            <div class="cal-title">PLANEJAMENTO SEMANAL: {inicio.strftime('%d/%m')} a {dias[-1].strftime('%d/%m/%Y')}</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        n1, n2 = st.columns(2)
        if n1.button("◀"): st.session_state.semana_ref = ref - timedelta(days=7); st.rerun()
        if n2.button("▶"): st.session_state.semana_ref = ref + timedelta(days=7); st.rerun()

    cols = st.columns(7)
    for i, dia in enumerate(dias):
        with cols[i]:
            is_today = (dia == hoje)
            borda = "border: 2px solid #3b82f6;" if is_today else "border: 1px solid #e5e7eb;"
            
            st.markdown(f'<div class="dia-semana-label" style="background: {"#3b82f6" if is_today else "#e2e8f0"}; color: {"white" if is_today else "#334155"};">{DIAS_SEMANA[i]}<br><span style="font-size:1.1rem;">{dia.day}</span></div>', unsafe_allow_html=True)
            
            ativs = atividades_do_dia(dia)
            pills_html = '<div class="sem-atividade">Livre</div>' if not ativs else "".join([f'<div class="atividade-pill" style="background:{a["cor"]}; padding: 10px; font-size: 0.85rem;">{a["atividade"]}</div>' for a in ativs])
            
            st.markdown(f'<div class="day-card" style="height: 500px; {borda}">{pills_html}</div>', unsafe_allow_html=True)

# ---------------- ROTEAMENTO ----------------
if st.session_state.view == "mes":
    render_mes()
else:
    render_semana()
