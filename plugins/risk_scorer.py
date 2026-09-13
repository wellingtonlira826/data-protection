"""
Classifica o risco de cada entidade PII detectada.

Níveis:
    HIGH   → dados que identificam diretamente a pessoa (CPF, RG, cartão)
    MEDIUM → dados de contato rastreáveis (email, telefone, CEP)
    LOW    → dados contextuais (nome, localização, organização)
"""

from __future__ import annotations

from typing import TypedDict

# ── Mapa de risco ─────────────────────────────────────────────────────────────

class RiscoEntry(TypedDict):
    """Entrada de risco para uma entidade PII."""

    nivel: str
    label: str


RISK_MAP: dict[str, RiscoEntry] = {
    "CPF": {"nivel": "HIGH", "label": "ALTO"},
    "CNPJ": {"nivel": "HIGH", "label": "ALTO"},
    "RG": {"nivel": "HIGH", "label": "ALTO"},
    "PIS_PASEP": {"nivel": "HIGH", "label": "ALTO"},
    "CARTAO_CREDITO": {"nivel": "HIGH", "label": "ALTO"},
    "TITULO_ELEITOR": {"nivel": "HIGH", "label": "ALTO"},
    "CNH": {"nivel": "HIGH", "label": "ALTO"},
    "EMAIL_ADDRESS": {"nivel": "MEDIUM", "label": "MEDIO"},
    "TELEFONE_BR": {"nivel": "MEDIUM", "label": "MEDIO"},
    "PHONE_NUMBER": {"nivel": "MEDIUM", "label": "MEDIO"},
    "CEP": {"nivel": "MEDIUM", "label": "MEDIO"},
    "PERSON": {"nivel": "LOW", "label": "BAIXO"},
    "LOCATION": {"nivel": "LOW", "label": "BAIXO"},
    "ORGANIZATION": {"nivel": "LOW", "label": "BAIXO"},
    "DATE_TIME": {"nivel": "LOW", "label": "BAIXO"},
    "URL": {"nivel": "LOW", "label": "BAIXO"},
}

# ── Ordenação ─────────────────────────────────────────────────────────────────

_RISK_ORDER: dict[str, int] = {
    "HIGH": 0,
    "MEDIUM": 1,
    "LOW": 2,
}

# ── Funções ───────────────────────────────────────────────────────────────────

def score(entity_type: str) -> tuple[str, str]:
    """Retorna o nível de risco e o label textual para uma entidade.

    Args:
        entity_type: Tipo da entidade (CPF, CNPJ, EMAIL_ADDRESS, etc.).

    Returns:
        Tupla (nivel, label). Nível é HIGH/MEDIUM/LOW; label é ALTO/MEDIO/BAIXO.
        Retorna (LOW, BAIXO) para entidades não mapeadas.
    """
    entry = RISK_MAP.get(entity_type, {"nivel": "LOW", "label": "BAIXO"})
    return entry["nivel"], entry["label"]


def score_nivel(entity_type: str) -> str:
    """Retorna apenas o nível de risco (HIGH/MEDIUM/LOW).

    Args:
        entity_type: Tipo da entidade.

    Returns:
        Nível de risco. LOW para entidades não mapeadas.
    """
    return score(entity_type)[0]


def score_label(entity_type: str) -> str:
    """Retorna o label de risco formatado como 'LABEL (NÍVEL)'.

    Args:
        entity_type: Tipo da entidade.

    Returns:
        String formatada, ex: 'ALTO (HIGH)'.

    Obs.:
        Em versões futuras, pode incorporar ícone de apresentação aqui.
        Por enquanto retorna texto puro para manter o módulo agnóstico
        em relação à camada de apresentação.
    """
    nivel, label = score(entity_type)
    return f"{label} ({nivel})"


def sort_key(record: dict) -> int:
    """Retorna a chave de ordenação para um registro de detecção.

    Registros são ordenados do maior para o menor risco (HIGH → MEDIUM → LOW).

    Args:
        record: Dict com chave '_nivel' ou 'entidade'.

    Returns:
        Inteiro: 0 para HIGH, 1 para MEDIUM, 2 para LOW,
                 99 para entidades não mapeadas ou risco desconhecido.
    """
    nivel = record.get("_nivel") or score_nivel(record.get("entidade", ""))
    return _RISK_ORDER.get(nivel, 99)
