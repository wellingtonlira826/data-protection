"""
Dados de demonstração para testar o fluxo completo sem credenciais reais.

Simula um projeto Jira e um space Confluence com PII realista e
diversificada (CPF, CNPJ, RG, PIS, título de eleitor, cartão de crédito,
e-mail, telefone, CEP, etc.) para validação do pipeline de detecção.
"""

from __future__ import annotations

from typing import TypedDict

# ── Tipos ─────────────────────────────────────────────────────────────────────

class JiraDemoTrecho(TypedDict):
    """Um fragmento de texto simulado de um issue Jira."""

    texto: str
    autor: str
    campo: str
    issue_key: str
    issue_url: str
    issue_type: str
    prioridade: str


class ConfluenceDemoTrecho(TypedDict):
    """Um fragmento de texto simulado de uma página Confluence."""

    texto: str
    autor: str
    pagina: str
    page_url: str


# ── Dados de projetos e spaces (para listagem sem conexão real) ───────────────

JIRA_DEMO_PROJETOS: list[dict] = [
    {"key": "PROJ",  "name": "Projeto Principal",          "count": 284},
    {"key": "ALPHA", "name": "Alpha Payments Service",     "count": 156},
    {"key": "BETA",  "name": "Beta Data Platform",         "count": 89},
    {"key": "HR",    "name": "Recursos Humanos",           "count": 43},
    {"key": "FIN",   "name": "Financeiro e Compliance",    "count": 31},
    {"key": "OPS",   "name": "Operacoes e Infra",          "count": 22},
]

CONFLUENCE_DEMO_SPACES: list[dict] = [
    {"key": "DS",   "name": "Data Science e Analytics",   "count": 142},
    {"key": "ENG",  "name": "Engenharia de Software",     "count": 97},
    {"key": "HR",   "name": "RH e Cultura Organizacional","count": 54},
    {"key": "PROD", "name": "Produto e Design",           "count": 38},
    {"key": "SEC",  "name": "Seguranca da Informacao",    "count": 19},
]

# ── Histórico executivo demo (6 meses de dados fictícios) ────────────────────
# Simula evolução real: pico em março, queda progressiva após implantação da plataforma.

EXEC_DEMO_HISTORICO: list[dict] = [
    # mes_ano, fonte, projetos, total, alto, medio, baixo, secrets, compliance_score, entidades
    {"mes_ano": "2025-04", "fonte": "Jira",       "projetos": "PROJ+ALPHA", "total_deteccoes": 312, "alto": 89,  "medio": 143, "baixo": 80,  "secrets": 47, "compliance_score": 41.2, "entidades": ["CPF","CPF","CNPJ","JWT_TOKEN","AWS_ACCESS_KEY","EMAIL_ADDRESS","PHONE_NUMBER","CPF","CNPJ","JWT_TOKEN"]},
    {"mes_ano": "2025-04", "fonte": "Confluence", "projetos": "DS+ENG",     "total_deteccoes": 198, "alto": 52,  "medio": 91,  "baixo": 55,  "secrets": 31, "compliance_score": 39.5, "entidades": ["CPF","EMAIL_ADDRESS","CNPJ","PHONE_NUMBER","PRIVATE_KEY","CONNECTION_STRING","CPF","CEP"]},
    {"mes_ano": "2025-05", "fonte": "Jira",       "projetos": "PROJ+ALPHA", "total_deteccoes": 287, "alto": 74,  "medio": 131, "baixo": 82,  "secrets": 39, "compliance_score": 45.8, "entidades": ["CPF","JWT_TOKEN","CNPJ","EMAIL_ADDRESS","AWS_ACCESS_KEY","PHONE_NUMBER","CPF","RG"]},
    {"mes_ano": "2025-05", "fonte": "Confluence", "projetos": "DS+ENG",     "total_deteccoes": 161, "alto": 38,  "medio": 77,  "baixo": 46,  "secrets": 22, "compliance_score": 48.1, "entidades": ["CPF","EMAIL_ADDRESS","CNPJ","GITHUB_TOKEN","PHONE_NUMBER","CPF","CEP","CARTAO_CREDITO"]},
    {"mes_ano": "2025-06", "fonte": "Jira",       "projetos": "PROJ+ALPHA+HR", "total_deteccoes": 241, "alto": 58, "medio": 112, "baixo": 71, "secrets": 28, "compliance_score": 54.3, "entidades": ["CPF","EMAIL_ADDRESS","JWT_TOKEN","CNPJ","PHONE_NUMBER","CPF","AWS_ACCESS_KEY","RG"]},
    {"mes_ano": "2025-06", "fonte": "Confluence", "projetos": "DS+HR",      "total_deteccoes": 134, "alto": 29,  "medio": 64,  "baixo": 41,  "secrets": 17, "compliance_score": 57.0, "entidades": ["CPF","EMAIL_ADDRESS","CNPJ","PHONE_NUMBER","CEP","CPF","PRIVATE_KEY"]},
    {"mes_ano": "2025-07", "fonte": "Jira",       "projetos": "PROJ+ALPHA+HR", "total_deteccoes": 189, "alto": 41, "medio": 90,  "baixo": 58,  "secrets": 19, "compliance_score": 63.7, "entidades": ["CPF","EMAIL_ADDRESS","CNPJ","JWT_TOKEN","PHONE_NUMBER","CPF","RG"]},
    {"mes_ano": "2025-07", "fonte": "Confluence", "projetos": "DS+HR+ENG",  "total_deteccoes": 102, "alto": 18,  "medio": 51,  "baixo": 33,  "secrets": 11, "compliance_score": 66.2, "entidades": ["CPF","EMAIL_ADDRESS","CNPJ","PHONE_NUMBER","CEP","CPF"]},
    {"mes_ano": "2025-08", "fonte": "Jira",       "projetos": "PROJ+ALPHA+HR", "total_deteccoes": 143, "alto": 27, "medio": 68,  "baixo": 48,  "secrets": 12, "compliance_score": 71.4, "entidades": ["CPF","EMAIL_ADDRESS","CNPJ","PHONE_NUMBER","CPF","RG","CEP"]},
    {"mes_ano": "2025-08", "fonte": "Confluence", "projetos": "DS+HR+ENG",  "total_deteccoes": 78,  "alto": 11,  "medio": 38,  "baixo": 29,  "secrets": 6,  "compliance_score": 74.8, "entidades": ["CPF","EMAIL_ADDRESS","CNPJ","PHONE_NUMBER","CEP"]},
    {"mes_ano": "2025-09", "fonte": "Jira",       "projetos": "PROJ+ALPHA+HR+FIN", "total_deteccoes": 98, "alto": 14, "medio": 47, "baixo": 37, "secrets": 7, "compliance_score": 78.9, "entidades": ["CPF","EMAIL_ADDRESS","CNPJ","PHONE_NUMBER","RG","CPF"]},
    {"mes_ano": "2025-09", "fonte": "Confluence", "projetos": "DS+HR+ENG",  "total_deteccoes": 54,  "alto": 6,   "medio": 26,  "baixo": 22,  "secrets": 3,  "compliance_score": 81.3, "entidades": ["CPF","EMAIL_ADDRESS","PHONE_NUMBER","CEP","CNPJ"]},
]

# ── Jira demo ─────────────────────────────────────────────────────────────────

JIRA_DEMO_TRECHOS: list[JiraDemoTrecho] = [
    JiraDemoTrecho(
        texto=(
            "Integração com API de pagamentos configurada. "
            "Token de acesso: Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
            ".eyJzdWIiOiJ1c2VyMTIzIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        ),
        autor="dev.backend@empresa.com.br",
        campo="Descrição",
        issue_key="PROJ-110",
        issue_url="https://demo.atlassian.net/browse/PROJ-110",
        issue_type="Task",
        prioridade="Alta",
    ),
    JiraDemoTrecho(
        texto=(
            "String de conexão do banco de staging: "
            "postgresql://admin:S3nh@Secreta123@db.staging.internal:5432/core_db"
        ),
        autor="infra.team@empresa.com.br",
        campo="Comentário",
        issue_key="PROJ-111",
        issue_url="https://demo.atlassian.net/browse/PROJ-111",
        issue_type="Bug",
        prioridade="Alta",
    ),
    JiraDemoTrecho(
        texto=(
            "Deploy na AWS: aws_access_key_id = AKIAIOSFODNN7EXAMPLE, "
            "aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        ),
        autor="devops@empresa.com.br",
        campo="Descrição",
        issue_key="PROJ-112",
        issue_url="https://demo.atlassian.net/browse/PROJ-112",
        issue_type="Task",
        prioridade="Alta",
    ),

    JiraDemoTrecho(
        texto=(
            "Preciso atualizar o cadastro do cliente João Silva, "
            "CPF 123.456.789-09, que mora na Rua das Flores, 123 - "
            "São Paulo, CEP 01310-100."
        ),
        autor="ana.costa@empresa.com.br",
        campo="Descrição",
        issue_key="PROJ-101",
        issue_url="https://demo.atlassian.net/browse/PROJ-101",
        issue_type="Bug",
        prioridade="Alta",
    ),
    JiraDemoTrecho(
        texto=(
            "Contato do fornecedor: pedro.alves@fornecedor.com.br | "
            "(11) 98765-4321. CNPJ: 12.345.678/0001-90."
        ),
        autor="carlos.lima@empresa.com.br",
        campo="Comentário",
        issue_key="PROJ-102",
        issue_url="https://demo.atlassian.net/browse/PROJ-102",
        issue_type="Task",
        prioridade="Média",
    ),
    JiraDemoTrecho(
        texto=(
            "Cartão de crédito do teste: 4111 1111 1111 1111 "
            "CVV 123 validade 12/26."
        ),
        autor="dev.test@empresa.com.br",
        campo="Descrição",
        issue_key="PROJ-103",
        issue_url="https://demo.atlassian.net/browse/PROJ-103",
        issue_type="Story",
        prioridade="Alta",
    ),
    JiraDemoTrecho(
        texto=(
            "RG do funcionário: 12.345.678-9. PIS: 123.45678.90-1. "
            "Título de eleitor: 123456789012."
        ),
        autor="rh.sistema@empresa.com.br",
        campo="Campo customizado (customfield_10042)",
        issue_key="PROJ-104",
        issue_url="https://demo.atlassian.net/browse/PROJ-104",
        issue_type="Task",
        prioridade="Baixa",
    ),
    JiraDemoTrecho(
        texto=(
            "Maria Oliveira, email: maria.oliveira@cliente.com, "
            "telefone: (21) 3333-4444."
        ),
        autor="suporte@empresa.com.br",
        campo="Comentário",
        issue_key="PROJ-105",
        issue_url="https://demo.atlassian.net/browse/PROJ-105",
        issue_type="Bug",
        prioridade="Média",
    ),
]

# ── Confluence demo ───────────────────────────────────────────────────────────

CONFLUENCE_DEMO_TRECHOS: list[ConfluenceDemoTrecho] = [
    ConfluenceDemoTrecho(
        texto=(
            "Procedimento de onboarding: CPF do colaborador deve ser "
            "inserido no sistema RH. Exemplo de teste usado em homologação: "
            "987.654.321-00."
        ),
        autor="rh.admin@empresa.com.br",
        pagina="Processo de Onboarding",
        page_url="https://demo.atlassian.net/wiki/spaces/DS/pages/1001",
    ),
    ConfluenceDemoTrecho(
        texto=(
            "Contato do parceiro técnico: suporte@parceiro.com.br | "
            "(11) 4002-8922. CNPJ: 98.765.432/0001-10."
        ),
        autor="ti.infraestrutura@empresa.com.br",
        pagina="Parceiros e Fornecedores",
        page_url="https://demo.atlassian.net/wiki/spaces/DS/pages/1002",
    ),
    ConfluenceDemoTrecho(
        texto=(
            "Dados de teste: cartão 5500 0000 0000 0004, CEP 20040-020, "
            "responsável: Carlos Eduardo, RG 98.765.432-1."
        ),
        autor="qa.team@empresa.com.br",
        pagina="Massa de Dados para QA",
        page_url="https://demo.atlassian.net/wiki/spaces/DS/pages/1003",
    ),
]
