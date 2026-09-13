# Data Protection — PII Detection & Compliance Platform

Plataforma corporativa de **detecção, classificação e anonimização de dados pessoais (PII)** baseada em [Microsoft Presidio](https://github.com/microsoft/presidio) + spaCy, com interface Streamlit em dark theme.

Desenvolvida para equipes de segurança e conformidade que precisam identificar dados pessoais em fontes como Jira, Confluence ou texto livre — e gerar relatórios e notificações alinhados a LGPD, GDPR e PCI-DSS.

---

## Funcionalidades

| Recurso | Descrição |
|---|---|
| Detecção de PII em PT-BR | CPF, CNPJ, RG, PIS/PASEP, CNH, cartão de crédito, CEP, telefone, e-mail, nome, etc. |
| Score de conformidade | Calcula 0–100% com barra visual e status (Risco elevado / Atenção / Dentro do limite) |
| Gráficos interativos | Donut de risco + barras por entidade — clique para filtrar a tabela instantaneamente |
| Integração Jira | Varre issues em busca de PII via API (Cloud e Server/Data Center) |
| Integração Confluence | Varre páginas e espaços via API |
| Anonimização | Substitui PII por tokens, com diff lado a lado e download do texto limpo |
| Notificações por e-mail | Gera rascunho Outlook (mailto) por usuário ou em lote para todos os expostos |
| Marcar como resolvido | Por usuário — exclui dos KPIs, gráficos e tabela (falso-positivo / já tratado) |
| Exportação | CSV e Excel (.xlsx) em todas as tabelas |
| Relatório executivo | Sumário consolidado para download (.txt) |
| Histórico de varreduras | Últimas 10 scans registradas na sidebar |
| Frameworks | LGPD, GDPR, PCI-DSS v4.0, NIST AI RMF, EU AI Act, OWASP LLM Top 10, MITRE ATLAS, ISO 42001/27701 |

---

## Requisitos

- Python **3.12** (recomendado; mínimo 3.11)
- Modelo spaCy em português: `pt_core_news_lg`

---

## Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/wellingtonlira826/data-protection.git
cd data-protection
```

### 2. Crie um ambiente virtual (opcional, mas recomendado)

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Baixe o modelo de linguagem em português

```bash
python -m spacy download pt_core_news_lg
```

### 5. Rode a aplicação

```bash
python -m streamlit run app.py
```

Acesse em `http://localhost:8501`

---

## Estrutura do projeto

```
data-protection/
├── app.py                    # App principal Streamlit (v3.0)
├── presidio_pt.py            # Motor NLP — analyzer Presidio em PT-BR
├── corporate_dashboard.py    # Dashboard de analytics separado
├── pyproject.toml            # Metadados e dependências do pacote
├── requirements.txt          # Dependências para instalação direta
├── DESIGN.md                 # Design system — tokens, cores, tipografia
├── .streamlit/
│   └── config.toml           # Tema dark + configurações do servidor
└── plugins/
    ├── risk_scorer.py        # Classificação de risco por tipo de entidade
    ├── frameworks.py         # Mapeamento LGPD / GDPR / PCI-DSS / AI frameworks
    ├── demo_data.py          # Dados simulados para modo demonstração
    ├── jira_plugin.py        # Integração Jira (Cloud e Server)
    └── confluence_plugin.py  # Integração Confluence (Cloud e Server)
```

---

## Uso rápido

### Modo demonstração (padrão)

Ao abrir o app, o **Modo demonstração** já vem ativado na sidebar. Ele carrega automaticamente dados simulados de Jira e Confluence com PII fictícia — nenhuma credencial necessária.

### Análise de texto livre

1. Acesse a aba **Texto Livre**
2. Cole qualquer texto (ex.: e-mail, log de sistema, ticket)
3. Clique em **Executar análise**
4. Explore os KPIs, gráficos interativos e tabela de resultados

### Varredura Jira / Confluence real

1. Desative o **Modo demonstração** na sidebar
2. Acesse a aba **Jira** ou **Confluence**
3. Clique em **Parametros de varredura** para expandir o formulário
4. Preencha URL, usuário, API Token e Project Key / Space Key
5. Clique em **Conectar e Executar Varredura**

> Para Jira Cloud: use o e-mail como usuário e um [API Token](https://id.atlassian.com/manage-profile/security/api-tokens) como senha.

### Filtros interativos

- Clique em uma fatia do **donut** de risco para filtrar a tabela por nível
- Clique em uma barra do gráfico de **entidades** para filtrar por tipo de PII
- Use as **pills** (Todos / Alto / Médio / Baixo) acima dos gráficos para filtro rápido
- Clique em **Limpar filtros** para resetar

### Notificações

- Em **Notificações por usuário**, clique em **Notificar por e-mail** para abrir rascunho Outlook
- Use **Notificar todos** para gerar um e-mail em lote para todos os usuários expostos
- Use **Marcar resolvido** para excluir um usuário dos KPIs e gráficos (falso-positivo ou já tratado)

### Anonimização

1. Acesse a aba **Anonymizar**
2. Cole o texto com PII
3. Clique em **Anonimizar**
4. Veja o diff original vs. limpo e baixe o resultado

---

## Configurações

### Entidades e confiança mínima

Na sidebar, clique em **Configurações de análise** para ajustar:
- Quais tipos de PII detectar (CPF, CNPJ, e-mail, telefone, etc.)
- Confiança mínima do modelo (padrão: 40%)
- E-mail em cópia (CC) para notificações

### Tema

O tema dark está configurado em `.streamlit/config.toml`. Para alterar cores, edite os tokens em `DESIGN.md` e aplique em `app.py`.

---

## Tecnologias

- [Microsoft Presidio](https://github.com/microsoft/presidio) — motor de detecção de PII
- [spaCy](https://spacy.io/) + `pt_core_news_lg` — NLP em português
- [Streamlit](https://streamlit.io/) — interface web
- [Plotly](https://plotly.com/) — gráficos interativos
- [atlassian-python-api](https://github.com/atlassian-api/atlassian-python-api) — integração Jira/Confluence

---

## Licença

MIT — veja [LICENSE](LICENSE) para detalhes.
