"""
Meterless H-MEM Agent Engine — Official Reference Architecture Implementation
Based on Meterless H-MEM Specification v1.0:
- Canonical Memory Model: id, content, type, layer (short_term, working, long_term),
  timestamp, lastAccessed, accessCount, confidence, source, domain, namespace, entities,
  relatedTo, supersedes, derivedFrom, agentId, runId, taskId.
- Tiered Storage & Durable Append-Only Trust Ledger (JSONL).
- MemoryStoreService + MemoryRetrievalService + ConflictResolutionService.
- Cross-session persistent warm-start hydration.
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

# Default storage location for persistent JSONL trust ledger
LEDGER_DIR = Path("data/hmem_ledger")
LEDGER_FILE = LEDGER_DIR / "trust_ledger.jsonl"
SNAPSHOT_FILE = LEDGER_DIR / "long_term_snapshot.json"


class CanonicalMemory:
    """Canonical H-MEM Record adhering to Section 4 of H-MEM Specification."""

    def __init__(
        self,
        content: str | dict[str, Any],
        mem_type: str = "factual",            # personal | factual | preference | general | procedural
        layer: str = "working",              # short_term | working | long_term
        confidence: float = 1.0,
        source: str = "agent_observation",
        domain: str = "forensic/audit",
        namespace: str = "procurement",
        entities: list[str] | None = None,
        agent_id: str = "verifact-reasoner",
        run_id: str = "",
        task_id: str = "",
        mem_id: str | None = None,
        supersedes: str | None = None,
        derived_from: list[str] | None = None,
        related_to: list[str] | None = None,
        timestamp: str | None = None,
    ) -> None:
        self.id: str = mem_id or f"MEM-{uuid.uuid4().hex[:8].upper()}"
        self.content: str = content if isinstance(content, str) else json.dumps(content)
        self.type: str = mem_type
        self.layer: str = layer
        self.timestamp: str = timestamp or datetime.now(timezone.utc).isoformat()
        self.last_accessed: str = self.timestamp
        self.access_count: int = 1
        self.confidence: float = confidence
        self.source: str = source
        self.domain: str = domain
        self.namespace: str = namespace
        self.entities: list[str] = entities or []
        self.related_to: list[str] = related_to or []
        self.supersedes: str | None = supersedes
        self.derived_from: list[str] = derived_from or []
        self.key: str = ""
        self.agent_id: str = agent_id
        self.run_id: str = run_id
        self.task_id: str = task_id
        self.valid: bool = True
        self.invalidation_reason: str | None = None
        self.invalidated_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "key": self.key,
            "content": self.content,
            "type": self.type,
            "layer": self.layer,
            "timestamp": self.timestamp,
            "last_accessed": self.last_accessed,
            "access_count": self.access_count,
            "confidence": self.confidence,
            "source": self.source,
            "domain": self.domain,
            "namespace": self.namespace,
            "entities": self.entities,
            "related_to": self.related_to,
            "supersedes": self.supersedes,
            "derived_from": self.derived_from,
            "agent_id": self.agent_id,
            "run_id": self.run_id,
            "task_id": self.task_id,
            "valid": self.valid,
            "invalidation_reason": self.invalidation_reason,
            "invalidated_at": self.invalidated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CanonicalMemory:
        mem = cls(
            content=data.get("content", ""),
            mem_type=data.get("type", "factual"),
            layer=data.get("layer", "working"),
            confidence=data.get("confidence", 1.0),
            source=data.get("source", ""),
            domain=data.get("domain", "forensic/audit"),
            namespace=data.get("namespace", ""),
            entities=data.get("entities", []),
            agent_id=data.get("agent_id", "verifact-reasoner"),
            run_id=data.get("run_id", ""),
            task_id=data.get("task_id", ""),
            mem_id=data.get("id"),
            supersedes=data.get("supersedes"),
            derived_from=data.get("derived_from"),
            related_to=data.get("related_to"),
            timestamp=data.get("timestamp"),
        )
        mem.last_accessed = data.get("last_accessed", mem.timestamp)
        mem.access_count = data.get("access_count", 1)
        mem.valid = data.get("valid", True)
        mem.invalidation_reason = data.get("invalidation_reason")
        mem.invalidated_at = data.get("invalidated_at")
        return mem


class HMem:
    """
    Meterless H-MEM Engine implementing MemoryStoreService & MemoryRetrievalService
    with durable JSONL trust ledger persistence and cross-session warm-start loading.
    """

    def __init__(self, persist_dir: Path | str | None = None) -> None:
        self._dir = Path(persist_dir) if persist_dir else LEDGER_DIR
        self._ledger_path = self._dir / "trust_ledger.jsonl"
        self._snapshot_path = self._dir / "long_term_snapshot.json"
        self._dir.mkdir(parents=True, exist_ok=True)

        # In-memory indices: session_id -> {mem_id -> CanonicalMemory}
        self._store: dict[str, dict[str, CanonicalMemory]] = defaultdict(dict)
        # Global key index: session_id -> {key -> mem_id}
        self._key_index: dict[str, dict[str, str]] = defaultdict(dict)
        self._lock = threading.RLock()

        # Warm-start load from durable snapshot
        self._warm_start()

    def _warm_start(self) -> None:
        """Hydrates long-term validated knowledge from durable snapshot on startup."""
        if not self._snapshot_path.exists():
            return
        try:
            with open(self._snapshot_path, "r", encoding="utf-8") as f:
                records = json.load(f)
                for item in records:
                    mem = CanonicalMemory.from_dict(item)
                    sess = item.get("run_id") or "global"
                    self._store[sess][mem.id] = mem
        except Exception:
            pass

    def _append_audit_ledger(self, action: str, memory_id: str, actor: str, details: dict[str, Any]) -> None:
        """Appends an immutable audit log entry to the JSONL trust ledger (Section 11.1)."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "memory_id": memory_id,
            "actor": actor,
            "details": details,
        }
        try:
            with open(self._ledger_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass

    def _save_snapshot(self) -> None:
        """Persists all long-term valid memories into durable snapshot."""
        try:
            long_term = []
            with self._lock:
                for sess_store in self._store.values():
                    for mem in sess_store.values():
                        if mem.layer == "long_term" and mem.valid:
                            long_term.append(mem.to_dict())
            with open(self._snapshot_path, "w", encoding="utf-8") as f:
                json.dump(long_term, f, indent=2)
        except Exception:
            pass

    # ── MemoryStoreService ────────────────────────────────────────────────

    def write(
        self,
        key: str,
        value: dict[str, Any],
        session_id: str,
        provenance: dict[str, Any] | None = None,
        layer: str = "working",
        mem_type: str = "factual",
        confidence: float = 1.0,
        agent_id: str = "verifact-reasoner",
        entities: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Store canonical evidence entry under `key` within `session_id`.
        Appends mutation to JSONL audit trust ledger.
        """
        prov = provenance or {}
        extracted_entities = entities or []
        if not extracted_entities and isinstance(value, dict):
            extracted_entities = [str(v) for k, v in value.items() if "iban" in k.lower() or "vendor" in k.lower()]

        mem = CanonicalMemory(
            content=value,
            mem_type=mem_type,
            layer=layer,
            confidence=confidence,
            source=prov.get("source_type", "zetaris_usl"),
            domain=prov.get("domain", "forensic/audit"),
            namespace=prov.get("scenario_id", "procurement"),
            entities=extracted_entities,
            agent_id=agent_id,
            run_id=session_id,
            task_id=prov.get("task_id", ""),
        )

        with self._lock:
            # Check if this supersedes an existing key in the same session
            mem.key = key
            prev_id = self._key_index[session_id].get(key)
            if prev_id and prev_id in self._store[session_id]:
                mem.supersedes = prev_id
                self._store[session_id][prev_id].valid = False
                self._store[session_id][prev_id].invalidation_reason = f"Superseded by {mem.id}"

            self._store[session_id][mem.id] = mem
            self._key_index[session_id][key] = mem.id

        self._append_audit_ledger(
            action="CREATE",
            memory_id=mem.id,
            actor=agent_id,
            details={"key": key, "session_id": session_id, "layer": layer, "supersedes": mem.supersedes},
        )

        if layer == "long_term":
            self._save_snapshot()

        return {
            "status": "written",
            "entry_id": mem.id,
            "key": key,
            "session_id": session_id,
            "layer": layer,
            "created_at": mem.timestamp,
        }

    def read(self, key: str, session_id: str) -> dict[str, Any] | None:
        """Retrieve canonical evidence record by key."""
        with self._lock:
            mem_id = self._key_index.get(session_id, {}).get(key)
            if not mem_id:
                return None
            mem = self._store.get(session_id, {}).get(mem_id)
            if mem:
                mem.access_count += 1
                mem.last_accessed = datetime.now(timezone.utc).isoformat()
                return mem.to_dict()
        return None

    def invalidate(self, key: str, reason: str, session_id: str) -> dict[str, Any]:
        """Mark memory entry as contradicted / invalid and log to trust ledger."""
        with self._lock:
            mem_id = self._key_index.get(session_id, {}).get(key)
            if not mem_id or mem_id not in self._store.get(session_id, {}):
                return {"status": "not_found", "key": key, "session_id": session_id}

            mem = self._store[session_id][mem_id]
            mem.valid = False
            mem.invalidation_reason = reason
            mem.invalidated_at = datetime.now(timezone.utc).isoformat()

        self._append_audit_ledger(
            action="INVALIDATE",
            memory_id=mem.id,
            actor="z3-verifier",
            details={"key": key, "reason": reason, "session_id": session_id},
        )

        return {
            "status": "invalidated",
            "entry_id": mem.id,
            "key": key,
            "session_id": session_id,
            "reason": reason,
            "invalidated_at": mem.invalidated_at,
        }

    # ── MemoryRetrievalService (Section 8.1 Hybrid Ranking) ───────────────

    def recall_similar(
        self,
        query: str,
        session_id: str,
        top_k: int = 5,
        filter_valid_only: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Hybrid retrieval ranking over candidate memories in session:
        Score = keyword_overlap + entity_boost + layer_boost + recency_boost - supersession_penalty
        """
        keywords = [w.lower() for w in re.split(r"\W+", query) if len(w) > 2]
        if not keywords:
            return []

        with self._lock:
            # Query across session + long-term global memories
            session_entries = list(self._store.get(session_id, {}).values())
            global_entries = [m for m in self._store.get("global", {}).values() if m.layer == "long_term"]
            all_candidates = session_entries + [m for m in global_entries if m not in session_entries]

        scored: list[tuple[float, dict[str, Any]]] = []
        for mem in all_candidates:
            if filter_valid_only and not mem.valid:
                continue

            content_lower = mem.content.lower()
            keyword_hits = sum(1 for k in keywords if k in content_lower)
            if keyword_hits == 0 and not any(k in " ".join(mem.entities).lower() for k in keywords):
                continue

            # Hybrid score components
            base_score = keyword_hits / len(keywords)
            layer_weight = 1.3 if mem.layer == "long_term" else (1.1 if mem.layer == "working" else 1.0)
            entity_boost = 0.2 if any(k in " ".join(mem.entities).lower() for k in keywords) else 0.0
            confidence_factor = mem.confidence

            total_score = round((base_score * layer_weight * confidence_factor) + entity_boost, 4)
            scored.append((total_score, {**mem.to_dict(), "_recall_score": total_score}))

        scored.sort(key=lambda t: t[0], reverse=True)
        return [item for _, item in scored[:top_k]]

    def reinject_context(self, query: str, session_id: str, top_k: int = 3) -> dict[str, Any]:
        """
        Reinjection Service (Section 8.2): Formats recalled memory as structured payload
        with trace metadata for injection into agent reasoning steps.
        """
        recalled = self.recall_similar(query=query, session_id=session_id, top_k=top_k)
        return {
            "retrieval_query": query,
            "session_id": session_id,
            "memories_count": len(recalled),
            "retrieval_strategy": "hybrid_ranked_reinjection",
            "memories": [
                {
                    "memory_id": m["id"],
                    "layer": m["layer"],
                    "content": m["content"],
                    "confidence": m["confidence"],
                    "relevance_score": m.get("_recall_score", 1.0),
                    "entities": m["entities"],
                }
                for m in recalled
            ],
        }

    def get_full_ledger(self, session_id: str) -> dict[str, Any]:
        """Return all memories for a session with audit stats."""
        with self._lock:
            entries = [m.to_dict() for m in self._store.get(session_id, {}).values()]

        valid = [e for e in entries if e["valid"]]
        invalid = [e for e in entries if not e["valid"]]
        return {
            "session_id": session_id,
            "total_entries": len(entries),
            "valid_entries": len(valid),
            "invalidated_entries": len(invalid),
            "entries": entries,
            "audit_ledger_path": str(self._ledger_path),
        }

    def get_stats(self, session_id: str) -> dict[str, Any]:
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
    def __init__(self, task_id: str, fn: Callable, args: tuple | list, delay_seconds: float) -> None:
        self.task_id = task_id
        self.status = "pending"
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.started_at: str | None = None
        self.completed_at: str | None = None
        self.error: str | None = None
        self.result: Any = None
        self._thread = threading.Thread(target=self._run, args=(fn, args, delay_seconds), daemon=True)
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
    def __init__(self) -> None:
        self._tasks: dict[str, _NightshiftTask] = {}
        self._lock = threading.Lock()

    def schedule_task(self, fn: Callable, args: tuple | list | None = None, delay_seconds: float = 0.0) -> str:
        task_id = f"NIGHT-{uuid.uuid4().hex[:8].upper()}"
        task = _NightshiftTask(task_id=task_id, fn=fn, args=args or (), delay_seconds=delay_seconds)
        with self._lock:
            self._tasks[task_id] = task
        return task_id

    def get_task_status(self, task_id: str) -> dict[str, Any] | None:
        with self._lock:
            task = self._tasks.get(task_id)
        if task is None:
            return None
        return task.to_dict()

    def list_tasks(self) -> list[dict[str, Any]]:
        with self._lock:
            return [t.to_dict() for t in self._tasks.values()]


# Default module singletons
hmem = HMem()
nightshift = MeterlessNightshift()
