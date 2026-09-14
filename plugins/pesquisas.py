"""
Pesquisas dirigidas para Jira (JQL) e Confluence (CQL).

Cada entrada tem nome, descricao e a query text ~ que funciona
identicamente em JQL e CQL — basta trocar a chave 'query' em ambos.
"""
from __future__ import annotations

PESQUISAS_DIRIGIDAS: list[dict] = [
    {
        "nome": "Bearer / Auth tokens",
        "descricao": "Tokens de autorizacao HTTP (Authorization: Bearer ...)",
        "query": (
            'text ~ "Bearer " OR text ~ "Authorization:" OR '
            'text ~ "Bearer token" OR text ~ "auth_token"'
        ),
    },
    {
        "nome": "API Keys",
        "descricao": "Chaves de API e access tokens genéricos",
        "query": (
            'text ~ "api_key" OR text ~ "apikey" OR text ~ "api-key" OR '
            'text ~ "x-api-key" OR text ~ "access_token" OR text ~ "API_KEY"'
        ),
    },
    {
        "nome": "Senhas e Secrets",
        "descricao": "Passwords, secrets e passphrases em texto",
        "query": (
            'text ~ "password" OR text ~ "senha" OR text ~ "secret" OR '
            'text ~ "passwd" OR text ~ "passphrase" OR text ~ "client_secret"'
        ),
    },
    {
        "nome": "Connection Strings",
        "descricao": "Strings de conexao a bancos de dados e servicos",
        "query": (
            'text ~ "jdbc:" OR text ~ "mongodb://" OR text ~ "postgresql://" OR '
            'text ~ "mysql://" OR text ~ "connectionString" OR text ~ "Data Source="'
        ),
    },
    {
        "nome": "AWS Credentials",
        "descricao": "Chaves de acesso AWS (Access Key ID comeca com AKIA)",
        "query": (
            'text ~ "AKIA" OR text ~ "aws_access_key_id" OR '
            'text ~ "aws_secret_access_key" OR text ~ "AWS_SECRET" OR text ~ "aws_session_token"'
        ),
    },
    {
        "nome": "Chaves Privadas",
        "descricao": "RSA, EC e outras chaves privadas PEM",
        "query": (
            'text ~ "BEGIN RSA PRIVATE" OR text ~ "BEGIN PRIVATE KEY" OR '
            'text ~ "BEGIN EC PRIVATE" OR text ~ "BEGIN OPENSSH PRIVATE"'
        ),
    },
    {
        "nome": "GitHub / GitLab tokens",
        "descricao": "Personal access tokens do GitHub (ghp_) e GitLab (glpat-)",
        "query": (
            'text ~ "ghp_" OR text ~ "gho_" OR text ~ "github_token" OR '
            'text ~ "GITHUB_TOKEN" OR text ~ "glpat-" OR text ~ "GITLAB_TOKEN"'
        ),
    },
    {
        "nome": "JWT tokens",
        "descricao": "JSON Web Tokens — comecam com eyJ (header base64)",
        "query": 'text ~ "eyJhbGci" OR text ~ "eyJ0eXAi" OR text ~ "eyJpc3Mi"',
    },
    {
        "nome": "CPF / CNPJ",
        "descricao": "Documentos pessoais brasileiros (CPF e CNPJ)",
        "query": (
            'text ~ "CPF:" OR text ~ "CPF " OR text ~ "CNPJ:" OR '
            'text ~ "CNPJ " OR text ~ ".cpf" OR text ~ "/cpf"'
        ),
    },
    {
        "nome": "Emails pessoais",
        "descricao": "Enderecos de email de provedores pessoais",
        "query": (
            'text ~ "@gmail.com" OR text ~ "@hotmail.com" OR '
            'text ~ "@yahoo.com" OR text ~ "@outlook.com" OR text ~ "@live.com"'
        ),
    },
    {
        "nome": "URLs com credenciais",
        "descricao": "URLs com usuario:senha embutidos (http://user:pass@host)",
        "query": (
            'text ~ "http://" AND (text ~ ":password" OR text ~ ":senha" OR text ~ "@" )'
        ),
    },
    {
        "nome": "Tokens de servicos cloud",
        "descricao": "Tokens Azure, GCP, Slack, Stripe, Twilio etc.",
        "query": (
            'text ~ "AZURE_" OR text ~ "GCP_" OR text ~ "xoxb-" OR '
            'text ~ "xoxp-" OR text ~ "sk_live_" OR text ~ "AC" AND text ~ "auth_token"'
        ),
    },
]


def montar_query_dirigida(nomes_selecionados: list[str], custom: str = "") -> str:
    """Combina as queries das pesquisas selecionadas com OR.

    Args:
        nomes_selecionados: Lista de nomes de PESQUISAS_DIRIGIDAS selecionados.
        custom: Query adicional informada pelo usuario (JQL ou CQL livre).

    Returns:
        String de query combinada, pronta para usar como jql_extra ou cql_extra.
    """
    partes: list[str] = []
    lookup = {p["nome"]: p["query"] for p in PESQUISAS_DIRIGIDAS}
    for nome in nomes_selecionados:
        if nome in lookup:
            partes.append(f"({lookup[nome]})")
    if custom.strip():
        partes.append(f"({custom.strip()})")
    return " OR ".join(partes)
