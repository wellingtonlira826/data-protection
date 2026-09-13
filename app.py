"""
Presidio PT — Data Protection Dashboard v3.0
Corporate executive design. Dark theme. Blue palette. Zero emojis.
Execute: python -m streamlit run app.py
"""

import time
import urllib.parse
from collections import Counter
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from presidio_pt import build_analyzer
from plugins.risk_scorer import score, sort_key
from plugins.demo_data import JIRA_DEMO_TRECHOS, CONFLUENCE_DEMO_TRECHOS
from plugins.frameworks import (
    AI_FRAMEWORKS,
    PII_FRAMEWORK_MAP,
    NIVEL_COR,
    frameworks_para_entidade,
    frameworks_impactados,
)

# ─────────────────────────────────────────────────────────────────────────────
# DESIGN TOKENS
# ─────────────────────────────────────────────────────────────────────────────
BLUE_DARK   = "#1E3A8A"
BLUE_ROYAL  = "#3B82F6"
BLUE_MID    = "#2563EB"
BLUE_LIGHT  = "#93C5FD"
BLUE_PALE   = "#1E3A8A1A"
BG_PAGE     = "#0B1121"
BG_SECTION  = "#0F1729"
BG_WHITE    = "#1A2332"
BG_SIDEBAR  = "#0A1020"
TEXT_DARK   = "#E2E8F0"
TEXT_MID    = "#94A3B8"
TEXT_MUTED  = "#64748B"
BORDER      = "#1E3A5F"
BORDER_MED  = "#2D4A72"
RED_DARK    = "#EF4444"
RED_BG      = "#DC262620"
ORANGE_DARK = "#F97316"
ORANGE_BG   = "#F9731620"
GREEN_DARK  = "#22C55E"
GREEN_BG    = "#22C55E20"
BLUE_CARD_BORDER_TOP = "#3B82F6"

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Data Protection | Presidio PT",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS GLOBAL
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

  html, body, .stApp {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background-color: {BG_PAGE} !important;
  }}
  .stApp *:not([data-testid="stIconMaterial"]):not([data-testid="stIconEmoji"]):not(.material-symbols-rounded):not(.material-symbols-outlined):not(.material-icons) {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  }}
  /* Restore Streamlit Material icon font — critical: never override this */
  [data-testid="stIconMaterial"],
  [data-testid="stIconEmoji"],
  .material-symbols-rounded,
  .material-symbols-outlined,
  .material-icons {{
    font-family: 'Material Symbols Rounded', 'Material Icons', 'Material Symbols Outlined', sans-serif !important;
    font-style: normal !important;
    font-variation-settings: normal !important;
    background: transparent !important;
    line-height: 1 !important;
    letter-spacing: normal !important;
    text-transform: none !important;
    display: inline-block !important;
    white-space: nowrap !important;
    word-wrap: normal !important;
    direction: ltr !important;
    -webkit-font-smoothing: antialiased !important;
  }}
  /* Icon color: inherit from parent button/span so hover states work */
  [data-testid="stIconMaterial"] {{ color: inherit !important; }}

  .stApp {{ background-color: {BG_PAGE} !important; }}
  .stMain {{ background-color: {BG_SECTION} !important; }}
  /* Default text for non-overridden elements */
  .stApp div, .stApp span:not([data-baseweb="tag"] span),
  .stApp p, .stApp li {{ color: {TEXT_DARK}; }}

  section[data-testid="stSidebar"] {{
    background-color: {BG_SIDEBAR} !important;
    border-right: 1px solid {BORDER} !important;
    box-shadow: 2px 0 8px rgba(0,0,0,.35);
  }}
  section[data-testid="stSidebar"] > div {{
    background-color: {BG_SIDEBAR} !important;
  }}
  section[data-testid="stSidebar"] {{
    overflow-y: auto !important;
    overflow-x: hidden !important;
  }}

  .stMainBlockContainer {{
    padding-top: 0 !important;
    padding-bottom: 2rem;
    max-width: 100% !important;
  }}
  .block-container {{
    padding-top: 0 !important;
    padding-bottom: 2rem;
    max-width: 100% !important;
  }}

  /* ── Cabeçalho corporativo ── */
  .corp-header {{
    background: linear-gradient(90deg, {BLUE_DARK} 0%, #162d6e 100%);
    padding: 0 32px;
    height: 60px;
    display: flex;
    align-items: center;
    gap: 14px;
    margin: -1rem -1rem 1.5rem -1rem;
    box-shadow: 0 2px 12px rgba(0,0,0,.45);
    border-bottom: 1px solid {BORDER_MED};
  }}
  .corp-logo-box {{
    width: 36px; height: 36px;
    background: rgba(59,130,246,.2);
    border: 1.5px solid rgba(59,130,246,.4);
    border-radius: 6px;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
  }}
  .corp-logo-text {{ font-size: 11px; font-weight: 800; color: {BLUE_LIGHT}; letter-spacing: .5px; }}
  .corp-title {{ color: {TEXT_DARK}; font-size: 16px; font-weight: 700; letter-spacing: -.2px; }}
  .corp-divider {{ width: 1px; height: 24px; background: rgba(255,255,255,.12); margin: 0 4px; }}
  .corp-sub {{ color: rgba(255,255,255,.45); font-size: 12px; font-weight: 400; }}
  .corp-header-right {{ margin-left: auto; display: flex; align-items: center; gap: 10px; }}
  .corp-badge {{
    background: rgba(255,255,255,.06);
    border: 1px solid rgba(255,255,255,.1);
    border-radius: 4px;
    padding: 3px 10px;
    font-size: 11px; color: rgba(255,255,255,.5);
    font-weight: 500;
  }}
  .corp-status-dot {{
    width: 7px; height: 7px; border-radius: 50%;
    background: {GREEN_DARK};
    box-shadow: 0 0 6px {GREEN_DARK};
    display: inline-block; margin-right: 5px;
  }}
  .corp-status-label {{ font-size: 11px; color: {GREEN_DARK}; font-weight: 600; }}

  /* ── KPI Cards ── */
  .kpi-card {{
    background: {BG_WHITE};
    border: 1px solid {BORDER};
    border-top: 3px solid {BLUE_CARD_BORDER_TOP};
    border-radius: 8px;
    padding: 16px 18px 14px;
    box-shadow: 0 1px 4px rgba(0,0,0,.25);
    transition: box-shadow .15s;
    height: 100%;
  }}
  .kpi-card:hover {{ box-shadow: 0 3px 12px rgba(0,0,0,.35); }}
  .kpi-label {{
    font-size: 10px; font-weight: 700; color: {TEXT_MID};
    text-transform: uppercase; letter-spacing: .7px;
    margin-bottom: 8px;
  }}
  .kpi-value {{
    font-size: 28px; font-weight: 700; color: {TEXT_DARK};
    line-height: 1; margin-bottom: 5px; letter-spacing: -.5px;
  }}
  .kpi-sub {{ font-size: 11px; font-weight: 500; color: {TEXT_MID}; }}
  .kpi-danger  .kpi-value {{ color: {RED_DARK}; }}
  .kpi-warning .kpi-value {{ color: {ORANGE_DARK}; }}
  .kpi-info    .kpi-value {{ color: {BLUE_ROYAL}; }}
  .kpi-success .kpi-value {{ color: {GREEN_DARK}; }}
  .kpi-danger  {{ border-top-color: {RED_DARK} !important; }}
  .kpi-warning {{ border-top-color: {ORANGE_DARK} !important; }}
  .kpi-success {{ border-top-color: {GREEN_DARK} !important; }}

  /* ── Trend indicators ── */
  .kpi-trend-up   {{ color: {GREEN_DARK}; font-size: 10px; font-weight: 700; }}
  .kpi-trend-down {{ color: {RED_DARK};   font-size: 10px; font-weight: 700; }}

  /* ── Section headers ── */
  .sec-hdr {{
    font-size: 11px; font-weight: 700; color: {TEXT_MID};
    text-transform: uppercase; letter-spacing: .6px;
    padding-bottom: 8px;
    border-bottom: 2px solid {BLUE_DARK};
    margin: 1.75rem 0 1rem;
    display: inline-block;
  }}
  .sec-hdr-sm {{
    font-size: 10.5px; font-weight: 700; color: {TEXT_MID};
    text-transform: uppercase; letter-spacing: .7px;
    padding-bottom: 6px;
    border-bottom: 1px solid {BORDER};
    margin: 1.25rem 0 .75rem;
    display: inline-block;
  }}

  /* ── Risk badges ── */
  .rb {{
    display: inline-flex; align-items: center; gap: 4px;
    padding: 3px 10px; border-radius: 4px;
    font-size: 11px; font-weight: 700; letter-spacing: .2px;
  }}
  .rb-high   {{ background: {RED_BG};    color: {RED_DARK};    border: 1px solid {RED_DARK}; }}
  .rb-medium {{ background: {ORANGE_BG}; color: {ORANGE_DARK}; border: 1px solid {ORANGE_DARK}; }}
  .rb-low    {{ background: {GREEN_BG};  color: {GREEN_DARK};  border: 1px solid {GREEN_DARK}; }}
  .rb-info   {{ background: rgba(59,130,246,.12); color: {BLUE_ROYAL}; border: 1px solid {BLUE_ROYAL}; }}
  .rb-neutral{{ background: {BG_PAGE};   color: {TEXT_MID};    border: 1px solid {BORDER}; }}

  /* ── Framework pill ── */
  .fw-pill {{
    display: inline-block;
    background: rgba(59,130,246,.08);
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 11px; font-weight: 500; color: {BLUE_ROYAL};
    margin: 2px 2px 4px 0; white-space: nowrap;
  }}

  /* ── Chart container ── */
  .chart-card {{
    background: {BG_WHITE};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,.2);
    margin-bottom: 1rem;
  }}
  .chart-title {{
    font-size: 11px; font-weight: 700; color: {TEXT_MID};
    text-transform: uppercase; letter-spacing: .5px;
    margin-bottom: 4px;
  }}

  /* ── Report card ── */
  .report-card {{
    background: {BG_WHITE};
    border: 1px solid {BORDER};
    border-left: 4px solid {BLUE_ROYAL};
    border-radius: 8px;
    padding: 20px 24px;
    margin: 1rem 0;
  }}
  .report-stat {{
    display: inline-block;
    background: {BG_PAGE};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 8px 14px;
    margin: 4px 4px 4px 0;
    font-size: 12px; color: {TEXT_MID};
  }}
  .report-stat strong {{ color: {TEXT_DARK}; font-size: 14px; }}

  /* ── Anonymizer diff ── */
  .anon-panel {{
    background: {BG_PAGE};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 16px;
    font-family: 'Courier New', monospace;
    font-size: 13px;
    line-height: 1.7;
    color: {TEXT_MID};
    min-height: 160px;
    white-space: pre-wrap;
    word-break: break-word;
  }}
  .anon-panel-label {{
    font-size: 10px; font-weight: 700; color: {TEXT_MID};
    text-transform: uppercase; letter-spacing: .6px;
    margin-bottom: 8px;
  }}
  .anon-original {{ border-color: rgba(239,68,68,.3); }}
  .anon-clean    {{ border-color: rgba(34,197,94,.3); }}

  /* ── Scan history item ── */
  .hist-item {{
    background: {BG_PAGE};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 8px 10px;
    margin-bottom: 6px;
    font-size: 11px;
    cursor: default;
  }}
  .hist-item-header {{
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 3px;
  }}
  .hist-item-tipo {{ font-weight: 700; color: {TEXT_DARK}; }}
  .hist-item-time {{ color: {TEXT_MUTED}; font-size: 10px; }}
  .hist-item-stats {{ color: {TEXT_MID}; font-size: 10.5px; }}

  /* ── Notification block ── */
  .notify-email {{ font-size: 14px; font-weight: 600; color: {BLUE_ROYAL}; margin-bottom: 8px; }}

  /* ── Sidebar labels ── */
  .sb-sec {{
    font-size: 10px; font-weight: 700; color: {TEXT_MID};
    text-transform: uppercase; letter-spacing: .7px;
    padding: 14px 0 6px;
    border-bottom: 1px solid {BORDER};
    margin-bottom: 7px;
  }}
  .sb-sec:first-child {{ padding-top: 4px; }}

  /* ── Tabs ── */
  div[data-testid="stTabs"] button[role="tab"] {{
    color: {TEXT_MID} !important;
    font-size: 13px !important; font-weight: 500 !important;
    background: transparent !important;
    padding: 8px 16px !important;
    border-radius: 6px 6px 0 0 !important;
  }}
  div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {{
    color: {TEXT_DARK} !important; font-weight: 600 !important;
    background: {BLUE_DARK} !important;
  }}

  /* ── Buttons ── */
  .stButton > button {{
    background-color: {BLUE_DARK} !important;
    color: {TEXT_DARK} !important;
    border: none !important; border-radius: 6px !important;
    font-size: 13px !important; font-weight: 600 !important;
    padding: 0.5rem 1.3rem !important; letter-spacing: .2px !important;
    transition: background-color .18s, box-shadow .18s;
    box-shadow: 0 1px 3px rgba(0,0,0,.3);
  }}
  .stButton > button:hover {{
    background-color: {BLUE_ROYAL} !important;
    box-shadow: 0 2px 8px rgba(59,130,246,.25);
  }}
  .stDownloadButton > button {{
    background-color: {BG_WHITE} !important;
    color: {BLUE_ROYAL} !important;
    border: 1.5px solid {BLUE_ROYAL} !important;
    border-radius: 6px !important; font-weight: 600 !important;
    font-size: 13px !important; letter-spacing: .2px !important;
    transition: all .18s;
  }}
  .stDownloadButton > button:hover {{
    background-color: rgba(59,130,246,.1);
    color: {TEXT_DARK} !important;
  }}
  a[data-testid="stLinkButton"] > button {{
    background-color: {BG_WHITE} !important;
    color: {BLUE_ROYAL} !important;
    border: 1.5px solid {BLUE_ROYAL} !important;
    border-radius: 6px !important; font-weight: 600 !important;
    font-size: 12px !important; transition: all .18s;
  }}
  a[data-testid="stLinkButton"] > button:hover {{
    background-color: rgba(59,130,246,.1) !important;
    color: {TEXT_DARK} !important;
  }}

  /* ── Inputs ── */
  .stTextInput input, .stTextArea textarea {{
    background: {BG_WHITE} !important; color: {TEXT_DARK} !important;
    border-color: {BORDER_MED} !important; border-radius: 6px !important;
    box-shadow: none !important;
  }}
  .stTextInput input:focus, .stTextArea textarea:focus {{
    border-color: {BLUE_ROYAL} !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,.2) !important;
  }}
  /* ── Password visibility toggle button ── */
  [data-baseweb="input"] button,
  .stTextInput [data-baseweb="input"] > div > button {{
    background: transparent !important;
    border: none !important;
    color: {TEXT_MID} !important;
    padding: 0 8px !important;
    display: flex; align-items: center;
  }}
  [data-baseweb="input"] button svg,
  .stTextInput [data-baseweb="input"] > div > button svg {{
    fill: {TEXT_MID} !important;
    background: transparent !important;
  }}
  [data-baseweb="input"] button [data-testid="stIconMaterial"] {{
    color: {TEXT_MID} !important;
    font-size: 20px !important;
  }}

  /* ── Expanders ── */
  div[data-testid="stExpander"] {{
    background: {BG_WHITE} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 8px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,.2) !important;
    margin-bottom: 8px;
  }}
  div[data-testid="stExpander"] summary {{
    font-weight: 600 !important; color: {TEXT_DARK} !important;
    font-size: 13px !important; background: {BG_WHITE} !important;
    padding: 10px 14px !important; cursor: pointer;
  }}
  div[data-testid="stExpander"] summary:hover {{ background: {BG_SECTION} !important; }}

  /* ── Labels ── */
  label, .stWidgetLabel, .stWidgetLabel p {{
    color: {TEXT_DARK} !important; font-size: 12px !important;
    font-weight: 600 !important;
  }}
  p, .stMarkdown p {{ color: {TEXT_MID} !important; }}
  h1, h2, h3 {{ color: {TEXT_DARK} !important; }}

  /* ── DataFrame (Streamlit 1.38+ grid renderer) ── */
  .stDataFrame {{
    border: 1px solid {BORDER} !important;
    border-radius: 8px !important;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,.2);
  }}
  .stDataFrame [data-testid="stDataFrameResizable"] {{
    border-radius: 8px !important;
    overflow: hidden;
  }}
  /* Column headers */
  .stDataFrame .dvn-scroller .dvn-scroller-inner {{
    background: {BG_PAGE} !important;
  }}
  /* Fallback: older HTML table renderer */
  .stDataFrame table {{
    background: {BG_WHITE} !important;
    border-collapse: collapse;
    width: 100%;
  }}
  .stDataFrame table thead th {{
    background: {BG_PAGE} !important;
    color: {TEXT_MID} !important;
    font-weight: 700 !important;
    font-size: 11px !important;
    letter-spacing: .4px !important;
    text-transform: uppercase !important;
    border-bottom: 2px solid {BORDER} !important;
    padding: 10px 14px !important;
  }}
  .stDataFrame table tbody td {{
    color: {TEXT_DARK} !important;
    background: {BG_WHITE} !important;
    font-size: 12.5px !important;
    padding: 9px 14px !important;
    border-bottom: 1px solid {BORDER} !important;
  }}
  .stDataFrame table tbody tr:hover td {{
    background: rgba(59,130,246,.06) !important;
  }}

  /* ── Selectbox / Multiselect ── */
  .stSelectbox > div > div, .stMultiSelect > div > div {{
    background: {BG_WHITE} !important; border-color: {BORDER_MED} !important;
    border-radius: 6px !important; color: {TEXT_DARK} !important;
  }}

  /* ── Multiselect chips (selected tags) ── */
  span[data-baseweb="tag"] {{
    background-color: {BLUE_DARK} !important;
    border: 1px solid {BORDER_MED} !important;
    border-radius: 4px !important;
    padding: 2px 4px !important;
  }}
  span[data-baseweb="tag"] span {{
    color: {TEXT_DARK} !important;
    font-size: 11px !important;
    font-weight: 500 !important;
    background: transparent !important;
  }}
  span[data-baseweb="tag"] button {{
    background: transparent !important;
  }}
  span[data-baseweb="tag"] button svg {{
    fill: {TEXT_MID} !important;
  }}

  /* ── SVG icons (dropdowns, sidebar collapse, etc.) ── */
  .stSelectbox svg, .stMultiSelect svg, .stDateInput svg,
  .stNumberInput svg, .stTimeInput svg {{
    fill: {TEXT_MID} !important;
    color: {TEXT_MID} !important;
  }}
  /* Sidebar toggle / collapse button */
  [data-testid="collapsedControl"] svg, [data-testid="expandedControl"] svg,
  button[kind="header"] svg, [aria-label="Close sidebar"] svg,
  [aria-label="Open sidebar"] svg,
  [data-testid="stSidebarNavCollapseButton"] svg,
  [data-testid="stSidebarCollapseButton"] svg {{
    fill: {TEXT_DARK} !important;
  }}
  /* Sidebar toggle icon text (Material Symbols) */
  [data-testid="stSidebarNavCollapseButton"] [data-testid="stIconMaterial"],
  [data-testid="stSidebarCollapseButton"] [data-testid="stIconMaterial"],
  button[aria-label*="sidebar"] [data-testid="stIconMaterial"],
  button[aria-label*="Sidebar"] [data-testid="stIconMaterial"] {{
    color: {TEXT_DARK} !important;
  }}
  /* Sidebar internal widget SVGs */
  section[data-testid="stSidebar"] .stSelectbox svg,
  section[data-testid="stSidebar"] .stMultiSelect svg,
  section[data-testid="stSidebar"] svg {{
    fill: {TEXT_MID} !important;
    background: transparent !important;
  }}

  /* ── Dropdown list options ── */
  [data-baseweb="popover"] {{
    background: {BG_WHITE} !important;
    border: 1px solid {BORDER_MED} !important;
  }}
  [data-baseweb="popover"] li {{
    background: {BG_WHITE} !important;
    color: {TEXT_DARK} !important;
  }}
  [data-baseweb="popover"] li:hover {{
    background: {BG_SECTION} !important;
  }}
  [data-baseweb="menu"] {{
    background: {BG_WHITE} !important;
    border: 1px solid {BORDER_MED} !important;
  }}
  [data-baseweb="menu"] li, [data-baseweb="menu"] [role="option"] {{
    background: {BG_WHITE} !important;
    color: {TEXT_DARK} !important;
  }}
  [data-baseweb="menu"] li:hover, [data-baseweb="menu"] [role="option"]:hover {{
    background: {BG_SECTION} !important;
  }}

  /* ── Alerts ── */
  div[data-testid="stAlert"][data-baseweb="notification"] {{
    border-radius: 8px !important; box-shadow: 0 1px 3px rgba(0,0,0,.2) !important;
  }}

  /* ── Form container ── */
  div[data-testid="stForm"] {{
    background: {BG_WHITE} !important; border: 1px solid {BORDER} !important;
    border-radius: 8px !important; padding: 1.25rem !important;
    box-shadow: 0 1px 3px rgba(0,0,0,.2) !important;
  }}

  /* ── Empty state ── */
  .empty-state {{
    background: {BG_WHITE}; border: 1px solid {BORDER}; border-radius: 8px;
    padding: 40px 20px; text-align: center; color: {TEXT_MID}; margin: 2rem 0;
  }}
  .empty-state strong {{
    color: {TEXT_DARK}; font-size: 14px; display: block; margin-bottom: 6px;
  }}
  .empty-state span {{ font-size: 12.5px; }}

  /* ── Compliance gauge ── */
  .compliance-bar-bg {{
    background: {BG_PAGE}; border: 1px solid {BORDER};
    border-radius: 99px; height: 6px; margin-top: 8px; overflow: hidden;
  }}
  .compliance-bar-fill {{
    height: 100%; border-radius: 99px;
    transition: width .3s ease;
  }}

  /* ── Progress bar ── */
  div[data-testid="stProgressBar"] > div > div {{
    background-color: {BLUE_DARK} !important;
  }}

  /* ── Toggle ── */
  .stToggle p {{ color: {TEXT_DARK} !important; }}

  /* ── Sidebar multiselect — cap chip area height ── */
  section[data-testid="stSidebar"] .stMultiSelect [data-baseweb="select"] > div:first-child {{
    max-height: 120px !important;
    overflow-y: auto !important;
    scrollbar-width: thin;
    scrollbar-color: {BORDER_MED} {BG_SIDEBAR};
  }}

  /* ── Checkbox colors ── */
  .stCheckbox svg {{ fill: {BLUE_ROYAL} !important; }}
  .stCheckbox label span {{ color: {TEXT_DARK} !important; }}

  /* ── Number input ── */
  .stNumberInput input {{
    background: {BG_WHITE} !important; color: {TEXT_DARK} !important;
    border-color: {BORDER_MED} !important;
  }}

  /* ── Date input ── */
  .stDateInput input {{
    background: {BG_WHITE} !important; color: {TEXT_DARK} !important;
    border-color: {BORDER_MED} !important;
  }}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CABEÇALHO CORPORATIVO
# ─────────────────────────────────────────────────────────────────────────────
_now = datetime.now().strftime("%d %b %Y  %H:%M")
st.markdown(f"""
<div class="corp-header">
  <div class="corp-logo-box">
    <span class="corp-logo-text">DP</span>
  </div>
  <span class="corp-title">Data Protection</span>
  <div class="corp-divider"></div>
  <span class="corp-sub">Presidio PT &mdash; PII Detection &amp; Compliance</span>
  <div class="corp-header-right">
    <span class="corp-status-dot"></span>
    <span class="corp-status-label">Online</span>
    <div class="corp-badge">v3.0 &nbsp;&middot;&nbsp; {_now}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# ENGINES (cached)
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner="Carregando motor de análise NLP...")
def get_analyzer():
    return build_analyzer()


@st.cache_resource
def get_anonymizer():
    try:
        from presidio_anonymizer import AnonymizerEngine
        return AnonymizerEngine()
    except ImportError:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────

TODAS_ENTIDADES = [
    "CPF", "CNPJ", "RG", "PIS_PASEP", "TITULO_ELEITOR", "CNH",
    "CARTAO_CREDITO", "CEP", "TELEFONE_BR", "EMAIL_ADDRESS",
    "PHONE_NUMBER", "PERSON", "LOCATION", "ORGANIZATION", "DATE_TIME",
]

with st.sidebar:
    # ── Branding ─────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="padding:16px 0 12px;border-bottom:1px solid {BORDER};margin-bottom:10px;">
      <div style="
        background: linear-gradient(135deg, {BLUE_DARK} 0%, {BLUE_ROYAL} 100%);
        border-radius: 8px; padding: 14px 16px;
      ">
        <div style="font-size:13px;font-weight:800;color:{TEXT_DARK};letter-spacing:.6px;">
          DATA PROTECTION
        </div>
        <div style="font-size:10px;color:{BLUE_LIGHT};margin-top:3px;letter-spacing:.3px;">
          AI Security Platform &middot; v3.0
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Status + demo toggle ──────────────────────────────────────────────────
    demo_mode = st.toggle("Modo demonstracao", value=True)
    badge_html = (
        f'<span class="rb rb-info" style="margin-top:4px;display:inline-block;">DEMO ATIVO</span>'
        if demo_mode else
        f'<span class="rb rb-neutral" style="margin-top:4px;display:inline-block;">MODO REAL</span>'
    )
    st.markdown(badge_html, unsafe_allow_html=True)

    st.markdown(f"<div style='height:10px;'></div>", unsafe_allow_html=True)

    # ── Configuracoes (popover) ───────────────────────────────────────────────
    with st.popover("Configuracoes de analise", use_container_width=True):
        st.markdown(f'<div class="sb-sec" style="margin-top:4px;">Entidades</div>',
                    unsafe_allow_html=True)
        entidades_sel = st.multiselect(
            "Entidades ativas",
            TODAS_ENTIDADES,
            default=TODAS_ENTIDADES,
            placeholder="Selecione entidades...",
            help="Filtra quais tipos de PII serao detectados na varredura",
            label_visibility="collapsed",
        )
        st.markdown(f'<div class="sb-sec">Confianca minima</div>', unsafe_allow_html=True)
        confianca_min = st.slider(
            "Confianca minima",
            0.0, 1.0, 0.4, 0.05,
            label_visibility="collapsed",
        )
        st.markdown(f'<div class="sb-sec">Notificacao</div>', unsafe_allow_html=True)
        email_cc = st.text_input(
            "E-mail CC",
            placeholder="seguranca@empresa.com.br",
            label_visibility="collapsed",
        )
        st.markdown(
            f'<div style="font-size:11px;color:{TEXT_MUTED};margin-top:8px;">'
            f'{len(entidades_sel)} de {len(TODAS_ENTIDADES)} entidades &nbsp;&middot;&nbsp;'
            f' confianca &ge; {confianca_min:.0%}</div>',
            unsafe_allow_html=True,
        )

    # ── Historico de varreduras ───────────────────────────────────────────────
    if st.session_state.get("scan_history"):
        st.markdown(f'<div class="sb-sec">Historico</div>', unsafe_allow_html=True)
        for h in reversed(st.session_state["scan_history"][-5:]):
            n_altos   = h.get("altos", 0)
            cor_altos = RED_DARK if n_altos > 0 else TEXT_MID
            st.markdown(f"""
            <div class="hist-item">
              <div class="hist-item-header">
                <span class="hist-item-tipo">{h['tipo']}</span>
                <span class="hist-item-time">{h['hora']}</span>
              </div>
              <div class="hist-item-stats">
                {h['total']} detecoes &nbsp;&middot;&nbsp;
                <span style="color:{cor_altos};font-weight:600;">{n_altos} alto risco</span>
              </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Limpar sessao ─────────────────────────────────────────────────────────
    st.markdown(f"<div style='height:8px;'></div>", unsafe_allow_html=True)
    if st.button("Limpar sessao", use_container_width=True, icon=":material/refresh:"):
        for k in ["jira_registros", "cf_registros", "texto_registros",
                  "scan_history", "resolved_jira", "resolved_confluence", "resolved_texto"]:
            st.session_state.pop(k, None)
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# FUNÇÕES AUXILIARES
# ─────────────────────────────────────────────────────────────────────────────

def risco_badge(nivel: str, size: str = "md") -> str:
    cfg = {
        "HIGH":   ("ALTO",  "rb-high"),
        "MEDIUM": ("MÉDIO", "rb-medium"),
        "LOW":    ("BAIXO", "rb-low"),
    }
    label, cls = cfg.get(nivel, ("INFO", "rb-neutral"))
    padding   = "2px 6px"  if size == "sm" else "3px 10px"
    font_size = "10px"     if size == "sm" else "11px"
    return f'<span class="rb {cls}" style="padding:{padding};font-size:{font_size};">{label}</span>'


def gerar_mailto(para: str, assunto: str, corpo: str, cc: str = "") -> str:
    cc_part = f"&cc={urllib.parse.quote(cc)}" if cc else ""
    return (
        f"mailto:{urllib.parse.quote(para)}"
        f"?subject={urllib.parse.quote(assunto)}"
        f"{cc_part}"
        f"&body={urllib.parse.quote(corpo)}"
    )


def corpo_email(usuario: str, refs: list[str], tipos_pii: list[str]) -> str:
    refs_str  = "\n".join(f"  - {r}" for r in refs)
    tipos_str = ", ".join(sorted(set(tipos_pii)))
    return (
        f"Prezado(a),\n\n"
        f"Durante varredura automatizada de conformidade, identificamos dados pessoais "
        f"nos itens abaixo, em possível desacordo com a LGPD (Lei 13.709/2018):\n\n"
        f"Itens identificados:\n{refs_str}\n\n"
        f"Tipos de dados pessoais: {tipos_str}\n\n"
        f"Ação requerida:\n"
        f"  1. Acesse o item e remova ou anonimize os dados listados.\n"
        f"  2. Se os dados forem necessários, abra solicitação formal ao time de Data Protection "
        f"informando a base legal (LGPD Art. 7).\n"
        f"  3. Responda em até 5 dias úteis confirmando a ação.\n\n"
        f"Aviso automático — Presidio PT Data Protection Platform.\n"
        f"Dúvidas: data-protection@empresa.com.br\n\n"
        f"Atenciosamente,\nTime de Data Protection & AI Security"
    )


def _registrar_scan(tipo: str, registros: list[dict]) -> None:
    history = st.session_state.get("scan_history", [])
    history.append({
        "tipo":  tipo,
        "hora":  datetime.now().strftime("%H:%M"),
        "total": len(registros),
        "altos": sum(1 for r in registros if r["_nivel"] == "HIGH"),
    })
    st.session_state["scan_history"] = history[-10:]


def analisar_trechos(trechos: list[dict]) -> list[dict]:
    analyzer         = get_analyzer()
    entidades_filtro = entidades_sel if entidades_sel else None
    registros: list[dict] = []

    for t in trechos:
        texto   = t["texto"]
        results = analyzer.analyze(
            text=texto,
            language="pt",
            entities=entidades_filtro,
            score_threshold=confianca_min,
        )
        for r in results:
            nivel, _ = score(r.entity_type)
            registros.append({
                **t,
                "entidade":    r.entity_type,
                "valor":       texto[r.start:r.end],
                "confianca":   r.score,
                "_nivel":      nivel,
                "_frameworks": frameworks_para_entidade(r.entity_type),
            })

    registros.sort(key=sort_key)
    return registros


def _get_registros_active(registros: list[dict], tipo: str) -> tuple[list[dict], int]:
    """Return (active_registros, resolved_count)."""
    resolved = st.session_state.get(f"resolved_{tipo}", set())
    if not resolved:
        return registros, 0
    active = [r for r in registros if r.get("autor", "") not in resolved]
    return active, len(registros) - len(active)


def _compliance_score(registros: list[dict]) -> int:
    if not registros:
        return 100
    total  = len(registros)
    altos  = sum(1 for r in registros if r["_nivel"] == "HIGH")
    medios = sum(1 for r in registros if r["_nivel"] == "MEDIUM")
    penalidade = (altos * 12 + medios * 4) / max(total, 1) * 100
    return max(0, round(100 - penalidade))


# ─────────────────────────────────────────────────────────────────────────────
# RENDER: KPIs (6 cards)
# ─────────────────────────────────────────────────────────────────────────────

def _render_kpis(registros: list[dict]) -> None:
    total   = len(registros)
    altos   = sum(1 for r in registros if r["_nivel"] == "HIGH")
    medios  = sum(1 for r in registros if r["_nivel"] == "MEDIUM")
    baixos  = sum(1 for r in registros if r["_nivel"] == "LOW")
    users   = len({r.get("autor", "") for r in registros})
    n_fws   = len(frameworks_impactados(registros))
    comp    = _compliance_score(registros)

    comp_cor = (
        RED_DARK    if comp < 60 else
        ORANGE_DARK if comp < 80 else
        GREEN_DARK
    )
    comp_label = (
        "Risco elevado"   if comp < 60 else
        "Atenção requerida" if comp < 80 else
        "Dentro do limite"
    )

    # Barra de preenchimento para compliance
    comp_fill_color = comp_cor
    comp_width      = comp

    # Row 1: compliance score (dominant) + 2 critical KPIs
    col_comp, col_alto, col_medio, col_sec = st.columns([3, 2, 2, 5])
    with col_comp:
        st.markdown(f"""
        <div class="kpi-card" style="border-top:3px solid {comp_cor};min-height:90px;">
          <div class="kpi-label">Score de Conformidade</div>
          <div class="kpi-value" style="font-size:38px;color:{comp_cor};">{comp}%</div>
          <div style="margin-top:10px;">
            <div class="compliance-bar-bg">
              <div class="compliance-bar-fill"
                style="width:{comp_width}%;background:{comp_cor};"></div>
            </div>
          </div>
          <div class="kpi-sub" style="color:{comp_cor};margin-top:6px;">{comp_label}</div>
        </div>
        """, unsafe_allow_html=True)
    with col_alto:
        st.markdown(f"""
        <div class="kpi-card kpi-danger" style="min-height:90px;">
          <div class="kpi-label">Risco alto</div>
          <div class="kpi-value" style="font-size:38px;">{altos}</div>
          <div class="kpi-sub" style="color:{RED_DARK};">Acao imediata</div>
        </div>
        """, unsafe_allow_html=True)
    with col_medio:
        st.markdown(f"""
        <div class="kpi-card kpi-warning" style="min-height:90px;">
          <div class="kpi-label">Risco medio</div>
          <div class="kpi-value" style="font-size:38px;">{medios}</div>
          <div class="kpi-sub" style="color:{ORANGE_DARK};">Requer revisao</div>
        </div>
        """, unsafe_allow_html=True)
    with col_sec:
        # Secondary KPIs — compact row inside the last column
        st.markdown(f"""
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;height:100%;">
          <div class="kpi-card kpi-info" style="padding:12px 14px;">
            <div class="kpi-label">Risco baixo</div>
            <div class="kpi-value" style="font-size:22px;">{baixos}</div>
            <div class="kpi-sub" style="color:{BLUE_ROYAL};">Contextuais</div>
          </div>
          <div class="kpi-card" style="padding:12px 14px;">
            <div class="kpi-label">Usuarios</div>
            <div class="kpi-value" style="font-size:22px;">{users}</div>
            <div class="kpi-sub" style="color:{TEXT_MID};">Expostos</div>
          </div>
          <div class="kpi-card" style="padding:12px 14px;">
            <div class="kpi-label">Frameworks</div>
            <div class="kpi-value" style="font-size:22px;">{n_fws}</div>
            <div class="kpi-sub" style="color:{TEXT_MID};">Ativados</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="font-size:11px;color:{TEXT_MUTED};text-align:right;margin:.4rem 0 1rem;">
      Baseado em {altos} ocorrência(s) critica(s) de {total} detecçoes totais
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# RENDER: CHARTS (distribuição de risco + top entidades)
# ─────────────────────────────────────────────────────────────────────────────

def _plotly_layout(fig: go.Figure, height: int = 300) -> go.Figure:
    fig.update_layout(
        height=height,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=TEXT_DARK, size=11),
        margin=dict(l=4, r=4, t=16, b=4),
        legend=dict(
            bgcolor="rgba(0,0,0,0)", borderwidth=0,
            font=dict(size=11, color=TEXT_MID),
            orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5,
        ),
        xaxis=dict(
            gridcolor=BORDER, linecolor=BORDER_MED,
            tickfont=dict(size=10, color=TEXT_MID),
        ),
        yaxis=dict(
            gridcolor=BORDER, linecolor="rgba(0,0,0,0)",
            tickfont=dict(size=10, color=TEXT_MID),
        ),
        hoverlabel=dict(
            bgcolor=BG_WHITE, bordercolor=BORDER_MED,
            font=dict(size=12, color=TEXT_DARK),
        ),
    )
    return fig


def _render_charts(registros: list[dict], tipo: str = "texto") -> None:
    # ── Quick-filter pills (interative, synced with tabela) ───────────────
    altos  = sum(1 for r in registros if r["_nivel"] == "HIGH")
    medios = sum(1 for r in registros if r["_nivel"] == "MEDIUM")
    baixos = sum(1 for r in registros if r["_nivel"] == "LOW")

    _NIVEL_MAP  = {"Alto": "HIGH", "Medio": "MEDIUM", "Baixo": "LOW"}
    _NIVEL_RMAP = {"HIGH": "Alto", "MEDIUM": "Medio", "LOW": "Baixo"}

    pills_options = [
        "Todos",
        f"Alto ({altos})",
        f"Medio ({medios})",
        f"Baixo ({baixos})",
    ]
    # Determine default from existing session-state filter
    _cur_nivel  = st.session_state.get(f"qfilt_nivel_{tipo}", "ALL")
    _cnt_map    = {"HIGH": altos, "MEDIUM": medios, "LOW": baixos}
    _label_map  = {"HIGH": "Alto", "MEDIUM": "Medio", "LOW": "Baixo"}
    if _cur_nivel != "ALL" and _cur_nivel in _label_map:
        _lbl = _label_map[_cur_nivel]
        _cnt = _cnt_map[_cur_nivel]
        _default_pill = f"{_lbl} ({_cnt})"
    else:
        _default_pill = "Todos"
    # Validate default is still a valid option
    if _default_pill not in pills_options:
        _default_pill = "Todos"

    selected_pill = st.pills(
        "Filtro rapido",
        pills_options,
        default=_default_pill,
        key=f"pills_{tipo}",
        label_visibility="collapsed",
    )
    # Sync pill → session_state
    if selected_pill is None or selected_pill == "Todos":
        st.session_state[f"qfilt_nivel_{tipo}"] = "ALL"
        st.session_state[f"qfilt_entity_{tipo}"] = ""
    else:
        # Extract label without count
        pill_label = selected_pill.split(" (")[0]
        st.session_state[f"qfilt_nivel_{tipo}"] = _NIVEL_MAP.get(pill_label, "ALL")

    col_donut, col_bar, col_conf = st.columns([1, 2, 1])

    # ── Donut: distribuição de risco (clicável) ───────────────────────────
    with col_donut:
        st.markdown(f'<div class="chart-title">Distribuicao de risco — clique para filtrar</div>',
                    unsafe_allow_html=True)
        contagem = Counter(r["_nivel"] for r in registros)
        labels   = ["Alto", "Medio", "Baixo"]
        values   = [contagem.get("HIGH", 0), contagem.get("MEDIUM", 0), contagem.get("LOW", 0)]
        colors   = [RED_DARK, ORANGE_DARK, GREEN_DARK]

        fig_d = go.Figure(go.Pie(
            labels=labels, values=values,
            hole=0.60,
            marker=dict(colors=colors, line=dict(color=BG_PAGE, width=2)),
            textfont=dict(size=11, color=TEXT_DARK),
            hovertemplate="<b>%{label}</b><br>%{value} detecoes<br>%{percent}<extra></extra>",
        ))
        fig_d.update_layout(
            height=240,
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=0, b=40),
            showlegend=True,
            legend=dict(
                bgcolor="rgba(0,0,0,0)", borderwidth=0,
                font=dict(size=11, color=TEXT_MID),
                orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5,
            ),
            hoverlabel=dict(bgcolor=BG_WHITE, bordercolor=BORDER_MED,
                            font=dict(size=12, color=TEXT_DARK)),
        )
        donut_event = st.plotly_chart(
            fig_d, use_container_width=True,
            config={"displayModeBar": False},
            on_select="rerun", selection_mode=["points"],
            key=f"donut_{tipo}",
        )
        # Handle donut click → set nivel filter
        if donut_event and donut_event.selection and donut_event.selection.points:
            clicked = donut_event.selection.points[0].get("label", "")
            nivel = _NIVEL_MAP.get(clicked, "ALL")
            st.session_state[f"qfilt_nivel_{tipo}"] = nivel
            st.session_state[f"qfilt_entity_{tipo}"] = ""

    # ── Barras horizontais: top entidades (clicável) ──────────────────────
    with col_bar:
        st.markdown(f'<div class="chart-title">Ocorrencias por entidade — clique para filtrar</div>',
                    unsafe_allow_html=True)
        entity_counts = Counter(r["entidade"] for r in registros)
        top = entity_counts.most_common(8)
        if top:
            y_labels = [t[0] for t in reversed(top)]
            x_vals   = [t[1] for t in reversed(top)]
            bar_colors = []
            for lbl in y_labels:
                nivel_e, _ = score(lbl)
                bar_colors.append(
                    RED_DARK    if nivel_e == "HIGH"   else
                    ORANGE_DARK if nivel_e == "MEDIUM" else
                    GREEN_DARK
                )
            fig_bar = go.Figure(go.Bar(
                y=y_labels, x=x_vals, orientation="h",
                marker=dict(color=bar_colors, line=dict(width=0)),
                hovertemplate="<b>%{y}</b><br>%{x} ocorrencias<extra></extra>",
            ))
            fig_bar = _plotly_layout(fig_bar, height=240)
            fig_bar.update_layout(margin=dict(l=4, r=4, t=0, b=0), showlegend=False)
            fig_bar.update_xaxes(showgrid=True, title_text="")
            fig_bar.update_yaxes(showgrid=False, title_text="")
            bar_event = st.plotly_chart(
                fig_bar, use_container_width=True,
                config={"displayModeBar": False},
                on_select="rerun", selection_mode=["points"],
                key=f"bar_{tipo}",
            )
            # Handle bar click → set entity filter
            if bar_event and bar_event.selection and bar_event.selection.points:
                clicked_ent = bar_event.selection.points[0].get("y", "")
                if clicked_ent:
                    st.session_state[f"qfilt_entity_{tipo}"] = clicked_ent
                    st.session_state[f"qfilt_nivel_{tipo}"] = "ALL"

    # ── Frameworks impactados ──────────────────────────────────────────────
    with col_conf:
        st.markdown(f'<div class="chart-title">Frameworks impactados</div>', unsafe_allow_html=True)
        fws = frameworks_impactados(registros)
        if fws:
            top_fw = list(fws.items())[:6]
            for fw_name, cnt in top_fw:
                pct = int(cnt / len(registros) * 100) if registros else 0
                st.markdown(f"""
                <div style="margin-bottom:8px;">
                  <div style="display:flex;justify-content:space-between;
                    font-size:11px;margin-bottom:3px;">
                    <span style="color:{TEXT_DARK};font-weight:600;">{fw_name}</span>
                    <span style="color:{TEXT_MID};">{cnt}</span>
                  </div>
                  <div style="background:{BORDER};border-radius:99px;height:4px;overflow:hidden;">
                    <div style="width:{pct}%;height:100%;background:{BLUE_ROYAL};
                      border-radius:99px;"></div>
                  </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f'<span style="color:{TEXT_MUTED};font-size:12px;">Nenhum framework ativado.</span>',
                        unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# RENDER: TABELA DE RESULTADOS
# ─────────────────────────────────────────────────────────────────────────────

def _render_tabela(registros: list[dict], tipo: str = "jira") -> None:
    with st.container():
        st.markdown('<div class="sec-hdr">Resultados da varredura</div>', unsafe_allow_html=True)

        # Read quick-filter state set by charts/pills
        _qnivel  = st.session_state.get(f"qfilt_nivel_{tipo}", "ALL")
        _qentity = st.session_state.get(f"qfilt_entity_{tipo}", "")

        _nivel_to_label = {
            "HIGH": "Alto (HIGH)", "MEDIUM": "Medio (MEDIUM)", "LOW": "Baixo (LOW)",
        }
        _default_nivel = _nivel_to_label.get(_qnivel, "Todos")
        _nivel_opts    = ["Todos", "Alto (HIGH)", "Medio (MEDIUM)", "Baixo (LOW)"]

        ents_uniq = sorted({r["entidade"] for r in registros})
        _default_ent = _qentity if _qentity in ents_uniq else "Todas"

        col_flt, col_ent, col_clear = st.columns([2, 2, 2])
        with col_flt:
            filtro = st.selectbox(
                "Nivel de risco",
                _nivel_opts,
                index=_nivel_opts.index(_default_nivel),
                key=f"filtro_{tipo}",
            )
        with col_ent:
            ent_filtro = st.selectbox(
                "Tipo de entidade",
                ["Todas"] + ents_uniq,
                index=(["Todas"] + ents_uniq).index(_default_ent),
                key=f"ent_{tipo}",
            )
        with col_clear:
            st.markdown("<div style='height:26px;'></div>", unsafe_allow_html=True)
            if st.button("Limpar filtros", key=f"clear_filt_{tipo}", use_container_width=True,
                         icon=":material/filter_alt_off:"):
                st.session_state[f"qfilt_nivel_{tipo}"] = "ALL"
                st.session_state[f"qfilt_entity_{tipo}"] = ""
                st.rerun()

        mapa = {"Alto (HIGH)": "HIGH", "Medio (MEDIUM)": "MEDIUM", "Baixo (LOW)": "LOW"}
        filtrados = registros
        if filtro != "Todos":
            filtrados = [r for r in filtrados if r["_nivel"] == mapa.get(filtro, filtro)]
        if ent_filtro != "Todas":
            filtrados = [r for r in filtrados if r["entidade"] == ent_filtro]

        if not filtrados:
            st.markdown(f"""
            <div class="empty-state">
              <strong>Nenhuma detecção para os filtros aplicados</strong>
              <span>Ajuste os filtros de risco ou tipo de entidade.</span>
            </div>
            """, unsafe_allow_html=True)
            return

        ref_col = "issue_key" if tipo == "jira" else "pagina"
        url_col = "issue_url" if tipo == "jira" else "page_url"

        rows = []
        for r in filtrados:
            ref  = r.get(ref_col, "")
            url  = r.get(url_col, "")
            link = f"[{ref}]({url})" if url else ref
            rows.append({
                "Risco":      r["_nivel"],
                "Entidade":   r["entidade"],
                "Valor":      r["valor"],
                "Referência": link,
                "Autor":      r.get("autor", ""),
                "Confiança":  f'{r["confianca"]:.0%}',
                "Frameworks": " | ".join(r["_frameworks"][:2]),
            })

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True, height=340)

        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            csv = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button(
                "Exportar CSV",
                csv,
                file_name=f"pii_{tipo}_scan.csv",
                mime="text/csv",
                use_container_width=True,
                key=f"dl_{tipo}",
            )
        with col_dl2:
            xlsx_data = _to_excel(df)
            st.download_button(
                "Exportar Excel",
                xlsx_data,
                file_name=f"pii_{tipo}_scan.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key=f"dl_xl_{tipo}",
            )


def _to_excel(df: pd.DataFrame) -> bytes:
    import io
    buf = io.BytesIO()
    try:
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Detecções")
    except Exception:
        # Fallback para CSV se openpyxl não estiver disponível
        return df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# RENDER: NOTIFICAÇÕES POR USUÁRIO
# ─────────────────────────────────────────────────────────────────────────────

def _render_notificacoes(registros: list[dict], tipo: str = "jira") -> None:
    with st.container():
        st.markdown('<div class="sec-hdr">Notificações por usuário</div>', unsafe_allow_html=True)

        ref_col = "issue_key" if tipo == "jira" else "pagina"

        por_usuario: dict[str, list] = {}
        for r in registros:
            por_usuario.setdefault(r.get("autor", "desconhecido"), []).append(r)

        if not por_usuario:
            st.markdown(f"""
            <div class="empty-state">
              <strong>Nenhuma notificação para emitir</strong>
              <span>Não há registros que possam ser notificados.</span>
            </div>
            """, unsafe_allow_html=True)
            return

        # ── Bulk notify ──────────────────────────────────────────────────────
        origem_bulk = "Jira" if tipo == "jira" else "Confluence"
        ref_col_bulk = "issue_key" if tipo == "jira" else "pagina"
        col_bulk, col_bulk_info = st.columns([2, 5])
        with col_bulk:
            all_refs  = sorted({r.get(ref_col_bulk, "") for r in registros})
            all_tipos = [r["entidade"] for r in registros]
            all_users = sorted(por_usuario.keys())
            # Build a single mailto with all users as recipients
            bulk_mailto = gerar_mailto(
                "; ".join(all_users),
                f"[Data Protection] PII detectado — {origem_bulk}: {len(registros)} ocorrências",
                corpo_email(
                    f"{len(all_users)} usuário(s) ({', '.join(all_users[:3])}{'...' if len(all_users)>3 else ''})",
                    all_refs[:20],
                    all_tipos,
                ),
                email_cc,
            )
            st.link_button(
                f"Notificar todos ({len(all_users)})",
                bulk_mailto,
                use_container_width=True,
                icon=":material/group:",
            )
        with col_bulk_info:
            n_altos_total = sum(1 for r in registros if r["_nivel"] == "HIGH")
            st.markdown(f"""
            <div style="font-size:12px;color:{TEXT_MID};padding:8px 0;">
              {len(all_users)} usuario(s) exposto(s) &nbsp;&middot;&nbsp;
              <span style="color:{RED_DARK};font-weight:600;">{n_altos_total} risco alto</span>
              &nbsp;&middot;&nbsp; {len(all_refs)} referencia(s) identificada(s)
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<hr style='border-color:{BORDER};margin:12px 0;'>".format(BORDER=BORDER),
                    unsafe_allow_html=True)

        resolved_set = st.session_state.get(f"resolved_{tipo}", set())

        # Show "resolved" counter + restore option
        if resolved_set:
            col_rv, col_rv2 = st.columns([3, 1])
            with col_rv:
                st.markdown(
                    f'<div style="font-size:12px;color:{TEXT_MUTED};padding:6px 0;">'
                    f'{len(resolved_set)} usuario(s) marcado(s) como resolvido/falso-positivo '
                    f'— excluido(s) dos KPIs e graficos.</div>',
                    unsafe_allow_html=True,
                )
            with col_rv2:
                if st.button("Restaurar todos", key=f"restore_{tipo}",
                             use_container_width=True, icon=":material/undo:"):
                    st.session_state[f"resolved_{tipo}"] = set()
                    st.rerun()

        for usuario, itens in sorted(por_usuario.items(), key=lambda x: -len(x[1])):
            n_altos  = sum(1 for i in itens if i["_nivel"] == "HIGH")
            n_medios = sum(1 for i in itens if i["_nivel"] == "MEDIUM")
            status = (
                f"ALTO — {n_altos} critica(s)" if n_altos
                else f"MEDIO — {n_medios} detecao(oes)"
            )
            with st.expander(f"{usuario}  —  {len(itens)} detecao(oes)  |  {status}"):
                refs   = sorted({r.get(ref_col, "") for r in itens})
                tipos  = [r["entidade"] for r in itens]
                fw_set: set[str] = set()
                for r in itens:
                    fw_set.update(r["_frameworks"])

                col_info, col_btns = st.columns([3, 1])
                with col_info:
                    st.markdown(f'<div class="notify-email">{usuario}</div>', unsafe_allow_html=True)
                    st.markdown(f"**Referencias:** {', '.join(refs)}")
                    st.markdown(f"**Tipos de PII:** {', '.join(sorted(set(tipos)))}")
                    pills_fw = "".join(f'<span class="fw-pill">{f}</span>' for f in sorted(fw_set))
                    st.markdown(f"**Frameworks:** {pills_fw}", unsafe_allow_html=True)

                with col_btns:
                    origem  = "Jira" if tipo == "jira" else "Confluence"
                    assunto = f"[Data Protection] PII detectado — {origem}: {', '.join(refs[:2])}"
                    mailto  = gerar_mailto(
                        usuario, assunto, corpo_email(usuario, refs, tipos), email_cc
                    )
                    st.link_button(
                        "Notificar por e-mail",
                        mailto,
                        use_container_width=True,
                        icon=":material/email:",
                    )
                    # Resolve / false-positive button
                    _btn_label = "Restaurar" if usuario in resolved_set else "Marcar resolvido"
                    _btn_icon  = ":material/undo:" if usuario in resolved_set else ":material/check_circle:"
                    if st.button(_btn_label, key=f"resolve_{usuario}_{tipo}",
                                 use_container_width=True, icon=_btn_icon):
                        _rs = st.session_state.get(f"resolved_{tipo}", set())
                        if usuario in _rs:
                            _rs.discard(usuario)
                        else:
                            _rs.add(usuario)
                        st.session_state[f"resolved_{tipo}"] = _rs
                        st.rerun()

                df_u = pd.DataFrame([{
                    "Risco":    r["_nivel"],
                    "Entidade": r["entidade"],
                    "Valor":    r["valor"],
                    "Ref":      r.get(ref_col, ""),
                } for r in itens])
                st.dataframe(df_u, use_container_width=True, hide_index=True, height=180)


# ─────────────────────────────────────────────────────────────────────────────
# RENDER: RELATÓRIO EXECUTIVO
# ─────────────────────────────────────────────────────────────────────────────

def _render_resumo_executivo(registros: list[dict], tipo: str) -> None:
    if not registros:
        return

    st.markdown('<div class="sec-hdr">Relatório executivo</div>', unsafe_allow_html=True)

    total   = len(registros)
    altos   = sum(1 for r in registros if r["_nivel"] == "HIGH")
    medios  = sum(1 for r in registros if r["_nivel"] == "MEDIUM")
    baixos  = sum(1 for r in registros if r["_nivel"] == "LOW")
    users   = len({r.get("autor", "") for r in registros})
    fws     = frameworks_impactados(registros)
    comp    = _compliance_score(registros)

    st.markdown(f"""
    <div class="report-card">
      <div style="font-size:13px;font-weight:700;color:{TEXT_DARK};margin-bottom:12px;">
        Sumário da varredura — {tipo.title()}
        <span style="font-size:11px;font-weight:400;color:{TEXT_MUTED};margin-left:8px;">
          {datetime.now().strftime('%d/%m/%Y %H:%M')}
        </span>
      </div>
      <div style="display:flex;flex-wrap:wrap;gap:0;">
        <div class="report-stat"><strong>{total}</strong><br>Total de detecções</div>
        <div class="report-stat" style="border-left-color:{RED_DARK}">
          <strong style="color:{RED_DARK};">{altos}</strong><br>Alto risco
        </div>
        <div class="report-stat">
          <strong style="color:{ORANGE_DARK};">{medios}</strong><br>Médio risco
        </div>
        <div class="report-stat">
          <strong style="color:{GREEN_DARK};">{baixos}</strong><br>Baixo risco
        </div>
        <div class="report-stat">
          <strong>{users}</strong><br>Usuários expostos
        </div>
        <div class="report-stat">
          <strong style="color:{'#EF4444' if comp < 60 else '#F97316' if comp < 80 else '#22C55E'};">
            {comp}%
          </strong><br>Score conformidade
        </div>
      </div>
      <div style="margin-top:14px;font-size:12px;color:{TEXT_MID};">
        <strong style="color:{TEXT_DARK};">Frameworks impactados:</strong>&nbsp;
        {"&nbsp;".join(f'<span class="fw-pill">{k} ({v})</span>' for k,v in list(fws.items())[:5])}
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Relatório para download
    linhas_usuarios: list[str] = []
    por_usuario: dict[str, list] = {}
    for r in registros:
        por_usuario.setdefault(r.get("autor", "desconhecido"), []).append(r)
    for usr, itens in sorted(por_usuario.items(), key=lambda x: -len(x[1])):
        n_a = sum(1 for i in itens if i["_nivel"] == "HIGH")
        n_m = sum(1 for i in itens if i["_nivel"] == "MEDIUM")
        linhas_usuarios.append(f"  - {usr}: {len(itens)} detecção(ões) [{n_a} alto, {n_m} médio]")

    relatorio = (
        f"DATA PROTECTION SCAN REPORT\n"
        f"{'='*60}\n"
        f"Data/hora  : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
        f"Fonte      : {tipo.title()}\n"
        f"Plataforma : Presidio PT v3.0\n\n"
        f"RESUMO EXECUTIVO\n{'-'*40}\n"
        f"Total de detecções : {total}\n"
        f"Alto risco         : {altos}\n"
        f"Médio risco        : {medios}\n"
        f"Baixo risco        : {baixos}\n"
        f"Usuários expostos  : {users}\n"
        f"Score conformidade : {comp}%\n\n"
        f"FRAMEWORKS IMPACTADOS\n{'-'*40}\n"
        + "\n".join(f"  - {k}: {v} ocorrência(s)" for k, v in fws.items())
        + f"\n\nUSUÁRIOS AFETADOS\n{'-'*40}\n"
        + "\n".join(linhas_usuarios)
        + f"\n\nDETECÇÕES (primeiras 50)\n{'-'*40}\n"
        + "\n".join(
            f"  [{r['_nivel']:6}] {r['entidade']:20} | "
            f"Confiança: {r['confianca']:.0%} | Autor: {r.get('autor','')}"
            for r in registros[:50]
        )
        + f"\n\n{'='*60}\n"
        f"Relatório gerado automaticamente pela plataforma Presidio PT.\n"
        f"Para dúvidas: data-protection@empresa.com.br\n"
    )

    st.download_button(
        "Baixar relatório executivo (.txt)",
        relatorio.encode("utf-8"),
        file_name=f"relatorio_dp_{tipo}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
        mime="text/plain",
        use_container_width=True,
        key=f"dl_rel_{tipo}",
    )


# ─────────────────────────────────────────────────────────────────────────────
# TAB HEADER
# ─────────────────────────────────────────────────────────────────────────────

def _tab_header(title: str, subtitle: str = "") -> None:
    st.markdown(f"""
    <div style="margin-bottom:1.5rem;">
      <div class="sec-hdr" style="display:block;margin-bottom:0.5rem;">{title}</div>
      {f'<p style="color:{TEXT_MID};font-size:13px;margin:0 0 1rem;">{subtitle}</p>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# ABAS PRINCIPAIS (5 abas)
# ─────────────────────────────────────────────────────────────────────────────

tab_texto, tab_jira, tab_confluence, tab_frameworks, tab_anonimizar = st.tabs([
    "Texto Livre",
    "Jira",
    "Confluence",
    "Frameworks",
    "Anonymizar",
])


# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — Texto Livre
# ════════════════════════════════════════════════════════════════════════════
with tab_texto:
    _tab_header(
        "Análise de Texto Livre",
        "Cole qualquer texto para detectar dados pessoais (PII) com o motor Presidio PT."
    )
    texto = st.text_area(
        "Texto para análise",
        height=180,
        placeholder=(
            "Ex: O cliente João Silva, CPF 123.456.789-09, mora em São Paulo, "
            "CEP 01310-100. Telefone: (11) 98765-4321."
        ),
        label_visibility="collapsed",
        key="texto_input",
    )

    col_btn, col_clear = st.columns([2, 1])
    with col_btn:
        run_texto = st.button("Executar análise", key="btn_texto", use_container_width=True)
    with col_clear:
        if st.button("Limpar resultados", key="btn_clear_texto", use_container_width=True):
            st.session_state.pop("texto_registros", None)
            st.rerun()

    if run_texto:
        if not texto.strip():
            st.warning("Insira algum texto para analisar.")
        else:
            with st.spinner("Analisando..."):
                regs_t = analisar_trechos([{
                    "texto": texto, "autor": "usuário", "campo": "entrada livre"
                }])
                st.session_state["texto_registros"] = regs_t
                _registrar_scan("Texto", regs_t)

    if st.session_state.get("texto_registros") is not None:
        regs_t = st.session_state["texto_registros"]
        if not regs_t:
            st.success("Nenhum dado pessoal detectado com os parâmetros configurados.")
        else:
            regs_t_active, _n_res_t = _get_registros_active(regs_t, "texto")
            if _n_res_t:
                st.info(f"{_n_res_t} detecao(oes) excluida(s) por resolucao/falso-positivo.")
            _render_kpis(regs_t_active)
            _render_charts(regs_t_active, "texto")
            _render_tabela(regs_t_active, "texto")
            _render_resumo_executivo(regs_t_active, "texto")


# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — Jira
# ════════════════════════════════════════════════════════════════════════════
with tab_jira:
    _tab_header(
        "Conexão e Varredura Jira",
        "Conecte-se a uma instância Jira e varra issues em busca de dados pessoais."
    )

    _jira_has_results = bool(st.session_state.get("jira_registros"))
    with st.expander(
        "Parametros de varredura" if not _jira_has_results else "Editar parametros de varredura",
        expanded=not _jira_has_results,
    ):
      with st.form("jira_form"):
        c1, c2 = st.columns(2)
        with c1:
            jira_versao  = st.selectbox("Versao", ["Cloud", "Server / Data Center"])
            jira_url     = st.text_input("URL da instancia",
                                          placeholder="https://empresa.atlassian.net",
                                          key="jira_url")
            jira_usuario = st.text_input("Usuario / e-mail", key="jira_user")
        with c2:
            jira_token   = st.text_input("API Token / Senha", type="password",
                                          key="jira_token")
            jira_project = st.text_input("Project Key", placeholder="PROJ",
                                          key="jira_project")
            jira_types   = st.multiselect(
                "Tipos de issue",
                ["Bug", "Story", "Task", "Epic", "Sub-task", "Improvement"],
                default=["Bug", "Story", "Task"], key="jira_types",
            )
        c3, c4 = st.columns(2)
        with c3:
            jira_campos = st.multiselect(
                "Campos a varrer",
                ["Titulo (summary)", "Descricao", "Comentarios", "Campos customizados"],
                default=["Titulo (summary)", "Descricao", "Comentarios"],
                key="jira_campos",
            )
            jira_data_str = st.text_input(
                "Issues criadas a partir de (DD/MM/AAAA)",
                value="",
                placeholder="01/01/2024",
                key="jira_data",
            )
        with c4:
            jira_jql = st.text_input("JQL extra (opcional)",
                                      placeholder='labels = "pii-review"',
                                      key="jira_jql")
            jira_max = st.number_input("Max. issues", min_value=10, max_value=500,
                                        value=50, step=10, key="jira_max")

        submitted_jira = st.form_submit_button(
            "Conectar e Executar Varredura", use_container_width=True
        )

    if submitted_jira or (demo_mode and "jira_registros" not in st.session_state):
        if demo_mode:
            with st.spinner("Carregando dados de demonstração..."):
                time.sleep(0.8)
                regs = analisar_trechos(JIRA_DEMO_TRECHOS)
                st.session_state["jira_registros"] = regs
                _registrar_scan("Jira", regs)
            st.success(f"Demonstração: {len(JIRA_DEMO_TRECHOS)} issues processadas.")
        else:
            from plugins.jira_plugin import JiraPlugin
            plugin = JiraPlugin()
            ok, msg = plugin.conectar(jira_url, jira_usuario, jira_token,
                                       jira_versao == "Cloud")
            if not ok:
                st.error(msg)
            else:
                st.success(msg)
                campos_map = {
                    "Título (summary)":    "summary",
                    "Descrição":           "description",
                    "Comentários":         "comments",
                    "Campos customizados": "custom",
                }
                campos_map2 = {
                    "Titulo (summary)":    "summary",
                    "Descricao":           "description",
                    "Comentarios":         "comments",
                    "Campos customizados": "custom",
                }
                campos_sel = [campos_map2.get(c, c) for c in jira_campos]
                data_str = ""
                if jira_data_str.strip():
                    try:
                        from datetime import date as _date
                        parts = jira_data_str.strip().split("/")
                        data_str = f"{parts[2]}-{parts[1]}-{parts[0]}"
                    except Exception:
                        st.warning("Formato de data inválido — use DD/MM/AAAA.")
                        data_str = ""
                try:
                    issues  = plugin.buscar_issues(jira_project, jira_types,
                                                    jira_jql, data_str, int(jira_max))
                    trechos = []
                    bar = st.progress(0, text="Processando issues...")
                    for i, issue in enumerate(issues):
                        trechos.extend(plugin.extrair_textos(issue, campos_sel))
                        bar.progress((i + 1) / len(issues),
                                     text=f"Issue {i+1} / {len(issues)}")
                    bar.empty()
                    regs = analisar_trechos(trechos)
                    st.session_state["jira_registros"] = regs
                    _registrar_scan("Jira", regs)
                    st.success(f"{len(issues)} issues processadas — {len(regs)} detecções.")
                except Exception as exc:
                    st.error(f"Erro: {exc}")

    if st.session_state.get("jira_registros"):
        regs = st.session_state["jira_registros"]
        regs_active, _n_res = _get_registros_active(regs, "jira")
        if _n_res:
            st.info(f"{_n_res} detecao(oes) excluida(s) por resolucao/falso-positivo.")
        _render_kpis(regs_active)
        _render_charts(regs_active, "jira")
        _render_tabela(regs_active, "jira")
        _render_notificacoes(regs_active, "jira")
        _render_resumo_executivo(regs_active, "jira")


# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — Confluence
# ════════════════════════════════════════════════════════════════════════════
with tab_confluence:
    _tab_header(
        "Conexão e Varredura Confluence",
        "Conecte-se a uma instância Confluence e varra páginas em busca de dados pessoais."
    )

    PAGE_STATUS_MAP = {
        "Publicadas (current)":  "current",
        "Rascunhos (draft)":     "draft",
        "Arquivadas (archived)": "archived",
    }

    _cf_has_results = bool(st.session_state.get("cf_registros"))
    with st.expander(
        "Parametros de varredura" if not _cf_has_results else "Editar parametros de varredura",
        expanded=not _cf_has_results,
    ):
      with st.form("confluence_form"):
        c1, c2 = st.columns(2)
        with c1:
            cf_versao  = st.selectbox("Versao", ["Cloud", "Server / Data Center"], key="cf_v")
            cf_url     = st.text_input("URL da instancia",
                                        placeholder="https://empresa.atlassian.net", key="cf_url")
            cf_usuario = st.text_input("Usuario / e-mail", key="cf_user")
        with c2:
            cf_token  = st.text_input("API Token / Senha", type="password", key="cf_tok")
            cf_space  = st.text_input("Space Key", placeholder="DS", key="cf_sp")
            cf_status = st.selectbox("Status das paginas", list(PAGE_STATUS_MAP.keys()),
                                      key="cf_st")
        c3, c4 = st.columns(2)
        with c3:
            cf_titulo = st.checkbox("Incluir titulo da pagina", value=True, key="cf_titulo")
            cf_corpo  = st.checkbox("Incluir corpo da pagina", value=True, key="cf_corpo")
        with c4:
            cf_max = st.number_input("Max. paginas", min_value=10, max_value=300,
                                      value=50, step=10, key="cf_max")

        submitted_cf = st.form_submit_button(
            "Conectar e Executar Varredura", use_container_width=True
        )

    if submitted_cf or (demo_mode and "cf_registros" not in st.session_state):
        if demo_mode:
            with st.spinner("Carregando dados de demonstração..."):
                time.sleep(0.8)
                regs_cf = analisar_trechos(CONFLUENCE_DEMO_TRECHOS)
                st.session_state["cf_registros"] = regs_cf
                _registrar_scan("Confluence", regs_cf)
            st.success(f"Demonstração: {len(CONFLUENCE_DEMO_TRECHOS)} páginas processadas.")
        else:
            from plugins.confluence_plugin import ConfluencePlugin
            plugin_cf = ConfluencePlugin()
            ok, msg = plugin_cf.conectar(cf_url, cf_usuario, cf_token, cf_versao == "Cloud")
            if not ok:
                st.error(msg)
            else:
                st.success(msg)
                try:
                    paginas = plugin_cf.buscar_paginas(
                        cf_space, PAGE_STATUS_MAP[cf_status], True, int(cf_max)
                    )
                    trechos_cf: list[dict] = []
                    bar = st.progress(0, text="Processando páginas...")
                    for i, page in enumerate(paginas):
                        trechos_cf.extend(plugin_cf.extrair_textos(page, cf_titulo, cf_corpo))
                        bar.progress((i + 1) / len(paginas),
                                     text=f"Página {i+1} / {len(paginas)}")
                    bar.empty()
                    regs_cf = analisar_trechos(trechos_cf)
                    st.session_state["cf_registros"] = regs_cf
                    _registrar_scan("Confluence", regs_cf)
                    st.success(f"{len(paginas)} páginas — {len(regs_cf)} detecções.")
                except Exception as exc:
                    st.error(f"Erro: {exc}")

    if st.session_state.get("cf_registros"):
        regs_cf = st.session_state["cf_registros"]
        regs_cf_active, _n_res_cf = _get_registros_active(regs_cf, "confluence")
        if _n_res_cf:
            st.info(f"{_n_res_cf} detecao(oes) excluida(s) por resolucao/falso-positivo.")
        _render_kpis(regs_cf_active)
        _render_charts(regs_cf_active, "confluence")
        _render_tabela(regs_cf_active, "confluence")
        _render_notificacoes(regs_cf_active, "confluence")
        _render_resumo_executivo(regs_cf_active, "confluence")


# ════════════════════════════════════════════════════════════════════════════
# TAB 4 — Frameworks e Compliance
# ════════════════════════════════════════════════════════════════════════════
with tab_frameworks:
    _tab_header(
        "Frameworks de Mercado — Data Security e AI",
        "Referência consolidada dos principais frameworks regulatórios e de segurança "
        "relevantes para Data Protection e AI Security."
    )

    todos_regs = (
        st.session_state.get("jira_registros", []) +
        st.session_state.get("cf_registros", []) +
        st.session_state.get("texto_registros", [])
    )
    fws_hit = frameworks_impactados(todos_regs)

    if fws_hit:
        st.markdown(
            '<div class="sec-hdr-sm">Frameworks ativados nas varreduras desta sessão</div>',
            unsafe_allow_html=True,
        )
        pills = "".join(
            f'<span class="fw-pill" style="background:{BLUE_DARK};color:{TEXT_DARK};'
            f'border-color:{BLUE_DARK};">{fw} ({cnt})</span>'
            for fw, cnt in fws_hit.items()
        )
        st.markdown(pills + "<br><br>", unsafe_allow_html=True)

    col_flt, _ = st.columns([2, 5])
    with col_flt:
        filtro_fw = st.selectbox(
            "Filtrar por nível de impacto",
            ["Todos", "CRITICO", "ALTO", "MEDIO", "BAIXO"],
            key="fw_filt",
        )

    nivel_borda = {
        "CRITICO": RED_DARK,
        "ALTO":    ORANGE_DARK,
        "MEDIO":   BLUE_ROYAL,
        "BAIXO":   GREEN_DARK,
    }
    nivel_label_pt = {
        "CRITICO": "CRÍTICO",
        "ALTO":    "ALTO",
        "MEDIO":   "MÉDIO",
        "BAIXO":   "BAIXO",
    }

    st.markdown('<div class="sec-hdr">Referência de frameworks</div>', unsafe_allow_html=True)

    for nome, fw in AI_FRAMEWORKS.items():
        nivel      = fw["nivel_impacto"]
        nivel_norm = nivel.replace("CRÍTICO", "CRITICO").replace("MÉDIO", "MEDIO")
        if filtro_fw != "Todos" and nivel_norm != filtro_fw:
            continue

        cor_borda  = nivel_borda.get(nivel_norm, BLUE_ROYAL)
        nivel_disp = nivel_label_pt.get(nivel_norm, nivel)
        hit_count  = fws_hit.get(nome.split(" ")[0], 0)
        hit_badge  = (
            f' &nbsp;<span class="rb rb-high" style="padding:2px 7px;font-size:10px;">'
            f'{hit_count} ocorrência(s)</span>'
            if hit_count else ""
        )

        with st.expander(
            f"{nome}  —  Impacto {nivel_disp}",
            expanded=(nivel_norm == "CRITICO"),
        ):
            col_left, col_right = st.columns([2, 3])

            with col_left:
                st.markdown(f"""
                <div style="color:{TEXT_MUTED};font-size:10.5px;font-weight:700;
                  text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;">
                  Controle Principal
                </div>
                <div style="color:{TEXT_DARK};font-size:13px;font-weight:600;
                  margin-bottom:14px;">{fw['controle']}</div>

                <div style="color:{TEXT_MUTED};font-size:10.5px;font-weight:700;
                  text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;">
                  Artigos / Funções
                </div>
                <div style="margin-bottom:16px;">
                  {"".join(f'<span class="fw-pill">{f}</span>' for f in fw["funcoes"])}
                </div>

                <div style="display:inline-block;padding:5px 14px;border-radius:4px;
                  background:{BLUE_PALE};border:1.5px solid {cor_borda};
                  color:{cor_borda};font-size:11px;font-weight:700;letter-spacing:.3px;">
                  Impacto: {nivel_disp}
                </div>
                {hit_badge}
                """, unsafe_allow_html=True)

            with col_right:
                st.markdown(f"""
                <div style="color:{TEXT_MUTED};font-size:10.5px;font-weight:700;
                  text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;">
                  Descrição e Impacto
                </div>
                <div style="color:{TEXT_MID};font-size:13px;line-height:1.65;
                  margin-bottom:16px;">{fw['descricao']}</div>
                <div style="color:{TEXT_MUTED};font-size:10.5px;font-weight:700;
                  text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px;">
                  Ações Recomendadas
                </div>
                """, unsafe_allow_html=True)

                for acao in fw["acoes"]:
                    st.markdown(f"""
                    <div style="display:flex;align-items:flex-start;gap:10px;
                      margin-bottom:8px;padding:10px 12px;
                      background:{BG_PAGE};border-radius:6px;
                      border-left:3px solid {cor_borda};">
                      <span style="color:{cor_borda};font-size:11px;
                        margin-top:1px;font-weight:700;">&#9658;</span>
                      <span style="color:{TEXT_MID};font-size:12px;">{acao}</span>
                    </div>
                    """, unsafe_allow_html=True)

    # Mapa PII × Frameworks
    st.markdown(
        '<div class="sec-hdr">Mapa de Entidades PII × Frameworks Regulatórios</div>',
        unsafe_allow_html=True,
    )
    rows_map = []
    for entidade, fws_list in PII_FRAMEWORK_MAP.items():
        nivel_r, _ = score(entidade)
        rows_map.append({
            "Entidade":   entidade,
            "Risco":      nivel_r,
            "Frameworks": " | ".join(fws_list),
        })

    df_map = pd.DataFrame(rows_map)
    st.dataframe(df_map, use_container_width=True, hide_index=True, height=380)

    col_dlfr1, col_dlfr2 = st.columns(2)
    with col_dlfr1:
        csv_map = df_map.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button(
            "Exportar mapa PII × Frameworks (CSV)",
            csv_map,
            "pii_framework_map.csv",
            "text/csv",
            use_container_width=True,
            key="dl_map",
        )
    with col_dlfr2:
        st.download_button(
            "Exportar mapa PII × Frameworks (Excel)",
            _to_excel(df_map),
            "pii_framework_map.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="dl_map_xl",
        )


# ════════════════════════════════════════════════════════════════════════════
# TAB 5 — Anonymizar
# ════════════════════════════════════════════════════════════════════════════
with tab_anonimizar:
    _tab_header(
        "Anonymização de Texto",
        "Detecte e substitua dados pessoais por tokens — gere versão anonimizada pronta "
        "para compartilhamento, logs e datasets de IA."
    )

    texto_anon_input = st.text_area(
        "Texto para anonymização",
        height=160,
        placeholder=(
            "Cole aqui qualquer texto contendo dados pessoais. "
            "O sistema detecta e substitui CPF, CNPJ, e-mails, telefones e outros PII."
        ),
        label_visibility="collapsed",
        key="anon_input",
    )

    col_run_anon, col_clear_anon = st.columns([2, 1])
    with col_run_anon:
        run_anon = st.button("Anonymizar texto", key="btn_anon", use_container_width=True)
    with col_clear_anon:
        if st.button("Limpar", key="btn_clear_anon", use_container_width=True):
            st.session_state.pop("anon_result", None)
            st.rerun()

    if run_anon:
        if not texto_anon_input.strip():
            st.warning("Insira algum texto para anonymizar.")
        else:
            anonymizer = get_anonymizer()
            if anonymizer is None:
                st.error(
                    "Módulo `presidio-anonymizer` não está instalado no ambiente. "
                    "Execute: `pip install presidio-anonymizer` e reinicie o app."
                )
            else:
                with st.spinner("Processando anonymização..."):
                    analyzer = get_analyzer()
                    entidades_filtro = entidades_sel if entidades_sel else None

                    resultados = analyzer.analyze(
                        text=texto_anon_input,
                        language="pt",
                        entities=entidades_filtro,
                        score_threshold=confianca_min,
                    )
                    if resultados:
                        anon_result = anonymizer.anonymize(
                            text=texto_anon_input, analyzer_results=resultados
                        )
                        texto_limpo = anon_result.text
                    else:
                        texto_limpo = texto_anon_input

                st.session_state["anon_result"] = {
                    "original":   texto_anon_input,
                    "limpo":      texto_limpo,
                    "resultados": [
                        {
                            "entidade":  r.entity_type,
                            "valor":     texto_anon_input[r.start:r.end],
                            "confianca": r.score,
                            "inicio":    r.start,
                            "fim":       r.end,
                        }
                        for r in sorted(resultados, key=lambda x: x.start)
                    ],
                }

    if st.session_state.get("anon_result"):
        anon_data   = st.session_state["anon_result"]
        original    = anon_data["original"]
        limpo       = anon_data["limpo"]
        deteccoes   = anon_data["resultados"]

        if not deteccoes:
            st.success("Nenhum dado pessoal encontrado — o texto já está limpo.")
            st.markdown(f"""
            <div class="anon-panel anon-clean">{limpo}</div>
            """, unsafe_allow_html=True)
        else:
            # KPIs rápidos
            k1, k2, k3 = st.columns(3)
            k1.markdown(f"""
            <div class="kpi-card kpi-warning">
              <div class="kpi-label">Itens substituídos</div>
              <div class="kpi-value">{len(deteccoes)}</div>
              <div class="kpi-sub" style="color:{ORANGE_DARK};">PII detectados</div>
            </div>""", unsafe_allow_html=True)
            k2.markdown(f"""
            <div class="kpi-card">
              <div class="kpi-label">Tipos únicos</div>
              <div class="kpi-value">{len({d['entidade'] for d in deteccoes})}</div>
              <div class="kpi-sub">Categorias de PII</div>
            </div>""", unsafe_allow_html=True)
            confianca_media = sum(d["confianca"] for d in deteccoes) / len(deteccoes)
            k3.markdown(f"""
            <div class="kpi-card kpi-info">
              <div class="kpi-label">Confiança média</div>
              <div class="kpi-value">{confianca_media:.0%}</div>
              <div class="kpi-sub" style="color:{BLUE_ROYAL};">Score do detector</div>
            </div>""", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

            # Side-by-side: original vs limpo
            col_orig, col_clean = st.columns(2)
            with col_orig:
                st.markdown(f'<div class="anon-panel-label">Texto original</div>',
                            unsafe_allow_html=True)
                st.markdown(f'<div class="anon-panel anon-original">{original}</div>',
                            unsafe_allow_html=True)
            with col_clean:
                st.markdown(f'<div class="anon-panel-label">Texto anonimizado</div>',
                            unsafe_allow_html=True)
                st.markdown(f'<div class="anon-panel anon-clean">{limpo}</div>',
                            unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Tabela de substituições
            st.markdown('<div class="sec-hdr-sm">Substituições realizadas</div>',
                        unsafe_allow_html=True)

            df_anon = pd.DataFrame([{
                "Entidade":  d["entidade"],
                "Valor original": d["valor"],
                "Substituído por": f"<{d['entidade']}>",
                "Confiança": f'{d["confianca"]:.0%}',
                "Posição":   f'{d["inicio"]}–{d["fim"]}',
            } for d in deteccoes])
            st.dataframe(df_anon, use_container_width=True, hide_index=True)

            # Downloads
            col_dl1, col_dl2, col_dl3 = st.columns(3)
            with col_dl1:
                st.download_button(
                    "Baixar texto anonimizado (.txt)",
                    limpo.encode("utf-8"),
                    file_name="texto_anonimizado.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key="dl_anon_txt",
                )
            with col_dl2:
                csv_anon = df_anon.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
                st.download_button(
                    "Baixar substituições (CSV)",
                    csv_anon,
                    file_name="substituicoes_pii.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="dl_anon_csv",
                )
            with col_dl3:
                st.download_button(
                    "Baixar substituições (Excel)",
                    _to_excel(df_anon),
                    file_name="substituicoes_pii.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key="dl_anon_xl",
                )

            # Aviso LGPD
            st.markdown(f"""
            <div style="background:rgba(59,130,246,.08);border:1px solid {BORDER_MED};
              border-left:3px solid {BLUE_ROYAL};border-radius:6px;
              padding:12px 16px;font-size:12px;color:{TEXT_MID};margin-top:1rem;">
              <strong style="color:{TEXT_DARK};">Aviso de conformidade LGPD:</strong>
              O texto anonimizado substitui dados pessoais por tokens do tipo
              <code style="background:{BG_PAGE};padding:1px 5px;border-radius:3px;
                color:{BLUE_LIGHT};">&lt;TIPO_PII&gt;</code>.
              Verifique se o nível de anonimização atende aos requisitos da sua base legal
              (LGPD Art. 12 — dado anonimizado). Para pseudonimização, consulte o time de
              Data Protection.
            </div>
            """, unsafe_allow_html=True)
