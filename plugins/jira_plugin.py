"""
Plugin Jira para o Presidio PT.

Suporta Jira Cloud e Jira Server/Data Center.
Fornece conexão, listagem de projetos, busca de issues via JQL e
extração de texto para detecção de PII.
"""

from __future__ import annotations

import logging
from typing import Any, TypedDict

from jira import JIRA
from jira.exceptions import JIRAError

logger = logging.getLogger(__name__)

# ── Constantes públicas ───────────────────────────────────────────────────────

ISSUE_TYPES_PADRAO: list[str] = [
    "Bug", "Story", "Task", "Epic", "Sub-task", "Improvement",
]

CAMPOS_DISPONIVEIS: dict[str, str] = {
    "Título (summary)": "summary",
    "Descrição": "description",
    "Comentários": "comments",
    "Campos customizados (customfield)": "custom",
}


# ── Tipos internos ────────────────────────────────────────────────────────────

class ConnResult(TypedDict):
    ok: bool
    message: str


class ProjetoInfo(TypedDict):
    key: str
    name: str


class IssueTextChunk(TypedDict):
    texto: str
    autor: str
    campo: str
    issue_key: str
    issue_url: str
    issue_type: str
    prioridade: str


# ── Plugin Jira ───────────────────────────────────────────────────────────────

class JiraPlugin:
    """Conector para Jira Cloud e Server/Data Center."""

    def __init__(self) -> None:
        self._client: JIRA | None = None
        self._base_url: str = ""

    def conectar(
        self,
        url: str,
        usuario: str,
        token: str,
        cloud: bool = True,
    ) -> ConnResult:
        self._base_url = url.rstrip("/")
        try:
            self._client = JIRA(
                server=self._base_url,
                basic_auth=(usuario, token),
            )
            me = self._client.myself()
            display_name = me.get("displayName", usuario)
            msg = f"Conectado como {display_name}."
            logger.info("Jira conectado: %s — %s", self._base_url, msg)
            return ConnResult(ok=True, message=msg)
        except JIRAError as exc:
            msg = f"Erro Jira ({exc.status_code}): {exc.text}"
            logger.error(
                "Falha Jira (%s): %s — URL=%s",
                exc.status_code,
                exc.text,
                self._base_url,
            )
            return ConnResult(ok=False, message=msg)
        except Exception as exc:
            msg = f"Erro de conexão: {exc}"
            logger.exception("Erro inesperado ao conectar Jira: %s", exc)
            return ConnResult(ok=False, message=msg)

    def listar_projetos(self) -> list[ProjetoInfo]:
        if not self._client:
            logger.warning("Não conectado ao listar projetos")
            return []
        try:
            return [
                ProjetoInfo(key=p.key, name=p.name)
                for p in self._client.projects()
            ]
        except Exception:
            logger.exception("Erro ao listar projetos Jira")
            return []

    def buscar_issues(
        self,
        project_key: str,
        issue_types: list[str] | None = None,
        jql_extra: str = "",
        data_inicio: str = "",
        max_results: int = 50,
    ) -> list[Any]:
        if not self._client:
            raise RuntimeError("JiraPlugin não está conectado.")

        condicoes: list[str] = [f"project = {project_key}"]

        if issue_types:
            tipos = ", ".join(f'"{t}"' for t in issue_types)
            condicoes.append(f"issuetype in ({tipos})")

        if data_inicio:
            condicoes.append(f"created >= '{data_inicio}'")

        if jql_extra.strip():
            condicoes.append(f"({jql_extra.strip()})")

        jql = " AND ".join(condicoes) + " ORDER BY created DESC"

        try:
            issues = self._client.search_issues(
                jql,
                maxResults=max_results,
                fields=(
                    "summary,description,comment,customfield*,"
                    "reporter,assignee,issuetype,priority,status,labels"
                ),
            )
            return issues if isinstance(issues, list) else []
        except JIRAError as exc:
            logger.error(
                "JQL error para projeto '%s': %s — JQL: %s",
                project_key,
                exc.text,
                jql,
            )
            return []
        except Exception:
            logger.exception(
                "Erro inesperado ao buscar issues do projeto '%s'",
                project_key,
            )
            return []

    def extrair_textos(
        self,
        issue: Any,
        campos: list[str] | None = None,
    ) -> list[IssueTextChunk]:
        campos_selecionados = campos or list(CAMPOS_DISPONIVEIS.values())
        issue_url = f"{self._base_url}/browse/{issue.key}"

        reporter = getattr(issue.fields, "reporter", None)
        reporter_email = (
            getattr(reporter, "emailAddress", None)
            or (reporter.displayName if reporter else "desconhecido")
        )

        assignee = getattr(issue.fields, "assignee", None)
        assignee_email = (
            getattr(assignee, "emailAddress", None)
            or (assignee.displayName if assignee else reporter_email)
        )

        issue_type = (
            getattr(getattr(issue.fields, "issuetype", None), "name", "")
        )
        prioridade = (
            getattr(
                getattr(issue.fields, "priority", None), "name", ""
            )
        )

        resultados: list[IssueTextChunk] = []

        def _add(texto: str, autor: str, campo: str) -> None:
            if texto and str(texto).strip():
                resultados.append(
                    IssueTextChunk(
                        texto=str(texto).strip(),
                        autor=autor,
                        campo=campo,
                        issue_key=issue.key,
                        issue_url=issue_url,
                        issue_type=issue_type,
                        prioridade=prioridade,
                    )
                )

        if "summary" in campos_selecionados:
            _add(
                getattr(issue.fields, "summary", ""),
                reporter_email,
                "Título",
            )

        if "description" in campos_selecionados:
            _add(
                getattr(issue.fields, "description", ""),
                reporter_email,
                "Descrição",
            )

        if "comments" in campos_selecionados:
            comentarios = getattr(
                getattr(issue.fields, "comment", None), "comments", []
            )
            for c in comentarios:
                email_coment = (
                    getattr(c.author, "emailAddress", None)
                    or getattr(c.author, "displayName", "desconhecido")
                )
                _add(c.body, email_coment, "Comentário")

        if "custom" in campos_selecionados:
            for field_name in vars(issue.fields):
                if field_name.startswith("customfield_"):
                    valor = getattr(issue.fields, field_name)
                    if isinstance(valor, str) and valor.strip():
                        _add(
                            valor,
                            assignee_email,
                            f"Campo customizado ({field_name})",
                        )

        return resultados
