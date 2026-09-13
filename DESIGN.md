---
version: v3.0
name: Data Protection
description: Plataforma corporativa de detecção de PII e conformidade regulatória. Dark theme. Paleta azul marinho. Tipografia Inter. Zero emojis.
colors:
  # Palette primária (blues)
  blue_dark:   "#1E3A8A"   # Azul marinho — marca, bordas de destaque, botões
  blue_royal:  "#3B82F6"   # Azul royal — interação, links, hover, gráficos
  blue_mid:    "#2563EB"   # Azul intermediário — séries gráficas secundárias
  blue_light:  "#93C5FD"   # Azul claro — badges informativos, sidebar accent
  blue_pale:   "#1E3A8A1A" # Azul pálido translúcido — fills, hover states (dark)
  # Fundos (dark)
  bg_page:     "#0B1121"   # Fundo geral — azul escuro profundo
  bg_section:  "#0F1729"   # Fundo de seção — levemente mais claro
  bg_white:    "#1A2332"   # Cards e containers (dark)
  bg_sidebar:  "#0A1020"   # Sidebar (dark)
  # Texto (dark)
  text_dark:   "#E2E8F0"   # Texto principal — quase branco
  text_mid:    "#94A3B8"   # Texto secundário — slate
  text_muted:  "#64748B"   # Texto desabilitado, metadados
  # Bordas
  border:      "#1E3A5F"   # Borda padrão — azul escuro
  border_med:  "#2D4A72"   # Borda mais visível
  # Risco
  red_dark:    "#EF4444"   # Risco alto
  red_bg:      "#DC262620" # Fundo badge alto (translúcido)
  orange_dark: "#F97316"   # Risco médio
  orange_bg:   "#F9731620" # Fundo badge médio
  green_dark:  "#22C55E"   # Risco baixo / sucesso
  green_bg:    "#22C55E20" # Fundo badge baixo
typography:
  heading-xl:
    fontFamily: Inter
    fontSize: 22px
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.5px"
  heading-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: 700
    lineHeight: 1.3
    letterSpacing: "-0.2px"
  section-label:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: 700
    lineHeight: 1.4
    letterSpacing: "0.6px"
    textTransform: uppercase
  body-md:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: 400
    lineHeight: 1.6
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: 400
    lineHeight: 1.5
  caption:
    fontFamily: Inter
    fontSize: 10.5px
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: "0.3px"
  kpi-value:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "-0.5px"
  kpi-label:
    fontFamily: Inter
    fontSize: 10px
    fontWeight: 700
    lineHeight: 1.3
    letterSpacing: "0.7px"
  code:
    fontFamily: "JetBrains Mono, Consolas, monospace"
    fontSize: 12px
rounded:
  sm: 4px
  md: 6px
  lg: 8px
  xl: 12px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
elevation:
  sm:  "0 1px 3px rgba(0,0,0,.20)"
  md:  "0 1px 4px rgba(0,0,0,.25)"
  lg:  "0 2px 8px rgba(0,0,0,.35)"
  xl:  "0 3px 12px rgba(0,0,0,.45)"
components:
  kpi_card:
    backgroundColor: "{colors.bg_white}"
    border: "1px solid {colors.border}"
    borderTop: "3px solid {colors.blue_royal}"
    borderRadius: "{rounded.lg}"
    padding: "16px 18px 14px"
    boxShadow: "{elevation.md}"
  kpi_card_danger:
    borderTop: "3px solid {colors.red_dark}"
  kpi_card_warning:
    borderTop: "3px solid {colors.orange_dark}"
  kpi_card_success:
    borderTop: "3px solid {colors.green_dark}"
  compliance_bar:
    backgroundColor: "{colors.bg_page}"
    border: "1px solid {colors.border}"
    borderRadius: 99px
    height: 6px
  sec_header:
    borderBottom: "2px solid {colors.blue_dark}"
    paddingBottom: 8px
    marginTop: "1.75rem"
    marginBottom: "1rem"
    display: inline-block
  sec_header_sm:
    borderBottom: "1px solid {colors.border}"
    paddingBottom: 6px
    marginTop: "1.25rem"
    marginBottom: ".75rem"
    display: inline-block
  risk_badge_high:
    backgroundColor: "{colors.red_bg}"
    color: "{colors.red_dark}"
    border: "1px solid {colors.red_dark}"
    borderRadius: 4px
    padding: "3px 10px"
    fontSize: 11px
    fontWeight: 700
  risk_badge_medium:
    backgroundColor: "{colors.orange_bg}"
    color: "{colors.orange_dark}"
    border: "1px solid {colors.orange_dark}"
    borderRadius: 4px
    padding: "3px 10px"
    fontSize: 11px
    fontWeight: 700
  risk_badge_low:
    backgroundColor: "{colors.green_bg}"
    color: "{colors.green_dark}"
    border: "1px solid {colors.green_dark}"
    borderRadius: 4px
    padding: "3px 10px"
    fontSize: 11px
    fontWeight: 700
  fw_pill:
    backgroundColor: "rgba(59,130,246,.08)"
    border: "1px solid {colors.border}"
    borderRadius: "{rounded.sm}"
    padding: "2px 8px"
    fontSize: 11px
    fontWeight: 500
    color: "{colors.blue_royal}"
  chart_card:
    backgroundColor: "{colors.bg_white}"
    border: "1px solid {colors.border}"
    borderRadius: "{rounded.lg}"
    padding: "16px"
    boxShadow: "{elevation.md}"
  report_card:
    backgroundColor: "{colors.bg_white}"
    border: "1px solid {colors.border}"
    borderLeft: "4px solid {colors.blue_royal}"
    borderRadius: "{rounded.lg}"
    padding: "20px 24px"
  anon_panel:
    backgroundColor: "{colors.bg_page}"
    border: "1px solid {colors.border}"
    borderRadius: "{rounded.lg}"
    fontFamily: "Courier New, monospace"
    fontSize: 13px
    lineHeight: 1.7
  hist_item:
    backgroundColor: "{colors.bg_page}"
    border: "1px solid {colors.border}"
    borderRadius: "{rounded.md}"
    padding: "8px 10px"
---

## Visão Geral

Data Protection é uma plataforma corporativa de **detecção, classificação e anonimização de dados pessoais (PII)** baseada em Microsoft Presidio + spaCy. O design é executivo dark: azul marinho como cor primária, fundo quase preto, tipografia Inter, zero emojis.

O tom é técnico e sério. Não há elementos lúdicos — cada componente comunica status, risco ou ação de forma clara e direta.

### Versão v3.0 — Novidades

- **5 abas**: adicionada aba "Anonymizar" para substituição de PII por tokens
- **Score de conformidade**: barra de compliance calculada automaticamente (0–100%)
- **6 KPIs**: adicionado "Risco baixo" como coluna separada para visão completa
- **Gráficos Plotly**: donut de distribuição + barras horizontais por entidade + barras de frameworks
- **Relatório executivo**: geração e download de sumário (.txt) com estatísticas consolidadas
- **Exportação Excel**: além de CSV, download em .xlsx disponível em todas as tabelas
- **Histórico de varreduras**: sidebar registra últimas 10 scans com hora e contagem
- **Filtro duplo na tabela**: filtro por nível de risco + filtro por tipo de entidade
- **Tema dark completo**: config.toml atualizado para `base = "dark"`

---

## Cores

| Token | Hex | Uso |
|---|---|---|
| `blue_dark` | `#1E3A8A` | Marca, seção headers, botões primários |
| `blue_royal` | `#3B82F6` | Interação, links, hover, gráficos principais |
| `blue_mid` | `#2563EB` | Séries secundárias de gráfico |
| `blue_light` | `#93C5FD` | Sidebar accent, badges informativos |
| `bg_page` | `#0B1121` | Fundo da página |
| `bg_section` | `#0F1729` | Fundo de seção/main |
| `bg_white` | `#1A2332` | Cards, containers, formulários |
| `bg_sidebar` | `#0A1020` | Sidebar background |
| `text_dark` | `#E2E8F0` | Texto principal (quase branco) |
| `text_mid` | `#94A3B8` | Texto secundário, labels |
| `text_muted` | `#64748B` | Placeholders, metadados |
| `border` | `#1E3A5F` | Bordas padrão |
| `border_med` | `#2D4A72` | Bordas de destaque |
| `red_dark` | `#EF4444` | Risco alto |
| `orange_dark` | `#F97316` | Risco médio |
| `green_dark` | `#22C55E` | Risco baixo, sucesso, status online |

### Cores de risco — regras de uso

| Nível | Cor texto | Fundo (translúcido) | Uso |
|---|---|---|---|
| Alto | `#EF4444` | `#DC262620` | Badges HIGH, KPI danger, alertas críticos |
| Médio | `#F97316` | `#F9731620` | Badges MEDIUM, KPI warning, avisos |
| Baixo | `#22C55E` | `#22C55E20` | Badges LOW, KPI success, status positivo |

---

## Tipografia

**Inter** (Google Fonts). Pesos: 700 para valores e títulos, 600 para labels e botões, 400 para corpo. `letter-spacing` negativo em títulos (executivo), positivo em labels uppercase (acessibilidade).

---

## Componentes v3.0

### KPI Card
6 cards em linha por varredura. Card `kpi-danger` tem `border-top` vermelho, `kpi-warning` laranja, `kpi-success` verde, padrão azul royal. Inclui compliance score como barra horizontal separada abaixo dos cards.

### Compliance Bar
Barra de progresso horizontal 0–100%. Cor muda: vermelho < 60%, laranja 60–80%, verde > 80%. Mostra percentual à direita e legenda textual à esquerda.

### Charts (Plotly — dark)
- **Donut:** distribuição de risco HIGH/MEDIUM/LOW. `hole=0.60`, cores de risco, legenda horizontal abaixo.
- **Barras horizontais:** top 8 entidades PII por ocorrência. Cor da barra segue nível de risco da entidade.
- **Mini barras frameworks:** barras de progresso HTML para top 6 frameworks impactados.

### Relatório Executivo
Card com `border-left: 4px solid blue_royal`. Exibe stats em chips inline (`report-stat`). Botão de download gera `.txt` com sumário estruturado: header, resumo, frameworks, usuários, primeiras 50 detecções.

### Aba Anonymizar
Text input → Presidio anonymizer → side-by-side `anon-panel` (original e limpo). Tabela de substituições com entidade, valor original, token substituto, confiança, posição. Downloads: `.txt` limpo, `.csv` substituições, `.xlsx` substituições.

### Histórico de Varreduras
Sidebar registra últimas 10 scans em `st.session_state["scan_history"]`. Cada item: tipo (Jira/Confluence/Texto), hora (HH:MM), total de detecções, contagem de alto risco.

---

## Layout

`layout="wide"`. Header corporativo com `margin: -1rem -1rem 0 -1rem` para cobertura total. KPIs em 6 colunas. Charts em 3 colunas (donut | barras | mini bars). Sidebar fixa, scroll próprio. Padding principal: 0 no topo, 2rem na base.

---

## Do's and Don'ts

- Faça: zero emojis em toda a UI, relatórios e notificações por email.
- Faça: manter tema dark consistente — todos os elementos devem ter fundo escuro.
- Faça: usar `blue_royal` para elementos interativos, `blue_dark` para marca e cabeçalhos.
- Não: usar backgrounds claros em cards ou containers — o tema é integralmente dark.
- Não: usar cores de risco como fundo de página ou área ampla.
- Não: misturar mais de 3 tons de azul no mesmo componente.
- Não: usar sombras claras (`rgba(255,255,255,...)`) — sombras são sempre escuras no dark theme.
