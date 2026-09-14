"""
Plugin de email via Microsoft Graph API.

Envia notificações e solicitações de remediação usando token OAuth de
curta duração obtido no Microsoft Developer Portal (validade ~1h).
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import requests

logger = logging.getLogger(__name__)

TEMPLATES_PATH = Path(__file__).parent.parent / "email_templates.json"

# ── Placeholders disponíveis ──────────────────────────────────────────────────

PLACEHOLDERS: list[tuple[str, str]] = [
    ("{issue_key}",        "Chave da issue — ex: PROJ-42"),
    ("{issue_url}",        "URL completa da issue no Jira"),
    ("{projeto}",          "Chave do projeto — ex: PROJ"),
    ("{entidades}",        "Tipos de dado detectados — ex: CPF, EMAIL"),
    ("{nivel_max}",        "Nivel de risco mais alto: HIGH / MEDIUM / LOW"),
    ("{total_deteccoes}",  "Quantidade total de deteccoes"),
    ("{data}",             "Data do scan (hoje)"),
    ("{solicitante}",      "Email / nome do usuario autenticado no Graph"),
]

# ── Templates padrão ──────────────────────────────────────────────────────────

DEFAULT_TEMPLATES: list[dict] = [
    {
        "nome": "Solicitacao de Remocao de Historico Jira",
        "assunto": "[LGPD/Compliance] Remocao de Historico - {issue_key}",
        "corpo": (
            "<p>Prezado(a) Administrador(a),</p>"
            "<p>Durante varredura automatizada realizada em <b>{data}</b>, foram detectadas "
            "as seguintes entidades no historico (changelog) da issue "
            "<a href=\"{issue_url}\">{issue_key}</a>:</p>"
            "<ul>"
            "<li><b>Tipos de dado:</b> {entidades}</li>"
            "<li><b>Nivel de risco:</b> {nivel_max}</li>"
            "<li><b>Total de deteccoes:</b> {total_deteccoes}</li>"
            "</ul>"
            "<p>Os campos ativos ja foram anonimizados. Porem, o <b>changelog/historico</b> "
            "ainda contem os valores originais e e visivel a todos os usuarios com acesso ao projeto.</p>"
            "<p>Solicito a remocao das entradas do historico para garantir conformidade com a "
            "<b>LGPD (Art. 18)</b>.</p>"
            "<p>Atenciosamente,<br/>{solicitante}</p>"
            "<hr/><small>Gerado automaticamente pelo Data Protection Scanner v3.0</small>"
        ),
    },
    {
        "nome": "Notificacao de PII Detectado",
        "assunto": "[Data Protection] PII Detectado - {issue_key}",
        "corpo": (
            "<p>Prezado(a),</p>"
            "<p>A varredura automatizada identificou dados potencialmente sensiveis na issue "
            "<a href=\"{issue_url}\">{issue_key}</a> (projeto <b>{projeto}</b>).</p>"
            "<ul>"
            "<li><b>Tipos de dado:</b> {entidades}</li>"
            "<li><b>Nivel de risco:</b> {nivel_max}</li>"
            "<li><b>Total de deteccoes:</b> {total_deteccoes}</li>"
            "<li><b>Data da varredura:</b> {data}</li>"
            "</ul>"
            "<p>Por favor, revise o conteudo e remova qualquer dado pessoal desnecessario.</p>"
            "<p>Atenciosamente,<br/>{solicitante}</p>"
            "<hr/><small>Gerado automaticamente pelo Data Protection Scanner v3.0</small>"
        ),
    },
    {
        "nome": "Confirmacao de Remediacao",
        "assunto": "[Data Protection] Remediacao Concluida - {issue_key}",
        "corpo": (
            "<p>Prezado(a),</p>"
            "<p>A remediacao de dados sensiveis foi concluida na issue "
            "<a href=\"{issue_url}\">{issue_key}</a>.</p>"
            "<ul>"
            "<li><b>Entidades removidas:</b> {entidades}</li>"
            "<li><b>Data:</b> {data}</li>"
            "<li><b>Responsavel:</b> {solicitante}</li>"
            "</ul>"
            "<p>Os valores foram substituidos por tokens <code>[TIPO_ENTIDADE]</code> via Presidio.</p>"
            "<p>Atenciosamente,<br/>{solicitante}</p>"
            "<hr/><small>Gerado automaticamente pelo Data Protection Scanner v3.0</small>"
        ),
    },
]


# ── Persistência de templates ─────────────────────────────────────────────────

def carregar_templates() -> list[dict]:
    """Carrega templates do arquivo JSON; retorna padrões se não existir."""
    if TEMPLATES_PATH.exists():
        try:
            data = json.loads(TEMPLATES_PATH.read_text(encoding="utf-8"))
            if isinstance(data, list) and data:
                return data
        except Exception:
            logger.exception("Erro ao carregar templates de email")
    return [t.copy() for t in DEFAULT_TEMPLATES]


def salvar_templates(templates: list[dict]) -> None:
    """Persiste templates em JSON."""
    try:
        TEMPLATES_PATH.write_text(
            json.dumps(templates, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        logger.exception("Erro ao salvar templates de email")


def preencher_template(template: dict, vars: dict[str, str]) -> dict[str, str]:
    """Substitui placeholders e retorna {assunto, corpo} preenchidos."""
    assunto = template.get("assunto", "")
    corpo = template.get("corpo", "")
    for k, v in vars.items():
        assunto = assunto.replace(f"{{{k}}}", str(v))
        corpo = corpo.replace(f"{{{k}}}", str(v))
    return {"assunto": assunto, "corpo": corpo}


def variaveis_de_chunks(
    issue_key: str,
    chunks: list,
    solicitante: str = "",
    data: str = "",
) -> dict[str, str]:
    """Monta o dict de variáveis para preencher templates a partir dos chunks de scan."""
    from plugins.scanner import ResultadoChunk
    entidades: set[str] = set()
    niveis: list[str] = []
    total = 0
    issue_url = ""

    for r in chunks:
        if not isinstance(r, ResultadoChunk):
            continue
        issue_url = issue_url or r.chunk.get("issue_url", "")
        for d in r.deteccoes:
            entidades.add(d.entidade)
            niveis.append(d.nivel)
            total += 1

    nivel_ordem = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
    nivel_max = max(niveis, key=lambda n: nivel_ordem.get(n, 0)) if niveis else "LOW"

    return {
        "issue_key": issue_key,
        "issue_url": issue_url or f"(sem URL)",
        "projeto": issue_key.split("-")[0] if "-" in issue_key else issue_key,
        "entidades": ", ".join(sorted(entidades)) or "—",
        "nivel_max": nivel_max,
        "total_deteccoes": str(total),
        "data": data,
        "solicitante": solicitante or "Data Protection Scanner",
    }


# ── Plugin Graph ──────────────────────────────────────────────────────────────

class GraphEmailPlugin:
    """Envia emails via Microsoft Graph API com token OAuth de curta duração."""

    BASE = "https://graph.microsoft.com/v1.0"

    def __init__(self, token: str) -> None:
        self._token = token.strip()
        self._headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }
        self._me: dict[str, Any] | None = None

    def verificar_token(self) -> dict[str, Any]:
        """Valida o token chamando GET /me. Retorna info do usuário ou erro."""
        try:
            resp = requests.get(f"{self.BASE}/me", headers=self._headers, timeout=10)
            resp.raise_for_status()
            self._me = resp.json()
            nome = self._me.get("displayName", "")
            email = self._me.get("mail") or self._me.get("userPrincipalName", "")
            return {
                "ok": True,
                "nome": nome,
                "email": email,
                "mensagem": f"Token valido — {nome} <{email}>",
            }
        except requests.HTTPError as exc:
            code = exc.response.status_code if exc.response is not None else "?"
            return {"ok": False, "nome": "", "email": "", "mensagem": f"Token invalido ou expirado (HTTP {code})."}
        except Exception as exc:
            return {"ok": False, "nome": "", "email": "", "mensagem": f"Erro ao verificar token: {exc}"}

    @property
    def remetente_email(self) -> str:
        if self._me:
            return self._me.get("mail") or self._me.get("userPrincipalName", "")
        return ""

    def enviar(
        self,
        para: list[str],
        assunto: str,
        corpo_html: str,
        cc: list[str] | None = None,
    ) -> dict[str, Any]:
        """Envia email. Retorna {"ok": bool, "mensagem": str}."""
        destinatarios = [addr.strip() for addr in para if addr.strip()]
        if not destinatarios:
            return {"ok": False, "mensagem": "Nenhum destinatario informado."}

        payload: dict[str, Any] = {
            "message": {
                "subject": assunto,
                "body": {"contentType": "HTML", "content": corpo_html},
                "toRecipients": [
                    {"emailAddress": {"address": addr}} for addr in destinatarios
                ],
            },
            "saveToSentItems": True,
        }
        if cc:
            cc_limpo = [addr.strip() for addr in cc if addr.strip()]
            if cc_limpo:
                payload["message"]["ccRecipients"] = [
                    {"emailAddress": {"address": addr}} for addr in cc_limpo
                ]

        try:
            resp = requests.post(
                f"{self.BASE}/me/sendMail",
                headers=self._headers,
                data=json.dumps(payload),
                timeout=15,
            )
            resp.raise_for_status()
            return {"ok": True, "mensagem": f"Email enviado para {', '.join(destinatarios)}."}
        except requests.HTTPError as exc:
            code = exc.response.status_code if exc.response is not None else "?"
            try:
                detalhe = exc.response.json().get("error", {}).get("message", "")
            except Exception:
                detalhe = ""
            return {"ok": False, "mensagem": f"Erro ao enviar (HTTP {code}): {detalhe}"}
        except Exception as exc:
            return {"ok": False, "mensagem": f"Erro: {exc}"}
