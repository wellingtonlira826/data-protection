"""
Processamento paralelo de chunks de texto para detecção de PII e secrets.

Separa a camada de análise (Presidio) da camada de extração (plugins Jira/Confluence),
permitindo processar N chunks simultaneamente com ThreadPoolExecutor.

O AnalyzerEngine do Presidio é thread-safe — a inferência spaCy (Cython) libera
o GIL, então múltiplas threads ganham paralelismo real no processamento.
"""
from __future__ import annotations

import logging
import os
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any

from presidio_analyzer import AnalyzerEngine

from plugins.frameworks import frameworks_para_entidade
from plugins.risk_scorer import score

logger = logging.getLogger(__name__)

# Entidades que contêm credenciais — valor nunca é exibido completo na UI
SECRET_ENTITIES: frozenset[str] = frozenset({
    "JWT_TOKEN",
    "AWS_ACCESS_KEY",
    "GITHUB_TOKEN",
    "PRIVATE_KEY",
    "CONNECTION_STRING",
    "SECRET_IN_CONTEXT",
})

_DEFAULT_WORKERS = min(8, (os.cpu_count() or 1) + 2)


def _mascarar(valor: str, entity_type: str) -> str:
    """Retorna valor mascarado para secrets, original para PII."""
    if entity_type not in SECRET_ENTITIES:
        return valor
    if len(valor) <= 8:
        return "****"
    return valor[:4] + "..." + valor[-4:]


@dataclass
class Deteccao:
    """Uma entidade PII ou secret detectada em um chunk de texto."""

    entidade: str
    valor: str
    inicio: int
    fim: int
    confianca: float
    nivel: str        # HIGH / MEDIUM / LOW
    label: str        # ALTO / MEDIO / BAIXO
    frameworks: list[str]
    is_secret: bool

    @property
    def valor_display(self) -> str:
        """Valor seguro para exibição — sempre mascarado para secrets."""
        return _mascarar(self.valor, self.entidade)


@dataclass
class ResultadoChunk:
    """Resultado de análise de um chunk de texto."""

    chunk: dict[str, Any]
    deteccoes: list[Deteccao] = field(default_factory=list)
    erro: str | None = None

    @property
    def tem_high(self) -> bool:
        return any(d.nivel == "HIGH" for d in self.deteccoes)

    @property
    def tem_secret(self) -> bool:
        return any(d.is_secret for d in self.deteccoes)

    @property
    def total_deteccoes(self) -> int:
        return len(self.deteccoes)


def _processar_chunk(
    chunk: dict[str, Any],
    analyzer: AnalyzerEngine,
    language: str,
) -> ResultadoChunk:
    texto = chunk.get("texto", "")
    if not texto.strip():
        return ResultadoChunk(chunk=chunk)

    try:
        resultados = analyzer.analyze(text=texto, language=language)
    except Exception as exc:
        logger.warning("Erro ao analisar chunk '%s': %s", chunk.get("issue_key") or chunk.get("pagina", "?"), exc)
        return ResultadoChunk(chunk=chunk, erro=str(exc))

    deteccoes: list[Deteccao] = []
    for r in resultados:
        valor = texto[r.start:r.end]
        nivel, label = score(r.entity_type)
        deteccoes.append(
            Deteccao(
                entidade=r.entity_type,
                valor=valor,
                inicio=r.start,
                fim=r.end,
                confianca=r.score,
                nivel=nivel,
                label=label,
                frameworks=frameworks_para_entidade(r.entity_type),
                is_secret=r.entity_type in SECRET_ENTITIES,
            )
        )

    return ResultadoChunk(chunk=chunk, deteccoes=deteccoes)


def scan_chunks(
    chunks: list[dict[str, Any]],
    analyzer: AnalyzerEngine,
    language: str = "pt",
    max_workers: int = _DEFAULT_WORKERS,
    progress_cb: Callable[[int, int], None] | None = None,
) -> list[ResultadoChunk]:
    """Processa chunks em paralelo com ThreadPoolExecutor.

    Args:
        chunks: Lista de IssueTextChunk ou PageTextChunk.
        analyzer: AnalyzerEngine já inicializado (compartilhado entre threads).
        language: Idioma para análise ("pt" ou "en").
        max_workers: Threads paralelas. Padrão: min(8, cpu_count + 2).
        progress_cb: Callback(concluidos, total) — útil para barra de progresso.

    Returns:
        Lista de ResultadoChunk na mesma ordem dos chunks de entrada.
    """
    total = len(chunks)
    if total == 0:
        return []

    resultados: list[ResultadoChunk | None] = [None] * total
    concluidos = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_processar_chunk, chunk, analyzer, language): idx
            for idx, chunk in enumerate(chunks)
        }

        for future in as_completed(futures):
            idx = futures[future]
            try:
                resultados[idx] = future.result()
            except Exception as exc:
                logger.error("Worker falhou no chunk %d: %s", idx, exc)
                resultados[idx] = ResultadoChunk(
                    chunk=chunks[idx],
                    erro=str(exc),
                )

            concluidos += 1
            if progress_cb:
                try:
                    progress_cb(concluidos, total)
                except Exception:
                    pass

    final = [r for r in resultados if r is not None]
    total_deteccoes = sum(r.total_deteccoes for r in final)
    secrets_encontrados = sum(1 for r in final if r.tem_secret)

    logger.info(
        "Scan concluído: %d chunks | %d detecções | %d chunks com secrets",
        len(final),
        total_deteccoes,
        secrets_encontrados,
    )
    return final


def resumir(resultados: list[ResultadoChunk]) -> dict[str, Any]:
    """Agrega resultados de scan em métricas para o dashboard."""
    total_chunks = len(resultados)
    total_deteccoes = sum(r.total_deteccoes for r in resultados)
    erros = sum(1 for r in resultados if r.erro)

    contagem_por_nivel: dict[str, int] = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    contagem_por_entidade: dict[str, int] = {}
    contagem_secrets: int = 0

    for r in resultados:
        for d in r.deteccoes:
            contagem_por_nivel[d.nivel] = contagem_por_nivel.get(d.nivel, 0) + 1
            contagem_por_entidade[d.entidade] = contagem_por_entidade.get(d.entidade, 0) + 1
            if d.is_secret:
                contagem_secrets += 1

    high = contagem_por_nivel["HIGH"]
    total_classificados = total_deteccoes or 1
    compliance_score = max(0, round(100 - (high / total_classificados * 100)))

    return {
        "total_chunks": total_chunks,
        "total_deteccoes": total_deteccoes,
        "erros": erros,
        "por_nivel": contagem_por_nivel,
        "por_entidade": dict(
            sorted(contagem_por_entidade.items(), key=lambda x: -x[1])
        ),
        "total_secrets": contagem_secrets,
        "compliance_score": compliance_score,
    }
