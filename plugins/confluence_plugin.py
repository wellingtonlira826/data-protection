"""
Plugin Confluence para o Presidio PT.

Suporta Confluence Cloud e Server/Data Center.
Fornece conexão, listagem de spaces, busca de páginas e extração de
texto para detecção de PII usando o motor Presidio.
"""

from __future__ import annotations

import logging
from typing import Any, TypedDict

from atlassian import Confluence
from html.parser import HTMLParser

logger = logging.getLogger(__name__)


# ── HTML stripping (auxiliar) ─────────────────────────────────────────────────

class _HTMLStripper(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []
        self._skip = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("script", "style"):
            self._skip = True

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style"):
            self._skip = False

    def handle_data(self, data: str) -> None:
        if not self._skip:
            stripped = data.strip()
            if stripped:
                self._parts.append(stripped)

    def get_text(self) -> str:
        return " ".join(self._parts)


def _strip_html(html: str) -> str:
    if not html:
        return ""
    stripper = _HTMLStripper()
    try:
        stripper.feed(html)
    except Exception:
        logger.exception("Erro ao parsear HTML para extração de texto")
    return stripper.get_text()


# ── Mapeamento de status de página ───────────────────────────────────────────

PAGE_STATUS_MAP: dict[str, str] = {
    "Publicadas (current)": "current",
    "Rascunhos (draft)": "draft",
    "Arquivadas (archived)": "archived",
}


# ── Tipos internos ────────────────────────────────────────────────────────────

class ConnResult(TypedDict):
    ok: bool
    message: str


class SpaceInfo(TypedDict):
    key: str
    name: str


class PageTextChunk(TypedDict):
    texto: str
    autor: str
    pagina: str
    page_url: str


# ── Plugin Confluence ─────────────────────────────────────────────────────────

class ConfluencePlugin:
    """Conector para Confluence Cloud e Server/Data Center."""

    def __init__(self) -> None:
        self._client: Confluence | None = None
        self._base_url: str = ""
        self._cloud: bool = True

    def conectar(
        self,
        url: str,
        usuario: str,
        token: str,
        cloud: bool = True,
    ) -> ConnResult:
        self._base_url = url.rstrip("/")
        self._cloud = cloud
        try:
            self._client = Confluence(
                url=self._base_url,
                username=usuario,
                password=token,
                cloud=cloud,
            )
            conexao = self._client.get_spaces(limit=1)
            results = (
                conexao.get("results", [])
                if isinstance(conexao, dict)
                else []
            )
            qtd = len(results) if isinstance(results, list) else 0
            msg = f"Conectado. {qtd} space(s) acessível(is)."
            logger.info("Confluence conectado: %s — %s", self._base_url, msg)
            return ConnResult(ok=True, message=msg)
        except Exception as exc:
            msg = f"Erro ao conectar: {exc}"
            logger.error("Falha ao conectar Confluence: %s", exc)
            return ConnResult(ok=False, message=msg)

    def listar_spaces(self) -> list[SpaceInfo]:
        if not self._client:
            logger.warning("Não conectado ao listar spaces")
            return []
        try:
            resultado = self._client.get_spaces(limit=50)
            spaces = (
                resultado.get("results", [])
                if isinstance(resultado, dict)
                else []
            )
            return [SpaceInfo(key=s["key"], name=s["name"]) for s in spaces]
        except Exception:
            logger.exception("Erro ao listar spaces Confluence")
            return []

    def buscar_paginas(
        self,
        space_key: str,
        status: str = "current",
        incluir_filhas: bool = True,
        max_results: int = 50,
    ) -> list[dict[str, Any]]:
        if not self._client:
            raise RuntimeError("ConfluencePlugin não está conectado.")
        try:
            paginas = self._client.get_all_pages_from_space(
                space_key,
                start=0,
                limit=max_results,
                status=status,
                expand="body.storage,history.createdBy,version.by,ancestors",
            )
            return paginas if isinstance(paginas, list) else []
        except Exception:
            logger.exception(
                "Erro ao buscar páginas do space '%s' (status=%s)",
                space_key,
                status,
            )
            return []

    def extrair_textos(
        self,
        page: dict[str, Any],
        incluir_titulo: bool = True,
        incluir_corpo: bool = True,
    ) -> list[PageTextChunk]:
        titulo = page.get("title", "")
        page_id = page.get("id", "")

        if self._cloud:
            page_url = (
                f"{self._base_url}/wiki/spaces/"
                f"{page.get('space', {}).get('key', '')}/pages/{page_id}"
            )
        else:
            page_url = (
                f"{self._base_url}/pages/viewpage.action?pageId={page_id}"
            )

        history = page.get("history", {})
        criado_por = history.get("createdBy", {})
        autor_email = (
            criado_por.get("email")
            or criado_por.get("displayName", "desconhecido")
        )

        version = page.get("version", {})
        modificado_por = version.get("by", {})
        mod_email = (
            modificado_por.get("email")
            or modificado_por.get("displayName", autor_email)
        )

        body_html = page.get("body", {}).get("storage", {}).get("value", "")
        corpo_texto = _strip_html(body_html)

        resultados: list[PageTextChunk] = []

        if incluir_titulo and titulo.strip():
            resultados.append(
                PageTextChunk(
                    texto=titulo,
                    autor=autor_email,
                    pagina=titulo,
                    page_url=page_url,
                )
            )

        if incluir_corpo and corpo_texto.strip():
            resultados.append(
                PageTextChunk(
                    texto=corpo_texto,
                    autor=mod_email,
                    pagina=titulo,
                    page_url=page_url,
                )
            )

        return resultados
