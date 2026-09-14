"""
Mapeamento de entidades PII para frameworks regulatórios e de segurança.
Referência para engenheiros de Data Protection e AI Security.

Este módulo fornece:
- PII_FRAMEWORK_MAP: qual framework regulatório (LGPD, GDPR, ISO, etc.)
  se aplica a cada tipo de entidade PII detectada.
- AI_FRAMEWORKS: catálogo de frameworks de AI Security com impacto,
  controle, descrição e ações recomendadas por framework.
- Funções auxiliares para consulta e agregação.
"""

from __future__ import annotations

from typing import TypedDict

# ── Mapeamento PII → Frameworks ──────────────────────────────────────────────

PII_FRAMEWORK_MAP: dict[str, list[str]] = {
    # PII brasileira
    "CPF": ["LGPD Art.5/11", "GDPR Art.9", "ISO 27701", "ISO 27001"],
    "CNPJ": ["LGPD Art.5", "GDPR Art.4", "ISO 27001"],
    "RG": ["LGPD Art.5/11", "GDPR Art.9", "ISO 27701"],
    "PIS_PASEP": ["LGPD Art.5/11", "GDPR Art.9", "ISO 27701"],
    "TITULO_ELEITOR": ["LGPD Art.5/11", "GDPR Art.9", "ISO 27701"],
    "CNH": ["LGPD Art.5", "GDPR Art.4", "ISO 27001"],
    "CARTAO_CREDITO": ["PCI-DSS Req.3", "LGPD Art.5", "GDPR Art.4", "ISO 27001"],
    # PII de contato
    "EMAIL_ADDRESS": ["LGPD Art.5", "GDPR Art.4", "CCPA", "CAN-SPAM"],
    "TELEFONE_BR": ["LGPD Art.5", "GDPR Art.4"],
    "PHONE_NUMBER": ["LGPD Art.5", "GDPR Art.4"],
    "CEP": ["LGPD Art.5", "GDPR Art.4"],
    # PII contextual
    "PERSON": ["LGPD Art.5", "GDPR Art.4", "ISO 27001"],
    "LOCATION": ["LGPD Art.5", "GDPR Art.4"],
    "ORGANIZATION": ["LGPD Art.5", "GDPR Art.4"],
    "DATE_TIME": ["LGPD Art.5", "GDPR Art.4"],
    "URL": ["LGPD Art.5", "GDPR Art.4"],
    # Secrets e credenciais — OWASP LLM Top 10
    "JWT_TOKEN": ["OWASP LLM LLM06", "OWASP LLM LLM01", "NIST AI RMF", "ISO 27001"],
    "AWS_ACCESS_KEY": ["OWASP LLM LLM06", "MITRE ATLAS AML.T0024", "ISO 27001"],
    "GITHUB_TOKEN": ["OWASP LLM LLM06", "MITRE ATLAS AML.T0024", "ISO 27001"],
    "PRIVATE_KEY": ["OWASP LLM LLM06", "PCI-DSS Req.3", "ISO 27001"],
    "CONNECTION_STRING": ["OWASP LLM LLM06", "LGPD Art.5", "ISO 27001"],
    "SECRET_IN_CONTEXT": ["OWASP LLM LLM06", "OWASP LLM LLM02", "ISO 27001"],
}


# ── Frameworks de AI Security ─────────────────────────────────────────────────

class FrameworkEntry(TypedDict):
    """Estrutura de um framework de AI Security no catálogo."""

    icon: str
    nivel_impacto: str
    funcoes: list[str]
    controle: str
    descricao: str
    acoes: list[str]


AI_FRAMEWORKS: dict[str, FrameworkEntry] = {
    "NIST AI RMF 1.0": {
        "icon": "building",
        "nivel_impacto": "CRITICO",
        "funcoes": ["GOVERN", "MAP", "MEASURE", "MANAGE"],
        "controle": "AI RMF — Trustworthy AI: Privacy",
        "descricao": (
            "PII exposta em datasets de treino ou prompts viola as dimensões de "
            "Privacy e Fairness do framework. O ciclo GOVERN→MAP→MEASURE→MANAGE "
            "exige identificação contínua de PII no pipeline de dados de IA."
        ),
        "acoes": [
            "Implementar Data Minimization antes do treino",
            "Documentar linhagem de dados com referência a PII",
            "Realizar Privacy Impact Assessment (PIA) nos modelos",
            "Monitorar inferências para evitar vazamento de PII nos outputs",
        ],
    },
    "EU AI Act": {
        "icon": "eu_flag",
        "nivel_impacto": "ALTO",
        "funcoes": ["Art. 10 — Data Governance", "Art. 13 — Transparency"],
        "controle": "High Risk AI Systems — Data Quality",
        "descricao": (
            "Sistemas de IA de alto risco (RH, biometria, infraestrutura crítica) devem "
            "garantir qualidade dos dados e minimização de PII sob o Art. 10. "
            "Violações resultam em multas de até €30M ou 6% do faturamento global."
        ),
        "acoes": [
            "Classificar o sistema de IA pelo nível de risco (Annex III)",
            "Implementar Data Governance para datasets de treino",
            "Garantir direito de explicação das decisões automatizadas",
            "Registrar o sistema no EU AI Act database se alto risco",
        ],
    },
    "OWASP LLM Top 10": {
        "icon": "lock_open",
        "nivel_impacto": "ALTO",
        "funcoes": ["LLM06", "LLM02", "LLM01"],
        "controle": "Sensitive Information Disclosure / Prompt Injection",
        "descricao": (
            "LLM06 – Sensitive Information Disclosure: PII nos dados de treino pode "
            "ser extraída via prompt crafting. LLM02 – Insecure Output Handling: "
            "outputs do modelo podem reproduzir PII verbatim. "
            "LLM01 – Prompt Injection: vetor de ataque para exfiltração de dados."
        ),
        "acoes": [
            "Aplicar Presidio/scrubbing antes de ingerir dados no LLM",
            "Implementar output filtering para bloquear PII nas respostas",
            "Usar técnicas de Differential Privacy no fine-tuning",
            "Auditar datasets com ferramentas de data lineage",
        ],
    },
    "MITRE ATLAS": {
        "icon": "target",
        "nivel_impacto": "MEDIO",
        "funcoes": ["AML.T0024", "AML.T0025"],
        "controle": "Exfiltration via ML Inference API",
        "descricao": (
            "AML.T0024 – Exfiltration via ML Inference API: adversários consultam "
            "o modelo para reconstruir PII do dataset de treino (membership inference). "
            "AML.T0025 – Data Poisoning: inserção de PII sintética para contaminar o modelo."
        ),
        "acoes": [
            "Rate limiting nas APIs de inferência",
            "Monitorar padrões anômalos de consulta (membership inference attacks)",
            "Aplicar Machine Unlearning para remover PII de modelos já treinados",
            "Auditar regularmente com ferramentas de model privacy audit",
        ],
    },
    "ISO/IEC 42001:2023": {
        "icon": "clipboard_list",
        "nivel_impacto": "MEDIO",
        "funcoes": ["Cl. 6.1 — Riscos", "Cl. 8.4 — Ciclo de vida de IA"],
        "controle": "AI Management System — Privacy Risk",
        "descricao": (
            "Primeiro padrão ISO dedicado a Sistemas de Gestão de IA. "
            "A Cláusula 6.1 exige avaliação de riscos de privacidade no ciclo de vida do sistema. "
            "A Cláusula 8.4 cobre requisitos para dados de treino, incluindo minimização de PII."
        ),
        "acoes": [
            "Estabelecer AI Risk Register com categorias de privacidade",
            "Documentar Data Impact Assessment para cada modelo",
            "Implementar controles de acesso a datasets de treino",
            "Integrar revisões de PII no pipeline CI/CD de ML",
        ],
    },
    "ISO 27701:2019": {
        "icon": "lock",
        "nivel_impacto": "ALTO",
        "funcoes": ["Cl. 7.2 — Condições", "Cl. 7.4 — Minimização"],
        "controle": "Privacy Information Management System",
        "descricao": (
            "Extensão do ISO 27001 focada em PIMS (Privacy Information Management). "
            "Exige controles específicos sobre como PII é coletada, processada e armazenada. "
            "Cobre o papel de PII Controller e PII Processor — ambos relevantes "
            "em pipelines de dados de IA."
        ),
        "acoes": [
            "Mapear todos os fluxos de PII no pipeline de IA (RoPA)",
            "Implementar Privacy by Design no desenvolvimento de modelos",
            "Garantir contratos DPA com fornecedores de dados de treino",
            "Auditar retenção e descarte de PII em armazenamento de modelos",
        ],
    },
    "LGPD (Lei 13.709/2018)": {
        "icon": "br_flag",
        "nivel_impacto": "CRITICO",
        "funcoes": ["Art. 5", "Art. 11", "Art. 18", "Art. 37"],
        "controle": "Lei Geral de Proteção de Dados — Brasil",
        "descricao": (
            "Art. 5: define dados pessoais e dados sensíveis (biométricos, saúde, origem étnica). "
            "Art. 11: proíbe tratamento de dados sensíveis sem base legal clara. "
            "Art. 18: garante direitos do titular (acesso, correção, eliminação). "
            "Multa: até R$50M por infração ou 2% do faturamento."
        ),
        "acoes": [
            "Mapear bases legais para cada tipo de PII processada pela IA",
            "Implementar mecanismo de exercício de direitos do titular",
            "Nomear DPO (Encarregado) se processar dados em larga escala",
            "Notificar ANPD em até 72h em caso de incidente com PII",
        ],
    },
    "PCI-DSS v4.0": {
        "icon": "payment_card",
        "nivel_impacto": "CRITICO",
        "funcoes": ["Req. 3 — Protect Data", "Req. 6 — Secure Systems"],
        "controle": "Payment Card Industry Data Security Standard",
        "descricao": (
            "Req. 3: dados de cartão (PAN, CVV, trilha) nunca devem ser armazenados "
            "em texto puro — especialmente em logs, comentários de código ou datasets de IA. "
            "Req. 6: sistemas que processam PAN devem ter controles de segurança rigorosos. "
            "Multa: até US$100k/mês até conformidade ser comprovada."
        ),
        "acoes": [
            "Implementar tokenização antes de qualquer dado de cartão entrar em datasets",
            "Varrer repositórios de código e Jira por PAN (Primary Account Number)",
            "Configurar DLP para bloquear upload de dados de cartão em ferramentas colaborativas",
            "Auditar logs de LLM para garantir que PANs não aparecem em histórico",
        ],
    },
}

# ── Níveis de impacto ────────────────────────────────────────────────────────

NIVEL_COR: dict[str, str] = {
    "CRITICO": "#ff4b4b",
    "ALTO": "#ffa500",
    "MEDIO": "#4a9ede",
    "BAIXO": "#21c354",
}

NIVEL_LABELS: dict[str, str] = {
    "CRITICO": "CRÍTICO",
    "ALTO": "ALTO",
    "MEDIO": "MÉDIO",
    "BAIXO": "BAIXO",
}


# ── Funções auxiliares ────────────────────────────────────────────────────────

def frameworks_para_entidade(entity_type: str) -> list[str]:
    """Retorna a lista de frameworks aplicáveis a uma entidade PII.

    Args:
        entity_type: Tipo da entidade (CPF, CNPJ, EMAIL_ADDRESS, etc.).

    Returns:
        Lista de referências de framework. Retorna LGPD + GDPR como fallback
        para entidades não mapeadas explicitamente.
    """
    return PII_FRAMEWORK_MAP.get(entity_type, ["LGPD Art.5", "GDPR Art.4"])


def frameworks_impactados(registros: list[dict]) -> dict[str, int]:
    """Conta quantas detecções impactam cada framework.

    Percorre a lista de registros detectados e conta, para cada framework
    associado às entidades envolvidas, quantas detecções o tocam.

    Args:
        registros: Lista de dicts com chave 'entidade' contendo o tipo
                   da entidade PII detectada.

    Returns:
        Dicionário {nome_framework: quantidade_de_deteccoes}, ordenado
        decrescentemente por contagem.
    """
    contagem: dict[str, int] = {}
    for r in registros:
        for fw in frameworks_para_entidade(r.get("entidade", "")):
            fw_base = fw.split(" ")[0]
            contagem[fw_base] = contagem.get(fw_base, 0) + 1
    return dict(sorted(contagem.items(), key=lambda x: -x[1]))
