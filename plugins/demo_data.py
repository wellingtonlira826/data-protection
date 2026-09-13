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


# ── Jira demo ─────────────────────────────────────────────────────────────────

JIRA_DEMO_TRECHOS: list[JiraDemoTrecho] = [
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
