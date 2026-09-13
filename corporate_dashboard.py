"""
Corporate Executive Dashboard
=================================
Streamlit application with a pure corporate executive design.
Paleta azul profissional, sem emojis, layout wide, dados fictícios cacheados.

Execução:
    python -m streamlit run corporate_dashboard.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ─────────────────────────────────────────────────────────────────────────────
# 1. CONFIGURAÇÃO DE PÁGINA — deve ser a primeira chamada Streamlit
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Corporate Analytics | Executive Dashboard",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# 2. DESIGN TOKENS — paleta corporativa baseada em tons de azul
# ─────────────────────────────────────────────────────────────────────────────
BLUE_DARK   = "#1E3A8A"   # Azul Marinho Escuro — elementos principais / bordas de destaque
BLUE_ROYAL  = "#3B82F6"   # Azul Royal Corporativo — série primária dos gráficos
BLUE_MID    = "#2563EB"   # Azul intermediário — série secundária
BLUE_LIGHT  = "#93C5FD"   # Azul Claro — destaques de dados / barras de comparação
BLUE_PALE   = "#DBEAFE"   # Azul muito suave — preenchimento de área / hover
BG_PAGE     = "#F8FAFC"   # Cinza Claro Azulado — fundo da página
BG_WHITE    = "#FFFFFF"   # Branco Puro — containers / cards / sidebar
TEXT_DARK   = "#0F172A"   # Grafite escuro — texto principal
TEXT_MID    = "#475569"   # Slate — texto secundário / labels
BORDER_CLR  = "#E2E8F0"   # Borda suave — separadores

# Paleta sequencial para gráficos com múltiplas séries
CHART_COLORS = [BLUE_ROYAL, BLUE_MID, "#60A5FA", BLUE_DARK, BLUE_LIGHT, "#1D4ED8"]

# Data de referência simulada para o cabeçalho
DATA_ATUALIZACAO = "12 de setembro de 2024"

# ─────────────────────────────────────────────────────────────────────────────
# 3. CSS GLOBAL — injeção via Markdown para cobertura total da UI
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
  /* Importação da fonte Inter — tipografia corporativa neutra */
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

  html, body, [class*="css"] {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    color: {TEXT_DARK};
  }}

  /* ── Fundo da página ── */
  .stApp {{
    background-color: {BG_PAGE};
  }}

  /* ── Sidebar — fundo branco com divisor vertical ── */
  section[data-testid="stSidebar"] {{
    background-color: {BG_WHITE};
    border-right: 1px solid {BORDER_CLR};
    box-shadow: 2px 0 8px rgba(15,23,42,.04);
  }}
  section[data-testid="stSidebar"] .stMarkdown p {{
    color: {TEXT_MID};
    font-size: 12px;
  }}

  /* ── Padding do conteúdo principal ── */
  .block-container {{
    padding-top: 1.5rem;
    padding-bottom: 2.5rem;
    max-width: 100% !important;
  }}

  /* ── Botões primários ── */
  .stButton > button {{
    background-color: {BLUE_DARK} !important;
    color: {BG_WHITE} !important;
    border: none !important;
    border-radius: 6px !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.4rem !important;
    letter-spacing: .2px !important;
    transition: background-color .18s ease, box-shadow .18s ease;
    box-shadow: 0 1px 3px rgba(15,23,42,.12);
  }}
  .stButton > button:hover {{
    background-color: {BLUE_ROYAL} !important;
    box-shadow: 0 2px 8px rgba(30,58,138,.25) !important;
  }}

  /* ── Botão de download — estilo secundário (outline) ── */
  .stDownloadButton > button {{
    background-color: {BG_WHITE} !important;
    color: {BLUE_DARK} !important;
    border: 1.5px solid {BLUE_DARK} !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    letter-spacing: .2px !important;
    transition: all .18s ease;
    box-shadow: 0 1px 2px rgba(15,23,42,.06);
  }}
  .stDownloadButton > button:hover {{
    background-color: {BLUE_PALE} !important;
    border-color: {BLUE_ROYAL} !important;
    color: {BLUE_ROYAL} !important;
  }}

  /* ── Dataframe — borda, radius, hover refinado ── */
  .stDataFrame > div {{
    border: 1px solid {BORDER_CLR};
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(15,23,42,.05);
  }}
  .stDataFrame > div > div > div > table thead th {{
    background: {BG_PAGE} !important;
    color: {TEXT_MID} !important;
    font-weight: 600 !important;
    font-size: 11px !important;
    letter-spacing: .5px !important;
    text-transform: uppercase !important;
    border-bottom: 2px solid {BORDER_CLR} !important;
    padding: 10px 14px !important;
  }}
  .stDataFrame > div > div > div > table tbody td {{
    color: {TEXT_DARK} !important;
    font-size: 12.5px !important;
    padding: 9px 14px !important;
    border-bottom: 1px solid {BORDER_CLR} !important;
  }}
  .stDataFrame > div > div > div > table tbody tr:hover td {{
    background: {BLUE_PALE} !important;
  }}
  .stDataFrame > div > div > div > table tbody tr:last-child td {{
    border-bottom: none !important;
  }}

  /* ── Inputs e selects na sidebar ── */
  .stSelectbox label, .stMultiSelect label,
  .stDateInput label, .stNumberInput label {{
    color: {TEXT_DARK} !important;
    font-size: 12px !important;
    font-weight: 600 !important;
  }}

  /* ── Radio na sidebar — opções visíveis ── */
  div[data-testid="stRadio"] div[role="radiogroup"] label p {{
    color: {TEXT_DARK} !important;
    font-size: 13px !important;
    font-weight: 400 !important;
    margin: 0 !important;
  }}
  div[data-testid="stRadio"] div[role="radiogroup"] label {{
    gap: 8px !important;
    padding: 5px 0 !important;
  }}

  /* ── Divisor horizontal padrão ── */
  hr {{
    border: none;
    border-top: 1px solid {BORDER_CLR};
    margin: 0.5rem 0 1rem;
  }}

  /* ── Títulos de seção da sidebar ── */
  .sb-title {{
    font-size: 10px;
    font-weight: 700;
    color: {TEXT_MID};
    text-transform: uppercase;
    letter-spacing: .7px;
    padding: 14px 0 6px;
    border-bottom: 1px solid {BORDER_CLR};
    margin-bottom: 8px;
  }}

  /* ── Container branco genérico ── */
  .white-card {{
    background: {BG_WHITE};
    border: 1px solid {BORDER_CLR};
    border-radius: 8px;
    padding: 20px 22px;
    box-shadow: 0 1px 3px rgba(15,23,42,.06);
    margin-bottom: 1rem;
  }}

  /* ── Section header — refinado ── */
  .sec-hdr {{
    font-size: 11px;
    font-weight: 700;
    color: {TEXT_MID};
    text-transform: uppercase;
    letter-spacing: .6px;
    padding-bottom: 8px;
    border-bottom: 2px solid {BLUE_DARK};
    margin: 1.75rem 0 1rem;
    display: inline-block;
  }}
  .sec-hdr-sm {{
    font-size: 10.5px;
    font-weight: 700;
    color: {TEXT_MID};
    text-transform: uppercase;
    letter-spacing: .7px;
    padding-bottom: 6px;
    border-bottom: 1px solid {BORDER_CLR};
    margin: 1.25rem 0 .75rem;
    display: inline-block;
  }}

  /* ── KPI card — refinado ── */
  .kpi-card {{
    background: {BG_WHITE};
    border: 1px solid {BORDER_CLR};
    border-top: 4px solid {BLUE_DARK};
    border-radius: 8px;
    padding: 18px 22px 16px;
    box-shadow: 0 1px 4px rgba(15,23,42,.07);
    transition: border-color .15s, box-shadow .15s;
  }}
  .kpi-card:hover {{
    border-color: {BLUE_LIGHT};
    box-shadow: 0 2px 8px rgba(15,23,42,.10);
  }}
  .kpi-label {{
    font-size: 10.5px;
    font-weight: 700;
    color: {TEXT_MID};
    text-transform: uppercase;
    letter-spacing: .7px;
    margin-bottom: 10px;
  }}
  .kpi-value {{
    font-size: 30px;
    font-weight: 700;
    color: {TEXT_DARK};
    line-height: 1;
    margin-bottom: 6px;
    letter-spacing: -.5px;
  }}
  .kpi-sub {{ font-size: 11px; font-weight: 500; color: {TEXT_MID}; }}
  .kpi-info .kpi-value {{ color: {BLUE_ROYAL}; }}
  .kpi-success .kpi-value {{ color: "#16A34A"; }}
  .kpi-danger .kpi-value {{ color: "#DC2626"; }}

  /* ── Empty state ── */
  .empty-state {{
    background: {BG_WHITE};
    border: 1px solid {BORDER_CLR};
    border-radius: 8px;
    padding: 36px 20px;
    text-align: center;
    color: {TEXT_MID};
    margin: 2rem 0;
  }}
  .empty-state strong {{
    color: {TEXT_DARK};
    font-size: 14px;
    display: block;
    margin-bottom: 6px;
  }}

  /* ── Tabs ── */
  div[data-testid="stTabs"] button[role="tab"] {{
    color: {TEXT_MID} !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    background: transparent !important;
    padding: 8px 16px !important;
    border-radius: 6px 6px 0 0 !important;
  }}
  div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {{
    color: {BLUE_DARK} !important;
    font-weight: 600 !important;
    background: {BG_WHITE} !important;
  }}

  /* ── Alertas ── */
  div[data-testid="stAlert"][data-baseweb="notification"] {{
    border-radius: 8px !important;
  }}

  /* ── Form container ── */
  div[data-testid="stForm"] {{
    background: {BG_WHITE} !important;
    border: 1px solid {BORDER_CLR} !important;
    border-radius: 8px !important;
    padding: 1.25rem !important;
    box-shadow: 0 1px 3px rgba(15,23,42,.05) !important;
  }}

  /* ── Link buttons ── */
  a[data-testid="stLinkButton"] > button {{
    background-color: {BG_WHITE} !important;
    color: {BLUE_DARK} !important;
    border: 1.5px solid {BLUE_DARK} !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    font-size: 12px !important;
    transition: all .18s;
  }}
  a[data-testid="stLinkButton"] > button:hover {{
    background-color: {BLUE_PALE} !important;
    border-color: {BLUE_ROYAL} !important;
    color: {BLUE_ROYAL} !important;
  }}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# 4. GERACAO DE DADOS FICTICIOS COM CACHE
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner="Carregando base de dados corporativa...")
def carregar_dados() -> pd.DataFrame:
    rng = np.random.default_rng(seed=42)

    meses     = pd.date_range("2023-01-01", "2024-12-01", freq="MS")
    regioes   = ["Norte", "Sul", "Leste", "Oeste"]
    unidades  = ["Varejo", "Corporativo", "Industrial"]

    base_receita = {"Varejo": 1_200_000, "Corporativo": 2_100_000, "Industrial": 1_700_000}
    peso_regiao  = {"Norte": 0.85, "Sul": 1.22, "Leste": 1.10, "Oeste": 0.92}
    sazo = {
        1: 0.91, 2: 0.94, 3: 0.97, 4: 1.00,
        5: 1.02, 6: 1.04, 7: 1.03, 8: 1.05,
        9: 1.07, 10: 1.09, 11: 1.11, 12: 1.15,
    }

    n_periodos = len(meses)
    registros  = []

    for i, mes in enumerate(meses):
        fator_crescimento = 1.0 + (i / n_periodos) * 0.15
        for ub in unidades:
            for reg in regioes:
                base = base_receita[ub] * peso_regiao[reg]
                receita = (
                    base
                    * fator_crescimento
                    * sazo[mes.month]
                    * (1.0 + rng.normal(0, 0.048))
                )
                meta      = receita * (1.0 + rng.uniform(0.05, 0.12))
                margem    = rng.uniform(18.0, 38.0)
                clientes  = max(int(receita / 44_000 + rng.normal(0, 2.5)), 1)
                negocios  = max(int(clientes * rng.uniform(0.28, 0.58)), 0)

                registros.append({
                    "Data":            mes,
                    "Ano":             mes.year,
                    "Mes":             mes.month,
                    "Periodo":         mes.strftime("%b %Y"),
                    "Regiao":          reg,
                    "Unidade_Negocio": ub,
                    "Receita":         round(receita, 2),
                    "Meta":            round(meta, 2),
                    "Margem_Pct":      round(margem, 2),
                    "Clientes_Ativos": clientes,
                    "Negociacoes":     negocios,
                })

    df = pd.DataFrame(registros)
    df["Atingimento_Pct"] = (df["Receita"] / df["Meta"] * 100).round(2)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 5. FUNCOES AUXILIARES
# ─────────────────────────────────────────────────────────────────────────────

def fmt_moeda(valor: float) -> str:
    if valor >= 1_000_000:
        return f"R$ {valor / 1_000_000:.2f}M"
    if valor >= 1_000:
        return f"R$ {valor / 1_000:.1f}K"
    return f"R$ {valor:,.0f}"


def fmt_pct(valor: float, casas: int = 1) -> str:
    return f"{valor:.{casas}f}%"


def kpi_card(col, titulo: str, valor: str, legenda: str, cor_legenda: str = None) -> None:
    cor = cor_legenda or TEXT_MID
    col.markdown(f"""
    <div class="kpi-card">
      <div class="kpi-label">{titulo}</div>
      <div class="kpi-value">{valor}</div>
      <div class="kpi-sub" style="color:{cor};">{legenda}</div>
    </div>
    """, unsafe_allow_html=True)


def aplicar_layout_plotly(fig: go.Figure, height: int = 380) -> go.Figure:
    fig.update_layout(
        height=height,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=TEXT_DARK, size=12),
        margin=dict(l=4, r=4, t=40, b=4),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="right",  x=1,
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0,
            font=dict(size=11, color=TEXT_MID),
        ),
        xaxis=dict(
            gridcolor="rgba(0,0,0,0)",
            linecolor=BORDER_CLR,
            tickfont=dict(size=11, color=TEXT_MID),
            title_font=dict(size=12, color=TEXT_MID),
        ),
        yaxis=dict(
            gridcolor=BORDER_CLR,
            gridwidth=1,
            linecolor="rgba(0,0,0,0)",
            tickfont=dict(size=11, color=TEXT_MID),
            title_font=dict(size=12, color=TEXT_MID),
        ),
        hoverlabel=dict(
            bgcolor=BG_WHITE,
            bordercolor=BORDER_CLR,
            font=dict(size=12, color=TEXT_DARK),
        ),
    )
    return fig


def secao_titulo(titulo: str, descricao: str = "") -> None:
    desc_html = (
        f'<p style="font-size:13px;color:{TEXT_MID};margin:2px 0 0;">{descricao}</p>'
        if descricao else ""
    )
    st.markdown(f"""
    <div style="margin-bottom:.75rem;">
      <h2 style="font-size:15px;font-weight:700;color:{TEXT_DARK};
        margin:0;letter-spacing:-.2px;">{titulo}</h2>
      {desc_html}
    </div>
    <hr>
    """, unsafe_allow_html=True)


def container_grafico(conteudo_fn, *args, **kwargs) -> None:
    with st.container():
        st.markdown(f"""
        <div style="background:{BG_WHITE};border:1px solid {BORDER_CLR};
          border-radius:8px;padding:18px 18px 4px;
          box-shadow:0 1px 3px rgba(15,23,42,.05);margin-bottom:1rem;">
        """, unsafe_allow_html=True)
        conteudo_fn(*args, **kwargs)
        st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# 6. CARREGAMENTO DOS DADOS BASE
# ─────────────────────────────────────────────────────────────────────────────

df_base = carregar_dados()


# ─────────────────────────────────────────────────────────────────────────────
# 7. BARRA LATERAL — Logo, Navegacao e Filtros Globais
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:

    # Logo corporativo
    st.markdown(f"""
    <div style="padding:18px 0 16px;border-bottom:1px solid {BORDER_CLR};">
      <div style="
        background: linear-gradient(135deg, {BLUE_DARK} 0%, {BLUE_ROYAL} 100%);
        border-radius: 8px; padding: 14px 16px; text-align: center;
      ">
        <div style="font-size:13px;font-weight:700;color:{BG_WHITE};
          letter-spacing:.6px;line-height:1.2;">CORP ANALYTICS</div>
        <div style="font-size:10px;color:{BLUE_LIGHT};margin-top:3px;
          letter-spacing:.4px;font-weight:400;">Executive Intelligence Platform</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Menu de navegacao
    st.markdown(f'<div class="sb-title">Navegação</div>', unsafe_allow_html=True)
    pagina = st.radio(
        label="Selecione a página",
        options=[
            "Visão Geral",
            "Análise de Vendas",
            "Desempenho Regional",
            "Explorador de Dados",
        ],
        label_visibility="collapsed",
    )

    # Filtros Globais
    st.markdown(f'<div class="sb-title">Filtros Globais</div>', unsafe_allow_html=True)

    anos_disp = sorted(df_base["Ano"].unique().tolist())
    nomes_mes = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]

    col_a, col_b = st.columns(2)
    with col_a:
        ano_ini = st.selectbox("Ano início", anos_disp, index=0,               key="a_ini")
        mes_ini = st.selectbox("Mês início", range(1, 13),
                               format_func=lambda m: nomes_mes[m - 1],          key="m_ini")
    with col_b:
        ano_fim = st.selectbox("Ano fim",   anos_disp, index=len(anos_disp)-1, key="a_fim")
        mes_fim = st.selectbox("Mês fim",   range(1, 13),
                               format_func=lambda m: nomes_mes[m - 1],
                               index=11,                                         key="m_fim")

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    ubs_disp = sorted(df_base["Unidade_Negocio"].unique().tolist())
    ubs_sel = st.multiselect(
        "Unidade de Negócio",
        options=ubs_disp,
        default=ubs_disp,
        key="ubs",
    )

    regs_disp = sorted(df_base["Regiao"].unique().tolist())
    regs_sel = st.multiselect(
        "Região",
        options=regs_disp,
        default=regs_disp,
        key="regs",
    )

    # Rodape da sidebar
    st.markdown(f"""
    <div style="margin-top:24px;padding-top:14px;border-top:1px solid {BORDER_CLR};
      font-size:11px;color:{TEXT_MID};line-height:1.7;">
      <span style="font-weight:600;color:{TEXT_DARK};">Última atualização</span><br>
      {DATA_ATUALIZACAO}<br>
      <span style="color:{BLUE_ROYAL};font-weight:600;">v2.4.1</span>
      &nbsp;&middot;&nbsp; Corporate Analytics
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# 8. APLICACAO DOS FILTROS GLOBAIS
# ─────────────────────────────────────────────────────────────────────────────

data_ini_ts = pd.Timestamp(ano_ini, mes_ini, 1)
data_fim_ts = pd.Timestamp(ano_fim, mes_fim, 1)

_ubs  = ubs_sel  if ubs_sel  else ubs_disp
_regs = regs_sel if regs_sel else regs_disp

df = df_base[
    (df_base["Data"] >= data_ini_ts) &
    (df_base["Data"] <= data_fim_ts) &
    (df_base["Unidade_Negocio"].isin(_ubs)) &
    (df_base["Regiao"].isin(_regs))
].copy()


# ─────────────────────────────────────────────────────────────────────────────
# 9. CABECALHO PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

col_hdr, col_badge = st.columns([6, 1])
with col_hdr:
    st.markdown(f"""
    <div style="margin-bottom:1.25rem;">
      <h1 style="font-size:22px;font-weight:700;color:{TEXT_DARK};
        margin:0 0 4px;letter-spacing:-.5px;">{pagina}</h1>
      <p style="font-size:13px;color:{TEXT_MID};margin:0;">
        Corporate Analytics Platform
        &nbsp;&middot;&nbsp; Dados atualizados em {DATA_ATUALIZACAO}
      </p>
    </div>
    """, unsafe_allow_html=True)
with col_badge:
    st.markdown(f"""
    <div style="background:{BG_WHITE};border:1px solid {BORDER_CLR};
      border-radius:6px;padding:8px 14px;text-align:right;
      font-size:11px;color:{TEXT_MID};line-height:1.55;margin-top:4px;">
      <strong style="color:{TEXT_DARK};font-size:13px;">
        {len(df):,}
      </strong><br>registros filtrados
    </div>
    """, unsafe_allow_html=True)

st.markdown(f'<hr style="margin:0 0 1.5rem;">', unsafe_allow_html=True)

# Guard: sem dados
if df.empty:
    st.markdown(f"""
    <div class="empty-state">
      <strong>Nenhum dado encontrado</strong>
      <span>Ajuste o intervalo de datas ou os filtros de Unidade e Região na barra lateral.</span>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
# 10. FUNCAO DE EXPORTACAO CSV (reutilizada em todas as paginas)
# ─────────────────────────────────────────────────────────────────────────────

def botao_exportar(dataframe: pd.DataFrame, nome_arquivo: str = "export_corporativo.csv") -> None:
    csv_bytes = dataframe.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button(
        label="Exportar dados filtrados (CSV)",
        data=csv_bytes,
        file_name=nome_arquivo,
        mime="text/csv",
        use_container_width=True,
    )


# ═════════════════════════════════════════════════════════════════════════════
# PAGINA 1 — VISAO GERAL
# ═════════════════════════════════════════════════════════════════════════════
if pagina == "Visão Geral":

    # Computacao dos KPIs
    receita_total  = df["Receita"].sum()
    meta_total     = df["Meta"].sum()
    atingimento    = (receita_total / meta_total * 100) if meta_total > 0 else 0.0
    margem_media   = df["Margem_Pct"].mean()
    clientes_total = df["Clientes_Ativos"].sum()

    df_ant = df_base[
        (df_base["Data"] >= pd.Timestamp(ano_ini - 1, mes_ini, 1)) &
        (df_base["Data"] <= pd.Timestamp(max(ano_fim - 1, ano_ini - 1), mes_fim, 1)) &
        (df_base["Unidade_Negocio"].isin(_ubs)) &
        (df_base["Regiao"].isin(_regs))
    ]
    receita_ant = df_ant["Receita"].sum()
    var_receita  = ((receita_total / receita_ant) - 1) * 100 if receita_ant > 0 else 0.0
    margem_ant   = df_ant["Margem_Pct"].mean() if not df_ant.empty else margem_media
    var_margem   = margem_media - margem_ant

    # Linha de KPIs — 4 cards refinados
    k1, k2, k3, k4 = st.columns(4)

    seta_r = "+" if var_receita >= 0 else ""
    cor_r  = "#16A34A" if var_receita >= 0 else "#DC2626"
    kpi_card(k1, "Faturamento Total",
             fmt_moeda(receita_total),
             f"{seta_r}{fmt_pct(var_receita)} vs. ano anterior", cor_r)

    cor_a  = "#16A34A" if atingimento >= 90 else "#DC2626"
    kpi_card(k2, "Atingimento de Meta",
             fmt_pct(atingimento),
             f"Meta: {fmt_moeda(meta_total)}", cor_a)

    seta_m = "+" if var_margem >= 0 else ""
    cor_m  = "#16A34A" if var_margem >= 0 else "#DC2626"
    kpi_card(k3, "Margem Bruta Média",
             fmt_pct(margem_media),
             f"{seta_m}{fmt_pct(var_margem, 1)} pp vs. ano anterior", cor_m)

    kpi_card(k4, "Clientes Ativos (total)",
             f"{clientes_total:,}".replace(",", "."),
             "Soma do período filtrado", TEXT_MID)

    st.markdown("<br>", unsafe_allow_html=True)

    # Grafico 1: Tendencia de Faturamento (Area)
    secao_titulo(
        "Tendência de Faturamento",
        "Evolução mensal por Unidade de Negócio — valores em R$ mil"
    )

    df_trend = (
        df.groupby(["Data", "Unidade_Negocio"], as_index=False)
          .agg(Receita=("Receita", "sum"), Meta=("Meta", "sum"))
          .sort_values("Data")
    )
    df_trend["Receita_K"] = df_trend["Receita"] / 1_000
    df_trend["Meta_K"]    = df_trend["Meta"]    / 1_000

    fig_area = px.area(
        df_trend,
        x="Data", y="Receita_K",
        color="Unidade_Negocio",
        color_discrete_sequence=CHART_COLORS,
        labels={
            "Data":            "Período",
            "Receita_K":       "Faturamento (R$ mil)",
            "Unidade_Negocio": "Unidade de Negócio",
        },
        template="none",
    )
    df_meta_total = df.groupby("Data", as_index=False)["Meta"].sum()
    df_meta_total["Meta_K"] = df_meta_total["Meta"] / 1_000
    fig_area.add_trace(go.Scatter(
        x=df_meta_total["Data"],
        y=df_meta_total["Meta_K"],
        mode="lines",
        name="Meta Consolidada",
        line=dict(color=BLUE_DARK, width=1.5, dash="dash"),
        showlegend=True,
    ))
    fig_area = aplicar_layout_plotly(fig_area, height=340)
    fig_area.update_traces(
        selector=dict(type="scatter", fill="tozeroy"),
        line=dict(width=2),
        opacity=0.85,
    )
    fig_area.update_xaxes(
        tickformat="%b\n%Y",
        dtick="M1",
        tickangle=0,
        showgrid=False,
    )
    container_grafico(lambda: st.plotly_chart(fig_area, use_container_width=True))

    # Graficos 2+3 lado a lado
    col_g1, col_g2 = st.columns(2, gap="large")

    # Grafico 2: Barras agrupadas Receita vs Meta por Regiao
    with col_g1:
        secao_titulo(
            "Receita vs. Meta por Região",
            "Comparativo de desempenho — R$ mil"
        )
        df_reg = (
            df.groupby("Regiao", as_index=False)
              .agg(Receita=("Receita", "sum"), Meta=("Meta", "sum"))
              .sort_values("Receita", ascending=False)
        )
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            name="Faturamento",
            x=df_reg["Regiao"],
            y=(df_reg["Receita"] / 1_000).round(0),
            marker_color=BLUE_ROYAL,
            marker_line_width=0,
        ))
        fig_bar.add_trace(go.Bar(
            name="Meta",
            x=df_reg["Regiao"],
            y=(df_reg["Meta"] / 1_000).round(0),
            marker_color=BLUE_LIGHT,
            marker_line_width=0,
        ))
        fig_bar.update_layout(barmode="group")
        fig_bar = aplicar_layout_plotly(fig_bar, height=320)
        fig_bar.update_yaxes(title_text="R$ mil", tickformat=",.0f")
        container_grafico(lambda: st.plotly_chart(fig_bar, use_container_width=True))

    # Grafico 3: Dispersao Margem x Faturamento
    with col_g2:
        secao_titulo(
            "Margem x Faturamento por Segmento",
            "Eficiência operacional — tamanho proporcional às negociações"
        )
        df_sc = (
            df.groupby(["Unidade_Negocio", "Regiao"], as_index=False)
              .agg(
                  Receita=("Receita", "sum"),
                  Margem=("Margem_Pct", "mean"),
                  Negociacoes=("Negociacoes", "sum"),
              )
        )
        fig_sc = px.scatter(
            df_sc,
            x=(df_sc["Receita"] / 1_000).round(0),
            y=df_sc["Margem"].round(1),
            color="Unidade_Negocio",
            size="Negociacoes",
            hover_data={"Regiao": True},
            color_discrete_sequence=CHART_COLORS,
            labels={
                "x":               "Faturamento (R$ mil)",
                "y":               "Margem Bruta (%)",
                "Unidade_Negocio": "Unidade",
            },
            template="none",
        )
        fig_sc = aplicar_layout_plotly(fig_sc, height=320)
        fig_sc.update_traces(marker_line_width=0)
        fig_sc.update_yaxes(ticksuffix="%")
        container_grafico(lambda: st.plotly_chart(fig_sc, use_container_width=True))

    # Tabela Resumo
    st.markdown("<br>", unsafe_allow_html=True)
    secao_titulo(
        "Resumo por Unidade de Negócio e Região",
        "Consolidado do período filtrado, ordenado por faturamento"
    )

    df_tbl = (
        df.groupby(["Unidade_Negocio", "Regiao"], as_index=False)
          .agg(
              Receita_Total=("Receita",         "sum"),
              Meta_Total   =("Meta",            "sum"),
              Margem_Media =("Margem_Pct",      "mean"),
              Clientes     =("Clientes_Ativos", "sum"),
              Negociacoes  =("Negociacoes",     "sum"),
          )
          .sort_values("Receita_Total", ascending=False)
    )
    df_tbl["Atingimento (%)"] = (df_tbl["Receita_Total"] / df_tbl["Meta_Total"] * 100).round(1)
    df_tbl["Receita_Total"]   = df_tbl["Receita_Total"].map(lambda v: f"R$ {v:,.0f}")
    df_tbl["Meta_Total"]      = df_tbl["Meta_Total"].map(lambda v: f"R$ {v:,.0f}")
    df_tbl["Margem_Media"]    = df_tbl["Margem_Media"].map(lambda v: f"{v:.1f}%")
    df_tbl["Atingimento (%)"] = df_tbl["Atingimento (%)"].map(lambda v: f"{v:.1f}%")
    df_tbl = df_tbl.rename(columns={
        "Unidade_Negocio": "Unidade de Negócio",
        "Receita_Total":   "Faturamento Total",
        "Meta_Total":      "Meta",
        "Margem_Media":    "Margem Média",
        "Negociacoes":     "Negociações Fechadas",
    })

    st.dataframe(df_tbl, use_container_width=True, hide_index=True)
    botao_exportar(df, "visao_geral_filtrado.csv")


# ═════════════════════════════════════════════════════════════════════════════
# PAGINA 2 — ANALISE DE VENDAS
# ═════════════════════════════════════════════════════════════════════════════
elif pagina == "Análise de Vendas":

    secao_titulo(
        "Evolução de Faturamento vs. Meta",
        "Série temporal consolidada — linha tracejada representa meta do período"
    )

    df_vs = (
        df.groupby("Data", as_index=False)
          .agg(Faturamento=("Receita", "sum"), Meta=("Meta", "sum"))
          .sort_values("Data")
    )
    df_vs["Atingimento (%)"] = (df_vs["Faturamento"] / df_vs["Meta"] * 100).round(1)

    fig_ln = go.Figure()
    fig_ln.add_trace(go.Scatter(
        x=df_vs["Data"], y=(df_vs["Faturamento"] / 1_000).round(1),
        name="Faturamento",
        mode="lines+markers",
        line=dict(color=BLUE_ROYAL, width=2.5),
        marker=dict(size=5, color=BLUE_ROYAL),
        fill="tozeroy",
        fillcolor=f"rgba(59,130,246,.08)",
    ))
    fig_ln.add_trace(go.Scatter(
        x=df_vs["Data"], y=(df_vs["Meta"] / 1_000).round(1),
        name="Meta",
        mode="lines",
        line=dict(color=BLUE_DARK, width=1.8, dash="dot"),
    ))
    fig_ln = aplicar_layout_plotly(fig_ln, height=360)
    fig_ln.update_xaxes(tickformat="%b %Y", dtick="M1", tickangle=-30)
    fig_ln.update_yaxes(title_text="R$ mil", tickformat=",.0f")
    container_grafico(lambda: st.plotly_chart(fig_ln, use_container_width=True))

    st.markdown("<br>", unsafe_allow_html=True)

    col_v1, col_v2 = st.columns(2, gap="large")

    # Barras horizontais: Top segmentos por faturamento
    with col_v1:
        secao_titulo("Top Segmentos por Faturamento", "Unidade de Negócio x Região")
        df_seg = (
            df.assign(Segmento=df["Unidade_Negocio"] + " — " + df["Regiao"])
              .groupby("Segmento", as_index=False)
              .agg(Receita=("Receita", "sum"))
              .sort_values("Receita")
              .tail(10)
        )
        fig_hbar = px.bar(
            df_seg,
            x=(df_seg["Receita"] / 1_000).round(0),
            y="Segmento",
            orientation="h",
            color=(df_seg["Receita"] / 1_000).round(0),
            color_continuous_scale=[[0, BLUE_LIGHT], [1, BLUE_DARK]],
            labels={"x": "Faturamento (R$ mil)", "Segmento": ""},
            template="none",
        )
        fig_hbar.update_coloraxes(showscale=False)
        fig_hbar = aplicar_layout_plotly(fig_hbar, height=340)
        fig_hbar.update_xaxes(title_text="R$ mil")
        fig_hbar.update_traces(marker_line_width=0)
        container_grafico(lambda: st.plotly_chart(fig_hbar, use_container_width=True))

    # Atingimento de meta mensal
    with col_v2:
        secao_titulo("Atingimento de Meta Mensal (%)", "100% = meta exatamente atingida")
        df_at = (
            df.groupby("Data", as_index=False)
              .agg(R=("Receita", "sum"), M=("Meta", "sum"))
              .assign(Atingimento=lambda x: (x["R"] / x["M"] * 100).round(1))
              .sort_values("Data")
        )
        cores_at = [BLUE_ROYAL if v >= 90 else "#EF4444" for v in df_at["Atingimento"]]
        fig_at = go.Figure(go.Bar(
            x=df_at["Data"],
            y=df_at["Atingimento"],
            marker_color=cores_at,
            marker_line_width=0,
            name="Atingimento (%)",
        ))
        fig_at.add_hline(y=100, line_dash="dash", line_color=BLUE_DARK,
                          line_width=1.5, annotation_text="Meta 100%",
                          annotation_font=dict(size=11, color=BLUE_DARK))
        fig_at = aplicar_layout_plotly(fig_at, height=340)
        fig_at.update_xaxes(tickformat="%b\n%Y", dtick="M1", tickangle=0)
        fig_at.update_yaxes(ticksuffix="%", title_text="Atingimento (%)")
        container_grafico(lambda: st.plotly_chart(fig_at, use_container_width=True))

    botao_exportar(df, "analise_vendas_filtrado.csv")


# ═════════════════════════════════════════════════════════════════════════════
# PAGINA 3 — DESEMPENHO REGIONAL
# ═════════════════════════════════════════════════════════════════════════════
elif pagina == "Desempenho Regional":

    col_r1, col_r2 = st.columns(2, gap="large")

    # Barras verticais por Regiao e Unidade
    with col_r1:
        secao_titulo("Faturamento por Região", "Comparativo entre unidades de negócio")
        df_ru = (
            df.groupby(["Regiao", "Unidade_Negocio"], as_index=False)
              .agg(Receita=("Receita", "sum"))
        )
        fig_ru = px.bar(
            df_ru,
            x="Regiao", y=(df_ru["Receita"] / 1_000).round(0),
            color="Unidade_Negocio",
            barmode="group",
            color_discrete_sequence=CHART_COLORS,
            labels={"y": "Faturamento (R$ mil)", "Regiao": "Região", "Unidade_Negocio": "Unidade"},
            template="none",
        )
        fig_ru = aplicar_layout_plotly(fig_ru, height=340)
        fig_ru.update_traces(marker_line_width=0)
        fig_ru.update_yaxes(tickformat=",.0f", title_text="R$ mil")
        container_grafico(lambda: st.plotly_chart(fig_ru, use_container_width=True))

    # Margem media por regiao
    with col_r2:
        secao_titulo("Margem Bruta Média por Região", "Eficiência percentual — período filtrado")
        df_mg = (
            df.groupby("Regiao", as_index=False)
              .agg(Margem=("Margem_Pct", "mean"))
              .sort_values("Margem", ascending=False)
        )
        fig_mg = px.bar(
            df_mg,
            x="Regiao", y=df_mg["Margem"].round(1),
            color=df_mg["Margem"].round(1),
            color_continuous_scale=[[0, BLUE_LIGHT], [1, BLUE_DARK]],
            labels={"y": "Margem Bruta (%)", "Regiao": ""},
            template="none",
        )
        fig_mg.update_coloraxes(showscale=False)
        fig_mg = aplicar_layout_plotly(fig_mg, height=340)
        fig_mg.update_traces(marker_line_width=0)
        fig_mg.update_yaxes(ticksuffix="%", title_text="Margem (%)")
        container_grafico(lambda: st.plotly_chart(fig_mg, use_container_width=True))

    st.markdown("<br>", unsafe_allow_html=True)

    # Heatmap: Mes x Regiao
    secao_titulo(
        "Mapa de Calor — Faturamento por Período e Região",
        "Intensidade de cor proporcional ao volume (R$ mil)"
    )

    df_heat = (
        df.groupby(["Periodo", "Data", "Regiao"], as_index=False)
          .agg(Receita=("Receita", "sum"))
          .sort_values("Data")
    )
    pivot = df_heat.pivot_table(
        index="Regiao", columns="Periodo", values="Receita", aggfunc="sum"
    ) / 1_000

    colunas_ord = (
        df_heat[["Data","Periodo"]].drop_duplicates()
          .sort_values("Data")["Periodo"]
          .tolist()
    )
    pivot = pivot[[c for c in colunas_ord if c in pivot.columns]]

    fig_heat = go.Figure(go.Heatmap(
        z=pivot.values.round(0),
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=[[0, BLUE_PALE], [0.5, BLUE_ROYAL], [1, BLUE_DARK]],
        hovertemplate="<b>%{y}</b> — %{x}<br>R$ %{z:,.0f}K<extra></extra>",
        showscale=True,
        colorbar=dict(
            title=dict(text="R$ mil", font=dict(size=11, color=TEXT_MID)),
            tickfont=dict(size=10, color=TEXT_MID),
            len=0.8,
        ),
    ))
    fig_heat = aplicar_layout_plotly(fig_heat, height=280)
    fig_heat.update_layout(
        legend=dict(visible=False),
        xaxis=dict(tickangle=-35),
    )
    container_grafico(lambda: st.plotly_chart(fig_heat, use_container_width=True))

    botao_exportar(df, "desempenho_regional_filtrado.csv")


# ═════════════════════════════════════════════════════════════════════════════
# PAGINA 4 — EXPLORADOR DE DADOS
# ═════════════════════════════════════════════════════════════════════════════
elif pagina == "Explorador de Dados":

    # Estatisticas descritivas
    secao_titulo("Estatísticas Descritivas", "Variáveis quantitativas do período selecionado")

    colunas_stat = ["Receita", "Meta", "Margem_Pct", "Clientes_Ativos", "Negociacoes", "Atingimento_Pct"]
    df_stat = df[colunas_stat].describe().T.round(2)
    df_stat.index.name = "Variável"
    df_stat = df_stat.rename(columns={
        "count": "Registros", "mean": "Média", "std": "Desvio Padrão",
        "min": "Mínimo", "25%": "Percentil 25", "50%": "Mediana",
        "75%": "Percentil 75", "max": "Máximo",
    })
    st.dataframe(df_stat, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Tabela completa
    secao_titulo(
        "Base de Dados Completa",
        f"{len(df):,} registros correspondentes aos filtros aplicados"
    )

    col_ord, col_dir, _ = st.columns([2, 2, 4])
    with col_ord:
        col_sort = st.selectbox(
            "Ordenar por",
            options=["Receita", "Meta", "Margem_Pct", "Clientes_Ativos", "Atingimento_Pct", "Data"],
            index=0,
            key="sort_col",
        )
    with col_dir:
        ordem_asc = st.radio(
            "Direção",
            options=["Decrescente", "Crescente"],
            horizontal=True,
            key="sort_dir",
        )

    df_view = df.sort_values(col_sort, ascending=(ordem_asc == "Crescente")).reset_index(drop=True)

    colunas_exib = st.multiselect(
        "Colunas visíveis",
        options=df_view.columns.tolist(),
        default=["Data", "Periodo", "Regiao", "Unidade_Negocio",
                 "Receita", "Meta", "Margem_Pct", "Clientes_Ativos",
                 "Negociacoes", "Atingimento_Pct"],
        key="cols_exib",
    )

    st.dataframe(
        df_view[colunas_exib] if colunas_exib else df_view,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    botao_exportar(df_view, "explorador_dados_filtrado.csv")

    # Nota de rodape
    st.markdown(f"""
    <div style="background:{BLUE_PALE};border:1px solid #BFDBFE;
      border-radius:6px;padding:12px 16px;font-size:12px;color:{BLUE_DARK};margin-top:1rem;">
      <strong>Nota:</strong> Todos os dados exibidos são fictícios e gerados exclusivamente
      para fins de demonstração. Nenhuma informação real de clientes ou faturamento
      está representada nesta plataforma.
    </div>
    """, unsafe_allow_html=True)
