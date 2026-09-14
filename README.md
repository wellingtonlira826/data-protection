# Data Protection — PII + Secrets Scanner v3.0

Plataforma corporativa de deteccao, classificacao e remediacao de PII e secrets antes de agentes LLM consumirem dados de Jira e Confluence.

Baseada em Microsoft Presidio + spaCy (PT-BR), com interface Streamlit dark theme.

---

## Como rodar

### 1. Clone o repositorio

```bash
git clone https://github.com/wellingtonlira826/data-protection.git
cd data-protection
```

### 2. Instale as dependencias

```bash
pip install -r requirements.txt
pip install apscheduler>=3.10
python -m spacy download pt_core_news_lg
```

### 3. Rode a aplicacao

```bash
python -m streamlit run corporate_dashboard.py
```

Acesse em `http://localhost:8501`

---

## Funcionalidades

| Recurso | Descricao |
|---|---|
| Painel Executivo | KPIs mensais, tendencia de deteccoes, score de conformidade, top entidades, cobertura de frameworks |
| Varredura Jira | Lista projetos com contagem, multiselect, scan incremental, 5 modos de acao, scrubbing com preview |
| Varredura Confluence | Lista spaces com contagem, multiselect, scan incremental |
| Acoes de remediacao | readonly / Issue Properties / label / comment / scrubbing direto no card |
| Agendamentos | Cron builder (diario/semanal/mensal/custom) com APScheduler + SQLite |
| Texto Livre | Cola qualquer texto para detectar PII e secrets antes de enviar para LLM |
| Anonimizacao | Substitui PII por tokens, diff lado a lado, download do texto limpo |
| Frameworks | LGPD, GDPR, PCI-DSS, NIST AI RMF, EU AI Act, OWASP LLM Top 10, MITRE ATLAS, ISO 27701 |

---

## Estrutura do projeto

```
data-protection/
├── corporate_dashboard.py    # App principal Streamlit (v3.0)
├── presidio_pt.py            # Motor NLP — analyzer Presidio em PT-BR
├── pyproject.toml            # Metadados e dependencias do pacote
├── requirements.txt          # Dependencias para instalacao direta
├── DESIGN.md                 # Design system — tokens, cores, tipografia
├── .streamlit/
│   └── config.toml           # Tema dark + toolbarMode minimal
└── plugins/
    ├── __init__.py
    ├── risk_scorer.py        # Classificacao de risco por entidade
    ├── frameworks.py         # Mapeamento regulatorio
    ├── jira_plugin.py        # Integracao Jira Cloud/Server
    ├── jira_actions.py       # Acoes de remediacao (scrubbing, labels, properties)
    ├── confluence_plugin.py  # Integracao Confluence Cloud/Server
    ├── scanner.py            # Processamento paralelo com ThreadPoolExecutor
    ├── scan_state.py         # Persistencia SQLite (estado incremental + historico)
    ├── scheduler.py          # Agendamentos APScheduler + SQLite
    ├── attachment_scanner.py # Scan de anexos (PDF, DOCX, imagens)
    └── demo_data.py          # Dados simulados para modo demonstracao
```

---

## Tecnologias

- [Microsoft Presidio](https://github.com/microsoft/presidio) — deteccao de PII
- [spaCy](https://spacy.io/) + `pt_core_news_lg` — NLP em portugues
- [Streamlit](https://streamlit.io/) — interface web
- [Plotly](https://plotly.com/) — graficos interativos
- [APScheduler](https://apscheduler.readthedocs.io/) — agendamentos
- [atlassian-python-api](https://github.com/atlassian-api/atlassian-python-api) — Jira/Confluence

---

## Licenca

MIT — veja [LICENSE](LICENSE) para detalhes.
