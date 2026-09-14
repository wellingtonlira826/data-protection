"""
Persistência de estado de varreduras via SQLite.
Rastreia última execução por fonte (jira/confluence) e chave (project key / space key).
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

DEFAULT_DB_PATH: Path = Path.home() / ".data-protection" / "scan_state.db"


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scan_state (
            source       TEXT    NOT NULL,
            key          TEXT    NOT NULL,
            last_scan    TEXT    NOT NULL,
            total_items  INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (source, key)
        )
    """)
    conn.commit()


@contextmanager
def _connect(path: Path) -> Generator[sqlite3.Connection, None, None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    try:
        _init_schema(conn)
        yield conn
        conn.commit()
    finally:
        conn.close()


class ScanStateStore:
    """Gerencia estado persistente de varreduras incrementais."""

    def __init__(self, db_path: Path | str | None = None) -> None:
        self.db_path: Path = Path(db_path) if db_path else DEFAULT_DB_PATH

    def get_last_scan(self, source: str, key: str) -> datetime | None:
        """Retorna datetime UTC do último scan, ou None se nunca escaneado."""
        with _connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT last_scan FROM scan_state WHERE source = ? AND key = ?",
                (source, key),
            ).fetchone()
        if not row:
            return None
        return datetime.fromisoformat(row[0])

    def set_last_scan(
        self,
        source: str,
        key: str,
        dt: datetime | None = None,
        total_items: int = 0,
    ) -> None:
        """Grava ou atualiza timestamp do último scan."""
        ts = (dt or datetime.now(timezone.utc)).isoformat()
        with _connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO scan_state (source, key, last_scan, total_items)
                VALUES (?, ?, ?, ?)
                ON CONFLICT (source, key) DO UPDATE SET
                    last_scan   = excluded.last_scan,
                    total_items = excluded.total_items
                """,
                (source, key, ts, total_items),
            )

    def list_all(self) -> list[dict[str, str | int]]:
        """Lista todos os estados de scan registrados."""
        with _connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT source, key, last_scan, total_items "
                "FROM scan_state ORDER BY last_scan DESC"
            ).fetchall()
        return [
            {"source": r[0], "key": r[1], "last_scan": r[2], "total_items": r[3]}
            for r in rows
        ]

    def clear(self, source: str, key: str) -> None:
        """Remove estado para forçar rescan completo na próxima execução."""
        with _connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM scan_state WHERE source = ? AND key = ?",
                (source, key),
            )

    def last_scan_date_str(self, source: str, key: str) -> str | None:
        """Retorna a data do último scan no formato YYYY-MM-DD (para uso em JQL/CQL)."""
        dt = self.get_last_scan(source, key)
        if dt is None:
            return None
        return dt.strftime("%Y-%m-%d")

    # ── Historico executivo ───────────────────────────────────────────────────

    def _init_historico(self, conn: sqlite3.Connection) -> None:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS historico_execucoes (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp        TEXT    NOT NULL,
                mes_ano          TEXT    NOT NULL,
                fonte            TEXT    NOT NULL,
                projetos         TEXT    NOT NULL DEFAULT '',
                total_deteccoes  INTEGER NOT NULL DEFAULT 0,
                alto             INTEGER NOT NULL DEFAULT 0,
                medio            INTEGER NOT NULL DEFAULT 0,
                baixo            INTEGER NOT NULL DEFAULT 0,
                secrets          INTEGER NOT NULL DEFAULT 0,
                compliance_score REAL    NOT NULL DEFAULT 0.0,
                entidades_json   TEXT    NOT NULL DEFAULT '[]'
            )
        """)
        conn.commit()

    def salvar_execucao(
        self,
        fonte: str,
        projetos: str,
        total: int,
        alto: int,
        medio: int,
        baixo: int,
        secrets: int,
        compliance_score: float = 0.0,
        entidades: list[str] | None = None,
        ts: datetime | None = None,
    ) -> None:
        import json as _json
        _ts = (ts or datetime.now(timezone.utc))
        _mes_ano = _ts.strftime("%Y-%m")
        with _connect(self.db_path) as conn:
            self._init_historico(conn)
            conn.execute(
                """INSERT INTO historico_execucoes
                   (timestamp, mes_ano, fonte, projetos, total_deteccoes,
                    alto, medio, baixo, secrets, compliance_score, entidades_json)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    _ts.isoformat(), _mes_ano, fonte, projetos,
                    total, alto, medio, baixo, secrets,
                    round(compliance_score, 1),
                    _json.dumps(entidades or [], ensure_ascii=False),
                ),
            )

    def listar_historico(self, limit: int = 200) -> list[dict]:
        import json as _json
        try:
            with _connect(self.db_path) as conn:
                self._init_historico(conn)
                rows = conn.execute(
                    """SELECT timestamp, mes_ano, fonte, projetos,
                              total_deteccoes, alto, medio, baixo,
                              secrets, compliance_score, entidades_json
                       FROM historico_execucoes
                       ORDER BY timestamp DESC LIMIT ?""",
                    (limit,),
                ).fetchall()
        except Exception:
            return []
        return [
            {
                "timestamp": r[0], "mes_ano": r[1], "fonte": r[2],
                "projetos": r[3], "total_deteccoes": r[4],
                "alto": r[5], "medio": r[6], "baixo": r[7],
                "secrets": r[8], "compliance_score": r[9],
                "entidades": _json.loads(r[10]),
            }
            for r in rows
        ]

    def agregar_por_mes(self) -> list[dict]:
        """Agrega execuções por mês para gráficos de tendência."""
        try:
            with _connect(self.db_path) as conn:
                self._init_historico(conn)
                rows = conn.execute(
                    """SELECT mes_ano,
                              SUM(total_deteccoes), SUM(alto), SUM(medio),
                              SUM(baixo), SUM(secrets),
                              AVG(compliance_score), COUNT(*)
                       FROM historico_execucoes
                       GROUP BY mes_ano
                       ORDER BY mes_ano ASC"""
                ).fetchall()
        except Exception:
            return []
        return [
            {
                "mes_ano": r[0], "total": r[1], "alto": r[2],
                "medio": r[3], "baixo": r[4], "secrets": r[5],
                "compliance_score": round(r[6], 1), "varreduras": r[7],
            }
            for r in rows
        ]

    def top_entidades(self, limit: int = 12) -> list[dict]:
        """Conta frequência de cada entidade no histórico."""
        import json as _json
        from collections import Counter
        try:
            with _connect(self.db_path) as conn:
                self._init_historico(conn)
                rows = conn.execute(
                    "SELECT entidades_json FROM historico_execucoes"
                ).fetchall()
        except Exception:
            return []
        counter: Counter[str] = Counter()
        for (ej,) in rows:
            try:
                for e in _json.loads(ej):
                    counter[e] += 1
            except Exception:
                pass
        return [{"entidade": k, "count": v} for k, v in counter.most_common(limit)]

    def agregar_por_fonte(self) -> list[dict]:
        """Soma detecções agrupadas por fonte."""
        try:
            with _connect(self.db_path) as conn:
                self._init_historico(conn)
                rows = conn.execute(
                    """SELECT fonte, SUM(total_deteccoes), COUNT(*)
                       FROM historico_execucoes GROUP BY fonte"""
                ).fetchall()
        except Exception:
            return []
        return [{"fonte": r[0], "total": r[1], "varreduras": r[2]} for r in rows]
