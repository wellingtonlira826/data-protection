"""
Agendador de varreduras periódicas — SQLite + APScheduler BackgroundScheduler.

Armazena configs de jobs em SQLite e re-registra ao iniciar.
O scheduler é criado como singleton via st.cache_resource no dashboard.
"""
from __future__ import annotations

import json
import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_SCHEDULE_DB = Path.home() / ".data-protection" / "schedules.db"

# Frequencias amigáveis → cron expression
FREQ_CRON = {
    "Diario":      "0 8 * * *",
    "Semanal":     "0 8 * * 1",
    "Mensal":      "0 8 1 * *",
}

DIA_SEMANA_NUM = {
    "Segunda": 1, "Terca": 2, "Quarta": 3,
    "Quinta": 4, "Sexta": 5, "Sabado": 6, "Domingo": 0,
}


def _cron_para_descricao(cron: str) -> str:
    partes = cron.split()
    if len(partes) != 5:
        return cron
    minuto, hora, dia_mes, mes, dia_sem = partes
    h = f"{int(hora):02d}:{int(minuto):02d}" if hora.isdigit() and minuto.isdigit() else f"{hora}:{minuto}"
    if dia_sem != "*" and dia_mes == "*":
        nomes = {str(v): k for k, v in DIA_SEMANA_NUM.items()}
        dia_nome = nomes.get(dia_sem, f"dia {dia_sem}")
        return f"Toda {dia_nome} as {h}"
    if dia_mes != "*":
        return f"Todo dia {dia_mes} as {h}"
    return f"Diariamente as {h}"


class ScanScheduler:
    """Gerencia agendamentos com persistência em SQLite + execução via APScheduler."""

    def __init__(self, db_path: Path = DEFAULT_SCHEDULE_DB) -> None:
        self._db = db_path
        self._db.parent.mkdir(parents=True, exist_ok=True)
        self._sched: Any = None
        self._disponivel = False
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self._db) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schedules (
                    id          TEXT PRIMARY KEY,
                    nome        TEXT NOT NULL,
                    tipo        TEXT NOT NULL DEFAULT 'jira',
                    projetos    TEXT NOT NULL DEFAULT '[]',
                    cron        TEXT NOT NULL,
                    url         TEXT NOT NULL DEFAULT '',
                    usuario     TEXT NOT NULL DEFAULT '',
                    token       TEXT NOT NULL DEFAULT '',
                    auto_acao   TEXT NOT NULL DEFAULT 'properties',
                    ativo       INTEGER NOT NULL DEFAULT 1,
                    criado_em   TEXT NOT NULL DEFAULT '',
                    ultimo_run  TEXT NOT NULL DEFAULT ''
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scan_results (
                    id               TEXT PRIMARY KEY,
                    schedule_id      TEXT NOT NULL,
                    executado_em     TEXT NOT NULL,
                    total_deteccoes  INTEGER NOT NULL DEFAULT 0,
                    total_secrets    INTEGER NOT NULL DEFAULT 0,
                    compliance_score INTEGER NOT NULL DEFAULT 100,
                    projetos_json    TEXT NOT NULL DEFAULT '[]'
                )
            """)
            conn.commit()

    def start(self) -> None:
        """Inicia o BackgroundScheduler e re-registra todos os jobs ativos."""
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            self._sched = BackgroundScheduler()
            self._sched.start()
            self._disponivel = True
            ativos = [j for j in self.listar() if j["ativo"]]
            for job in ativos:
                self._registrar(job)
            logger.info("ScanScheduler iniciado — %d job(s) ativos", len(ativos))
        except ImportError:
            logger.warning("APScheduler nao instalado — execute: pip install apscheduler>=3.10")
            self._disponivel = False

    @property
    def disponivel(self) -> bool:
        return self._disponivel

    def _registrar(self, job: dict) -> None:
        if not self._sched:
            return
        try:
            from apscheduler.triggers.cron import CronTrigger
            partes = job["cron"].split()
            if len(partes) != 5:
                return
            trigger = CronTrigger(
                minute=partes[0], hour=partes[1],
                day=partes[2], month=partes[3], day_of_week=partes[4],
            )
            self._sched.add_job(
                self._executar_job,
                trigger=trigger,
                args=[job["id"]],
                id=job["id"],
                name=job["nome"],
                replace_existing=True,
            )
        except Exception as exc:
            logger.error("Erro ao registrar job '%s': %s", job["nome"], exc)

    def _executar_job(self, job_id: str) -> None:
        jobs = self.listar()
        job = next((j for j in jobs if j["id"] == job_id), None)
        if not job:
            return
        try:
            from plugins.jira_plugin import JiraPlugin
            from plugins.scanner import scan_chunks, resumir
            from presidio_pt import build_analyzer

            plugin = JiraPlugin()
            res = plugin.conectar(job["url"], job["usuario"], job["token"])
            if not res["ok"]:
                logger.error("Job '%s': falha ao conectar — %s", job["nome"], res["message"])
                return

            analyzer = build_analyzer()
            total_d = total_s = 0
            scores: list[int] = []
            projetos: list[str] = json.loads(job["projetos"])

            for pkey in (projetos or [""]):
                issues = plugin.buscar_issues(pkey, max_total=1000)
                chunks: list[Any] = []
                for issue in issues:
                    chunks.extend(plugin.extrair_textos(issue))
                resultados = scan_chunks(chunks, analyzer)
                met = resumir(resultados)
                total_d += met.get("total_deteccoes", 0)
                total_s += met.get("total_secrets", 0)
                scores.append(met.get("compliance_score", 100))

            avg_score = round(sum(scores) / len(scores)) if scores else 100
            ts = datetime.now(timezone.utc).isoformat()

            with sqlite3.connect(self._db) as conn:
                conn.execute("""
                    INSERT INTO scan_results
                    (id, schedule_id, executado_em, total_deteccoes, total_secrets,
                     compliance_score, projetos_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (str(uuid.uuid4()), job_id, ts, total_d, total_s, avg_score,
                      job["projetos"]))
                conn.execute("UPDATE schedules SET ultimo_run = ? WHERE id = ?", (ts, job_id))
                conn.commit()

            logger.info("Job '%s' concluido: %d deteccoes, score=%d%%",
                        job["nome"], total_d, avg_score)
        except Exception as exc:
            logger.exception("Erro ao executar job '%s': %s", job["nome"], exc)

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def criar(
        self,
        nome: str,
        tipo: str,
        projetos: list[str],
        cron: str,
        url: str = "",
        usuario: str = "",
        token: str = "",
        auto_acao: str = "properties",
    ) -> str:
        job_id = str(uuid.uuid4())[:8]
        ts = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self._db) as conn:
            conn.execute("""
                INSERT INTO schedules
                (id, nome, tipo, projetos, cron, url, usuario, token, auto_acao, ativo, criado_em)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            """, (job_id, nome, tipo, json.dumps(projetos), cron, url, usuario, token, auto_acao, ts))
            conn.commit()
        job = self._row_para_dict(
            (job_id, nome, tipo, json.dumps(projetos), cron, url, usuario, token, auto_acao, 1, ts, "")
        )
        self._registrar(job)
        return job_id

    def listar(self) -> list[dict]:
        with sqlite3.connect(self._db) as conn:
            rows = conn.execute("""
                SELECT id, nome, tipo, projetos, cron, url, usuario, token,
                       auto_acao, ativo, criado_em, ultimo_run
                FROM schedules ORDER BY nome
            """).fetchall()
        return [self._row_para_dict(r) for r in rows]

    def remover(self, job_id: str) -> None:
        with sqlite3.connect(self._db) as conn:
            conn.execute("DELETE FROM schedules WHERE id = ?", (job_id,))
            conn.commit()
        if self._sched:
            try:
                self._sched.remove_job(job_id)
            except Exception:
                pass

    def pausar(self, job_id: str) -> None:
        with sqlite3.connect(self._db) as conn:
            conn.execute("UPDATE schedules SET ativo = 0 WHERE id = ?", (job_id,))
            conn.commit()
        if self._sched:
            try:
                self._sched.pause_job(job_id)
            except Exception:
                pass

    def retomar(self, job_id: str) -> None:
        with sqlite3.connect(self._db) as conn:
            conn.execute("UPDATE schedules SET ativo = 1 WHERE id = ?", (job_id,))
            conn.commit()
        jobs = self.listar()
        job = next((j for j in jobs if j["id"] == job_id), None)
        if job:
            self._registrar(job)

    def proximo_run(self, job_id: str) -> str:
        if not self._sched:
            return "APScheduler nao instalado"
        try:
            j = self._sched.get_job(job_id)
            if j and j.next_run_time:
                return j.next_run_time.strftime("%Y-%m-%d %H:%M")
        except Exception:
            pass
        return "—"

    def listar_resultados(self, schedule_id: str | None = None, limit: int = 20) -> list[dict]:
        with sqlite3.connect(self._db) as conn:
            if schedule_id:
                rows = conn.execute("""
                    SELECT r.executado_em, r.total_deteccoes, r.total_secrets,
                           r.compliance_score, s.nome, r.projetos_json
                    FROM scan_results r JOIN schedules s ON r.schedule_id = s.id
                    WHERE r.schedule_id = ?
                    ORDER BY r.executado_em DESC LIMIT ?
                """, (schedule_id, limit)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT r.executado_em, r.total_deteccoes, r.total_secrets,
                           r.compliance_score, s.nome, r.projetos_json
                    FROM scan_results r JOIN schedules s ON r.schedule_id = s.id
                    ORDER BY r.executado_em DESC LIMIT ?
                """, (limit,)).fetchall()
        return [
            {
                "executado_em": r[0], "total_deteccoes": r[1], "total_secrets": r[2],
                "compliance_score": r[3], "schedule_nome": r[4],
                "projetos": json.loads(r[5] or "[]"),
            }
            for r in rows
        ]

    @staticmethod
    def _row_para_dict(r: tuple) -> dict:
        return {
            "id": r[0], "nome": r[1], "tipo": r[2],
            "projetos": json.loads(r[3] or "[]"),
            "cron": r[4], "url": r[5], "usuario": r[6], "token": r[7],
            "auto_acao": r[8], "ativo": bool(r[9]),
            "criado_em": r[10], "ultimo_run": r[11],
            "descricao_freq": _cron_para_descricao(r[4]),
        }
