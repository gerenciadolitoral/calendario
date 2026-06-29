"""
Painel de Atividades - GR Litoral / Itapipoca
Calendário mensal (clique no dia -> visão semanal estilo planner)
Fonte: Google Sheets (CSV público) - Col A = data, Col E = atividade, a partir da linha 7
"""

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

DIAS_SEMANA = ["SEGUNDA", "TERÇA", "QUARTA", "QUINTA", "SEXTA", "SÁBADO", "DOMINGO"]
MESES_PT = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
MAX_ATIVIDADES_DIA = 10

# Categorias por palavra-chave -> (cor, ordem de prioridade na busca)
CATEGORIAS = [
    ("Reunião",          ["reunião", "reuniao", "encontro"],                       "#4A90D9"),
    ("Mobilização",      ["mobilização", "mobilizacao"],                           "#E67E22"),
    ("Publicação/Story", ["publicar", "publicação", "publicacao", "story", "post", "reels", "matéria", "materia"], "#9B59B6"),
    ("Gravação",         ["gravação", "gravacao", "vídeo", "video"],                "#1ABC9C"),
    ("Faturamento",      ["faturamento", "leitura", "hidrômetro", "hidrometro"],    "#27AE60"),
    ("Instrumentação",   ["instrumentação", "instrumentacao", "piezômetro", "piezometro", "percolação", "percolacao"], "#16A085"),
    ("Monitoramento",    ["monitoramento", "captação", "captacao", "perenização", "perenizacao", "sigerh"], "#2980B9"),
    ("Vistoria/Fiscaliz.", ["vistoria", "fiscalização", "fiscalizacao", "inspeção", "inspecao"], "#C0392B"),
    ("Coleta/Água",      ["coleta", "análise qualitativa", "analise qualitativa", "sonda"], "#3498DB"),
    ("Diárias/Admin.",   ["diária", "diaria", "protheus", "estoque", "frota", "almoxarifado", "combustível", "combustivel"], "#7F8C8D"),
    ("Relatório/Ata",    ["relatório", "relatorio", "ata", "parecer", "diagnóstico", "diagnostico"], "#8E44AD"),
    ("Capacitação",      ["capacitação", "capacitacao", "curso", "treinamento", "oficina"], "#D35400"),
    ("Feriado/Data",     ["feriado", "ponto facultativo", "data magna", "carnaval", "sexta-feira santa"], "#BDC3C7"),
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

    # Linha 7 da planilha = índice 6 (0-based)
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


def gerar_observacoes_key(dia: date) -> str:
    return f"obs_{dia.isoformat()}"


# ---------------- ESTADO ----------------
st.set_page_config(page_title="Painel GR Litoral", layout="wide")

hoje = date.today()
if "ano" not in st.session_state:
    st.session_state.ano = hoje.year
if "mes" not in st.session_state:
    st.session_state.mes = hoje.month
if "view" not in st.session_state:
    st.session_state.view = "mes"
if "semana_ref" not in st.session_state:
    st.session_state.semana_ref = hoje
if "observacoes" not in st.session_state:
    st.session_state.observacoes = {}

try:
    df = carregar_dados()
except Exception as e:
    st.error(f"Erro ao carregar a planilha: {e}")
    st.stop()


def atividades_do_dia(dia: date):
    return df[df["data"] == dia].to_dict("records")


# ---------------- ESTILO ----------------
FONTE = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif"

st.markdown(f"""
<style>
* {{ font-family: {FONTE} !important; }}

.cal-header {{background:#1c1c1c; color:white; padding:14px 18px; border-radius:8px 8px 0 0;
             display:flex; justify-content:space-between; align-items:center;
             font-family:{FONTE};}}
.cal-title {{font-size:1.6rem; font-weight:800; letter-spacing:1px; margin:0;}}

.dia-semana-label {{text-align:center; font-weight:800; padding:6px; border-radius:6px;
                    margin-bottom:4px; font-size:0.8rem; font-family:{FONTE};}}

.day-card {{
    border:2px solid #ddd; border-radius:6px; padding:6px;
    height:170px; overflow-y:auto; box-sizing:border-box;
    font-family:{FONTE};
}}
.day-num {{font-weight:700; font-size:0.95rem; margin-bottom:4px; font-family:{FONTE};}}

.week-card {{
    border:1px solid #ccc; border-radius:0 0 6px 6px;
    padding:6px; box-sizing:border-box;
    height:420px; overflow-y:auto;
    font-family:{FONTE};
}}
.week-card-hoje {{ border:3px solid #F5A623; }}

.week-header {{
    text-align:center; padding:6px; border-radius:6px 6px 0 0;
    font-weight:800; color:white; font-family:{FONTE};
}}
.week-header .data-sub {{ font-size:0.75rem; font-weight:600; }}

.atividade-pill {{
    border-radius:5px; padding:4px 7px; margin-bottom:4px;
    font-size:0.72rem; line-height:1.3; color:white;
    word-wrap:break-word; overflow-wrap:break-word;
    font-family:{FONTE};
}}
.sem-atividade {{ font-size:0.72rem; color:#999; font-style:italic; font-family:{FONTE};}}
.mais-info {{ font-size:0.68rem; color:#888; font-family:{FONTE}; }}
</style>
""", unsafe_allow_html=True)


# ====================================================================
# VISÃO MENSAL
# ====================================================================
def render_mes():
    ano, mes = st.session_state.ano, st.session_state.mes

    st.markdown(f"""
    <div class="cal-header">
        <div class="cal-title">📅 MINHA SEMANA / MÊS</div>
        <div style="font-size:20px; font-weight:700; background:#F5A623; padding:6px 18px; border-radius:6px;">
            {MESES_PT[mes].upper()} / {ano}
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns([1, 1, 4, 1, 1])
    with c1:
        if st.button("◀ Ano"):
            st.session_state.ano -= 1
            st.rerun()
    with c2:
        if st.button("◀ Mês"):
            if mes == 1:
                st.session_state.mes, st.session_state.ano = 12, ano - 1
            else:
                st.session_state.mes -= 1
            st.rerun()
    with c4:
        if st.button("Mês ▶"):
            if mes == 12:
                st.session_state.mes, st.session_state.ano = 1, ano + 1
            else:
                st.session_state.mes += 1
            st.rerun()
    with c5:
        if st.button("Ano ▶"):
            st.session_state.ano += 1
            st.rerun()

    cores_semana = ["#F4D03F", "#5DADE2", "#F0B27A", "#52BE80", "#5DADE2", "#EC7063", "#A569BD"]
    cols = st.columns(7)
    for i, dia_nome in enumerate(DIAS_SEMANA):
        cols[i].markdown(
            f'<div class="dia-semana-label" style="background:{cores_semana[i]};color:white;">{dia_nome}</div>',
            unsafe_allow_html=True)

    cal = calendar.Calendar(firstweekday=0)  # segunda = 0
    semanas = cal.monthdatescalendar(ano, mes)

    for semana in semanas:
        cols = st.columns(7)
        for i, dia in enumerate(semana):
            with cols[i]:
                no_mes = dia.month == mes
                ativs = atividades_do_dia(dia)
                borda = "#F5A623" if dia == hoje else "#ddd"
                opacidade = "1" if no_mes else "0.35"

                pills_html = ""
                for a in ativs[:MAX_ATIVIDADES_DIA]:
                    texto = a["atividade"][:60] + ("…" if len(a["atividade"]) > 60 else "")
                    pills_html += f'<div class="atividade-pill" style="background:{a["cor"]};">{texto}</div>'
                if len(ativs) > MAX_ATIVIDADES_DIA:
                    pills_html += f'<div class="mais-info">+{len(ativs)-MAX_ATIVIDADES_DIA} mais</div>'

                # Bloco único de HTML - nada fragmentado, nada solto fora da div
                card_html = (
                    f'<div class="day-card" style="border-color:{borda}; opacity:{opacidade};">'
                    f'<div class="day-num">{dia.day}</div>'
                    f'{pills_html}'
                    f'</div>'
                )
                st.markdown(card_html, unsafe_allow_html=True)

                label_btn = "Abrir ›" if ativs else "·"
                if st.button(label_btn, key=f"btn_{dia.isoformat()}", use_container_width=True):
                    st.session_state.semana_ref = dia
                    st.session_state.view = "semana"
                    st.rerun()

    # Legenda
    with st.expander("🎨 Legenda de categorias"):
        leg_cols = st.columns(4)
        for idx, (nome, _, cor) in enumerate(CATEGORIAS):
            with leg_cols[idx % 4]:
                st.markdown(
                    f'<span style="background:{cor};color:white;padding:2px 8px;border-radius:4px;font-size:12px;">{nome}</span>',
                    unsafe_allow_html=True)


# ====================================================================
# VISÃO SEMANAL (estilo "Minha Semana")
# ====================================================================
def render_semana():
    ref = st.session_state.semana_ref
    inicio_semana = ref - timedelta(days=ref.weekday())  # segunda
    dias = [inicio_semana + timedelta(days=i) for i in range(7)]

    c1, c2, c3 = st.columns([1, 5, 1])
    with c1:
        if st.button("◀ Voltar ao mês"):
            st.session_state.view = "mes"
            st.rerun()
    with c2:
        st.markdown(
            f"<h2 style='text-align:center;'>MINHA SEMANA — {inicio_semana.strftime('%d/%m')} a {dias[-1].strftime('%d/%m/%Y')}</h2>",
            unsafe_allow_html=True)
    with c3:
        nav1, nav2 = st.columns(2)
        with nav1:
            if st.button("◀"):
                st.session_state.semana_ref = ref - timedelta(days=7)
                st.rerun()
        with nav2:
            if st.button("▶"):
                st.session_state.semana_ref = ref + timedelta(days=7)
                st.rerun()

    cores_semana = ["#F4D03F", "#5DADE2", "#F0B27A", "#52BE80", "#5DADE2", "#EC7063", "#A569BD"]
    cols = st.columns(7)

    for i, dia in enumerate(dias):
        with cols[i]:
            classe_extra = " week-card-hoje" if dia == hoje else ""

            ativs = atividades_do_dia(dia)
            pills_html = ""
            if not ativs:
                pills_html = '<div class="sem-atividade">Sem atividades</div>'
            else:
                for a in ativs[:MAX_ATIVIDADES_DIA]:
                    pills_html += f'<div class="atividade-pill" style="background:{a["cor"]};">{a["atividade"]}</div>'
                if len(ativs) > MAX_ATIVIDADES_DIA:
                    pills_html += f'<div class="mais-info">+{len(ativs)-MAX_ATIVIDADES_DIA} atividades não exibidas</div>'

            # Header + corpo do card num único bloco HTML (sem widgets nativos misturados)
            bloco_html = (
                f'<div class="week-header" style="background:{cores_semana[i]};">'
                f'{DIAS_SEMANA[i]}<br><span class="data-sub">{dia.strftime("%d/%m")}</span>'
                f'</div>'
                f'<div class="week-card{classe_extra}">{pills_html}</div>'
            )
            st.markdown(bloco_html, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📝 Observações da semana")
    chave = gerar_observacoes_key(inicio_semana)
    valor_atual = st.session_state.observacoes.get(chave, "")
    novo_valor = st.text_area("Anotações, lembretes ou pendências desta semana:",
                               value=valor_atual, height=120, key=f"ta_{chave}")
    st.session_state.observacoes[chave] = novo_valor
    st.caption("⚠️ Observações ficam salvas apenas durante esta sessão do navegador.")


# ---------------- ROTEAMENTO ----------------
if st.session_state.view == "mes":
    render_mes()
else:
    render_semana()
