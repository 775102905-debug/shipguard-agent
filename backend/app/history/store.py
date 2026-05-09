import sqlite3
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from ..core.config import settings
from .models import HistoryRecord

logger = logging.getLogger(__name__)

_HISTORY_DB_DIR = settings.ROOT_DIR / "data"
_HISTORY_DB_PATH = _HISTORY_DB_DIR / "shipguard_history.sqlite"


def _get_db() -> sqlite3.Connection:
    _HISTORY_DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_HISTORY_DB_PATH))
    conn.row_factory = sqlite3.Row
    _init_table(conn)
    return conn


def _init_table(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS history (
            report_id TEXT PRIMARY KEY,
            project_alias TEXT,
            project_fingerprint TEXT,
            review_mode TEXT,
            verdict TEXT,
            score INTEGER,
            dimension_scores TEXT,
            findings_summary TEXT,
            top_security_findings TEXT,
            top_structure_findings TEXT,
            top_dependency_findings TEXT,
            top_readme_findings TEXT,
            commercial_fix_plan TEXT,
            interview_notes TEXT,
            project_type TEXT,
            detected_languages TEXT,
            redaction_version TEXT,
            created_at TEXT
        )
    """)
    conn.commit()


def save_record(record: HistoryRecord) -> str:
    try:
        conn = _get_db()
        conn.execute("""
            INSERT OR REPLACE INTO history (
                report_id, project_alias, project_fingerprint, review_mode,
                verdict, score, dimension_scores, findings_summary,
                top_security_findings, top_structure_findings,
                top_dependency_findings, top_readme_findings,
                commercial_fix_plan, interview_notes,
                project_type, detected_languages, redaction_version, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.report_id,
            record.project_alias,
            record.project_fingerprint,
            record.review_mode,
            record.verdict,
            record.score,
            json.dumps(record.dimension_scores),
            json.dumps(record.findings_summary),
            json.dumps(record.top_security_findings),
            json.dumps(record.top_structure_findings),
            json.dumps(record.top_dependency_findings),
            json.dumps(record.top_readme_findings),
            record.commercial_fix_plan,
            record.interview_notes,
            record.project_type,
            json.dumps(record.detected_languages),
            record.redaction_version,
            record.created_at,
        ))
        conn.commit()
        conn.close()
        return record.report_id
    except Exception as e:
        logger.warning(f"History save failed (non-blocking): {e}")
        return ""


def list_reports(limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
    try:
        conn = _get_db()
        rows = conn.execute(
            "SELECT report_id, project_alias, review_mode, verdict, score, "
            "findings_summary, created_at FROM history ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.warning(f"History list failed: {e}")
        return []


def get_report(report_id: str) -> Optional[Dict[str, Any]]:
    try:
        conn = _get_db()
        row = conn.execute(
            "SELECT * FROM history WHERE report_id = ?", (report_id,)
        ).fetchone()
        conn.close()
        if row is None:
            return None
        d = dict(row)
        for field in ["dimension_scores", "findings_summary",
                       "top_security_findings", "top_structure_findings",
                       "top_dependency_findings", "top_readme_findings",
                       "detected_languages"]:
            if isinstance(d.get(field), str):
                d[field] = json.loads(d[field])
        return d
    except Exception as e:
        logger.warning(f"History get failed: {e}")
        return None


def get_total_count() -> int:
    try:
        conn = _get_db()
        count = conn.execute("SELECT COUNT(*) FROM history").fetchone()[0]
        conn.close()
        return count
    except Exception:
        return 0


def clear_all() -> int:
    try:
        conn = _get_db()
        count = conn.execute("DELETE FROM history").rowcount
        conn.commit()
        conn.close()
        return count
    except Exception as e:
        logger.warning(f"History clear failed: {e}")
        return 0
