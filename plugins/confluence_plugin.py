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

    def listar_spaces(self, max_results: int = 200, com_contagem: bool = True) -> list[dict]:
        """Lista spaces acessíveis com contagem de páginas (paralelo)."""
        if not self._client:
            logger.warning("Não conectado ao listar spaces")
            return []
        try:
            from concurrent.futures import ThreadPoolExecutor
            resultado = self._client.get_spaces(limit=max_results)
            spaces = resultado.get("results", []) if isinstance(resultado, dict) else []

            if not com_contagem:
                return [{"key": s["key"], "name": s["name"], "count": -1} for s in spaces]

            def _contar(space):
                key = space["key"]
                try:
                    r = self._client.cql(f'space = "{key}" AND type = page', limit=0)
                    count = r.get("totalSize", 0) if isinstance(r, dict) else 0
                    return {"key": key, "name": space["name"], "count": count}
                except Exception:
                    return {"key": key, "name": space["name"], "count": -1}

            with ThreadPoolExecutor(max_workers=min(8, len(spaces) or 1)) as ex:
                results = list(ex.map(_contar, spaces))

            return sorted(results, key=lambda x: x.get("count", 0), reverse=True)
        except Exception:
            logger.exception("Erro ao listar spaces Confluence")
            return []

    def buscar_paginas(
        self,
        space_key: str | list[str] = "",
        status: str = "current",
        incluir_filhas: bool = True,
        desde: str = "",
        page_size: int = 50,
        max_total: int = 0,
    ) -> list[dict[str, Any]]:
        """Busca páginas com paginação completa.

        Args:
            space_key: Chave do space ("DS"), lista de chaves (["DS","ENG"])
                       ou string vazia ("") para todos os spaces acessíveis.
            status: Status das páginas ("current", "draft", "archived").
            incluir_filhas: Reservado para uso futuro.
            desde: Filtro incremental por data de modificação (YYYY-MM-DD).
            page_size: Quantidade de páginas por requisição (padrão 50).
            max_total: Limite total de páginas retornadas (0 = sem limite).
        """
        if not self._client:
            raise RuntimeError("ConfluencePlugin não está conectado.")

        _expand = "body.storage,history.createdBy,version.by,ancestors,space"

        cql_parts: list[str] = []
        if isinstance(space_key, list):
            if space_key:
                chaves = " OR ".join(f'space = "{k}"' for k in space_key)
                cql_parts.append(f"({chaves})")
        elif space_key:
            cql_parts.append(f'space = "{space_key}"')

        if status and status != "all":
            cql_parts.append(f'status = "{status}"')
        if desde:
            cql_parts.append(f'lastModified >= "{desde}"')
        cql = " AND ".join(cql_parts) + " ORDER BY lastModified ASC"
        _espaco_log = space_key if isinstance(space_key, str) else ", ".join(space_key or ["todos"])

        all_pages: list[dict[str, Any]] = []
        start = 0

        while True:
            try:
                result = self._client.cql(
                    cql,
                    start=start,
                    limit=page_size,
                    expand=_expand,
                )
            except Exception:
                logger.exception(
                    "Erro ao buscar páginas do space '%s' via CQL (start=%d) — CQL: %s",
                    space_key,
                    start,
                    cql,
                )
                break

            if not isinstance(result, dict):
                break

            batch = result.get("results", [])
            if not batch:
                break

            # CQL search retorna cada item com o conteúdo dentro de "content"
            for item in batch:
                page = item.get("content") or item
                all_pages.append(page)

            if max_total and len(all_pages) >= max_total:
                all_pages = all_pages[:max_total]
                break

            if len(batch) < page_size:
                break

            start += len(batch)

        logger.info(
            "Confluence '%s': %d páginas recuperadas (desde='%s')",
            _espaco_log,
            len(all_pages),
            desde or "inicio",
        )
        return all_pages

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

    def listar_anexos(self, page_id: str) -> list["AnexoInfo"]:
        """Retorna metadados dos anexos de uma página Confluence."""
        from plugins.attachment_scanner import AnexoInfo
        if not self._client:
            raise RuntimeError("ConfluencePlugin não está conectado.")
        try:
            result = self._client.get_attachments_from_content(
                page_id, start=0, limit=200, expand="version"
            )
            if not isinstance(result, dict):
                return []
            anexos = []
            for att in result.get("results", []):
                links = att.get("_links", {})
                download_path = links.get("download", "")
                url_download = (
                    download_path
                    if download_path.startswith("http")
                    else f"{self._base_url}{download_path}"
                )
                ext_info = att.get("extensions", {})
                mime_type = ext_info.get("mediaType", "application/octet-stream")
                anexos.append(AnexoInfo(
                    id=str(att.get("id", "")),
                    nome=att.get("title", "anexo"),
                    mime_type=mime_type,
                    tamanho=ext_info.get("fileSize", 0),
                    url_download=url_download,
                    parent_key=page_id,
                    source="confluence",
                ))
            return anexos
        except Exception:
            logger.exception("Erro ao listar anexos da página '%s'", page_id)
            return []

    def baixar_anexo(self, url: str) -> bytes:
        """Baixa o conteúdo binário de um anexo pelo URL."""
        if not self._client:
            raise RuntimeError("ConfluencePlugin não está conectado.")
        response = self._client._session.get(url)
        response.raise_for_status()
        return response.content
