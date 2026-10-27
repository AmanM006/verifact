"""
Meterless H-MEM — Hierarchical Memory Engine
In-memory evidence ledger with session namespacing, provenance tracking,
keyword-similarity recall, invalidation, and background task scheduling.
"""

from __future__ import annotations

import re
import threading
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Callable


# ──────────────────────────────────────────────────────────────────────────────
# Evidence Ledger Entry
# ──────────────────────────────────────────────────────────────────────────────

class LedgerEntry:
    """A single persisted evidence record within a session."""

    def __init__(
        self,
        key: str,
        value: dict[str, Any],
        session_id: str,
        provenance: dict[str, Any],
    ) -> None:
        self.entry_id: str = f"HMEM-{uuid.uuid4().hex[:8].upper()}"
        self.key: str = key
        self.value: dict[str, Any] = value
        self.session_id: str = session_id
        self.provenance: dict[str, Any] = provenance
        self.created_at: str = datetime.now(timezone.utc).isoformat()
        self.valid: bool = True
        self.invalidation_reason: str | None = None
        self.invalidated_at: str | None = None
        # Pre-compute searchable text for recall
        self._search_text: str = self._build_search_text()

    def _build_search_text(self) -> str:
        parts: list[str] = [self.key]
        for v in self.value.values():
            parts.append(str(v))
        for v in self.provenance.values():
            parts.append(str(v))
        return " ".join(parts).lower()

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "key": self.key,
            "value": self.value,
            "session_id": self.session_id,
            "provenance": self.provenance,
            "created_at": self.created_at,
            "valid": self.valid,
            "invalidation_reason": self.invalidation_reason,
            "invalidated_at": self.invalidated_at,
        }


# ──────────────────────────────────────────────────────────────────────────────
# H-MEM Engine
# ──────────────────────────────────────────────────────────────────────────────

class HMem:
    """
    Meterless Hierarchical Memory Engine.
    Thread-safe in-memory evidence store with session namespacing.
    """

    def __init__(self) -> None:
        # session_id → {key → LedgerEntry}
        self._store: dict[str, dict[str, LedgerEntry]] = defaultdict(dict)
        self._lock = threading.RLock()

    # ── Core CRUD ──────────────────────────────────────────────────────────

    def write(
        self,
        key: str,
        value: dict[str, Any],
        session_id: str,
        provenance: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Store an evidence entry under `key` within `session_id`.
        Overwrites any existing entry for the same key.
        Returns the stored entry metadata.
        """
        entry = LedgerEntry(key=key, value=value, session_id=session_id, provenance=provenance)
        with self._lock:
            self._store[session_id][key] = entry
        return {
            "status": "written",
            "entry_id": entry.entry_id,
            "key": key,
            "session_id": session_id,
            "created_at": entry.created_at,
        }

    def read(self, key: str, session_id: str) -> dict[str, Any] | None:
        """
        Retrieve evidence entry by exact key within session.
        Returns None if not found.
        """
        with self._lock:
            entry = self._store.get(session_id, {}).get(key)
        if entry is None:
            return None
        return entry.to_dict()

    def recall_similar(
        self,
        query: str,
        session_id: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Keyword-similarity recall over all entries in session.
        Scores each entry by fraction of query keywords matched.
        Returns top_k entries sorted by descending relevance.
        """
        keywords = [w.lower() for w in re.split(r"\W+", query) if len(w) > 2]
        if not keywords:
            return []

        with self._lock:
            entries = list(self._store.get(session_id, {}).values())

        scored: list[tuple[float, dict[str, Any]]] = []
        for entry in entries:
            if not entry.valid:
                continue
            hits = sum(1 for k in keywords if k in entry._search_text)
            score = hits / len(keywords)
            if score > 0:
                scored.append((score, {**entry.to_dict(), "_recall_score": round(score, 4)}))

        scored.sort(key=lambda t: t[0], reverse=True)
        return [item for _, item in scored[:top_k]]

    def get_full_ledger(self, session_id: str) -> dict[str, Any]:
        """Return all entries (valid and invalid) for a session."""
        with self._lock:
            entries = [e.to_dict() for e in self._store.get(session_id, {}).values()]

        valid = [e for e in entries if e["valid"]]
        invalid = [e for e in entries if not e["valid"]]
        return {
            "session_id": session_id,
            "total_entries": len(entries),
            "valid_entries": len(valid),
            "invalidated_entries": len(invalid),
            "entries": entries,
        }

    def invalidate(self, key: str, reason: str, session_id: str) -> dict[str, Any]:
        """
        Mark an evidence entry as contradicted/invalidated.
        The entry is retained in the ledger but flagged as invalid.
        """
        with self._lock:
            entry = self._store.get(session_id, {}).get(key)
            if entry is None:
                return {"status": "not_found", "key": key, "session_id": session_id}
            entry.valid = False
            entry.invalidation_reason = reason
            entry.invalidated_at = datetime.now(timezone.utc).isoformat()

        return {
            "status": "invalidated",
            "entry_id": entry.entry_id,
            "key": key,
            "session_id": session_id,
            "reason": reason,
            "invalidated_at": entry.invalidated_at,
        }

    def get_stats(self, session_id: str) -> dict[str, Any]:
        """Return lightweight stats for a session without full ledger dump."""
        with self._lock:
            entries = list(self._store.get(session_id, {}).values())
        return {
            "session_id": session_id,
            "total": len(entries),
            "valid": sum(1 for e in entries if e.valid),
            "invalidated": sum(1 for e in entries if not e.valid),
        }


# ──────────────────────────────────────────────────────────────────────────────
# Meterless Nightshift — Background Task Scheduler
# ──────────────────────────────────────────────────────────────────────────────

class _NightshiftTask:
    """Internal task record for Nightshift scheduler."""

    def __init__(
        self,
        task_id: str,
        fn: Callable,
        args: tuple | list,
        delay_seconds: float,
    ) -> None:
        self.task_id = task_id
        self.status = "pending"
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.started_at: str | None = None
        self.completed_at: str | None = None
        self.error: str | None = None
        self.result: Any = None
        self._thread = threading.Thread(
            target=self._run,
            args=(fn, args, delay_seconds),
            daemon=True,
        )
        self._thread.start()

    def _run(self, fn: Callable, args: tuple | list, delay: float) -> None:
        time.sleep(delay)
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.status = "running"
        try:
            self.result = fn(*args)
            self.status = "completed"
        except Exception as exc:
            self.error = str(exc)
            self.status = "failed"
        self.completed_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.status,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error": self.error,
            "result": self.result,
        }


class MeterlessNightshift:
    """
    Meterless Nightshift — lightweight background task scheduler.
    Used for monitoring and deferred analysis tasks.
    """

    def __init__(self) -> None:
        self._tasks: dict[str, _NightshiftTask] = {}
        self._lock = threading.Lock()

    def schedule_task(
        self,
        fn: Callable,
        args: tuple | list,
        delay_seconds: float = 0.0,
    ) -> str:
        """
        Schedule `fn(*args)` to run after `delay_seconds`.
        Returns task_id for status polling.
        """
        task_id = f"NIGHT-{uuid.uuid4().hex[:8].upper()}"
        task = _NightshiftTask(
            task_id=task_id,
            fn=fn,
            args=args,
            delay_seconds=delay_seconds,
        )
        with self._lock:
            self._tasks[task_id] = task
        return task_id

    def get_task_status(self, task_id: str) -> dict[str, Any]:
        """Return current status and result of a scheduled task."""
        with self._lock:
            task = self._tasks.get(task_id)
        if task is None:
            return {"task_id": task_id, "status": "not_found"}
        return task.to_dict()

    def list_tasks(self) -> list[dict[str, Any]]:
        """Return status of all scheduled tasks."""
        with self._lock:
            return [t.to_dict() for t in self._tasks.values()]


# ──────────────────────────────────────────────────────────────────────────────
# Singleton instances
# ──────────────────────────────────────────────────────────────────────────────

hmem = HMem()
nightshift = MeterlessNightshift()
