"""
Data Protection Platform v3.0
=================================
Plataforma corporativa de detecção de PII e secrets antes de agentes LLM
consumirem dados de Jira e Confluence.

Execução:
    python -m streamlit run corporate_dashboard.py
"""

from __future__ import annotations

import io
import os
from datetime import datetime, timezone

# Desabilita telemetria da biblioteca jira-python (nao envia dados para Atlassian)
os.environ.setdefault("JIRA_INTERNAL_EVENTS_ENABLED", "false")

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plugins.email_plugin import (
    GraphEmailPlugin,
    PLACEHOLDERS as EMAIL_PLACEHOLDERS,
    carregar_templates,
    salvar_templates,
    preencher_template,
    variaveis_de_chunks,
    extrair_imagens_data_uri,
)
from plugins.html_editor import html_paste_editor

st.set_page_config(
    page_title="Data Protection | PII & Secrets Scanner",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# DESIGN TOKENS — dark theme conforme DESIGN.md
# ─────────────────────────────────────────────────────────────────────────────
BD = "#1E3A8A"; BR = "#3B82F6"; BM = "#2563EB"; BL = "#93C5FD"
BP = "#1E3A8A1A"; BPG = "#0B1121"; BPS = "#0F1729"; BPW = "#1A2332"
BPB = "#0A1020"; TD = "#E2E8F0"; TM = "#94A3B8"; TMU = "#64748B"
BOR = "#1E3A5F"; BORM = "#2D4A72"
RD = "#EF4444"; RBG = "#DC262620"
OD = "#F97316"; OBG = "#F9731620"
GD = "#22C55E"; GBG = "#22C55E20"

# ─────────────────────────────────────────────────────────────────────────────
# CSS GLOBAL
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {{ font-family:'Inter',sans-serif; color:{TD}; }}

.stApp {{ background:{BPG}; }}

/* Header: fundo transparente, só mantém o toggle do sidebar */
header[data-testid="stHeader"] {{
  background:{BPG} !important;
  border-bottom:none !important;
}}
/* Oculta apenas o menu e botoes de toolbar — não o toggle */
#MainMenu {{ display:none !important; }}
[data-testid="stToolbarActions"] {{ display:none !important; }}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {{
  background:{BPB} !important;
  border-right:1px solid {BOR} !important;
  padding:0 !important;
}}
section[data-testid="stSidebar"] > div:first-child {{
  padding:0 16px 16px !important;
}}

/* Nav radio */
section[data-testid="stSidebar"] [data-testid="stRadio"] > label {{
  display:none !important;
}}
section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] {{
  gap:2px !important;
}}
section[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"] {{
  background:transparent !important;
  border-radius:7px !important;
  padding:7px 10px !important;
  margin:1px 0 !important;
  cursor:pointer !important;
  transition:background .15s !important;
  border-left:3px solid transparent !important;
}}
section[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"]:hover {{
  background:{BPW} !important;
}}
section[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) {{
  background:{BD}22 !important;
  border-left:3px solid {BR} !important;
}}
/* Texto do item */
section[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"] p {{
  font-size:13px !important;
  font-weight:500 !important;
  color:{TM} !important;
  margin:0 !important;
}}
section[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) p {{
  color:{TD} !important;
  font-weight:600 !important;
}}
/* Esconde o circulo do radio */
section[data-testid="stSidebar"] div[data-baseweb="radio"] > div:first-child {{
  display:none !important;
}}

/* Garante que o botão de colapsar o sidebar fique visível */
[data-testid="stSidebarCollapseButton"] {{
  display:flex !important;
  visibility:visible !important;
}}
[data-testid="stSidebarCollapseButton"] button {{
  display:flex !important;
  visibility:visible !important;
  background:{BPW} !important;
  border:1px solid {BOR} !important;
  border-radius:6px !important;
  color:{TM} !important;
}}

.block-container {{ padding-top:1.25rem; padding-bottom:2.5rem; max-width:100% !important; }}

.stButton > button {{
  background:{BD} !important; color:#fff !important; border:none !important;
  border-radius:6px !important; font-size:13px !important; font-weight:600 !important;
  padding:.45rem 1.25rem !important; letter-spacing:.2px !important;
  transition:background .15s,box-shadow .15s;
}}
.stButton > button:hover {{ background:{BR} !important; box-shadow:0 2px 8px rgba(59,130,246,.35) !important; }}

.stDownloadButton > button {{
  background:{BPW} !important; color:{BR} !important;
  border:1.5px solid {BOR} !important; border-radius:6px !important;
  font-weight:600 !important; font-size:13px !important;
}}
.stDownloadButton > button:hover {{ border-color:{BR} !important; }}

.stDataFrame > div {{ border:1px solid {BOR}; border-radius:8px; overflow:hidden; }}
.stDataFrame thead th {{
  background:{BPS} !important; color:{TM} !important;
  font-size:11px !important; font-weight:700 !important;
  text-transform:uppercase !important; letter-spacing:.5px !important;
  border-bottom:1px solid {BORM} !important; padding:10px 14px !important;
}}
.stDataFrame tbody td {{
  color:{TD} !important; font-size:12.5px !important;
  padding:9px 14px !important; border-bottom:1px solid {BOR} !important;
}}

.stTextArea textarea, .stTextInput input {{
  background:{BPW} !important; color:{TD} !important;
  border:1px solid {BOR} !important; border-radius:6px !important;
  font-family:'Inter',sans-serif !important; font-size:13px !important;
}}
.stTextArea textarea:focus, .stTextInput input:focus {{
  border-color:{BR} !important; box-shadow:0 0 0 2px rgba(59,130,246,.2) !important;
}}
.stSelectbox > div > div, .stMultiSelect > div > div {{
  background:{BPW} !important; border:1px solid {BOR} !important;
  border-radius:6px !important; color:{TD} !important;
}}
label, .stSelectbox label, .stMultiSelect label,
.stTextInput label, .stTextArea label, .stRadio label,
.stCheckbox label span {{
  color:{TM} !important; font-size:12px !important; font-weight:600 !important;
}}

div[data-testid="stTabs"] button[role="tab"] {{
  color:{TM} !important; font-size:13px !important; font-weight:500 !important;
  background:transparent !important; border-radius:6px 6px 0 0 !important;
  padding:8px 18px !important;
}}
div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {{
  color:{BR} !important; font-weight:700 !important;
  border-bottom:2px solid {BR} !important;
}}

div[data-testid="stExpander"] {{
  background:{BPW} !important; border:1px solid {BOR} !important;
  border-radius:8px !important;
}}
div[data-testid="stExpander"] summary {{ color:{TD} !important; font-weight:600 !important; }}

hr {{ border:none; border-top:1px solid {BOR}; margin:.5rem 0 1rem; }}

.kpi-card {{
  background:{BPW}; border:1px solid {BOR}; border-top:3px solid {BR};
  border-radius:8px; padding:16px 18px 14px;
  box-shadow:0 1px 4px rgba(0,0,0,.25);
}}
.kpi-card-danger  {{ border-top-color:{RD} !important; }}
.kpi-card-warning {{ border-top-color:{OD} !important; }}
.kpi-card-success {{ border-top-color:{GD} !important; }}
.kpi-label {{ font-size:10px; font-weight:700; color:{TM}; text-transform:uppercase; letter-spacing:.7px; margin-bottom:10px; }}
.kpi-value {{ font-size:28px; font-weight:700; color:{TD}; line-height:1; letter-spacing:-.5px; margin-bottom:5px; }}
.kpi-sub   {{ font-size:11px; color:{TMU}; }}

.badge-high   {{ background:{RBG}; color:{RD}; border:1px solid {RD}; border-radius:4px; padding:3px 10px; font-size:11px; font-weight:700; }}
.badge-medium {{ background:{OBG}; color:{OD}; border:1px solid {OD}; border-radius:4px; padding:3px 10px; font-size:11px; font-weight:700; }}
.badge-low    {{ background:{GBG}; color:{GD}; border:1px solid {GD}; border-radius:4px; padding:3px 10px; font-size:11px; font-weight:700; }}
.badge-secret {{ background:rgba(139,92,246,.15); color:#A78BFA; border:1px solid #7C3AED; border-radius:4px; padding:3px 10px; font-size:11px; font-weight:700; }}

.sec-hdr {{
  font-size:11px; font-weight:700; color:{TM}; text-transform:uppercase;
  letter-spacing:.6px; padding-bottom:8px; border-bottom:2px solid {BD};
  margin:1.75rem 0 1rem; display:inline-block;
}}
.anon-panel {{
  background:{BPG}; border:1px solid {BOR}; border-radius:8px;
  font-family:'JetBrains Mono',monospace; font-size:12.5px;
  color:{TD}; padding:14px; line-height:1.7; white-space:pre-wrap;
  min-height:120px; max-height:400px; overflow-y:auto;
}}
.report-card {{
  background:{BPW}; border:1px solid {BOR}; border-left:4px solid {BR};
  border-radius:8px; padding:20px 24px; margin-top:1rem;
}}
.hist-item {{
  background:{BPW}; border:1px solid {BOR}; border-left:3px solid {BORM};
  border-radius:6px; padding:9px 11px; margin-bottom:5px;
  font-size:11px; color:{TM};
}}
.sb-title {{
  font-size:10px; font-weight:700; color:{TMU}; text-transform:uppercase;
  letter-spacing:.8px; padding:18px 0 8px; margin-bottom:4px;
}}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# INICIALIZAÇÃO DE SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
def _init_state() -> None:
    defaults: dict = {
        "jira_plugin": None,
        "confluence_plugin": None,
        "jira_resultados": [],
        "jira_metricas": {},
        "jira_projetos": [],            # list[dict] com key/name/count
        "jira_proj_selecionados": [],   # [] = todos
        "confluence_resultados": [],
        "confluence_metricas": {},
        "confluence_spaces": [],
        "confluence_spaces_selecionados": [],
        "texto_resultados": [],
        "texto_metricas": {},
        "scan_history": [],
        "analyzer": None,
        "acoes_modo": "readonly",       # modo selecionado na aba Acoes
        "scrub_preview": [],            # lista de preview por issue
        "scrub_issue_selecionada": "",
        # Email (Microsoft Graph)
        "graph_token": "",
        "graph_me": None,               # {"nome": str, "email": str} após validação
        "email_templates": None,        # carregado lazy do arquivo JSON
        "email_dest_padrao": "",        # destinatário padrão persistido na sessão
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()

# ─────────────────────────────────────────────────────────────────────────────
# ANALYZER — cache pesado (spaCy + Presidio)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Carregando modelos de linguagem...")
def _build_analyzer():
    from presidio_pt import build_analyzer
    return build_analyzer()

def get_analyzer():
    if st.session_state.analyzer is None:
        st.session_state.analyzer = _build_analyzer()
    return st.session_state.analyzer


@st.cache_resource(show_spinner=False)
def get_scheduler():
    from plugins.scheduler import ScanScheduler
    sched = ScanScheduler()
    sched.start()
    return sched


# ── Modo cards: metadata para a aba Acoes ────────────────────────────────────
_MODO_INFO = {
    "readonly": {
        "titulo": "Apenas Visualizar",
        "para_quem": "Quero revisar os resultados sem alterar nada",
        "o_que_faz": "Nenhuma acao e executada no Jira. Use para entender o problema antes de decidir.",
        "quem_ve": "Apenas voce, no dashboard",
        "consequencia": "Nenhuma alteracao no Jira",
        "cor": TMU,
        "risco_label": "",
        "risco_bg": "",
    },
    "properties": {
        "titulo": "Registrar Internamente",
        "para_quem": "Quero rastrear sem aparecer para o time",
        "o_que_faz": "Salva um resumo tecnico nos metadados do card (Issue Properties). Outros usuarios nao verao absolutamente nada diferente no Jira.",
        "quem_ve": "Invisivel na UI do Jira — apenas via API ou relatorios",
        "consequencia": "Registro interno, sem impacto visual no Jira",
        "cor": BR,
        "risco_label": "",
        "risco_bg": "",
    },
    "label": {
        "titulo": "Adicionar Etiqueta",
        "para_quem": "Quero sinalizar o card para o time tratar",
        "o_que_faz": "Adiciona etiquetas como PII-HIGH ou SECRET-DETECTED no card. O time ve no board e pode filtrar.",
        "quem_ve": "Todos com acesso ao projeto verao as etiquetas",
        "consequencia": "Etiquetas visiveis no card — o time ve",
        "cor": OD,
        "risco_label": "VISIVEL",
        "risco_bg": OBG,
    },
    "comment": {
        "titulo": "Adicionar Comentario",
        "para_quem": "Quero deixar um registro publico de auditoria",
        "o_que_faz": "Adiciona comentario publico no historico do card (valores sempre mascarados). Fica permanente no historico.",
        "quem_ve": "Todos com acesso ao card, para sempre no historico",
        "consequencia": "Comentario no historico publico — permanente",
        "cor": OD,
        "risco_label": "HISTORICO",
        "risco_bg": OBG,
    },
    "scrub": {
        "titulo": "Remover Dados Sensiveis",
        "para_quem": "Quero apagar os dados do card permanentemente",
        "o_que_faz": "Substitui os dados detectados por [TIPO_DADO] diretamente no texto do card. ATENCAO: o texto original sera perdido e nao pode ser recuperado.",
        "quem_ve": "Todos verao o texto alterado. O historico de edicao mostra quem editou.",
        "consequencia": "IRREVERSIVEL — texto do card alterado permanentemente",
        "cor": RD,
        "risco_label": "IRREVERSIVEL",
        "risco_bg": RBG,
    },
}


def _render_modo_card(modo: str, selecionado: bool, disabled: bool = False) -> None:
    info = _MODO_INFO[modo]
    borda = f"2px solid {info['cor']}" if selecionado else f"1px solid {BOR}"
    bg = f"{info['cor']}18" if selecionado else BPW
    op = "0.45" if disabled else "1"

    badge_html = ""
    if info["risco_label"]:
        badge_html = (
            f'<span style="background:{info["risco_bg"]};color:{info["cor"]};'
            f'border:1px solid {info["cor"]};border-radius:3px;padding:2px 7px;'
            f'font-size:10px;font-weight:700;letter-spacing:.4px;">{info["risco_label"]}</span>'
        )

    st.markdown(f"""
    <div style="background:{bg};border:{borda};border-radius:10px;
      padding:14px 16px;opacity:{op};margin-bottom:2px;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
        <div style="font-size:13px;font-weight:700;color:{TD};">{info['titulo']}</div>
        {badge_html}
      </div>
      <div style="font-size:11.5px;color:{TM};font-style:italic;margin-bottom:7px;">{info['para_quem']}</div>
      <div style="font-size:11px;color:{TM};margin-bottom:9px;line-height:1.55;">{info['o_que_faz']}</div>
      <div style="display:flex;gap:12px;font-size:10px;flex-wrap:wrap;">
        <span style="color:{TMU};"><b style="color:{TM};">Quem ve:</b> {info['quem_ve']}</span>
      </div>
      <div style="margin-top:8px;padding-top:7px;border-top:1px solid {BOR}35;">
        <span style="font-size:10px;font-weight:700;color:{info['cor']};
          text-transform:uppercase;letter-spacing:.5px;">{info['consequencia']}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)
    if not disabled:
        label = "Selecionado" if selecionado else "Selecionar"
        if st.button(label, key=f"btn_modo_{modo}", use_container_width=True, disabled=selecionado):
            st.session_state.acoes_modo = modo
            st.rerun()


def _render_projetos_tabela(projetos: list[dict]) -> None:
    if not projetos:
        return
    max_c = max((p.get("count", 0) for p in projetos), default=1) or 1
    linhas = []
    for p in projetos:
        c = p.get("count", 0)
        barras = "█" * max(1, round(c / max_c * 18)) + "░" * (18 - max(1, round(c / max_c * 18)))
        linhas.append({
            "Chave": p["key"],
            "Nome": p["name"],
            "Cards": c if c >= 0 else "—",
            "Volume": f"{barras}  {c:,}" if c >= 0 else "—",
        })
    df_p = pd.DataFrame(linhas)
    st.dataframe(df_p, use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS DE UI
# ─────────────────────────────────────────────────────────────────────────────
def kpi(col, titulo: str, valor: str, sub: str, variante: str = "") -> None:
    cls = f"kpi-card {f'kpi-card-{variante}' if variante else ''}"
    col.markdown(f"""
    <div class="{cls}">
      <div class="kpi-label">{titulo}</div>
      <div class="kpi-value">{valor}</div>
      <div class="kpi-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)


def compliance_bar(score: int) -> None:
    cor = RD if score < 60 else (OD if score < 80 else GD)
    label = "Critico" if score < 60 else ("Atencao" if score < 80 else "Conforme")
    st.markdown(f"""
    <div style="margin:1rem 0 1.5rem;">
      <div style="display:flex;justify-content:space-between;
        font-size:11px;color:{TM};font-weight:600;margin-bottom:6px;">
        <span>COMPLIANCE SCORE — {label}</span>
        <span style="color:{cor};font-size:15px;font-weight:700;">{score}%</span>
      </div>
      <div style="background:{BPG};border:1px solid {BOR};border-radius:99px;height:6px;">
        <div style="width:{score}%;height:100%;border-radius:99px;
          background:{cor};transition:width .4s ease;"></div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def sec_hdr(titulo: str) -> None:
    st.markdown(f'<div class="sec-hdr">{titulo}</div>', unsafe_allow_html=True)


def badge(nivel: str) -> str:
    cls = {"HIGH": "badge-high", "MEDIUM": "badge-medium", "LOW": "badge-low"}.get(nivel, "badge-low")
    label = {"HIGH": "ALTO", "MEDIUM": "MEDIO", "LOW": "BAIXO"}.get(nivel, nivel)
    return f'<span class="{cls}">{label}</span>'


def badge_secret() -> str:
    return '<span class="badge-secret">SECRET</span>'


def _plot_dark(fig: go.Figure, height: int = 340) -> go.Figure:
    fig.update_layout(
        height=height,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter,sans-serif", color=TD, size=12),
        margin=dict(l=4, r=4, t=36, b=4),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="right", x=1, bgcolor="rgba(0,0,0,0)",
            font=dict(size=11, color=TM),
        ),
        xaxis=dict(gridcolor=BOR, linecolor=BOR, tickfont=dict(size=11, color=TM)),
        yaxis=dict(gridcolor=BOR, linecolor="rgba(0,0,0,0)", tickfont=dict(size=11, color=TM)),
        hoverlabel=dict(bgcolor=BPW, bordercolor=BOR, font=dict(size=12, color=TD)),
    )
    return fig


def _add_history(tipo: str, key: str, m: dict) -> None:
    _alto = m.get("por_nivel", {}).get("HIGH", 0)
    _medio = m.get("por_nivel", {}).get("MEDIUM", 0)
    _baixo = m.get("por_nivel", {}).get("LOW", 0)
    _secrets = m.get("total_secrets", 0)
    _total = m.get("total_deteccoes", 0)
    _score = m.get("compliance_score", 0.0)
    _pe = m.get("por_entidade", {})
    if isinstance(_pe, dict):
        _ents = list(_pe.keys())
    elif isinstance(_pe, list):
        _ents = [d.get("entidade", d) if isinstance(d, dict) else str(d) for d in _pe if d]
    else:
        _ents = []

    st.session_state.scan_history.insert(0, {
        "tipo": tipo, "key": key,
        "hora": datetime.now(timezone.utc).strftime("%H:%M"),
        "total": _total,
        "alto": _alto,
        "secrets": _secrets,
    })
    st.session_state.scan_history = st.session_state.scan_history[:10]

    if tipo.lower() != "demo":
        try:
            from plugins.scan_state import ScanStateStore as _SSS
            _SSS().salvar_execucao(
                fonte=tipo, projetos=key,
                total=_total, alto=_alto, medio=_medio,
                baixo=_baixo, secrets=_secrets,
                compliance_score=float(_score), entidades=_ents,
            )
        except Exception:
            pass

# ─────────────────────────────────────────────────────────────────────────────
# CHARTS
# ─────────────────────────────────────────────────────────────────────────────
def chart_donut(metricas: dict) -> go.Figure:
    pn = metricas.get("por_nivel", {})
    valores = [pn.get("HIGH", 0), pn.get("MEDIUM", 0), pn.get("LOW", 0)]
    labels = ["Alto", "Medio", "Baixo"]
    cores = [RD, OD, GD]
    fig = go.Figure(go.Pie(
        labels=labels, values=valores, hole=0.60,
        marker=dict(colors=cores, line=dict(color=BPG, width=2)),
        textfont=dict(size=11, color=TD),
        hovertemplate="<b>%{label}</b><br>%{value} deteccoes<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center",
                    font=dict(size=11, color=TM)),
        annotations=[dict(
            text=f"<b>{metricas.get('total_deteccoes', 0)}</b>",
            x=0.5, y=0.5, font=dict(size=22, color=TD), showarrow=False,
        )],
    )
    return _plot_dark(fig, height=280)


def chart_entity_bars(metricas: dict) -> go.Figure:
    from plugins.risk_scorer import score_nivel
    pe = metricas.get("por_entidade", {})
    top = list(pe.items())[:8]
    if not top:
        return go.Figure()
    nomes = [t[0] for t in top]
    vals = [t[1] for t in top]
    cores = []
    for n in nomes:
        nv = score_nivel(n)
        cores.append(RD if nv == "HIGH" else (OD if nv == "MEDIUM" else GD))
    fig = go.Figure(go.Bar(
        y=nomes, x=vals, orientation="h",
        marker=dict(color=cores, line=dict(width=0)),
        hovertemplate="<b>%{y}</b><br>%{x} ocorrencias<extra></extra>",
    ))
    fig.update_layout(yaxis=dict(autorange="reversed"))
    return _plot_dark(fig, height=280)


def chart_framework_bars(metricas: dict) -> None:
    from plugins.frameworks import frameworks_impactados
    from plugins.scanner import ResultadoChunk
    resultados = (
        st.session_state.get("jira_resultados") or
        st.session_state.get("confluence_resultados") or
        st.session_state.get("texto_resultados") or []
    )
    registros = [
        {"entidade": d.entidade}
        for r in resultados
        for d in r.deteccoes
    ]
    fw_count = frameworks_impactados(registros)
    top = list(fw_count.items())[:6]
    if not top:
        st.markdown(f'<p style="color:{TMU};font-size:12px;">Sem dados</p>', unsafe_allow_html=True)
        return
    total = max(v for _, v in top)
    for fw, cnt in top:
        pct = int(cnt / total * 100) if total > 0 else 0
        st.markdown(f"""
        <div style="margin-bottom:10px;">
          <div style="display:flex;justify-content:space-between;
            font-size:11px;color:{TM};margin-bottom:4px;">
            <span style="font-weight:600;">{fw}</span>
            <span>{cnt}</span>
          </div>
          <div style="background:{BOR};border-radius:4px;height:5px;">
            <div style="width:{pct}%;height:100%;border-radius:4px;background:{BR};"></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# RENDER RESULTADOS (reutilizável)
# ─────────────────────────────────────────────────────────────────────────────
def render_resultados(
    resultados: list,
    metricas: dict,
    source_label: str,
) -> None:
    if not resultados:
        st.markdown(f"""
        <div style="background:{BPW};border:1px solid {BOR};border-radius:8px;
          padding:36px;text-align:center;color:{TM};margin:2rem 0;">
          <div style="font-size:14px;font-weight:600;color:{TD};margin-bottom:6px;">
            Nenhum resultado disponivel
          </div>
          Execute a varredura para ver as deteccoes.
        </div>
        """, unsafe_allow_html=True)
        return

    pn = metricas.get("por_nivel", {})
    total = metricas.get("total_deteccoes", 0)
    secrets = metricas.get("total_secrets", 0)
    score = metricas.get("compliance_score", 100)

    # KPIs
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    kpi(k1, "Total Deteccoes", str(total), f"{source_label}")
    kpi(k2, "Risco Alto", str(pn.get("HIGH", 0)), "HIGH", "danger")
    kpi(k3, "Risco Medio", str(pn.get("MEDIUM", 0)), "MEDIUM", "warning")
    kpi(k4, "Risco Baixo", str(pn.get("LOW", 0)), "LOW", "success")
    kpi(k5, "Secrets", str(secrets), "JWT / API Key / Senha", "danger" if secrets > 0 else "")
    kpi(k6, "Compliance", f"{score}%", "Score calculado", "danger" if score < 60 else ("warning" if score < 80 else "success"))

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    compliance_bar(score)

    # Charts
    c1, c2, c3 = st.columns(3, gap="large")
    with c1:
        sec_hdr("Distribuicao de Risco")
        st.plotly_chart(chart_donut(metricas), use_container_width=True)
    with c2:
        sec_hdr("Top Entidades Detectadas")
        st.plotly_chart(chart_entity_bars(metricas), use_container_width=True)
    with c3:
        sec_hdr("Frameworks Impactados")
        chart_framework_bars(metricas)

    # Tabela com filtros
    sec_hdr("Deteccoes Detalhadas")
    f1, f2, _ = st.columns([2, 3, 3])
    with f1:
        filtro_nivel = st.selectbox(
            "Nivel de risco",
            ["Todos", "HIGH", "MEDIUM", "LOW"],
            key=f"fn_{source_label}",
        )
    with f2:
        todas_entidades = sorted({d.entidade for r in resultados for d in r.deteccoes})
        filtro_entidade = st.multiselect(
            "Tipo de entidade",
            todas_entidades,
            key=f"fe_{source_label}",
        )

    linhas = []
    for r in resultados:
        chunk = r.chunk
        for d in r.deteccoes:
            if filtro_nivel != "Todos" and d.nivel != filtro_nivel:
                continue
            if filtro_entidade and d.entidade not in filtro_entidade:
                continue
            linhas.append({
                "Issue / Pagina": chunk.get("issue_key") or chunk.get("pagina", "—"),
                "Campo": chunk.get("campo", "—"),
                "Entidade": d.entidade,
                "Valor": d.valor_display,
                "Nivel": d.nivel,
                "Confianca": f"{d.confianca:.0%}",
                "Secret": "Sim" if d.is_secret else "",
                "Frameworks": ", ".join(d.frameworks[:2]),
            })

    if linhas:
        df = pd.DataFrame(linhas)
        st.dataframe(df, use_container_width=True, hide_index=True)

        col_dl1, col_dl2, _ = st.columns([2, 2, 4])
        with col_dl1:
            st.download_button(
                "Exportar CSV",
                df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
                file_name=f"scan_{source_label.lower().replace(' ', '_')}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with col_dl2:
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as w:
                df.to_excel(w, index=False, sheet_name="Deteccoes")
            st.download_button(
                "Exportar Excel",
                buf.getvalue(),
                file_name=f"scan_{source_label.lower().replace(' ', '_')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
    else:
        st.markdown(f'<p style="color:{TMU};font-size:13px;">Nenhuma deteccao com os filtros aplicados.</p>', unsafe_allow_html=True)

    # Relatorio executivo
    sec_hdr("Relatorio Executivo")
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    fw_str = ""
    if resultados:
        from plugins.frameworks import frameworks_impactados
        registros = [{"entidade": d.entidade} for r in resultados for d in r.deteccoes]
        fw_count = frameworks_impactados(registros)
        fw_str = ", ".join(list(fw_count.keys())[:6])

    relatorio = "\n".join([
        "DATA PROTECTION SCANNER — RELATORIO EXECUTIVO",
        "=" * 52,
        f"Geracao: {ts}",
        f"Fonte:   {source_label}",
        "",
        "RESUMO",
        f"  Total de deteccoes : {total}",
        f"  Risco alto         : {pn.get('HIGH', 0)}",
        f"  Risco medio        : {pn.get('MEDIUM', 0)}",
        f"  Risco baixo        : {pn.get('LOW', 0)}",
        f"  Secrets detectados : {secrets}",
        f"  Compliance score   : {score}%",
        "",
        "FRAMEWORKS IMPACTADOS",
        f"  {fw_str}",
        "",
        "DETECCOES (primeiras 50)",
        "-" * 52,
    ] + [
        f"  {l['Issue / Pagina']:12} | {l['Entidade']:22} | {l['Nivel']:6} | {l['Valor']}"
        for l in linhas[:50]
    ])

    st.markdown(f'<div class="report-card">', unsafe_allow_html=True)
    col_r1, col_r2, col_r3 = st.columns(3)
    col_r1.markdown(f'<span style="font-size:12px;color:{TM};">Total</span><br>'
                    f'<span style="font-size:18px;font-weight:700;color:{TD};">{total}</span>', unsafe_allow_html=True)
    col_r2.markdown(f'<span style="font-size:12px;color:{TM};">Risco Alto</span><br>'
                    f'<span style="font-size:18px;font-weight:700;color:{RD};">{pn.get("HIGH", 0)}</span>', unsafe_allow_html=True)
    col_r3.markdown(f'<span style="font-size:12px;color:{TM};">Secrets</span><br>'
                    f'<span style="font-size:18px;font-weight:700;color:#A78BFA;">{secrets}</span>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.download_button(
        "Baixar Relatorio (.txt)",
        relatorio.encode("utf-8"),
        file_name=f"relatorio_{source_label.lower().replace(' ', '_')}.txt",
        mime="text/plain",
    )


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    # ── Logo ──────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="padding:20px 0 18px;">
      <div style="background:linear-gradient(135deg,{BD} 0%,{BM} 60%,{BR} 100%);
        border-radius:10px;padding:16px 18px;">
        <div style="font-size:11px;font-weight:700;color:{BL};letter-spacing:1.2px;
          text-transform:uppercase;margin-bottom:4px;">Data Protection</div>
        <div style="font-size:17px;font-weight:700;color:#fff;letter-spacing:-.3px;
          line-height:1.1;">PII + Secrets<br>Scanner</div>
        <div style="margin-top:8px;padding-top:8px;border-top:1px solid rgba(255,255,255,.15);
          font-size:10px;color:{BL};letter-spacing:.3px;">v3.0 &nbsp;·&nbsp; Presidio PT &nbsp;·&nbsp; LGPD</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Navegacao ─────────────────────────────────────────────────────────────
    st.markdown(f'<div class="sb-title">Navegacao</div>', unsafe_allow_html=True)
    pagina = st.radio(
        "pagina",
        ["Painel Executivo", "Varredura Jira", "Varredura Confluence", "Texto Livre", "Anonymizar", "Frameworks"],
        label_visibility="collapsed",
    )

    # ── Historico ─────────────────────────────────────────────────────────────
    if st.session_state.scan_history:
        st.markdown(f"""
        <div style="margin-top:6px;padding-top:2px;border-top:1px solid {BOR};">
          <div class="sb-title">Historico Recente</div>
        </div>
        """, unsafe_allow_html=True)
        for h in st.session_state.scan_history[:5]:
            _cor = RD if h["alto"] > 0 or h["secrets"] > 0 else GD
            _badge_alto = f'<span style="color:{RD};font-weight:700;">{h["alto"]}H</span>&nbsp;' if h["alto"] > 0 else ""
            _badge_sec  = f'<span style="color:#A78BFA;font-weight:700;">{h["secrets"]}S</span>' if h["secrets"] > 0 else ""
            st.markdown(f"""
            <div class="hist-item">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:3px;">
                <span style="font-weight:700;color:{TD};font-size:11.5px;">{h['tipo']}</span>
                <span style="color:{TMU};font-size:10px;">{h['hora']}</span>
              </div>
              <div style="color:{TMU};font-size:10.5px;margin-bottom:4px;
                white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{h['key']}</div>
              <div style="font-size:11px;">
                <span style="color:{_cor};font-weight:600;">{h['total']}</span>
                <span style="color:{TMU};"> detec.</span>
                &nbsp;{_badge_alto}{_badge_sec}
              </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Rodape ────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="margin-top:32px;padding-top:12px;border-top:1px solid {BOR};">
      <div style="font-size:10px;color:{TMU};line-height:1.8;">
        <span style="color:{BR};font-weight:700;">OWASP LLM Top 10</span>
        &nbsp;·&nbsp; LLM06 &nbsp;·&nbsp; LLM01<br>
        Protecao pre-ingestao por LLM agents
      </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# CABECALHO
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="margin-bottom:1.25rem;">
  <h1 style="font-size:22px;font-weight:700;color:{TD};margin:0 0 4px;letter-spacing:-.5px;">{pagina}</h1>
  <p style="font-size:13px;color:{TM};margin:0;">Data Protection Platform &middot; PII · Secrets · LGPD · OWASP LLM Top 10</p>
</div>
<hr>
""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGINA: PAINEL EXECUTIVO
# ═════════════════════════════════════════════════════════════════════════════
if pagina == "Painel Executivo":
    from plugins.scan_state import ScanStateStore as _ExecStore
    from plugins.demo_data import EXEC_DEMO_HISTORICO
    from plugins.frameworks import PII_FRAMEWORK_MAP, AI_FRAMEWORKS

    _estore = _ExecStore()
    _historico_db = _estore.listar_historico()
    _is_exec_demo = not _historico_db

    # Sem dados reais → agrega demo só em memória, nunca grava no banco
    if _is_exec_demo:
        from collections import Counter as _Counter
        _demo_por_mes: list[dict] = []
        _demo_por_fonte: dict[str, dict] = {}
        _demo_ent_counter: _Counter[str] = _Counter()

        _mes_agg: dict[str, dict] = {}
        for _h in EXEC_DEMO_HISTORICO:
            _m = _h["mes_ano"]
            if _m not in _mes_agg:
                _mes_agg[_m] = {"mes_ano": _m, "total": 0, "alto": 0, "medio": 0,
                                 "baixo": 0, "secrets": 0, "compliance_score": [], "varreduras": 0}
            _mes_agg[_m]["total"] += _h["total_deteccoes"]
            _mes_agg[_m]["alto"] += _h["alto"]
            _mes_agg[_m]["medio"] += _h["medio"]
            _mes_agg[_m]["baixo"] += _h["baixo"]
            _mes_agg[_m]["secrets"] += _h["secrets"]
            _mes_agg[_m]["compliance_score"].append(_h["compliance_score"])
            _mes_agg[_m]["varreduras"] += 1

            _f = _h["fonte"]
            if _f not in _demo_por_fonte:
                _demo_por_fonte[_f] = {"fonte": _f, "total": 0, "varreduras": 0}
            _demo_por_fonte[_f]["total"] += _h["total_deteccoes"]
            _demo_por_fonte[_f]["varreduras"] += 1

            for _e in _h["entidades"]:
                _demo_ent_counter[_e] += 1

        for _mv in _mes_agg.values():
            _scores = _mv.pop("compliance_score")
            _mv["compliance_score"] = round(sum(_scores) / len(_scores), 1)
            _demo_por_mes.append(_mv)

        _por_mes = sorted(_demo_por_mes, key=lambda x: x["mes_ano"])
        _por_fonte = list(_demo_por_fonte.values())
        _top_ents = [{"entidade": k, "count": v}
                     for k, v in _demo_ent_counter.most_common(12)]
        _historico_db = [{
            "timestamp": f"{h['mes_ano']}-15T08:00:00",
            "fonte": h["fonte"], "projetos": h["projetos"],
            "total_deteccoes": h["total_deteccoes"], "alto": h["alto"],
            "secrets": h["secrets"], "compliance_score": h["compliance_score"],
        } for h in EXEC_DEMO_HISTORICO]
    else:
        _por_mes = _estore.agregar_por_mes()
        _por_fonte = _estore.agregar_por_fonte()
        _top_ents = _estore.top_entidades(12)

    # ── KPI helper ────────────────────────────────────────────────────────────
    def _kpi_card(titulo: str, valor: str, delta: str, delta_ok: bool, subtitulo: str = "") -> str:
        _dcor = GD if delta_ok else RD
        _darrow = "▼" if delta_ok else "▲"
        _delta_html = (
            f'<div style="font-size:12px;color:{_dcor};font-weight:600;margin-top:6px;">{_darrow} {delta}</div>'
            if delta else
            f'<div style="font-size:12px;margin-top:6px;">&nbsp;</div>'
        )
        _sub_html = (
            f'<div style="font-size:11px;color:{TMU};margin-top:3px;">{subtitulo}</div>'
            if subtitulo else
            f'<div style="font-size:11px;margin-top:3px;">&nbsp;</div>'
        )
        return f"""
        <div style="background:{BPW};border:1px solid {BOR};border-radius:10px;
          padding:18px 20px;height:130px;box-sizing:border-box;">
          <div style="font-size:11px;font-weight:700;color:{TM};text-transform:uppercase;
            letter-spacing:.6px;margin-bottom:8px;">{titulo}</div>
          <div style="font-size:28px;font-weight:700;color:{TD};letter-spacing:-1px;
            line-height:1;">{valor}</div>
          {_delta_html}
          {_sub_html}
        </div>"""

    # ── Calculos KPI ──────────────────────────────────────────────────────────
    _meses_ord = sorted(_por_mes, key=lambda x: x["mes_ano"])
    _mes_atual = _meses_ord[-1] if _meses_ord else {}
    _mes_ant = _meses_ord[-2] if len(_meses_ord) > 1 else {}

    _tot_acum = sum(m["total"] for m in _meses_ord)
    _tot_atual = _mes_atual.get("total", 0)
    _tot_ant = _mes_ant.get("total", 1) or 1
    _delta_det = abs(_tot_atual - _tot_ant)
    _reducao_pct = round(((_tot_ant - _tot_atual) / _tot_ant) * 100, 1) if _tot_ant else 0
    _reducao_ok = _tot_atual < _tot_ant

    _score_atual = _mes_atual.get("compliance_score", 0.0)
    _score_ant = _mes_ant.get("compliance_score", 0.0)
    _score_delta = round(_score_atual - _score_ant, 1)

    _total_varreduras = sum(m["varreduras"] for m in _meses_ord)
    _alto_atual = _mes_atual.get("alto", 0)
    _alto_ant = _mes_ant.get("alto", 0)

    if _is_exec_demo:
        st.markdown(f"""
        <div style="background:{BPW};border:1px solid {BORM};border-radius:8px;
          padding:10px 16px;margin-bottom:16px;font-size:12px;color:{TM};">
          Exibindo dados de demonstracao (6 meses simulados). Os dados reais aparecao
          aqui apos a primeira varredura.
        </div>""", unsafe_allow_html=True)

    # ── KPIs ──────────────────────────────────────────────────────────────────
    _k1, _k2, _k3, _k4 = st.columns(4, gap="medium")
    _k1.markdown(_kpi_card(
        "Total de Varreduras", str(_total_varreduras),
        "", True, f"{len(_meses_ord)} mes{'es' if len(_meses_ord) != 1 else ''} de historico"
    ), unsafe_allow_html=True)
    _k2.markdown(_kpi_card(
        "Deteccoes Este Mes", str(_tot_atual),
        f"{abs(_reducao_pct)}% vs mes anterior", _reducao_ok,
        "queda = plataforma funcionando" if _reducao_ok else "alta = novos dados expostos"
    ), unsafe_allow_html=True)
    _k3.markdown(_kpi_card(
        "Score de Conformidade", f"{_score_atual:.0f}%",
        f"{abs(_score_delta)}pp vs mes anterior", _score_delta >= 0,
        "meta: 90%"
    ), unsafe_allow_html=True)
    _k4.markdown(_kpi_card(
        "Itens Alto Risco", str(_alto_atual),
        f"{abs(_alto_atual - _alto_ant)} vs mes anterior", _alto_atual <= _alto_ant,
        "HIGH + Secrets combinados"
    ), unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── Linha 1: Tendencia mensal + Score ─────────────────────────────────────
    _c_trend, _c_score = st.columns([3, 2], gap="medium")

    with _c_trend:
        sec_hdr("Tendencia Mensal de Deteccoes")
        if _por_mes:
            _df_mes = pd.DataFrame(_por_mes)
            _meses_labels = [m["mes_ano"] for m in _meses_ord]

            _fig_trend = go.Figure()
            _fig_trend.add_trace(go.Bar(
                name="Alto Risco", x=_meses_labels,
                y=[m["alto"] + m["secrets"] for m in _meses_ord],
                marker_color=RD, opacity=0.85,
            ))
            _fig_trend.add_trace(go.Bar(
                name="Medio", x=_meses_labels,
                y=[m["medio"] for m in _meses_ord],
                marker_color=OD, opacity=0.85,
            ))
            _fig_trend.add_trace(go.Bar(
                name="Baixo", x=_meses_labels,
                y=[m["baixo"] for m in _meses_ord],
                marker_color="#334155", opacity=0.85,
            ))
            _fig_trend.add_trace(go.Scatter(
                name="Total", x=_meses_labels,
                y=[m["total"] for m in _meses_ord],
                mode="lines+markers",
                line={"color": BL, "width": 2.5, "dash": "dot"},
                marker={"size": 7},
                yaxis="y",
            ))
            _fig_trend.update_layout(
                barmode="stack", paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)", height=280,
                margin={"l": 0, "r": 0, "t": 10, "b": 0},
                legend={"orientation": "h", "y": -0.15, "font": {"size": 11, "color": TM}},
                xaxis={"gridcolor": BOR, "tickfont": {"size": 11, "color": TM}},
                yaxis={"gridcolor": BOR, "tickfont": {"size": 11, "color": TM}},
                font={"color": TM},
            )
            st.plotly_chart(_fig_trend, use_container_width=True, config={"displayModeBar": False})
        else:
            st.markdown(f'<p style="color:{TMU};font-size:13px;">Sem dados ainda.</p>', unsafe_allow_html=True)

    with _c_score:
        sec_hdr("Evolucao do Score de Conformidade")
        if _por_mes:
            _fig_score = go.Figure()
            _fig_score.add_trace(go.Scatter(
                x=_meses_labels,
                y=[m["compliance_score"] for m in _meses_ord],
                mode="lines+markers",
                fill="tozeroy",
                fillcolor=f"rgba(34,197,94,.12)",
                line={"color": GD, "width": 2.5},
                marker={"size": 8, "color": GD},
            ))
            _fig_score.add_hline(y=90, line_dash="dash", line_color=GD,
                                 annotation_text="Meta 90%",
                                 annotation_font={"size": 10, "color": GD})
            _fig_score.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                height=280, margin={"l": 0, "r": 10, "t": 10, "b": 0},
                yaxis={"range": [0, 105], "gridcolor": BOR,
                       "ticksuffix": "%", "tickfont": {"size": 11, "color": TM}},
                xaxis={"gridcolor": BOR, "tickfont": {"size": 11, "color": TM}},
                showlegend=False, font={"color": TM},
            )
            st.plotly_chart(_fig_score, use_container_width=True, config={"displayModeBar": False})

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # ── Linha 2: Top entidades + Por fonte + Frameworks ───────────────────────
    _c_ent, _c_fonte, _c_fw = st.columns([3, 2, 3], gap="medium")

    with _c_ent:
        sec_hdr("Top Entidades Detectadas")
        if _top_ents:
            _df_ents = pd.DataFrame(_top_ents).sort_values("count")
            _cores_ent = []
            _secret_types = {"JWT_TOKEN", "AWS_ACCESS_KEY", "GITHUB_TOKEN", "PRIVATE_KEY",
                             "CONNECTION_STRING", "SECRET_IN_CONTEXT"}
            for _e in _df_ents["entidade"]:
                _cores_ent.append("#A78BFA" if _e in _secret_types else BR)
            _fig_ents = go.Figure(go.Bar(
                x=_df_ents["count"], y=_df_ents["entidade"],
                orientation="h",
                marker_color=_cores_ent,
                text=_df_ents["count"], textposition="outside",
                textfont={"size": 11, "color": TM},
            ))
            _fig_ents.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                height=320, margin={"l": 0, "r": 40, "t": 10, "b": 0},
                xaxis={"gridcolor": BOR, "tickfont": {"size": 10, "color": TM}},
                yaxis={"tickfont": {"size": 11, "color": TD}},
                showlegend=False,
            )
            st.plotly_chart(_fig_ents, use_container_width=True, config={"displayModeBar": False})
            st.markdown(
                f'<p style="font-size:10.5px;color:{TMU};">'
                f'<span style="color:#A78BFA;">■</span> Secrets / Credenciais &nbsp;&nbsp;'
                f'<span style="color:{BR};">■</span> PII Pessoal</p>',
                unsafe_allow_html=True,
            )

    with _c_fonte:
        sec_hdr("Deteccoes por Fonte")
        if _por_fonte:
            _cores_fonte = {
                "Jira": BR, "Confluence": "#7C3AED", "Texto": GD,
            }
            _fig_fonte = go.Figure(go.Pie(
                labels=[f["fonte"] for f in _por_fonte],
                values=[f["total"] for f in _por_fonte],
                hole=0.55,
                marker_colors=[_cores_fonte.get(f["fonte"], OD) for f in _por_fonte],
                textinfo="percent+label",
                textfont={"size": 11, "color": "#fff"},
                hovertemplate="%{label}<br>%{value} deteccoes<extra></extra>",
            ))
            _fig_fonte.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                height=200, margin={"l": 0, "r": 0, "t": 0, "b": 0},
                showlegend=False,
            )
            st.plotly_chart(_fig_fonte, use_container_width=True, config={"displayModeBar": False})

            for _f in sorted(_por_fonte, key=lambda x: -x["total"]):
                _pct_f = round(_f["total"] / max(sum(x["total"] for x in _por_fonte), 1) * 100)
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;'
                    f'font-size:12px;color:{TM};margin-bottom:4px;">'
                    f'<span style="color:{TD};">{_f["fonte"]}</span>'
                    f'<span>{_f["total"]:,} &nbsp;<span style="color:{TMU};">({_pct_f}%)</span></span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    with _c_fw:
        sec_hdr("Cobertura de Frameworks Regulatorios")
        # Inverte PII_FRAMEWORK_MAP: framework → soma de detecções das entidades mapeadas
        _ent_counts: dict[str, int] = {t["entidade"]: t["count"] for t in _top_ents}
        _fw_hits_map: dict[str, int] = {}
        for _ent, _fws in PII_FRAMEWORK_MAP.items():
            _cnt = _ent_counts.get(_ent, 0)
            if _cnt == 0:
                continue
            for _fw in _fws:
                _fw_key = _fw.split(" —")[0].strip()  # normaliza nome
                _fw_hits_map[_fw_key] = _fw_hits_map.get(_fw_key, 0) + _cnt

        _fw_scores = sorted(
            [{"framework": k[:30], "hits": v} for k, v in _fw_hits_map.items()],
            key=lambda x: -x["hits"],
        )[:10]

        _fw_lista_inv = list(reversed(_fw_scores))  # menor embaixo, maior em cima

        # Cor por tipo de framework
        def _fw_cor(name: str) -> str:
            if "OWASP" in name or "MITRE" in name or "NIST" in name:
                return "#A78BFA"
            if "PCI" in name:
                return RD
            if "LGPD" in name or "GDPR" in name or "ISO" in name:
                return BR
            return OD

        _fig_fw = go.Figure(go.Bar(
            x=[f["hits"] for f in _fw_lista_inv],
            y=[f["framework"] for f in _fw_lista_inv],
            orientation="h",
            marker_color=[_fw_cor(f["framework"]) for f in _fw_lista_inv],
            text=[f["hits"] for f in _fw_lista_inv],
            textposition="outside",
            textfont={"size": 11, "color": TM},
        ))
        _fig_fw.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=320, margin={"l": 0, "r": 50, "t": 10, "b": 0},
            xaxis={"gridcolor": BOR, "tickfont": {"size": 10, "color": TM},
                   "title": {"text": "deteccoes mapeadas", "font": {"size": 10, "color": TM}}},
            yaxis={"tickfont": {"size": 10, "color": TD}},
            showlegend=False,
        )
        if _fw_scores:
            st.plotly_chart(_fig_fw, use_container_width=True, config={"displayModeBar": False})
            st.markdown(
                f'<p style="font-size:10.5px;color:{TMU};">'
                f'<span style="color:#A78BFA;">■</span> AI/Security &nbsp;'
                f'<span style="color:{BR};">■</span> Privacidade &nbsp;'
                f'<span style="color:{RD};">■</span> PCI</p>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(f'<p style="color:{TMU};font-size:13px;">Execute varreduras para popular este grafico.</p>', unsafe_allow_html=True)

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # ── Tabela de execucoes recentes ──────────────────────────────────────────
    sec_hdr("Execucoes Recentes")
    _hist_rec = _historico_db[:20]
    if _hist_rec:
        _df_rec = pd.DataFrame([{
            "Data/Hora": h["timestamp"][:16].replace("T", " "),
            "Fonte": h["fonte"],
            "Projetos/Spaces": h["projetos"],
            "Total": h["total_deteccoes"],
            "Alto": h["alto"],
            "Secrets": h["secrets"],
            "Score": f"{h['compliance_score']:.0f}%",
        } for h in _hist_rec])
        st.dataframe(_df_rec, use_container_width=True, hide_index=True)

        _col_exp, _ = st.columns([2, 5])
        with _col_exp:
            _csv_exec = _df_rec.to_csv(index=False).encode()
            st.download_button("Exportar historico CSV", _csv_exec,
                               "historico_deteccoes.csv", "text/csv",
                               use_container_width=True)

# ═════════════════════════════════════════════════════════════════════════════
# PAGINA: VARREDURA JIRA
# ═════════════════════════════════════════════════════════════════════════════
elif pagina == "Varredura Jira":
    from plugins import JiraPlugin, ScanStateStore
    from plugins.scanner import scan_chunks, resumir
    from plugins.demo_data import JIRA_DEMO_TRECHOS, JIRA_DEMO_PROJETOS

    tab_conn, tab_scan, tab_res, tab_acoes, tab_agend = st.tabs(
        ["Conexao", "Scan", "Resultados", "Acoes", "Agendamentos"]
    )

    # ── Conexao ───────────────────────────────────────────────────────────────
    with tab_conn:
        _jp_state = st.session_state.jira_plugin
        if _jp_state is not None:
            if _jp_state == "demo":
                st.info("Modo Demo ativo. Usando dados simulados.")
            else:
                st.success("Conectado ao Jira.")
            if st.button("Desconectar", key="jira_desconect"):
                st.session_state.jira_plugin = None
                st.session_state.jira_projetos = []
                st.rerun()
        else:
            st.markdown(f'<p style="font-size:13px;color:{TM};">Conecte ao Jira Cloud ou Server/Data Center para varredura real. Sem credenciais, explore com o modo Demo.</p>', unsafe_allow_html=True)

            _jira_tipo = st.radio(
                "Tipo de instalacao",
                ["Cloud (Atlassian Cloud)", "Server / Data Center (on-premises)"],
                horizontal=True,
                key="jira_tipo_radio",
                label_visibility="collapsed",
            )
            _jira_cloud = (_jira_tipo == "Cloud (Atlassian Cloud)")

            if _jira_cloud:
                st.markdown(
                    f'<p style="font-size:12px;color:{TM};margin-bottom:4px;">'
                    'Cloud: use o email da conta Atlassian + API Token gerado em '
                    'atlassian.com > Account Settings > Security > API tokens.</p>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<p style="font-size:12px;color:{TM};margin-bottom:4px;">'
                    'Server/DC: use <b>PAT</b> (Personal Access Token, Jira 8.14+ / Data Center) '
                    '— deixe o campo Usuario em branco. Para versoes antigas, informe usuario + senha.</p>',
                    unsafe_allow_html=True,
                )

            with st.form("jira_conn"):
                _ph_url = "https://empresa.atlassian.net" if _jira_cloud else "https://jira.empresa.com.br"
                url = st.text_input("URL do Jira", placeholder=_ph_url)
                _lbl_usr = "Email" if _jira_cloud else "Usuario (opcional — deixe em branco para PAT)"
                usuario = st.text_input(_lbl_usr)
                _lbl_tok = "Token de API" if _jira_cloud else "PAT ou Senha"
                _hlp_tok = (
                    "Gere em: atlassian.com > Account Settings > Security > API tokens"
                    if _jira_cloud else
                    "PAT: Jira > menu de usuario > Personal Access Tokens"
                )
                token = st.text_input(_lbl_tok, type="password", help=_hlp_tok)
                c1, c2 = st.columns(2)
                conectar = c1.form_submit_button("Conectar", use_container_width=True)
                demo = c2.form_submit_button("Usar Demo (sem credenciais)", use_container_width=True)

            if conectar and url and token:
                if _jira_cloud and not usuario:
                    st.error("Email obrigatorio para Jira Cloud.")
                else:
                    _p = JiraPlugin()
                    _res = _p.conectar(url, usuario, token, _jira_cloud)
                    if _res["ok"]:
                        st.session_state.jira_plugin = _p
                        st.success(_res["message"])
                        st.rerun()
                    else:
                        st.error(_res["message"])

            if demo:
                st.session_state.jira_plugin = "demo"
                st.session_state.jira_projetos = JIRA_DEMO_PROJETOS
                st.rerun()

    # ── Scan ──────────────────────────────────────────────────────────────────
    with tab_scan:
        _store = ScanStateStore()
        _is_demo = st.session_state.jira_plugin == "demo"
        _is_real = st.session_state.jira_plugin not in (None, "demo")

        if st.session_state.jira_plugin is None:
            st.warning("Conecte ao Jira na aba Conexao para executar a varredura.")
            st.stop()

        if _is_demo:
            st.info("Modo Demo — usando dados fictícios com PII e secrets simulados.")

        # ── Listagem de projetos ───────────────────────────────────────────
        sec_hdr("Projetos Disponiveis")

        _projetos = st.session_state.jira_projetos
        _col_load, _col_info = st.columns([2, 5])
        with _col_load:
            _lbl_btn = "Atualizar lista" if _projetos else "Carregar Projetos"
            if st.button(_lbl_btn, use_container_width=True):
                if _is_demo:
                    st.session_state.jira_projetos = JIRA_DEMO_PROJETOS
                else:
                    with st.spinner("Buscando projetos e contando issues (paralelo)..."):
                        st.session_state.jira_projetos = (
                            st.session_state.jira_plugin.listar_projetos()
                        )
                st.rerun()
        with _col_info:
            if _projetos:
                _total_cards = sum(p.get("count", 0) for p in _projetos if p.get("count", 0) > 0)
                st.markdown(
                    f'<p style="font-size:12px;color:{TM};padding-top:8px;">'
                    f'{len(_projetos)} projetos — {_total_cards:,} cards no total</p>',
                    unsafe_allow_html=True,
                )

        if _projetos:
            _render_projetos_tabela(_projetos)

            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
            sec_hdr("Selecionar Projetos para Varrer")

            _selecao_modo = st.radio(
                "Escopo",
                ["Todos os projetos acessiveis", "Selecionar projetos especificos"],
                horizontal=True,
                key="jira_selecao_modo",
            )

            if _selecao_modo == "Selecionar projetos especificos":
                _todas_chaves = [p["key"] for p in _projetos]
                _selecionados = st.multiselect(
                    "Projetos",
                    options=_todas_chaves,
                    default=st.session_state.jira_proj_selecionados or _todas_chaves[:1],
                    format_func=lambda k: f"{k} — {next((p['name'] for p in _projetos if p['key'] == k), k)}",
                    key="jira_multiselect",
                )
                st.session_state.jira_proj_selecionados = _selecionados
                _total_sel = sum(
                    p.get("count", 0)
                    for p in _projetos
                    if p["key"] in _selecionados and p.get("count", 0) > 0
                )
                if _selecionados:
                    st.markdown(
                        f'<p style="font-size:11px;color:{TM};">Estimativa: ~{_total_sel:,} cards nos projetos selecionados</p>',
                        unsafe_allow_html=True,
                    )
            else:
                st.session_state.jira_proj_selecionados = []
                _total_cards_todos = sum(p.get("count", 0) for p in _projetos if p.get("count", 0) > 0)
                if _total_cards_todos > 5000:
                    st.warning(
                        f"Todos os projetos somam ~{_total_cards_todos:,} cards. "
                        "Use o scan incremental ou limite de issues para evitar longas esperas."
                    )

        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        sec_hdr("Opcoes de Varredura")
        _col1, _col2 = st.columns(2)
        with _col1:
            _proj_ref = (
                (st.session_state.jira_proj_selecionados or ["todos"])
                if _projetos else ["todos"]
            )
            _proj_ref_key = "_".join(_proj_ref[:3])
            _ultimo = _store.last_scan_date_str("jira", _proj_ref_key) if _proj_ref_key != "todos" else None
            _incremental = st.checkbox(
                f"Scan incremental{f' (desde {_ultimo})' if _ultimo else ' (primeiro scan = completo)'}",
                value=bool(_ultimo),
                key="jira_incr",
            )
            _max_issues = st.number_input(
                "Limite de issues por projeto (0 = sem limite)",
                value=500, step=100, min_value=0, key="jira_max",
            )
        with _col2:
            _incluir_anexos = st.checkbox("Incluir anexos (PDF, imagens, DOCX)", value=False, key="jira_anexos")
            _conf_scan_jira = st.slider(
                "Confianca minima do scan (%)",
                min_value=0, max_value=100, value=0, step=5,
                key="jira_conf_scan",
                help="Deteccoes com confianca abaixo deste valor sao descartadas na origem. "
                     "Aumente para reduzir falsos positivos (ex: 70%).",
            )
            if _is_demo and not _projetos:
                st.info("Clique em 'Carregar Projetos' para ver os projetos disponíveis.")

        if st.button("Executar Varredura Jira", use_container_width=True, key="btn_jira_scan"):
            _analyzer = get_analyzer()
            _chunks: list = []
            _proj_para_escanear = st.session_state.jira_proj_selecionados or [""]

            with st.status("Executando varredura Jira...", expanded=True) as _status:
                if _is_demo:
                    st.write(f"Modo demo: {len(JIRA_DEMO_TRECHOS)} chunks carregados.")
                    _chunks = list(JIRA_DEMO_TRECHOS)
                else:
                    _plugin_jira: JiraPlugin = st.session_state.jira_plugin
                    _desde = _store.last_scan_date_str("jira", _proj_ref_key) if _incremental and _proj_ref_key != "todos" else ""
                    _total_issues_count = 0

                    for _pkey in _proj_para_escanear:
                        _label_proj = _pkey or "todos os projetos"
                        st.write(f"Buscando issues — projeto: {_label_proj}...")
                        _issues = _plugin_jira.buscar_issues(
                            _pkey,
                            desde=_desde,
                            max_total=int(_max_issues),
                        )
                        st.write(f"  {len(_issues)} issues. Extraindo texto...")
                        _total_issues_count += len(_issues)
                        for _issue in _issues:
                            _chunks.extend(_plugin_jira.extrair_textos(_issue))

                        if _incluir_anexos and _issues:
                            from plugins.attachment_scanner import escanear_anexos
                            _pares: list = []
                            for _issue in _issues:
                                for _att in _plugin_jira.listar_anexos(_issue.key):
                                    try:
                                        _pares.append((_att, _plugin_jira.baixar_anexo(_att.url_download)))
                                    except Exception:
                                        pass
                            if _pares:
                                st.write(f"  Escaneando {len(_pares)} anexos...")
                                _res_anx = escanear_anexos(_pares, _analyzer)
                                for _ra in _res_anx:
                                    if _ra.resultado:
                                        _chunks.append(_ra.resultado.chunk)

                    if _proj_ref_key != "todos":
                        _store.set_last_scan("jira", _proj_ref_key, total_items=_total_issues_count)

                st.write(f"Processando {len(_chunks)} chunks em paralelo...")
                _resultados = scan_chunks(_chunks, _analyzer, min_confianca=_conf_scan_jira / 100)
                _metricas = resumir(_resultados)
                st.session_state.jira_resultados = _resultados
                st.session_state.jira_metricas = _metricas
                _add_history("Jira", "+".join(_proj_para_escanear[:3]) or "demo", _metricas)
                _status.update(
                    label=f"Varredura concluida — {_metricas['total_deteccoes']} deteccoes.",
                    state="complete",
                )

    # ── Resultados ────────────────────────────────────────────────────────────
    with tab_res:
        render_resultados(
            st.session_state.jira_resultados,
            st.session_state.jira_metricas,
            "Jira",
        )

    # ── Acoes ─────────────────────────────────────────────────────────────────
    with tab_acoes:
        _jp = st.session_state.jira_plugin
        _is_demo_ac = _jp == "demo"
        _is_real_ac = _jp not in (None, "demo")
        _res_jira = st.session_state.jira_resultados

        if _jp is None:
            st.markdown(f"""
            <div style="background:{BPW};border:1px solid {BOR};border-radius:8px;
              padding:36px;text-align:center;color:{TM};margin:2rem 0;">
              <div style="font-size:14px;font-weight:600;color:{TD};margin-bottom:6px;">
                Sem conexao ativa
              </div>
              Conecte ao Jira na aba Conexao para habilitar acoes.
            </div>
            """, unsafe_allow_html=True)
            st.stop()

        if _is_demo_ac:
            st.markdown(f"""
            <div style="background:{BPW};border:1.5px solid {BORM};border-radius:8px;
              padding:14px 18px;margin-bottom:18px;">
              <div style="font-size:13px;font-weight:700;color:{TD};margin-bottom:3px;">
                Modo Demo — acoes de escrita desabilitadas
              </div>
              <div style="font-size:12px;color:{TM};">
                Conecte ao Jira real na aba <b>Conexao</b> para habilitar as acoes de remediacao.
                As opcoes abaixo mostram exatamente o fluxo que estara disponivel.
              </div>
            </div>
            """, unsafe_allow_html=True)

        # ── Seletor visual de modo ─────────────────────────────────────────
        sec_hdr("O Que Voce Quer Fazer com os Cards?")
        st.markdown(
            f'<p style="font-size:12px;color:{TM};margin-bottom:12px;">'
            'Escolha uma acao. Cada uma tem um impacto diferente no Jira — leia antes de aplicar.</p>',
            unsafe_allow_html=True,
        )

        _cols_modo = st.columns(5, gap="small")
        for _col, _modo in zip(_cols_modo, ["readonly", "properties", "label", "comment", "scrub"]):
            with _col:
                _render_modo_card(
                    _modo,
                    selecionado=(st.session_state.acoes_modo == _modo),
                    disabled=_is_demo_ac,
                )

        _modo_atual = st.session_state.acoes_modo
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        # ── Configuracoes de Email (Microsoft Graph) ──────────────────────
        with st.expander("Configuracoes de Email (Microsoft Graph)", expanded=False):
            # Lazy load templates
            if st.session_state.email_templates is None:
                st.session_state.email_templates = carregar_templates()

            _em_c1, _em_c2 = st.columns([3, 1], gap="medium")
            with _em_c1:
                _token_input = st.text_input(
                    "Token Microsoft Graph (validade ~1h)",
                    value=st.session_state.graph_token,
                    type="password",
                    placeholder="Cole aqui o Bearer token do Graph Explorer",
                    key="graph_token_input",
                )
                if _token_input != st.session_state.graph_token:
                    st.session_state.graph_token = _token_input
                    st.session_state.graph_me = None

                _dest_input = st.text_input(
                    "Destinatario padrao",
                    value=st.session_state.email_dest_padrao,
                    placeholder="admin@empresa.com",
                    key="email_dest_input",
                    help="Email pre-preenchido nos formularios de envio. Editavel por card.",
                )
                if _dest_input != st.session_state.email_dest_padrao:
                    st.session_state.email_dest_padrao = _dest_input

            with _em_c2:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if st.button("Validar Token", key="btn_validar_token", use_container_width=True):
                    if not st.session_state.graph_token:
                        st.warning("Cole o token antes de validar.")
                    else:
                        _gp = GraphEmailPlugin(st.session_state.graph_token)
                        _vr = _gp.verificar_token()
                        if _vr["ok"]:
                            st.session_state.graph_me = {"nome": _vr["nome"], "email": _vr["email"]}
                            st.success(_vr["mensagem"])
                        else:
                            st.session_state.graph_me = None
                            st.error(_vr["mensagem"])

            if st.session_state.graph_me:
                st.markdown(
                    f'<p style="font-size:12px;color:{GD};margin:2px 0 12px;">'
                    f'Autenticado como <b>{st.session_state.graph_me["nome"]}</b> '
                    f'({st.session_state.graph_me["email"]})</p>',
                    unsafe_allow_html=True,
                )

            # ── Gerenciamento de templates ─────────────────────────────────
            st.markdown(
                f'<div style="font-size:13px;font-weight:700;color:{TD};'
                f'margin:14px 0 6px;">Templates de Email</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<p style="font-size:11.5px;color:{TM};margin-bottom:8px;">'
                f'Placeholders disponiveis: '
                + " ".join(f'<code>{p}</code>' for p, _ in EMAIL_PLACEHOLDERS)
                + "</p>",
                unsafe_allow_html=True,
            )

            _tpls = st.session_state.email_templates
            _tpl_nomes = [t["nome"] for t in _tpls]

            # Editar templates existentes
            for _ti, _tpl in enumerate(_tpls):
                _has_sig = bool(_tpl.get("assinatura"))
                _sig_tag = " [com assinatura]" if _has_sig else ""
                with st.expander(f"Template: {_tpl['nome']}{_sig_tag}", expanded=False):
                    _t_nome    = st.text_input("Nome", value=_tpl["nome"], key=f"tpl_nome_{_ti}")
                    _t_assunto = st.text_input("Assunto", value=_tpl["assunto"], key=f"tpl_assunto_{_ti}")
                    _t_corpo   = st.text_area(
                        "Corpo (HTML)",
                        value=_tpl["corpo"],
                        height=180,
                        key=f"tpl_corpo_{_ti}",
                    )
                    st.markdown(
                        f'<div style="font-size:12px;font-weight:600;color:{TD};margin:10px 0 4px;">'
                        f'Assinatura — cole do Outlook e clique em "Salvar assinatura"</div>',
                        unsafe_allow_html=True,
                    )
                    _t_assinatura = html_paste_editor(
                        value=_tpl.get("assinatura", ""),
                        key=f"tpl_assinatura_{_ti}",
                    )
                    if _tpl.get("imagens"):
                        st.markdown(
                            f'<p style="font-size:11px;color:{TM};margin-top:4px;">'
                            f'{len(_tpl["imagens"])} imagem(ns) salva(s) neste template.</p>',
                            unsafe_allow_html=True,
                        )
                    _tc1, _tc2 = st.columns(2, gap="small")
                    with _tc1:
                        if st.button("Salvar template", key=f"tpl_salvar_{_ti}", use_container_width=True):
                            _assin_clean, _imgs_novos = extrair_imagens_data_uri(_t_assinatura)
                            _tpls[_ti] = {
                                "nome": _t_nome,
                                "assunto": _t_assunto,
                                "corpo": _t_corpo,
                                "assinatura": _assin_clean,
                                "imagens": _imgs_novos,
                            }
                            salvar_templates(_tpls)
                            st.session_state.email_templates = _tpls
                            st.success("Template salvo.")
                            st.rerun()
                    with _tc2:
                        if st.button("Excluir template", key=f"tpl_del_{_ti}", use_container_width=True):
                            _tpls.pop(_ti)
                            salvar_templates(_tpls)
                            st.session_state.email_templates = _tpls
                            st.rerun()

            # Novo template
            with st.expander("+ Adicionar novo template", expanded=False):
                _nt_nome    = st.text_input("Nome do template", key="novo_tpl_nome")
                _nt_assunto = st.text_input("Assunto", key="novo_tpl_assunto")
                _nt_corpo   = st.text_area(
                    "Corpo (HTML)", height=140, key="novo_tpl_corpo",
                    placeholder="<p>Prezado(a),</p><p>...</p>",
                )
                st.markdown(
                    f'<div style="font-size:12px;font-weight:600;color:{TD};margin:8px 0 4px;">'
                    f'Assinatura (opcional)</div>',
                    unsafe_allow_html=True,
                )
                _nt_assinatura = html_paste_editor(value="", key="novo_tpl_assinatura")
                if st.button("Adicionar Template", key="btn_add_tpl", use_container_width=False):
                    if _nt_nome and _nt_assunto:
                        _assin_c, _imgs_c = extrair_imagens_data_uri(_nt_assinatura)
                        _tpls.append({
                            "nome": _nt_nome,
                            "assunto": _nt_assunto,
                            "corpo": _nt_corpo,
                            "assinatura": _assin_c,
                            "imagens": _imgs_c,
                        })
                        salvar_templates(_tpls)
                        st.session_state.email_templates = _tpls
                        st.success(f"Template '{_nt_nome}' adicionado.")
                        st.rerun()
                    else:
                        st.warning("Preencha pelo menos nome e assunto.")

        # ── Sem resultados ainda ──────────────────────────────────────────
        if not _res_jira:
            st.markdown(
                f'<p style="font-size:13px;color:{TMU};margin-top:4px;">'
                'Execute a varredura (aba Scan) para ver os cards com deteccoes aqui.</p>',
                unsafe_allow_html=True,
            )
        else:
            # Cache de permissoes por card {issue_key: True/False/None}
            if "acoes_permissoes" not in st.session_state:
                st.session_state.acoes_permissoes = {}

            _issues_detectadas = sorted({
                r.chunk.get("issue_key", "")
                for r in _res_jira if r.total_deteccoes > 0 and r.chunk.get("issue_key")
            })

            # Tipos detectados apenas de issues que realmente têm PII
            _todos_tipos = sorted({
                d.entidade
                for r in _res_jira
                if r.total_deteccoes > 0
                for d in r.deteccoes
            })

            # ── Filtros — sempre renderizados (mesmo sem detecções) ────────
            sec_hdr("Filtros")
            _fc1, _fc2, _fc3 = st.columns([3, 2, 2], gap="large")
            with _fc1:
                _tipo_filtro: list[str] = st.multiselect(
                    f"Tipo de dado ({len(_todos_tipos)} detectados)" if _todos_tipos else "Tipo de dado",
                    _todos_tipos,
                    key="acoes_tipo_filtro",
                    placeholder="Todos os tipos" if _todos_tipos else "Rode o scan para ver os tipos",
                    disabled=not _todos_tipos,
                )
            with _fc2:
                _alvo = st.radio(
                    "Nivel de risco",
                    ["Qualquer deteccao", "Apenas HIGH ou SECRET"],
                    key="jira_action_alvo",
                )
            with _fc3:
                _conf_min = st.slider(
                    "Confianca minima (%)",
                    min_value=0, max_value=100, value=0, step=5,
                    key="acoes_conf_min",
                    help="Deteccoes abaixo deste limiar sao ignoradas (falsos positivos)",
                )

            if not _issues_detectadas:
                st.markdown(
                    f'<p style="font-size:13px;color:{TMU};margin-top:8px;">'
                    'Nenhuma deteccao encontrada no ultimo scan Jira. '
                    'Execute a varredura na aba Scan com dados que contenham PII.</p>',
                    unsafe_allow_html=True,
                )

            # Funcao auxiliar: deteccoes de um card respeitando filtros
            def _dets_filtradas(resultados):
                out = []
                for _r in resultados:
                    for _d in _r.deteccoes:
                        if _tipo_filtro and _d.entidade not in _tipo_filtro:
                            continue
                        if _d.confianca * 100 < _conf_min:
                            continue
                        out.append((_r, _d))
                return out

            # Aplica filtro de risco e tipo nas issues
            _issues_filtradas = []
            for _ik in _issues_detectadas:
                _cr = [r for r in _res_jira if r.chunk.get("issue_key") == _ik]
                _df = _dets_filtradas(_cr)
                if not _df:
                    continue
                if _alvo == "Apenas HIGH ou SECRET" and not any(
                    _d.nivel == "HIGH" or _d.is_secret for _, _d in _df
                ):
                    continue
                _issues_filtradas.append(_ik)

            st.markdown(
                f'<p style="font-size:12px;color:{TM};margin:4px 0 12px;">'
                f'{len(_issues_filtradas)} cards com deteccoes (de {len(_issues_detectadas)} total)'
                f'{"  —  filtro ativo" if _tipo_filtro or _conf_min > 0 else ""}</p>',
                unsafe_allow_html=True,
            )

            # ── Verificar permissao em todos ──────────────────────────────
            _cp1, _cp2, _ = st.columns([2, 2, 3], gap="small")
            with _cp1:
                if st.button(
                    "Verificar permissao em todos" if _is_real_ac else "Indisponivel no demo",
                    key="btn_perm_all",
                    disabled=not _is_real_ac,
                    use_container_width=True,
                ):
                    with st.spinner(f"Verificando {len(_issues_filtradas[:30])} cards..."):
                        for _ik in _issues_filtradas[:30]:
                            try:
                                _p = _jp.actions.checar_permissao(_ik)
                                st.session_state.acoes_permissoes[_ik] = _p["pode_editar"]
                            except Exception:
                                st.session_state.acoes_permissoes[_ik] = False
                    st.rerun()
            with _cp2:
                if st.button("Limpar cache de permissoes", key="btn_perm_clear", use_container_width=True):
                    st.session_state.acoes_permissoes = {}
                    st.rerun()

            # ── Cards expandiveis com deteccoes e acoes por card ──────────
            sec_hdr("Cards com Deteccoes")

            if not _issues_filtradas:
                st.info("Nenhum card corresponde aos filtros selecionados.")
            else:
                for _ik in _issues_filtradas[:60]:
                    _cr = [r for r in _res_jira if r.chunk.get("issue_key") == _ik]
                    _df = _dets_filtradas(_cr)
                    _tipos_card = sorted({_d.entidade for _, _d in _df})
                    _tem_high = any(_d.nivel == "HIGH" for _, _d in _df)
                    _tem_secret = any(_d.is_secret for _, _d in _df)
                    _perm_status = st.session_state.acoes_permissoes.get(_ik)

                    # Label do expander com resumo
                    _risco_tag = " [HIGH]" if _tem_high else (" [SECRET]" if _tem_secret else "")
                    _tipos_str = ", ".join(_tipos_card[:4])
                    if len(_tipos_card) > 4:
                        _tipos_str += f" +{len(_tipos_card)-4}"
                    _perm_tag = "" if _perm_status is None else (" [SEM PERMISSAO]" if not _perm_status else " [PERMISSAO OK]")
                    _exp_label = f"{_ik}{_risco_tag} — {len(_df)} deteccoes — {_tipos_str}{_perm_tag}"

                    with st.expander(_exp_label, expanded=False):

                        # Status de permissao
                        if _perm_status is False:
                            st.warning(
                                "Sem permissao de edicao neste card. "
                                "Verifique se seu token tem permissao de escrita no projeto. "
                                "Acoes de escrita serao bloqueadas."
                            )
                        elif _perm_status is True:
                            st.success("Permissao de edicao confirmada.")

                        # Tabela de deteccoes
                        _linhas_det = []
                        for _r, _d in _df:
                            _linhas_det.append({
                                "Campo": _r.chunk.get("campo", "—"),
                                "Tipo de Dado": _d.entidade,
                                "Valor (mascarado)": _d.valor_display,
                                "Nivel": _d.nivel,
                                "Confianca": f"{_d.confianca:.0%}",
                                "Secret": "Sim" if _d.is_secret else "",
                            })
                        st.dataframe(
                            pd.DataFrame(_linhas_det),
                            use_container_width=True,
                            hide_index=True,
                        )

                        # Botoes por card
                        _bc1, _bc2, _bc3 = st.columns(3, gap="small")

                        with _bc1:
                            if st.button(
                                "Verificar permissao",
                                key=f"perm_{_ik}",
                                disabled=not _is_real_ac,
                                use_container_width=True,
                            ):
                                try:
                                    _p = _jp.actions.checar_permissao(_ik)
                                    st.session_state.acoes_permissoes[_ik] = _p["pode_editar"]
                                    if _p["pode_editar"]:
                                        st.success(_p["mensagem"])
                                    else:
                                        st.warning(_p["mensagem"])
                                except Exception as _pe:
                                    st.error(f"Erro ao verificar: {_pe}")
                                    st.session_state.acoes_permissoes[_ik] = False
                                st.rerun()

                        with _bc2:
                            if _modo_atual == "scrub":
                                # Só habilita preview se permissão confirmada
                                _preview_ok = _is_real_ac and _perm_status is True
                                if st.button(
                                    "Carregar Preview" if _preview_ok else (
                                        "Sem permissao" if _perm_status is False
                                        else "Verificar permissao primeiro"
                                    ),
                                    key=f"preview_{_ik}",
                                    disabled=not _preview_ok,
                                    use_container_width=True,
                                ):
                                    _chunks_ik = [r for r in _res_jira if r.chunk.get("issue_key") == _ik]
                                    _prev = _jp.actions.scrub_preview(_ik, _chunks_ik)
                                    st.session_state.scrub_preview = _prev
                                    st.session_state.scrub_issue_selecionada = _ik
                                    st.rerun()

                        with _bc3:
                            # Para scrub: requer permissão explicitamente confirmada (True)
                            # Para outros modos: basta não ter sido negada
                            if _modo_atual == "scrub":
                                _can_write = _is_real_ac and _perm_status is True
                            else:
                                _can_write = _is_real_ac and (_perm_status is not False)
                            _btn_label_card = (
                                "Aplicar Scrub" if _modo_atual == "scrub"
                                else "Corrigir Este Card"
                            )
                            if _modo_atual != "scrub":
                                if st.button(
                                    _btn_label_card if _can_write else "Sem permissao",
                                    key=f"apply_{_ik}",
                                    disabled=not _can_write,
                                    use_container_width=True,
                                    type="primary",
                                ):
                                    _ts_now = datetime.now(timezone.utc).isoformat()
                                    with st.status(f"Aplicando em {_ik}...", expanded=True):
                                        _ok_c, _err_c = 0, []
                                        for _ar in _jp.actions.aplicar(_ik, _cr, _ts_now, _modo_atual):
                                            if _ar["ok"]:
                                                _ok_c += 1
                                                st.write(f"{_ar['acao']}: {_ar['mensagem']}")
                                            else:
                                                _err_c.append(_ar["mensagem"])
                                        for _em in _err_c:
                                            st.error(_em)

                        # Botao de email por card
                        _tem_graph = bool(st.session_state.graph_token)
                        _email_key = f"show_email_{_ik}"
                        if _email_key not in st.session_state:
                            st.session_state[_email_key] = False

                        _bem_c1, _bem_c2 = st.columns([1, 3], gap="small")
                        with _bem_c1:
                            if st.button(
                                "Enviar Email",
                                key=f"btn_email_{_ik}",
                                disabled=not _tem_graph,
                                use_container_width=True,
                                help="Requer token Graph configurado acima" if not _tem_graph else "",
                            ):
                                st.session_state[_email_key] = not st.session_state[_email_key]

                        # Formulario de email inline
                        if st.session_state[_email_key] and _tem_graph:
                            _tpls_email = st.session_state.email_templates or []
                            _tpl_nomes_email = [t["nome"] for t in _tpls_email]
                            _ef1, _ef2 = st.columns([2, 2], gap="medium")
                            with _ef1:
                                _sel_tpl = st.selectbox(
                                    "Template",
                                    _tpl_nomes_email,
                                    key=f"email_tpl_{_ik}",
                                )
                                _dest_card = st.text_input(
                                    "Para",
                                    value=st.session_state.email_dest_padrao,
                                    key=f"email_dest_{_ik}",
                                    placeholder="destinatario@empresa.com",
                                )
                                _cc_card = st.text_input(
                                    "CC (opcional)",
                                    key=f"email_cc_{_ik}",
                                    placeholder="outro@empresa.com",
                                )
                            with _ef2:
                                _data_str = datetime.now(timezone.utc).strftime("%d/%m/%Y")
                                _solicitante = (
                                    st.session_state.graph_me["email"]
                                    if st.session_state.graph_me
                                    else "Data Protection Scanner"
                                )
                                _vars_email = variaveis_de_chunks(
                                    _ik, _cr,
                                    solicitante=_solicitante,
                                    data=_data_str,
                                )
                                _tpl_obj = next(
                                    (t for t in _tpls_email if t["nome"] == _sel_tpl),
                                    _tpls_email[0] if _tpls_email else {},
                                )
                                _filled = preencher_template(_tpl_obj, _vars_email)
                                st.markdown(
                                    f'<div style="font-size:11px;color:{TM};margin-bottom:2px;'
                                    f'font-weight:600;">Preview do assunto</div>'
                                    f'<div style="font-size:12px;padding:4px 8px;background:{BPW};'
                                    f'border-radius:4px;border:1px solid {BOR};">'
                                    f'{_filled["assunto"]}</div>',
                                    unsafe_allow_html=True,
                                )
                            if st.button(
                                "Enviar Agora",
                                key=f"email_enviar_{_ik}",
                                type="primary",
                                disabled=not _dest_card.strip(),
                            ):
                                _gp_send = GraphEmailPlugin(st.session_state.graph_token)
                                _cc_list = [c.strip() for c in _cc_card.split(",") if c.strip()]
                                _res_email = _gp_send.enviar(
                                    para=[_dest_card.strip()],
                                    assunto=_filled["assunto"],
                                    corpo_html=_filled["corpo"],
                                    cc=_cc_list or None,
                                    assinatura_html=_tpl_obj.get("assinatura", ""),
                                    imagens=_tpl_obj.get("imagens"),
                                )
                                if _res_email["ok"]:
                                    st.success(_res_email["mensagem"])
                                    st.session_state[_email_key] = False
                                else:
                                    st.error(_res_email["mensagem"])

                        # Para scrub sem permissão verificada: instrução clara
                        if _modo_atual == "scrub" and _perm_status is None:
                            st.info(
                                "Clique em **Verificar permissao** antes de carregar o preview "
                                "e aplicar o scrubbing neste card.",
                                icon="ℹ️",
                            )

                        # Preview de scrub para este card
                        if (
                            _modo_atual == "scrub"
                            and st.session_state.scrub_preview
                            and st.session_state.scrub_issue_selecionada == _ik
                        ):
                            st.markdown(f"""
                            <div style="background:{RBG};border:1px solid {RD};border-radius:8px;
                              padding:10px 14px;margin:10px 0 6px;">
                              <span style="font-size:11.5px;font-weight:700;color:{RD};">
                                ATENCAO: Scrubbing e irreversivel — o texto original sera perdido.
                              </span>
                            </div>
                            """, unsafe_allow_html=True)

                            for _pv in st.session_state.scrub_preview:
                                st.markdown(
                                    f"**Campo:** {_pv['campo']}  |  "
                                    f"Entidades: {', '.join(_pv['entidades'])}"
                                )
                                _pv_c1, _pv_c2 = st.columns(2, gap="medium")
                                _pv_c1.markdown(
                                    f'<div style="font-size:11px;color:{TM};margin-bottom:2px;'
                                    f'font-weight:600;">ANTES</div>'
                                    f'<div class="anon-panel" style="min-height:60px;'
                                    f'max-height:120px;">{_pv["antes"]}</div>',
                                    unsafe_allow_html=True,
                                )
                                _pv_c2.markdown(
                                    f'<div style="font-size:11px;color:{GD};margin-bottom:2px;'
                                    f'font-weight:600;">DEPOIS (scrubbed)</div>'
                                    f'<div class="anon-panel" style="min-height:60px;'
                                    f'max-height:120px;border-color:{GD}40;">{_pv["depois"]}</div>',
                                    unsafe_allow_html=True,
                                )

                            _confirmar = st.checkbox(
                                "Entendi que esta acao e irreversivel",
                                key=f"scrub_confirma_{_ik}",
                            )
                            if st.button(
                                "Aplicar Scrubbing Agora",
                                key=f"scrub_aplicar_{_ik}",
                                disabled=not (_can_write and _confirmar),
                                use_container_width=True,
                                type="primary",
                            ):
                                _chunks_scrub = [r for r in _res_jira if r.chunk.get("issue_key") == _ik]
                                with st.status(f"Aplicando scrub em {_ik}...", expanded=True) as _scrub_sts:
                                    _scrub_ok, _scrub_errs = 0, []
                                    for _ar in _jp.actions.scrub_aplicar(_ik, _chunks_scrub):
                                        if _ar["ok"]:
                                            _scrub_ok += 1
                                            st.write(f"{_ar['acao']}: {_ar['mensagem']}")
                                        else:
                                            _scrub_errs.append(_ar["mensagem"])
                                    _scrub_sts.update(
                                        label=f"Scrub concluido — {_scrub_ok} campo(s) anonimizado(s).",
                                        state="complete" if not _scrub_errs else "error",
                                    )
                                for _se in _scrub_errs:
                                    st.error(_se)
                                # Limpa preview após aplicar
                                st.session_state.scrub_preview = []
                                st.session_state.scrub_issue_selecionada = None

            # ── Acoes em Massa ────────────────────────────────────────────
            if _issues_filtradas:
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                sec_hdr("Acoes em Massa")

                _bm_c1, _bm_c2 = st.columns(2, gap="large")

                # ── Correcao em massa ──────────────────────────────────────
                with _bm_c1:
                    st.markdown(
                        f'<p style="font-size:12px;color:{TM};margin-bottom:8px;">'
                        f'Aplica o modo <b>{_MODO_INFO[_modo_atual]["titulo"]}</b> em todos os '
                        f'{len(_issues_filtradas)} cards filtrados.</p>',
                        unsafe_allow_html=True,
                    )
                    if _modo_atual == "scrub":
                        st.info("Correcao em massa indisponivel no modo Scrub — aplique card a card.", icon="ℹ️")
                    else:
                        if st.button(
                            "Aplicar Correcao em Todos" if _is_real_ac else "Indisponivel no demo",
                            key="btn_apply_all",
                            disabled=not _is_real_ac,
                            use_container_width=True,
                        ):
                            _ts_now = datetime.now(timezone.utc).isoformat()
                            _erros_bulk: list[str] = []
                            _ok_bulk = 0
                            with st.status("Aplicando correcoes...", expanded=True) as _sts:
                                for _ik in _issues_filtradas:
                                    _cr = [r for r in _res_jira if r.chunk.get("issue_key") == _ik]
                                    _perm = st.session_state.acoes_permissoes.get(_ik)
                                    if _perm is False:
                                        _erros_bulk.append(f"{_ik}: sem permissao (pulado)")
                                        continue
                                    for _ar in _jp.actions.aplicar(_ik, _cr, _ts_now, _modo_atual):
                                        if _ar["ok"]:
                                            _ok_bulk += 1
                                            st.write(f"{_ik}: {_ar['mensagem']}")
                                        else:
                                            _erros_bulk.append(f"{_ik}: {_ar['mensagem']}")
                                _sts.update(
                                    label=f"Concluido — {_ok_bulk} operacoes.",
                                    state="complete" if not _erros_bulk else "error",
                                )
                            for _e in _erros_bulk[:10]:
                                st.error(_e)

                # ── Email em massa ─────────────────────────────────────────
                with _bm_c2:
                    _tem_graph_bulk = bool(st.session_state.graph_token)
                    _tpls_bulk = st.session_state.email_templates or []
                    st.markdown(
                        f'<p style="font-size:12px;color:{TM};margin-bottom:8px;">'
                        f'Envia email para {len(_issues_filtradas)} cards filtrados usando '
                        f'um unico template e destinatario.</p>',
                        unsafe_allow_html=True,
                    )
                    if not _tem_graph_bulk:
                        st.info("Configure o token Graph na secao acima para habilitar.", icon="ℹ️")
                    else:
                        _tpl_nomes_bulk = [t["nome"] for t in _tpls_bulk]
                        _bulk_tpl = st.selectbox(
                            "Template para envio em massa",
                            _tpl_nomes_bulk,
                            key="bulk_email_tpl",
                        ) if _tpl_nomes_bulk else None
                        _bulk_dest = st.text_input(
                            "Destinatario (todos os cards)",
                            value=st.session_state.email_dest_padrao,
                            key="bulk_email_dest",
                            placeholder="admin@empresa.com",
                        )
                        _bulk_cc = st.text_input(
                            "CC (opcional)",
                            key="bulk_email_cc",
                            placeholder="outro@empresa.com",
                        )
                        if st.button(
                            f"Enviar Email para {len(_issues_filtradas)} Cards",
                            key="btn_email_all",
                            disabled=not (_bulk_dest.strip() and _bulk_tpl),
                            use_container_width=True,
                            type="primary",
                        ):
                            _gp_bulk = GraphEmailPlugin(st.session_state.graph_token)
                            _solicitante_bulk = (
                                st.session_state.graph_me["email"]
                                if st.session_state.graph_me else "Data Protection Scanner"
                            )
                            _tpl_obj_bulk = next(
                                (t for t in _tpls_bulk if t["nome"] == _bulk_tpl), {}
                            )
                            _cc_bulk = [c.strip() for c in _bulk_cc.split(",") if c.strip()]
                            _data_bulk = datetime.now(timezone.utc).strftime("%d/%m/%Y")
                            _email_ok_bulk, _email_err_bulk = 0, []
                            with st.status(
                                f"Enviando emails para {len(_issues_filtradas)} cards...",
                                expanded=True,
                            ) as _em_sts:
                                for _ik in _issues_filtradas:
                                    _cr_b = [r for r in _res_jira if r.chunk.get("issue_key") == _ik]
                                    _vars_b = variaveis_de_chunks(
                                        _ik, _cr_b,
                                        solicitante=_solicitante_bulk,
                                        data=_data_bulk,
                                    )
                                    _filled_b = preencher_template(_tpl_obj_bulk, _vars_b)
                                    _res_b = _gp_bulk.enviar(
                                        para=[_bulk_dest.strip()],
                                        assunto=_filled_b["assunto"],
                                        corpo_html=_filled_b["corpo"],
                                        cc=_cc_bulk or None,
                                        assinatura_html=_tpl_obj_bulk.get("assinatura", ""),
                                        imagens=_tpl_obj_bulk.get("imagens"),
                                    )
                                    if _res_b["ok"]:
                                        _email_ok_bulk += 1
                                        st.write(f"{_ik}: enviado")
                                    else:
                                        _email_err_bulk.append(f"{_ik}: {_res_b['mensagem']}")
                                _em_sts.update(
                                    label=f"Concluido — {_email_ok_bulk}/{len(_issues_filtradas)} emails enviados.",
                                    state="complete" if not _email_err_bulk else "error",
                                )
                            for _ee in _email_err_bulk[:10]:
                                st.error(_ee)

    # ── Agendamentos ──────────────────────────────────────────────────────────
    with tab_agend:
        from plugins.scheduler import ScanScheduler as _SS, FREQ_CRON, DIA_SEMANA_NUM, _cron_para_descricao
        _sched = get_scheduler()
        _jp_ag = st.session_state.jira_plugin

        if not _sched.disponivel:
            st.warning("APScheduler nao instalado. Execute: `pip install apscheduler>=3.10`")

        sec_hdr("Criar Agendamento")
        _ag_col1, _ag_col2 = st.columns(2, gap="large")
        with _ag_col1:
            _ag_nome = st.text_input("Nome do agendamento", placeholder="Scan semanal PROJ", key="ag_nome")
            _ag_tipo = st.radio("Tipo", ["Jira", "Confluence"], horizontal=True, key="ag_tipo")

            _ag_projs_disp = [p["key"] for p in (st.session_state.jira_projetos or JIRA_DEMO_PROJETOS)]
            _ag_proj_op = st.multiselect(
                "Projetos (vazio = todos)",
                _ag_projs_disp,
                key="ag_projetos",
                help="Deixe em branco para incluir todos os projetos acessiveis.",
            )
            _ag_acao = st.selectbox(
                "Acao automatica apos scan",
                ["readonly", "properties", "label", "comment"],
                key="ag_acao",
                help="properties: invisivel | label: etiqueta | comment: historico publico",
            )

        with _ag_col2:
            _ag_freq = st.radio(
                "Frequencia",
                ["Diario", "Semanal", "Mensal", "Personalizado"],
                key="ag_freq",
            )
            _ag_hora = st.number_input("Hora (0-23)", value=8, min_value=0, max_value=23, key="ag_hora")
            _ag_min = st.number_input("Minuto (0-59)", value=0, min_value=0, max_value=59, key="ag_min")

            if _ag_freq == "Semanal":
                _ag_dia = st.selectbox(
                    "Dia da semana",
                    list(DIA_SEMANA_NUM.keys()),
                    key="ag_dia_sem",
                )
                _ag_cron = f"{_ag_min} {_ag_hora} * * {DIA_SEMANA_NUM[_ag_dia]}"
            elif _ag_freq == "Mensal":
                _ag_dia_mes = st.number_input("Dia do mes (1-28)", value=1, min_value=1, max_value=28, key="ag_dia_mes")
                _ag_cron = f"{_ag_min} {_ag_hora} {_ag_dia_mes} * *"
            elif _ag_freq == "Personalizado":
                _ag_cron = st.text_input(
                    "Expressao cron (min hora dia mes dia_sem)",
                    value="0 8 * * 1",
                    key="ag_cron_custom",
                )
            else:
                _ag_cron = f"{_ag_min} {_ag_hora} * * *"

            st.markdown(
                f'<p style="font-size:11px;color:{TM};margin-top:4px;">'
                f'Agenda: <b>{_cron_para_descricao(_ag_cron)}</b></p>',
                unsafe_allow_html=True,
            )

            _ag_url = ""
            _ag_user = ""
            _ag_token_field = ""
            if _is_real_ac:
                with st.expander("Credenciais para execucao agendada"):
                    _ag_url = st.text_input("URL Jira", key="ag_url")
                    _ag_user = st.text_input("Email", key="ag_user")
                    _ag_token_field = st.text_input("Token", type="password", key="ag_token")
                    st.caption("As credenciais sao armazenadas localmente em SQLite para execucao automatica.")

        if st.button("Criar Agendamento", use_container_width=True, key="btn_criar_ag"):
            if not _ag_nome.strip():
                st.warning("Informe um nome para o agendamento.")
            elif not _sched.disponivel:
                st.error("Instale o APScheduler para habilitar agendamentos.")
            else:
                _sched.criar(
                    nome=_ag_nome.strip(),
                    tipo=_ag_tipo.lower(),
                    projetos=_ag_proj_op,
                    cron=_ag_cron,
                    url=_ag_url,
                    usuario=_ag_user,
                    token=_ag_token_field,
                    auto_acao=_ag_acao,
                )
                st.success(f"Agendamento '{_ag_nome}' criado: {_cron_para_descricao(_ag_cron)}")
                st.rerun()

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        sec_hdr("Agendamentos Ativos")
        _jobs = _sched.listar()
        if not _jobs:
            st.markdown(f'<p style="color:{TMU};font-size:13px;">Nenhum agendamento criado ainda.</p>', unsafe_allow_html=True)
        else:
            for _job in _jobs:
                _prox = _sched.proximo_run(_job["id"])
                _ult = _job["ultimo_run"][:16].replace("T", " ") if _job["ultimo_run"] else "nunca"
                _projs_txt = ", ".join(_job["projetos"]) if _job["projetos"] else "todos"
                _status_cor = GD if _job["ativo"] else TMU

                _jcol1, _jcol2, _jcol3, _jcol4 = st.columns([3, 2, 2, 1])
                _jcol1.markdown(
                    f'<span style="font-size:13px;font-weight:700;color:{TD};">{_job["nome"]}</span><br>'
                    f'<span style="font-size:11px;color:{TM};">{_job["descricao_freq"]} | projetos: {_projs_txt}</span>',
                    unsafe_allow_html=True,
                )
                _jcol2.markdown(
                    f'<span style="font-size:11px;color:{TM};">Proximo run</span><br>'
                    f'<span style="font-size:12px;color:{TD};">{_prox}</span>',
                    unsafe_allow_html=True,
                )
                _jcol3.markdown(
                    f'<span style="font-size:11px;color:{TM};">Ultimo run</span><br>'
                    f'<span style="font-size:12px;color:{TD};">{_ult}</span>',
                    unsafe_allow_html=True,
                )
                with _jcol4:
                    if st.button("Remover", key=f"del_job_{_job['id']}", use_container_width=True):
                        _sched.remover(_job["id"])
                        st.rerun()

        # Resultados de execucoes agendadas
        _hist_ag = _sched.listar_resultados(limit=10)
        if _hist_ag:
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            sec_hdr("Historico de Execucoes Agendadas")
            _df_hist = pd.DataFrame([{
                "Agendamento": h["schedule_nome"],
                "Executado em": h["executado_em"][:16].replace("T", " "),
                "Deteccoes": h["total_deteccoes"],
                "Secrets": h["total_secrets"],
                "Score": f"{h['compliance_score']}%",
            } for h in _hist_ag])
            st.dataframe(_df_hist, use_container_width=True, hide_index=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGINA: VARREDURA CONFLUENCE
# ═════════════════════════════════════════════════════════════════════════════
elif pagina == "Varredura Confluence":
    from plugins import ConfluencePlugin, ScanStateStore
    from plugins.scanner import scan_chunks, resumir
    from plugins.demo_data import CONFLUENCE_DEMO_TRECHOS, CONFLUENCE_DEMO_SPACES

    _ctab_conn, _ctab_scan, _ctab_res, _ctab_agend = st.tabs(
        ["Conexao", "Scan", "Resultados", "Agendamentos"]
    )

    # ── Conexao ───────────────────────────────────────────────────────────────
    with _ctab_conn:
        _cp_state = st.session_state.confluence_plugin
        if _cp_state is not None:
            if _cp_state == "demo":
                st.info("Modo Demo ativo. Usando dados simulados.")
            else:
                st.success("Conectado ao Confluence.")
            if st.button("Desconectar", key="conf_desconect"):
                st.session_state.confluence_plugin = None
                st.session_state.confluence_spaces = []
                st.rerun()
        else:
            st.markdown(f'<p style="font-size:13px;color:{TM};">Conecte ao Confluence Cloud ou Server/Data Center. Sem credenciais, explore com o modo Demo.</p>', unsafe_allow_html=True)

            _conf_tipo = st.radio(
                "Tipo de instalacao Confluence",
                ["Cloud (Atlassian Cloud)", "Server / Data Center (on-premises)"],
                horizontal=True,
                key="conf_tipo_radio",
                label_visibility="collapsed",
            )
            _conf_cloud = (_conf_tipo == "Cloud (Atlassian Cloud)")

            if _conf_cloud:
                st.markdown(
                    f'<p style="font-size:12px;color:{TM};margin-bottom:4px;">'
                    'Cloud: email da conta Atlassian + API Token de atlassian.com > Account Settings > Security.</p>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<p style="font-size:12px;color:{TM};margin-bottom:4px;">'
                    'Server/DC: use <b>PAT</b> (Confluence 7.9+ / Data Center) deixando Usuario em branco, '
                    'ou informe usuario + senha para versoes anteriores.</p>',
                    unsafe_allow_html=True,
                )

            with st.form("conf_conn"):
                _ph_url_c = "https://empresa.atlassian.net" if _conf_cloud else "https://confluence.empresa.com.br"
                url = st.text_input("URL do Confluence", placeholder=_ph_url_c)
                _lbl_usr_c = "Email" if _conf_cloud else "Usuario (opcional — deixe em branco para PAT)"
                usuario = st.text_input(_lbl_usr_c)
                _lbl_tok_c = "Token de API" if _conf_cloud else "PAT ou Senha"
                _hlp_tok_c = (
                    "Gere em: atlassian.com > Account Settings > Security > API tokens"
                    if _conf_cloud else
                    "PAT: Confluence > menu de usuario > Personal Access Tokens"
                )
                token = st.text_input(_lbl_tok_c, type="password", help=_hlp_tok_c)
                c1, c2 = st.columns(2)
                conectar = c1.form_submit_button("Conectar", use_container_width=True)
                demo = c2.form_submit_button("Usar Demo (sem credenciais)", use_container_width=True)

            if conectar and url and token:
                if _conf_cloud and not usuario:
                    st.error("Email obrigatorio para Confluence Cloud.")
                else:
                    _cp = ConfluencePlugin()
                    _res_cp = _cp.conectar(url, usuario, token, _conf_cloud)
                    if _res_cp["ok"]:
                        st.session_state.confluence_plugin = _cp
                        st.success(_res_cp["message"])
                        st.rerun()
                    else:
                        st.error(_res_cp["message"])
            if demo:
                st.session_state.confluence_plugin = "demo"
                st.session_state.confluence_spaces = CONFLUENCE_DEMO_SPACES
                st.rerun()

    # ── Scan ──────────────────────────────────────────────────────────────────
    with _ctab_scan:
        _cstore = ScanStateStore()
        _is_demo_c = st.session_state.confluence_plugin == "demo"
        _is_real_c = st.session_state.confluence_plugin not in (None, "demo")

        if st.session_state.confluence_plugin is None:
            st.warning("Conecte ao Confluence na aba Conexao para executar a varredura.")
            st.stop()

        if _is_demo_c:
            st.info("Modo Demo — usando dados fictícios de Confluence.")

        # ── Listagem de spaces ─────────────────────────────────────────────
        sec_hdr("Spaces Disponiveis")

        _spaces = st.session_state.confluence_spaces
        _cload_col, _cinfo_col = st.columns([2, 5])
        with _cload_col:
            _lbl_cs = "Atualizar lista" if _spaces else "Carregar Spaces"
            if st.button(_lbl_cs, use_container_width=True, key="btn_load_spaces"):
                if _is_demo_c:
                    st.session_state.confluence_spaces = CONFLUENCE_DEMO_SPACES
                else:
                    with st.spinner("Buscando spaces e contando paginas (paralelo)..."):
                        st.session_state.confluence_spaces = (
                            st.session_state.confluence_plugin.listar_spaces()
                        )
                st.rerun()
        with _cinfo_col:
            if _spaces:
                _total_pags = sum(s.get("count", 0) for s in _spaces if s.get("count", 0) > 0)
                st.markdown(
                    f'<p style="font-size:12px;color:{TM};padding-top:8px;">'
                    f'{len(_spaces)} spaces — {_total_pags:,} paginas no total</p>',
                    unsafe_allow_html=True,
                )

        if _spaces:
            # Re-use project table renderer with "Space" label
            _spaces_rows = [{"Chave": s["key"], "Nome": s["name"], "Paginas": s.get("count", 0)} for s in _spaces]
            _max_c = max((s.get("count", 0) for s in _spaces), default=1) or 1
            _bar_rows = []
            for _sr in _spaces_rows:
                _cnt = _sr["Paginas"]
                _bar_len = round((_cnt / _max_c) * 12)
                _bar = "█" * _bar_len + "░" * (12 - _bar_len)
                _bar_rows.append({**_sr, "Volume": f"{_bar} {_cnt}"})
            st.dataframe(pd.DataFrame(_bar_rows), use_container_width=True, hide_index=True)

            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
            sec_hdr("Selecionar Spaces para Varrer")

            _csel_modo = st.radio(
                "Escopo",
                ["Todos os spaces acessiveis", "Selecionar spaces especificos"],
                horizontal=True,
                key="conf_selecao_modo",
            )

            if _csel_modo == "Selecionar spaces especificos":
                _todas_chaves_c = [s["key"] for s in _spaces]
                _selecionados_c = st.multiselect(
                    "Spaces",
                    options=_todas_chaves_c,
                    default=st.session_state.confluence_spaces_selecionados or _todas_chaves_c[:1],
                    format_func=lambda k: f"{k} — {next((s['name'] for s in _spaces if s['key'] == k), k)}",
                    key="conf_multiselect",
                )
                st.session_state.confluence_spaces_selecionados = _selecionados_c
                _tot_sel_c = sum(s.get("count", 0) for s in _spaces if s["key"] in _selecionados_c and s.get("count", 0) > 0)
                if _selecionados_c:
                    st.markdown(
                        f'<p style="font-size:11px;color:{TM};">Estimativa: ~{_tot_sel_c:,} paginas nos spaces selecionados</p>',
                        unsafe_allow_html=True,
                    )
            else:
                st.session_state.confluence_spaces_selecionados = []
                _tot_c_todos = sum(s.get("count", 0) for s in _spaces if s.get("count", 0) > 0)
                if _tot_c_todos > 3000:
                    st.warning(
                        f"Todos os spaces somam ~{_tot_c_todos:,} paginas. "
                        "Use scan incremental ou limite de paginas."
                    )

        sec_hdr("Opcoes de Varredura")
        _copt1, _copt2 = st.columns(2)
        with _copt1:
            _space_ref_key = "_".join(
                (st.session_state.confluence_spaces_selecionados or ["todos"])[:3]
            )
            _ultimo_c = _cstore.last_scan_date_str("confluence", _space_ref_key) if _space_ref_key != "todos" else None
            _incremental_c = st.checkbox(
                f"Scan incremental{f' (desde {_ultimo_c})' if _ultimo_c else ' (primeiro scan = completo)'}",
                value=bool(_ultimo_c),
                key="conf_incr",
            )
            _max_pag = st.number_input("Limite de paginas por space (0 = sem limite)", value=200, step=50, min_value=0, key="conf_max")
        with _copt2:
            _status_pag = st.selectbox("Status das paginas", ["current", "draft", "archived"], key="conf_status")
            _incluir_anx_c = st.checkbox("Incluir anexos", value=False, key="conf_anexos")
            _conf_scan_conf = st.slider(
                "Confianca minima do scan (%)",
                min_value=0, max_value=100, value=0, step=5,
                key="conf_conf_scan",
                help="Deteccoes com confianca abaixo deste valor sao descartadas na origem. "
                     "Aumente para reduzir falsos positivos (ex: 70%).",
            )

        if st.button("Executar Varredura Confluence", use_container_width=True, key="btn_conf_scan"):
            _analyzer_c = get_analyzer()
            _chunks_c: list = []
            _spaces_para_scan = st.session_state.confluence_spaces_selecionados or [""]

            with st.status("Executando varredura Confluence...", expanded=True) as _cstatus:
                if _is_demo_c:
                    st.write(f"Modo demo: {len(CONFLUENCE_DEMO_TRECHOS)} chunks carregados.")
                    _chunks_c = list(CONFLUENCE_DEMO_TRECHOS)
                else:
                    _plugin_conf: ConfluencePlugin = st.session_state.confluence_plugin
                    _desde_c = _cstore.last_scan_date_str("confluence", _space_ref_key) if _incremental_c and _space_ref_key != "todos" else ""
                    _total_pags_count = 0

                    for _skey in _spaces_para_scan:
                        _label_space = _skey or "todos os spaces"
                        st.write(f"Buscando paginas — space: {_label_space}...")
                        _paginas = _plugin_conf.buscar_paginas(
                            _skey,
                            status=_status_pag,
                            desde=_desde_c,
                            max_total=int(_max_pag),
                        )
                        st.write(f"  {len(_paginas)} paginas. Extraindo texto...")
                        _total_pags_count += len(_paginas)
                        for _pg in _paginas:
                            _chunks_c.extend(_plugin_conf.extrair_textos(_pg))

                        if _incluir_anx_c and _paginas:
                            from plugins.attachment_scanner import escanear_anexos
                            _pares_c: list = []
                            for _pg in _paginas:
                                _pid = _pg.get("id", "")
                                if not _pid:
                                    continue
                                for _att in _plugin_conf.listar_anexos(_pid):
                                    try:
                                        _pares_c.append((_att, _plugin_conf.baixar_anexo(_att.url_download)))
                                    except Exception:
                                        pass
                            if _pares_c:
                                st.write(f"  Escaneando {len(_pares_c)} anexos...")
                                _ra_list = escanear_anexos(_pares_c, _analyzer_c)
                                for _ra in _ra_list:
                                    if _ra.resultado:
                                        _chunks_c.append(_ra.resultado.chunk)

                    if _space_ref_key != "todos":
                        _cstore.set_last_scan("confluence", _space_ref_key, total_items=_total_pags_count)

                st.write(f"Processando {len(_chunks_c)} chunks em paralelo...")
                _res_c = scan_chunks(_chunks_c, _analyzer_c, min_confianca=_conf_scan_conf / 100)
                _met_c = resumir(_res_c)
                st.session_state.confluence_resultados = _res_c
                st.session_state.confluence_metricas = _met_c
                _add_history("Confluence", "+".join(_spaces_para_scan[:3]) or "demo", _met_c)
                _cstatus.update(label=f"Concluido — {_met_c['total_deteccoes']} deteccoes.", state="complete")

    # ── Resultados ────────────────────────────────────────────────────────────
    with _ctab_res:
        render_resultados(
            st.session_state.confluence_resultados,
            st.session_state.confluence_metricas,
            "Confluence",
        )

    # ── Agendamentos ──────────────────────────────────────────────────────────
    with _ctab_agend:
        from plugins.scheduler import ScanScheduler as _SS2, FREQ_CRON as _FC2, DIA_SEMANA_NUM as _DSN2, _cron_para_descricao as _cpd2
        _sched_c = get_scheduler()

        if not _sched_c.disponivel:
            st.warning("APScheduler nao instalado. Execute: `pip install apscheduler>=3.10`")

        sec_hdr("Criar Agendamento Confluence")
        _cag1, _cag2 = st.columns(2, gap="large")
        with _cag1:
            _cag_nome = st.text_input("Nome do agendamento", placeholder="Scan semanal DS", key="cag_nome")
            _spaces_disp = [s["key"] for s in (st.session_state.confluence_spaces or CONFLUENCE_DEMO_SPACES)]
            _cag_spaces = st.multiselect(
                "Spaces (vazio = todos)",
                _spaces_disp,
                key="cag_spaces",
                help="Deixe em branco para incluir todos os spaces acessiveis.",
            )

        with _cag2:
            _cag_freq = st.radio(
                "Frequencia",
                ["Diario", "Semanal", "Mensal", "Personalizado"],
                key="cag_freq",
            )
            _cag_hora = st.number_input("Hora (0-23)", value=9, min_value=0, max_value=23, key="cag_hora")
            _cag_min = st.number_input("Minuto (0-59)", value=0, min_value=0, max_value=59, key="cag_min")

            if _cag_freq == "Semanal":
                _cag_dia = st.selectbox("Dia da semana", list(_DSN2.keys()), key="cag_dia")
                _cag_cron = f"{_cag_min} {_cag_hora} * * {_DSN2[_cag_dia]}"
            elif _cag_freq == "Mensal":
                _cag_dm = st.number_input("Dia do mes (1-28)", value=1, min_value=1, max_value=28, key="cag_dm")
                _cag_cron = f"{_cag_min} {_cag_hora} {_cag_dm} * *"
            elif _cag_freq == "Personalizado":
                _cag_cron = st.text_input("Expressao cron", value="0 9 * * 1", key="cag_cron_custom")
            else:
                _cag_cron = f"{_cag_min} {_cag_hora} * * *"

            st.markdown(
                f'<p style="font-size:11px;color:{TM};margin-top:4px;">'
                f'Agenda: <b>{_cpd2(_cag_cron)}</b></p>',
                unsafe_allow_html=True,
            )

        if st.button("Criar Agendamento Confluence", use_container_width=True, key="btn_criar_ag_conf"):
            if not _cag_nome.strip():
                st.warning("Informe um nome para o agendamento.")
            elif not _sched_c.disponivel:
                st.error("Instale o APScheduler para habilitar agendamentos.")
            else:
                _sched_c.criar(
                    nome=_cag_nome.strip(),
                    tipo="confluence",
                    projetos=_cag_spaces,
                    cron=_cag_cron,
                    url="",
                    usuario="",
                    token="",
                    auto_acao="readonly",
                )
                st.success(f"Agendamento '{_cag_nome}' criado: {_cpd2(_cag_cron)}")
                st.rerun()

        sec_hdr("Agendamentos Ativos")
        _jobs_c = [j for j in _sched_c.listar() if j.get("tipo") == "confluence"]
        if not _jobs_c:
            st.markdown(f'<p style="color:{TMU};font-size:13px;">Nenhum agendamento Confluence criado ainda.</p>', unsafe_allow_html=True)
        else:
            for _jc in _jobs_c:
                _prox_c = _sched_c.proximo_run(_jc["id"])
                _ult_c = _jc["ultimo_run"][:16].replace("T", " ") if _jc["ultimo_run"] else "nunca"
                _sp_txt = ", ".join(_jc["projetos"]) if _jc["projetos"] else "todos"
                _jcc1, _jcc2, _jcc3, _jcc4 = st.columns([3, 2, 2, 1])
                _jcc1.markdown(
                    f'<span style="font-size:13px;font-weight:700;color:{TD};">{_jc["nome"]}</span><br>'
                    f'<span style="font-size:11px;color:{TM};">{_jc["descricao_freq"]} | spaces: {_sp_txt}</span>',
                    unsafe_allow_html=True,
                )
                _jcc2.markdown(f'<span style="font-size:11px;color:{TM};">Proximo run</span><br><span style="font-size:12px;color:{TD};">{_prox_c}</span>', unsafe_allow_html=True)
                _jcc3.markdown(f'<span style="font-size:11px;color:{TM};">Ultimo run</span><br><span style="font-size:12px;color:{TD};">{_ult_c}</span>', unsafe_allow_html=True)
                with _jcc4:
                    if st.button("Remover", key=f"del_cjob_{_jc['id']}", use_container_width=True):
                        _sched_c.remover(_jc["id"])
                        st.rerun()


# ═════════════════════════════════════════════════════════════════════════════
# PAGINA: TEXTO LIVRE
# ═════════════════════════════════════════════════════════════════════════════
elif pagina == "Texto Livre":
    from plugins.scanner import scan_chunks, resumir

    st.markdown(f'<p style="font-size:13px;color:{TM};margin-bottom:1rem;">Cole qualquer texto para detectar PII e secrets antes de enviar para um LLM.</p>', unsafe_allow_html=True)

    texto = st.text_area(
        "Texto para analise",
        height=200,
        placeholder="Cole aqui o texto a ser analisado...",
        key="texto_livre_input",
    )

    if st.button("Analisar Texto", use_container_width=False):
        if not texto.strip():
            st.warning("Insira um texto para analisar.")
        else:
            analyzer = get_analyzer()
            chunk = {
                "texto": texto, "autor": "usuario", "campo": "Texto Livre",
                "issue_key": "TEXTO", "issue_url": "", "issue_type": "text", "prioridade": "",
            }
            with st.spinner("Analisando..."):
                resultados = scan_chunks([chunk], analyzer)
                metricas = resumir(resultados)
                st.session_state.texto_resultados = resultados
                st.session_state.texto_metricas = metricas
            _add_history("Texto", "livre", metricas)

    render_resultados(
        st.session_state.texto_resultados,
        st.session_state.texto_metricas,
        "Texto Livre",
    )


# ═════════════════════════════════════════════════════════════════════════════
# PAGINA: ANONYMIZAR
# ═════════════════════════════════════════════════════════════════════════════
elif pagina == "Anonymizar":
    from presidio_anonymizer import AnonymizerEngine

    st.markdown(f'<p style="font-size:13px;color:{TM};margin-bottom:1rem;">Substitui PII detectada por tokens — texto limpo para ingestão em LLM.</p>', unsafe_allow_html=True)

    texto_anon = st.text_area(
        "Texto original",
        height=160,
        placeholder="Cole o texto a ser anonimizado...",
        key="anon_input",
    )

    if st.button("Anonimizar", use_container_width=False):
        if not texto_anon.strip():
            st.warning("Insira um texto.")
        else:
            analyzer = get_analyzer()
            anonymizer = AnonymizerEngine()
            with st.spinner("Anonimizando..."):
                results = analyzer.analyze(text=texto_anon, language="pt")
                anon_result = anonymizer.anonymize(text=texto_anon, analyzer_results=results)
            st.session_state["anon_texto_original"] = texto_anon
            st.session_state["anon_texto_limpo"] = anon_result.text
            st.session_state["anon_itens"] = anon_result.items

    if "anon_texto_limpo" in st.session_state:
        c1, c2 = st.columns(2, gap="large")
        with c1:
            sec_hdr("Original")
            st.markdown(f'<div class="anon-panel">{st.session_state["anon_texto_original"]}</div>', unsafe_allow_html=True)
        with c2:
            sec_hdr("Anonimizado")
            st.markdown(f'<div class="anon-panel">{st.session_state["anon_texto_limpo"]}</div>', unsafe_allow_html=True)

        st.download_button(
            "Baixar texto limpo (.txt)",
            st.session_state["anon_texto_limpo"].encode("utf-8"),
            file_name="texto_anonimizado.txt",
            mime="text/plain",
        )

        sec_hdr("Substituicoes Realizadas")
        if st.session_state["anon_itens"]:
            rows = []
            for item in st.session_state["anon_itens"]:
                original = st.session_state["anon_texto_original"][item.start:item.end]
                from plugins.scanner import SECRET_ENTITIES
                valor_display = (original[:4] + "..." + original[-4:] if len(original) > 8 else "****") if item.entity_type in SECRET_ENTITIES else original
                rows.append({
                    "Entidade": item.entity_type,
                    "Valor Original": valor_display,
                    "Substituido Por": item.text,
                    "Inicio": item.start,
                    "Fim": item.end,
                })
            df_anon = pd.DataFrame(rows)
            st.dataframe(df_anon, use_container_width=True, hide_index=True)

            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as w:
                df_anon.to_excel(w, index=False, sheet_name="Substituicoes")
            col_d1, col_d2, _ = st.columns([2, 2, 4])
            col_d1.download_button("Exportar CSV", df_anon.to_csv(index=False).encode(), "substituicoes.csv", "text/csv", use_container_width=True)
            col_d2.download_button("Exportar Excel", buf.getvalue(), "substituicoes.xlsx", use_container_width=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGINA: FRAMEWORKS
# ═════════════════════════════════════════════════════════════════════════════
elif pagina == "Frameworks":
    from plugins.frameworks import AI_FRAMEWORKS, NIVEL_COR, NIVEL_LABELS

    st.markdown(f'<p style="font-size:13px;color:{TM};margin-bottom:1.5rem;">Catalogo de frameworks regulatórios e de AI Security mapeados às entidades detectadas.</p>', unsafe_allow_html=True)

    for nome, fw in AI_FRAMEWORKS.items():
        cor_nivel = NIVEL_COR.get(fw["nivel_impacto"], OD)
        label_nivel = NIVEL_LABELS.get(fw["nivel_impacto"], fw["nivel_impacto"])
        funcoes_html = " ".join(
            f'<span style="background:rgba(59,130,246,.1);border:1px solid {BOR};'
            f'border-radius:4px;padding:2px 8px;font-size:11px;color:{BR};'
            f'font-weight:500;margin-right:4px;">{f}</span>'
            for f in fw["funcoes"]
        )
        acoes_html = "".join(f'<li style="margin-bottom:4px;">{a}</li>' for a in fw["acoes"])

        st.markdown(f"""
        <div style="background:{BPW};border:1px solid {BOR};border-left:4px solid {cor_nivel};
          border-radius:8px;padding:18px 22px;margin-bottom:1rem;">
          <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px;">
            <span style="font-size:15px;font-weight:700;color:{TD};">{nome}</span>
            <span style="background:rgba(0,0,0,.2);color:{cor_nivel};border:1px solid {cor_nivel};
              border-radius:4px;padding:2px 10px;font-size:10px;font-weight:700;">
              {label_nivel}
            </span>
          </div>
          <div style="margin-bottom:8px;">{funcoes_html}</div>
          <p style="font-size:12.5px;color:{TM};line-height:1.6;margin:8px 0;">{fw["descricao"]}</p>
          <div style="font-size:11px;font-weight:700;color:{TMU};text-transform:uppercase;
            letter-spacing:.5px;margin:10px 0 6px;">Acoes Recomendadas</div>
          <ul style="margin:0;padding-left:18px;font-size:12px;color:{TM};line-height:1.7;">
            {acoes_html}
          </ul>
        </div>
        """, unsafe_allow_html=True)
