"""
Ações de remediação no Jira após detecção de PII/secrets.

Princípios de design:
- Modo read-only por padrão — write é opt-in explícito.
- Permissão verificada antes de qualquer escrita.
- Secrets nunca aparecem completos — sempre mascarados.
- Issue Properties como canal preferencial (oculto na UI, fora do histórico visível).
- Label como alternativa visível mas sem expor conteúdo.
- Comentário apenas se explicitamente solicitado (vai para o audit trail público).
- Scrub: substitui valores detectados por [ENTIDADE] diretamente no campo — IRREVERSÍVEL.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, TypedDict

from jira import JIRA
from jira.exceptions import JIRAError

from plugins.scanner import ResultadoChunk, SECRET_ENTITIES

logger = logging.getLogger(__name__)

# Chave usada em Jira Issue Properties — identificador fixo do scanner
_PROPERTY_KEY = "data-protection-scan"

# Labels adicionados por nível de severidade / ação de remediação
LABEL_SECRET   = "SECRET-DETECTED"
LABEL_PII_HIGH = "PII-HIGH"
LABEL_PII_MEDIUM = "PII-MEDIUM"
LABEL_REVIEWED = "DATA-PROTECTION-REVIEWED"
LABEL_SCRUBBED = "DATA-PROTECTION-SCRUBBED"


# ── Helpers de scrubbing ─────────────────────────────────────────────────────

def _anonimizar_adf(node: Any, replacements: dict[str, str]) -> Any:
    """Percorre um nó ADF (JSON) e substitui textos detectados preservando estrutura."""
    if isinstance(node, dict):
        if node.get("type") == "text" and "text" in node:
            texto = node["text"]
            for orig, repl in replacements.items():
                if orig and orig in texto:
                    texto = texto.replace(orig, repl)
            return {**node, "text": texto}
        return {k: _anonimizar_adf(v, replacements) for k, v in node.items()}
    if isinstance(node, list):
        return [_anonimizar_adf(item, replacements) for item in node]
    return node


def _extrair_texto_simples(content: Any) -> str:
    """Extrai texto plano de ADF ou string."""
    if isinstance(content, dict):
        partes: list[str] = []

        def _walk(node: Any) -> None:
            if isinstance(node, dict):
                if node.get("type") == "text":
                    partes.append(node.get("text", ""))
                for v in node.values():
                    if isinstance(v, (dict, list)):
                        _walk(v)
            elif isinstance(node, list):
                for item in node:
                    _walk(item)

        _walk(content)
        return " ".join(partes)
    return str(content or "")


def _replacements_de_deteccoes(deteccoes: list) -> dict[str, str]:
    """Monta dict {valor_original: [ENTIDADE]} para substituição."""
    repl: dict[str, str] = {}
    for d in deteccoes:
        if d.valor and d.valor.strip():
            repl[d.valor] = f"[{d.entidade}]"
    return repl


# ── Tipos de resultado ────────────────────────────────────────────────────────

class PermissaoResult(TypedDict):
    pode_editar: bool
    mensagem: str


class AcaoResult(TypedDict):
    acao: str          # "properties" | "label" | "comment" | "skipped"
    ok: bool
    mensagem: str


# ── Helpers internos ──────────────────────────────────────────────────────────

def _resumo_para_properties(resultados: list[ResultadoChunk], timestamp: str) -> dict[str, Any]:
    """Monta payload para Issue Properties — sem valores sensíveis."""
    total = sum(r.total_deteccoes for r in resultados)
    por_nivel: dict[str, int] = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    entidades: set[str] = set()
    tem_secret = False

    for r in resultados:
        for d in r.deteccoes:
            por_nivel[d.nivel] = por_nivel.get(d.nivel, 0) + 1
            entidades.add(d.entidade)
            if d.is_secret:
                tem_secret = True

    high = por_nivel["HIGH"]
    compliance_score = max(0, round(100 - (high / max(total, 1) * 100)))

    return {
        "scanner_version": "3.0",
        "timestamp": timestamp,
        "total_deteccoes": total,
        "por_nivel": por_nivel,
        "entidades_detectadas": sorted(entidades),
        "tem_secret": tem_secret,
        "compliance_score": compliance_score,
    }


def _labels_para_resultado(resultados: list[ResultadoChunk]) -> list[str]:
    labels = [LABEL_REVIEWED]
    tem_secret = any(r.tem_secret for r in resultados)
    niveis = {d.nivel for r in resultados for d in r.deteccoes}

    if tem_secret:
        labels.append(LABEL_SECRET)
    if "HIGH" in niveis:
        labels.append(LABEL_PII_HIGH)
    elif "MEDIUM" in niveis:
        labels.append(LABEL_PII_MEDIUM)

    return labels


def _corpo_comentario(resultados: list[ResultadoChunk], issue_key: str) -> str:
    """Gera corpo de comentário com valores sempre mascarados."""
    total = sum(r.total_deteccoes for r in resultados)
    if total == 0:
        return (
            f"[Data Protection] Varredura concluída em {issue_key} — "
            "nenhuma entidade sensível detectada."
        )

    por_nivel: dict[str, list[str]] = {"HIGH": [], "MEDIUM": [], "LOW": []}
    frameworks: set[str] = set()
    secrets_display: list[str] = []

    for r in resultados:
        for d in r.deteccoes:
            por_nivel[d.nivel].append(d.entidade)
            frameworks.update(d.frameworks)
            if d.is_secret:
                secrets_display.append(f"{d.entidade}: {d.valor_display}")

    linhas = [
        f"[Data Protection] Varredura concluída — {total} detecção(oes)",
        "",
    ]

    for nivel, label in [("HIGH", "Alto"), ("MEDIUM", "Medio"), ("LOW", "Baixo")]:
        if por_nivel[nivel]:
            contagem = len(por_nivel[nivel])
            entidades = ", ".join(sorted(set(por_nivel[nivel])))
            linhas.append(f"Nivel {label} ({contagem}): {entidades}")

    if secrets_display:
        linhas.append("")
        linhas.append("Credenciais detectadas (mascaradas):")
        for s in secrets_display:
            linhas.append(f"  - {s}")

    if frameworks:
        linhas.append("")
        fw_str = ", ".join(sorted(frameworks)[:6])
        linhas.append(f"Frameworks impactados: {fw_str}")

    linhas += [
        "",
        "Recomendacao: remover dados sensiveis e revogar credenciais expostas.",
        "---",
        "Gerado automaticamente pelo Data Protection Scanner v3.0.",
    ]

    return "\n".join(linhas)


# ── Classe principal ──────────────────────────────────────────────────────────

class JiraActions:
    """Executa ações de remediação em issues Jira após detecção de PII/secrets."""

    def __init__(self, client: JIRA, base_url: str) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")

    # ── Permissão ─────────────────────────────────────────────────────────────

    def checar_permissao(self, issue_key: str) -> PermissaoResult:
        """Verifica se o token atual tem permissão de edição na issue."""
        try:
            url = (
                f"{self._base_url}/rest/api/3/mypermissions"
                f"?issueKey={issue_key}&permissions=EDIT_ISSUES"
            )
            resp = self._client._session.get(url)
            resp.raise_for_status()
            data = resp.json()
            pode = (
                data.get("permissions", {})
                .get("EDIT_ISSUES", {})
                .get("havePermission", False)
            )
            msg = "Permissao de edicao confirmada." if pode else "Sem permissao de edicao nesta issue."
            return PermissaoResult(pode_editar=pode, mensagem=msg)
        except Exception as exc:
            logger.warning("Erro ao checar permissao em '%s': %s", issue_key, exc)
            return PermissaoResult(pode_editar=False, mensagem=f"Erro ao checar permissao: {exc}")

    # ── Issue Properties (oculto na UI) ───────────────────────────────────────

    def salvar_properties(
        self,
        issue_key: str,
        resultados: list[ResultadoChunk],
        timestamp: str,
    ) -> AcaoResult:
        """Grava resultado do scan em Issue Properties — invisivel na UI do Jira."""
        payload = _resumo_para_properties(resultados, timestamp)
        url = f"{self._base_url}/rest/api/3/issue/{issue_key}/properties/{_PROPERTY_KEY}"
        try:
            resp = self._client._session.put(
                url,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
            return AcaoResult(acao="properties", ok=True, mensagem="Resultado salvo em Issue Properties.")
        except Exception as exc:
            logger.error("Erro ao salvar properties em '%s': %s", issue_key, exc)
            return AcaoResult(acao="properties", ok=False, mensagem=f"Erro: {exc}")

    def ler_properties(self, issue_key: str) -> dict[str, Any] | None:
        """Lê resultado anterior salvo em Issue Properties."""
        url = f"{self._base_url}/rest/api/3/issue/{issue_key}/properties/{_PROPERTY_KEY}"
        try:
            resp = self._client._session.get(url)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json().get("value")
        except Exception as exc:
            logger.warning("Erro ao ler properties de '%s': %s", issue_key, exc)
            return None

    # ── Labels ────────────────────────────────────────────────────────────────

    def adicionar_labels(
        self,
        issue_key: str,
        resultados: list[ResultadoChunk],
    ) -> AcaoResult:
        """Adiciona labels de risco à issue sem expor conteúdo detectado."""
        novos_labels = _labels_para_resultado(resultados)
        try:
            issue = self._client.issue(issue_key, fields="labels")
            labels_atuais = [
                lbl.name if hasattr(lbl, "name") else str(lbl)
                for lbl in issue.fields.labels
            ]
            labels_finais = list(set(labels_atuais + novos_labels))
            issue.update(fields={"labels": labels_finais})
            return AcaoResult(
                acao="label",
                ok=True,
                mensagem=f"Labels adicionados: {', '.join(novos_labels)}",
            )
        except JIRAError as exc:
            logger.error("JIRAError ao adicionar labels em '%s': %s", issue_key, exc.text)
            return AcaoResult(acao="label", ok=False, mensagem=f"Erro Jira: {exc.text}")
        except Exception as exc:
            logger.error("Erro ao adicionar labels em '%s': %s", issue_key, exc)
            return AcaoResult(acao="label", ok=False, mensagem=f"Erro: {exc}")

    # ── Comentário (opt-in — vai para o audit trail público) ──────────────────

    def adicionar_comentario(
        self,
        issue_key: str,
        resultados: list[ResultadoChunk],
    ) -> AcaoResult:
        """Adiciona comentario publico com resumo mascarado.

        Visivel para todos com acesso a issue e registrado no historico.
        Usar apenas quando transparencia para o time e desejada.
        """
        corpo = _corpo_comentario(resultados, issue_key)
        try:
            self._client.add_comment(issue_key, corpo)
            return AcaoResult(
                acao="comment",
                ok=True,
                mensagem="Comentario adicionado (visivel no historico da issue).",
            )
        except JIRAError as exc:
            logger.error("JIRAError ao comentar em '%s': %s", issue_key, exc.text)
            return AcaoResult(acao="comment", ok=False, mensagem=f"Erro Jira: {exc.text}")
        except Exception as exc:
            logger.error("Erro ao comentar em '%s': %s", issue_key, exc)
            return AcaoResult(acao="comment", ok=False, mensagem=f"Erro: {exc}")

    # ── Scrubbing (redação direta nos campos) ─────────────────────────────────

    def scrub_preview(
        self,
        issue_key: str,
        resultados: list[ResultadoChunk],
    ) -> list[dict[str, Any]]:
        """Retorna preview do que seria alterado — sem escrever nada no Jira.

        Cada item: {"campo": str, "antes": str, "depois": str, "entidades": list[str]}
        """
        try:
            issue = self._client.issue(issue_key, fields="summary,description,comment")
        except Exception as exc:
            logger.error("Erro ao buscar issue '%s' para preview: %s", issue_key, exc)
            return []

        por_campo: dict[str, list] = {}
        for r in resultados:
            campo = r.chunk.get("campo", "")
            por_campo.setdefault(campo, []).extend(r.deteccoes)

        previews: list[dict[str, Any]] = []

        # Título (summary)
        if "Título" in por_campo:
            summary = getattr(issue.fields, "summary", "") or ""
            repl = _replacements_de_deteccoes(por_campo["Título"])
            novo = summary
            for orig, sub in repl.items():
                novo = novo.replace(orig, sub)
            if novo != summary:
                previews.append({
                    "campo": "Título (summary)",
                    "antes": summary[:400],
                    "depois": novo[:400],
                    "entidades": list({d.entidade for d in por_campo["Título"]}),
                    "campo_api": "summary",
                })

        # Descrição (pode ser ADF ou string)
        if "Descrição" in por_campo:
            desc = getattr(issue.fields, "description", None)
            if desc:
                repl = _replacements_de_deteccoes(por_campo["Descrição"])
                texto_antes = _extrair_texto_simples(desc)
                if isinstance(desc, dict):
                    desc_novo = _anonimizar_adf(desc, repl)
                    texto_depois = _extrair_texto_simples(desc_novo)
                else:
                    texto_depois = texto_antes
                    for orig, sub in repl.items():
                        texto_depois = texto_depois.replace(orig, sub)
                if texto_antes != texto_depois:
                    previews.append({
                        "campo": "Descrição",
                        "antes": texto_antes[:600],
                        "depois": texto_depois[:600],
                        "entidades": list({d.entidade for d in por_campo["Descrição"]}),
                        "campo_api": "description",
                    })

        # Comentários
        if "Comentário" in por_campo:
            comentarios = getattr(
                getattr(issue.fields, "comment", None), "comments", []
            ) or []
            repl = _replacements_de_deteccoes(por_campo["Comentário"])
            for i, c in enumerate(comentarios):
                body = c.body or ""
                texto_antes = _extrair_texto_simples(body)
                if isinstance(body, dict):
                    corpo_novo = _anonimizar_adf(body, repl)
                    texto_depois = _extrair_texto_simples(corpo_novo)
                else:
                    texto_depois = texto_antes
                    for orig, sub in repl.items():
                        texto_depois = texto_depois.replace(orig, sub)
                if texto_antes != texto_depois:
                    previews.append({
                        "campo": f"Comentário #{i + 1} (por {getattr(getattr(c, 'author', None), 'displayName', '?')})",
                        "antes": texto_antes[:600],
                        "depois": texto_depois[:600],
                        "entidades": list({d.entidade for d in por_campo["Comentário"]}),
                        "campo_api": f"comment:{c.id}",
                    })

        return previews

    def scrub_aplicar(
        self,
        issue_key: str,
        resultados: list[ResultadoChunk],
        audit_comment: bool = True,
    ) -> list[AcaoResult]:
        """Aplica scrubbing: substitui valores detectados diretamente nos campos.

        IRREVERSÍVEL — o texto original é sobrescrito na API do Jira.
        Requer permissão de edição.
        """
        acoes: list[AcaoResult] = []

        perm = self.checar_permissao(issue_key)
        if not perm["pode_editar"]:
            acoes.append(AcaoResult(
                acao="scrub", ok=False,
                mensagem=f"Sem permissao de edicao: {perm['mensagem']}",
            ))
            return acoes

        try:
            issue = self._client.issue(issue_key, fields="summary,description,comment,labels")
        except Exception as exc:
            acoes.append(AcaoResult(acao="scrub", ok=False, mensagem=f"Erro ao buscar issue: {exc}"))
            return acoes

        por_campo: dict[str, list] = {}
        for r in resultados:
            campo = r.chunk.get("campo", "")
            por_campo.setdefault(campo, []).extend(r.deteccoes)

        entidades_scrubadas: set[str] = set()

        # Scrub summary
        if "Título" in por_campo:
            summary = getattr(issue.fields, "summary", "") or ""
            repl = _replacements_de_deteccoes(por_campo["Título"])
            novo = summary
            for orig, sub in repl.items():
                novo = novo.replace(orig, sub)
            if novo != summary:
                try:
                    issue.update(fields={"summary": novo})
                    for d in por_campo["Título"]:
                        entidades_scrubadas.add(d.entidade)
                    acoes.append(AcaoResult(acao="scrub", ok=True, mensagem="Titulo anonimizado."))
                except Exception as exc:
                    acoes.append(AcaoResult(acao="scrub", ok=False, mensagem=f"Erro titulo: {exc}"))

        # Scrub description
        if "Descrição" in por_campo:
            desc = getattr(issue.fields, "description", None)
            if desc:
                repl = _replacements_de_deteccoes(por_campo["Descrição"])
                if isinstance(desc, dict):
                    novo_desc = _anonimizar_adf(desc, repl)
                else:
                    novo_desc = str(desc)
                    for orig, sub in repl.items():
                        novo_desc = novo_desc.replace(orig, sub)
                if novo_desc != desc:
                    try:
                        issue.update(fields={"description": novo_desc})
                        for d in por_campo["Descrição"]:
                            entidades_scrubadas.add(d.entidade)
                        acoes.append(AcaoResult(acao="scrub", ok=True, mensagem="Descricao anonimizada."))
                    except Exception as exc:
                        acoes.append(AcaoResult(acao="scrub", ok=False, mensagem=f"Erro descricao: {exc}"))

        # Scrub comments
        if "Comentário" in por_campo:
            comentarios = getattr(
                getattr(issue.fields, "comment", None), "comments", []
            ) or []
            repl = _replacements_de_deteccoes(por_campo["Comentário"])
            for c in comentarios:
                body = c.body or ""
                if isinstance(body, dict):
                    novo_body = _anonimizar_adf(body, repl)
                    mudou = _extrair_texto_simples(novo_body) != _extrair_texto_simples(body)
                else:
                    novo_body = str(body)
                    for orig, sub in repl.items():
                        novo_body = novo_body.replace(orig, sub)
                    mudou = novo_body != body
                if mudou:
                    try:
                        self._client.edit_comment(issue_key, c.id, novo_body)
                        for d in por_campo["Comentário"]:
                            entidades_scrubadas.add(d.entidade)
                        acoes.append(AcaoResult(
                            acao="scrub", ok=True,
                            mensagem=f"Comentario {c.id} anonimizado.",
                        ))
                    except Exception as exc:
                        acoes.append(AcaoResult(
                            acao="scrub", ok=False,
                            mensagem=f"Erro comentario {c.id}: {exc}",
                        ))

        if not entidades_scrubadas:
            acoes.append(AcaoResult(acao="scrub", ok=True, mensagem="Nenhum campo alterado — valores nao encontrados literalmente nos campos."))
            return acoes

        # Label de confirmação
        labels_atuais = [
            lbl.name if hasattr(lbl, "name") else str(lbl)
            for lbl in issue.fields.labels
        ]
        labels_novos = list(set(labels_atuais + [LABEL_SCRUBBED, LABEL_REVIEWED]))
        try:
            issue.update(fields={"labels": labels_novos})
            acoes.append(AcaoResult(
                acao="label", ok=True,
                mensagem=f"Label {LABEL_SCRUBBED} adicionado.",
            ))
        except Exception as exc:
            acoes.append(AcaoResult(acao="label", ok=False, mensagem=f"Erro label: {exc}"))

        # Comentário de auditoria
        if audit_comment:
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            ents = ", ".join(sorted(entidades_scrubadas))
            corpo = (
                f"[Data Protection Scanner] Dados sensiveis removidos em {ts}.\n"
                f"Entidades redatadas: {ents}.\n"
                "Os valores foram substituidos por [TIPO_ENTIDADE] diretamente no texto.\n"
                "---\nGerado automaticamente pelo Data Protection Scanner v3.0."
            )
            try:
                self._client.add_comment(issue_key, corpo)
                acoes.append(AcaoResult(
                    acao="comment", ok=True,
                    mensagem="Comentario de auditoria adicionado ao historico.",
                ))
            except Exception as exc:
                acoes.append(AcaoResult(acao="comment", ok=False, mensagem=f"Erro comentario auditoria: {exc}"))

        # Salvar em Issue Properties para registro interno
        acoes.append(self.salvar_properties(issue_key, resultados, datetime.now(timezone.utc).isoformat()))

        return acoes

    # ── Orquestrador ──────────────────────────────────────────────────────────

    def aplicar(
        self,
        issue_key: str,
        resultados: list[ResultadoChunk],
        timestamp: str,
        modo: str = "properties",
    ) -> list[AcaoResult]:
        """Aplica ações com verificação de permissão.

        Args:
            issue_key: Chave da issue (ex: "PROJ-42").
            resultados: Chunks com detecções desta issue.
            timestamp: ISO timestamp do scan (ex: datetime.now(UTC).isoformat()).
            modo: "readonly"   — apenas checa permissao, nao escreve nada.
                  "properties" — salva em Issue Properties (invisivel na UI).
                  "label"      — adiciona labels + salva em properties.
                  "comment"    — tudo acima + comentario publico.

        Returns:
            Lista de AcaoResult com o resultado de cada etapa.
        """
        acoes: list[AcaoResult] = []

        perm = self.checar_permissao(issue_key)
        if not perm["pode_editar"]:
            acoes.append(AcaoResult(
                acao="skipped",
                ok=False,
                mensagem=f"Sem permissao: {perm['mensagem']}",
            ))
            return acoes

        if modo == "readonly":
            acoes.append(AcaoResult(
                acao="skipped",
                ok=True,
                mensagem="Modo read-only — nenhuma acao aplicada.",
            ))
            return acoes

        if modo == "scrub":
            return self.scrub_aplicar(issue_key, resultados, audit_comment=True)

        # properties: sempre executado em todos os modos write
        acoes.append(self.salvar_properties(issue_key, resultados, timestamp))

        if modo in ("label", "comment"):
            acoes.append(self.adicionar_labels(issue_key, resultados))

        if modo == "comment":
            acoes.append(self.adicionar_comentario(issue_key, resultados))

        return acoes
