"""
Plugin Jira para o Presidio PT.

Suporta Jira Cloud e Jira Server/Data Center.
Fornece conexão, listagem de projetos, busca de issues via JQL,
extração de texto para detecção de PII e acesso às ações de remediação.
"""

from __future__ import annotations

import logging
from typing import Any, TypedDict, TYPE_CHECKING

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from jira import JIRA
from jira.exceptions import JIRAError

if TYPE_CHECKING:
    from plugins.jira_actions import JiraActions

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
    count: int


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

    @property
    def actions(self) -> "JiraActions":
        """Retorna instância de JiraActions para remediação pós-scan."""
        from plugins.jira_actions import JiraActions  # import lazy — evita circular
        if not self._client:
            raise RuntimeError("JiraPlugin não está conectado.")
        return JiraActions(self._client, self._base_url)

    def conectar(
        self,
        url: str,
        usuario: str,
        token: str,
        cloud: bool = True,
    ) -> ConnResult:
        self._base_url = url.rstrip("/")
        try:
            if cloud:
                # Cloud: email + API token (basic auth)
                self._client = JIRA(
                    server=self._base_url,
                    basic_auth=(usuario, token),
                )
            elif usuario:
                # Server/DC: username + password (legacy / older versions)
                self._client = JIRA(
                    server=self._base_url,
                    basic_auth=(usuario, token),
                    options={"verify": False},
                )
            else:
                # Server/DC: PAT (Personal Access Token) — Jira Server 8.14+ / Data Center
                self._client = JIRA(
                    server=self._base_url,
                    token_auth=token,
                    options={"verify": False},
                )
            me = self._client.myself()
            display_name = me.get("displayName", usuario or "usuario")
            modo = "Cloud" if cloud else ("Server/PAT" if not usuario else "Server/Senha")
            msg = f"Conectado como {display_name} [{modo}]."
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
            msg = f"Erro de conexao: {exc}"
            logger.exception("Erro inesperado ao conectar Jira: %s", exc)
            return ConnResult(ok=False, message=msg)

    def listar_projetos(self, max_results: int = 0, com_contagem: bool = True) -> list[dict]:
        """Lista projetos acessíveis, opcionalmente com contagem de issues (paralelo).

        max_results: 0 = sem limite (todos os projetos acessíveis).
        """
        if not self._client:
            logger.warning("Não conectado ao listar projetos")
            return []
        try:
            from concurrent.futures import ThreadPoolExecutor

            raw: list[dict] = []
            page_size = 100

            def _paginar(endpoint: str) -> list[dict]:
                acc: list[dict] = []
                start = 0
                while True:
                    data = self._client._get_json(
                        endpoint,
                        params={"startAt": start, "maxResults": page_size},
                    )
                    # /project (Server legado) retorna lista plana diretamente
                    if isinstance(data, list):
                        acc.extend(data)
                        break
                    batch = data.get("values", [])
                    acc.extend(batch)
                    total = data.get("total")
                    is_last = data.get("isLast", False)
                    if is_last or len(batch) < page_size:
                        break
                    if total is not None and len(acc) >= total:
                        break
                    start += page_size
                return acc

            # /project/search = Jira Cloud + Server 8.x+; /project = Server legado
            for _ep in ("project/search", "project"):
                try:
                    raw = _paginar(_ep)
                    break
                except Exception:
                    raw = []

            if max_results:
                raw = raw[:max_results]

            if not com_contagem:
                return [{"key": p["key"], "name": p["name"], "count": -1} for p in raw]

            def _contar(p: dict):
                try:
                    r = self._client.search_issues(
                        f'project = "{p["key"]}"', maxResults=0, fields="summary"
                    )
                    return {"key": p["key"], "name": p["name"], "count": r.total}
                except Exception:
                    return {"key": p["key"], "name": p["name"], "count": -1}

            with ThreadPoolExecutor(max_workers=min(8, len(raw) or 1)) as ex:
                results = list(ex.map(_contar, raw))

            return sorted(results, key=lambda x: x.get("count", 0), reverse=True)
        except Exception:
            logger.exception("Erro ao listar projetos Jira")
            return []

    def buscar_issues(
        self,
        project_key: str | list[str] = "",
        issue_types: list[str] | None = None,
        jql_extra: str = "",
        data_inicio: str = "",
        desde: str = "",
        page_size: int = 100,
        max_total: int = 0,
    ) -> list[Any]:
        """Busca issues com paginação completa.

        Args:
            project_key: Chave do projeto ("PROJ"), lista de chaves (["PROJ","ALPHA"])
                         ou string vazia ("") para todos os projetos acessíveis.
            issue_types: Filtro por tipo de issue.
            jql_extra: Cláusula JQL adicional.
            data_inicio: Filtro por data de criação (YYYY-MM-DD).
            desde: Filtro incremental por data de atualização (YYYY-MM-DD).
            page_size: Quantidade de issues por requisição (padrão 100).
            max_total: Limite total de issues retornadas (0 = sem limite).
        """
        if not self._client:
            raise RuntimeError("JiraPlugin não está conectado.")

        condicoes: list[str] = []

        if isinstance(project_key, list):
            if project_key:
                chaves = ", ".join(f'"{k}"' for k in project_key)
                condicoes.append(f"project in ({chaves})")
        elif project_key:
            condicoes.append(f"project = {project_key}")

        if issue_types:
            tipos = ", ".join(f'"{t}"' for t in issue_types)
            condicoes.append(f"issuetype in ({tipos})")

        if data_inicio:
            condicoes.append(f"created >= '{data_inicio}'")

        if desde:
            condicoes.append(f"updated >= '{desde}'")

        if jql_extra.strip():
            condicoes.append(f"({jql_extra.strip()})")

        jql = " AND ".join(condicoes) + " ORDER BY updated ASC"

        _fields = (
            "summary,description,comment,customfield*,"
            "reporter,assignee,issuetype,priority,status,labels,updated"
        )

        all_issues: list[Any] = []
        start_at = 0

        while True:
            try:
                batch = self._client.search_issues(
                    jql,
                    startAt=start_at,
                    maxResults=page_size,
                    fields=_fields,
                )
            except JIRAError as exc:
                logger.error(
                    "JQL error para projeto '%s' (startAt=%d): %s — JQL: %s",
                    project_key,
                    start_at,
                    exc.text,
                    jql,
                )
                break
            except Exception:
                logger.exception(
                    "Erro inesperado ao buscar issues do projeto '%s' (startAt=%d)",
                    project_key,
                    start_at,
                )
                break

            if not batch:
                break

            all_issues.extend(batch)

            if max_total and len(all_issues) >= max_total:
                all_issues = all_issues[:max_total]
                break

            if len(batch) < page_size:
                break

            start_at += len(batch)

        logger.info(
            "Jira '%s': %d issues recuperadas (desde='%s')",
            project_key,
            len(all_issues),
            desde or "inicio",
        )
        return all_issues

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

    def listar_anexos(self, issue_key: str) -> list["AnexoInfo"]:
        """Retorna metadados dos anexos de uma issue."""
        from plugins.attachment_scanner import AnexoInfo
        if not self._client:
            raise RuntimeError("JiraPlugin não está conectado.")
        try:
            issue = self._client.issue(issue_key, fields="attachment")
            anexos = []
            for att in getattr(issue.fields, "attachment", []) or []:
                anexos.append(AnexoInfo(
                    id=str(att.id),
                    nome=att.filename,
                    mime_type=getattr(att, "mimeType", "application/octet-stream"),
                    tamanho=getattr(att, "size", 0),
                    url_download=att.content,
                    parent_key=issue_key,
                    source="jira",
                ))
            return anexos
        except JIRAError as exc:
            logger.error("Erro ao listar anexos de '%s': %s", issue_key, exc.text)
            return []
        except Exception:
            logger.exception("Erro inesperado ao listar anexos de '%s'", issue_key)
            return []

    def baixar_anexo(self, url: str) -> bytes:
        """Baixa o conteúdo binário de um anexo pelo URL."""
        if not self._client:
            raise RuntimeError("JiraPlugin não está conectado.")
        response = self._client._session.get(url)
        response.raise_for_status()
        return response.content
