"""
Zetaris Networked Data Platform — Simulated USL (Universal Semantic Layer)
Provides a virtual federated query layer over 3 synthetic data sources:
  - Source 1: erp_transactions  (SQLite in-memory)
  - Source 2: comms_audit       (dict-based, Slack / email / metrics / git logs)
  - Source 3: documents         (dict-based, PDF extracts with bbox provenance)
"""

from __future__ import annotations

import re
import sqlite3
import time
import uuid
from typing import Any

# ──────────────────────────────────────────────────────────────────────────────
# Synthetic data embedded directly in the client
# ──────────────────────────────────────────────────────────────────────────────

_ERP_SCHEMA = """
CREATE TABLE IF NOT EXISTS erp_transactions (
    row_id          INTEGER PRIMARY KEY,
    record_type     TEXT,
    scenario_id     TEXT,
    ref_number      TEXT,
    vendor          TEXT,
    iban            TEXT,
    sku             TEXT,
    quantity        INTEGER,
    amount          REAL,
    currency        TEXT DEFAULT 'USD',
    status          TEXT,
    actor           TEXT,
    event_date      TEXT,
    notes           TEXT
);
"""

_ERP_ROWS = [
    # ── Scenario 1: procurement_fraud ──────────────────────────────────────
    (1001, "purchase_order",   "procurement_fraud",  "PO-2024-1001",  "Apex Supplies Ltd",      "GB29NWBK60161331926819", None,       None,   42000.00,   "USD", "Authorized", "CFO-jenkins",  "2024-09-14", "IBAN ending 8821 — originally authorized"),
    (2047, "payment_dispatch", "procurement_fraud",  "PAY-2024-2047", "Apex Supplies Ltd",      "DE89370400440532013304", None,       None,   94750.00,   "USD", "Dispatched", "AP-system",    "2024-09-19", "IBAN ending 3304 — different from PO! Overpayment $52,750"),
    # ── Scenario 2: sla_breach_coverup ────────────────────────────────────
    (5001, "sla_contract_ref", "sla_breach_coverup", "SLA-PAYMENTS-2024", None,                 None,                     None,       None,   15000.00,   "USD", "Active",     "legal",        "2024-01-01", "Penalty rate $15,000/hr for p99 > 500ms over 2 min"),
    (5002, "penalty_invoice",  "sla_breach_coverup", "PENALTY-OCT2024",   "CloudVendor Inc",    None,                     None,       None,    5750.00,   "USD", "Pending",    "finance",      "2024-10-15", "23-min breach × $250/min = $5,750 penalty"),
    # ── Scenario 3: supply_chain_ghosting ─────────────────────────────────
    (3301, "purchase_order",   "supply_chain_ghosting","PO-2024-3301", "Horizon Manufacturing", None,                 "SKU-7821", 45000, 2300000.00, "USD", "Paid",       "procurement",  "2024-10-01", "Full pre-payment before shipment"),
    (3401, "payment",          "supply_chain_ghosting","PAY-2024-3401","Horizon Manufacturing", None,                 "SKU-7821", 45000, 2300000.00, "USD", "Cleared",    "finance",      "2024-10-08", "Payment cleared Oct 8, ship departed Oct 12"),
    (3501, "warehouse_receipt","supply_chain_ghosting","WH-LA-WEST-07","Horizon Manufacturing", None,                 "SKU-7821", 31200,       None,  None,  "Received",   "W. Okonkwo",   "2024-10-24", "31,200 received vs 38,500 post-customs expected"),
]

_COMMS_DATA: dict[str, list[dict[str, Any]]] = {
    "procurement_fraud": [
        {
            "id": "SLK-4471",
            "record_type": "slack_message",
            "channel": "#finance-approvals",
            "author": "CFO-jenkins",
            "timestamp": "2024-09-18T11:42:00Z",
            "content": "Approved vendor change per email thread #4471 — updated banking details for Apex. Proceed with payment.",
            "reactions": 2,
        },
        {
            "id": "EMAIL-4471",
            "record_type": "email_thread",
            "subject": "Apex Supplies banking update",
            "thread_id": "4471",
            "status": "NOT_FOUND",
            "content": "Thread #4471 does not exist in the email archive. Search returned 0 results.",
            "timestamp": None,
        },
        {
            "id": "SLK-4472",
            "record_type": "slack_message",
            "channel": "#finance-approvals",
            "author": "AP-clerk-santos",
            "timestamp": "2024-09-19T08:15:00Z",
            "content": "Processing PAY-2024-2047 for Apex Supplies — $94,750 to updated IBAN as per CFO approval SLK-4471.",
            "reactions": 0,
        },
    ],
    "sla_breach_coverup": [
        {
            "id": "PD-2024-8821",
            "record_type": "pagerduty_incident",
            "service": "payments-api",
            "severity": "P1",
            "fired_at": "2024-10-15T14:23:07Z",
            "acked_at": "2024-10-15T14:27:33Z",
            "resolved_at": "2024-10-15T14:46:02Z",
            "content": "P1 alert: payments-api high latency — p99 exceeded threshold.",
        },
        {
            "id": "GRF-PAYMENTS-P99",
            "record_type": "grafana_metric_export",
            "metric": "http_request_duration_p99",
            "service": "payments-api",
            "data_points": [
                {"ts": "2024-10-15T14:22:45Z", "value_ms": 45},
                {"ts": "2024-10-15T14:22:51Z", "value_ms": 8200},
                {"ts": "2024-10-15T14:23:07Z", "value_ms": 9400},
                {"ts": "2024-10-15T14:46:02Z", "value_ms": 52},
            ],
            "content": "p99 spiked to 8,200ms at 14:22:51 — 16 seconds BEFORE PagerDuty alert at 14:23:07.",
        },
        {
            "id": "GIT-a7f3c19",
            "record_type": "git_commit",
            "sha": "a7f3c19",
            "author": "j.malik",
            "timestamp": "2024-10-15T14:21:33Z",
            "message": "hotfix: disable connection pool limits temporarily",
            "files": ["config/payments-api/pool.yaml"],
            "approvals": ["r.chen"],
            "required_approvals": 2,
            "content": "Connection pool limits disabled. 1 of 2 required approvals obtained. Runbook RB-007 violated.",
        },
        {
            "id": "AUDIT-DEPLOY-14213",
            "record_type": "audit_log",
            "actor": "j.malik",
            "action": "config_deploy",
            "timestamp": "2024-10-15T14:21:33Z",
            "approval_count": 1,
            "required_approvals": 2,
            "content": "Deployment proceeded with insufficient approvals. Policy violation documented.",
        },
    ],
    "supply_chain_ghosting": [
        {
            "id": "CUSTOMS-LA-OCT22",
            "record_type": "customs_clearance",
            "port": "Los Angeles",
            "cleared_at": "2024-10-22",
            "sku": "SKU-7821",
            "qty_cleared": 38500,
            "qty_manifest": 45000,
            "discrepancy": -6500,
            "loss_declaration": None,
            "officer_id": "CBP-4421",
            "content": "6,500 unit shortfall at customs. No loss/damage declaration filed.",
        },
        {
            "id": "INS-CLAIM-2024-1188",
            "record_type": "insurance_claim",
            "claimant": "Horizon Manufacturing",
            "policy": "Marine Cargo CMC-44210",
            "qty_claimed": 2100,
            "value_claimed": 107331.00,
            "actual_discrepancy": 13800,
            "filed_at": "2024-10-25",
            "content": "Claim for 2,100 units filed; actual missing = 13,800 units. Underreported by 11,700 units.",
        },
    ],
}

_DOCUMENTS_DATA: dict[str, list[dict[str, Any]]] = {
    "procurement_fraud": [
        {
            "doc_id": "INV-APEX-2024-09",
            "doc_type": "invoice_pdf",
            "filename": "apex_invoice_sep2024.pdf",
            "page": 1,
            "bbox": [72, 180, 540, 220],
            "text": (
                "INVOICE | Apex Supplies Ltd | Suite 400, 55 Water St, New York, NY 10041 | "
                "Invoice #: INV-7821 | Date: 2024-09-17 | Amount Due: $94,750.00 | "
                "IBAN: DE89370400440532013304"
            ),
        },
        {
            "doc_id": "EDGAR-55WATER-ST",
            "doc_type": "sec_edgar_lookup",
            "filename": "sec_edgar_results.html",
            "page": 1,
            "bbox": [0, 0, 800, 80],
            "text": (
                "SEC EDGAR Entity Search | Address: Suite 400, 55 Water St, New York, NY 10041 | "
                "Registered Entity: TechNova LLC | EIN: 83-4421109 | "
                "Apex Supplies Ltd — NOT registered at this address."
            ),
        },
    ],
    "sla_breach_coverup": [
        {
            "doc_id": "SLA-PAYMENTS-2024",
            "doc_type": "sla_contract",
            "filename": "payments_api_sla_v3.2.pdf",
            "page": 4,
            "bbox": [72, 310, 540, 380],
            "text": (
                "SLA Contract v3.2 — Section 4.1: payments-api p99 latency SLA = 500ms. "
                "Penalty clause 4.1(b): breach >2 minutes triggers $15,000/hour penalty (pro-rated per minute)."
            ),
        },
        {
            "doc_id": "RB-CONN-POOL-007",
            "doc_type": "runbook",
            "filename": "runbook_rb007_conn_pool.pdf",
            "page": 2,
            "bbox": [72, 140, 540, 200],
            "text": (
                "Runbook RB-007: Connection Pool Configuration Changes. "
                "MANDATORY: All changes require approval from 2 senior engineers before production deployment. "
                "Escalate to: SRE Lead + Engineering Manager."
            ),
        },
    ],
    "supply_chain_ghosting": [
        {
            "doc_id": "SHIP-SHANGHAI-OCT12",
            "doc_type": "shipping_manifest",
            "filename": "mv_horizon_star_manifest.pdf",
            "page": 1,
            "bbox": [72, 200, 540, 260],
            "text": (
                "Shipping Manifest | MV Horizon Star | Shanghai Yangshan | "
                "Departure: 2024-10-12 | SKU-7821 | Quantity: 45,000 units | Seal #: SHNG-77821-X"
            ),
        },
        {
            "doc_id": "INS-CLAIM-2024-1188-PDF",
            "doc_type": "insurance_claim_pdf",
            "filename": "insurance_claim_1188.pdf",
            "page": 1,
            "bbox": [72, 150, 540, 220],
            "text": (
                "Insurance Claim #INS-1188 | Claimant: Horizon Manufacturing | "
                "Policy: Marine Cargo CMC-44210 | Claimed Loss: 2,100 units SKU-7821 | "
                "Claimed Value: $107,331.00 | Filed: 2024-10-25"
            ),
        },
    ],
}


# ──────────────────────────────────────────────────────────────────────────────
# ZetarisClient
# ──────────────────────────────────────────────────────────────────────────────

class ZetarisClient:
    """
    Simulated Zetaris Networked Data Platform USL.
    Provides a unified query interface over 3 federated data sources.
    """

    SOURCE_ERP = "erp_transactions"
    SOURCE_COMMS = "comms_audit"
    SOURCE_DOCS = "documents"

    def __init__(self) -> None:
        self._connected: bool = False
        self._sqlite_conn: sqlite3.Connection | None = None
        self._comms: dict[str, list[dict]] = {}
        self._docs: dict[str, list[dict]] = {}

    # ── Lifecycle ──────────────────────────────────────────────────────────

    def connect(self) -> dict[str, Any]:
        """Initialise the virtual USL — load all synthetic data sources."""
        t0 = time.perf_counter()

        # Source 1 — SQLite in-memory ERP
        self._sqlite_conn = sqlite3.connect(":memory:", check_same_thread=False)
        self._sqlite_conn.row_factory = sqlite3.Row
        cur = self._sqlite_conn.cursor()
        cur.execute(_ERP_SCHEMA)
        cur.executemany(
            "INSERT INTO erp_transactions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            _ERP_ROWS,
        )
        self._sqlite_conn.commit()

        # Source 2 — comms_audit dict
        self._comms = _COMMS_DATA

        # Source 3 — documents dict
        self._docs = _DOCUMENTS_DATA

        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        self._connected = True
        return {
            "status": "connected",
            "sources": [self.SOURCE_ERP, self.SOURCE_COMMS, self.SOURCE_DOCS],
            "erp_rows_loaded": len(_ERP_ROWS),
            "comms_scenarios": list(self._comms.keys()),
            "doc_scenarios": list(self._docs.keys()),
            "init_time_ms": elapsed_ms,
        }

    def _ensure_connected(self) -> None:
        if not self._connected:
            self.connect()

    # ── SQL / ERP queries ──────────────────────────────────────────────────

    def _query_erp(self, sql: str) -> tuple[list[dict[str, Any]], float]:
        """Execute SQL against the in-memory ERP SQLite database."""
        t0 = time.perf_counter()
        cur = self._sqlite_conn.cursor()  # type: ignore[union-attr]
        cur.execute(sql)
        rows = [dict(r) for r in cur.fetchall()]
        elapsed = round((time.perf_counter() - t0) * 1000, 2)
        return rows, elapsed

    # ── Comms / docs lookup ────────────────────────────────────────────────

    def _query_comms(self, scenario_id: str) -> tuple[list[dict[str, Any]], float]:
        t0 = time.perf_counter()
        rows = self._comms.get(scenario_id, [])
        elapsed = round((time.perf_counter() - t0) * 1000, 2)
        return rows, elapsed

    def _query_docs(self, scenario_id: str) -> tuple[list[dict[str, Any]], float]:
        t0 = time.perf_counter()
        rows = self._docs.get(scenario_id, [])
        elapsed = round((time.perf_counter() - t0) * 1000, 2)
        return rows, elapsed

    # ── Public API ─────────────────────────────────────────────────────────

    def query(
        self,
        sql: str,
        source_hint: str | None = None,
    ) -> dict[str, Any]:
        """
        Route and execute a virtual query across federated sources.
        Returns rows with full source provenance metadata.

        For ERP queries, `sql` is a real SQL string.
        For comms/docs, `sql` is treated as a scenario_id lookup.
        """
        self._ensure_connected()
        query_id = f"QRY-{uuid.uuid4().hex[:8].upper()}"

        source = source_hint or self._detect_source(sql)

        if source == self.SOURCE_ERP:
            rows, elapsed = self._query_erp(sql)
        elif source == self.SOURCE_COMMS:
            rows, elapsed = self._query_comms(sql)
        elif source == self.SOURCE_DOCS:
            rows, elapsed = self._query_docs(sql)
        else:
            # Default: try ERP SQL
            rows, elapsed = self._query_erp(sql)

        return {
            "rows": rows,
            "row_count": len(rows),
            "source": source,
            "query_id": query_id,
            "execution_time_ms": elapsed,
            "provenance": {
                "usl_layer": "Zetaris Networked Data Platform v2.1",
                "query_routed_to": source,
                "federation_type": "virtual_USL",
            },
        }

    def query_scenario_all(self, scenario_id: str) -> dict[str, Any]:
        """
        Fetch all records across all three sources for a given scenario.
        Returns a combined provenance-tagged result set.
        """
        self._ensure_connected()
        t0 = time.perf_counter()

        erp_rows, _ = self._query_erp(
            f"SELECT * FROM erp_transactions WHERE scenario_id = '{scenario_id}'"
        )
        comms_rows, _ = self._query_comms(scenario_id)
        doc_rows, _ = self._query_docs(scenario_id)

        # Tag each row with its source
        for r in erp_rows:
            r["_source"] = self.SOURCE_ERP
            r["_provenance"] = {"table": "erp_transactions", "row_id": r.get("row_id")}
        for r in comms_rows:
            r["_source"] = self.SOURCE_COMMS
            r["_provenance"] = {"collection": "comms_audit", "record_id": r.get("id")}
        for r in doc_rows:
            r["_source"] = self.SOURCE_DOCS
            r["_provenance"] = {
                "collection": "documents",
                "doc_id": r.get("doc_id"),
                "page": r.get("page"),
                "bbox": r.get("bbox"),
            }

        elapsed = round((time.perf_counter() - t0) * 1000, 2)
        all_rows = erp_rows + comms_rows + doc_rows

        return {
            "scenario_id": scenario_id,
            "rows": all_rows,
            "row_count": len(all_rows),
            "breakdown": {
                self.SOURCE_ERP: len(erp_rows),
                self.SOURCE_COMMS: len(comms_rows),
                self.SOURCE_DOCS: len(doc_rows),
            },
            "execution_time_ms": elapsed,
            "provenance": {
                "usl_layer": "Zetaris Networked Data Platform v2.1",
                "federation_type": "cross_silo_virtual_USL",
                "sources_queried": [self.SOURCE_ERP, self.SOURCE_COMMS, self.SOURCE_DOCS],
            },
        }

    def semantic_search(
        self,
        query: str,
        sources: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Cross-source semantic lookup using simple keyword matching
        (simulates Zetaris semantic search over federated sources).
        """
        self._ensure_connected()
        t0 = time.perf_counter()
        sources = sources or [self.SOURCE_ERP, self.SOURCE_COMMS, self.SOURCE_DOCS]
        keywords = [w.lower() for w in re.split(r"\W+", query) if len(w) > 3]

        results: list[dict[str, Any]] = []

        if self.SOURCE_ERP in sources:
            erp_rows, _ = self._query_erp("SELECT * FROM erp_transactions")
            for row in erp_rows:
                row_text = " ".join(str(v) for v in row.values()).lower()
                score = sum(1 for k in keywords if k in row_text) / max(len(keywords), 1)
                if score > 0:
                    results.append({
                        **row,
                        "_source": self.SOURCE_ERP,
                        "_relevance_score": round(score, 3),
                        "_provenance": {"table": "erp_transactions", "row_id": row.get("row_id")},
                    })

        all_comms = [r for rows in self._comms.values() for r in rows]
        if self.SOURCE_COMMS in sources:
            for row in all_comms:
                row_text = " ".join(str(v) for v in row.values()).lower()
                score = sum(1 for k in keywords if k in row_text) / max(len(keywords), 1)
                if score > 0:
                    results.append({
                        **row,
                        "_source": self.SOURCE_COMMS,
                        "_relevance_score": round(score, 3),
                        "_provenance": {"collection": "comms_audit", "record_id": row.get("id")},
                    })

        all_docs = [r for rows in self._docs.values() for r in rows]
        if self.SOURCE_DOCS in sources:
            for row in all_docs:
                row_text = " ".join(str(v) for v in row.values()).lower()
                score = sum(1 for k in keywords if k in row_text) / max(len(keywords), 1)
                if score > 0:
                    results.append({
                        **row,
                        "_source": self.SOURCE_DOCS,
                        "_relevance_score": round(score, 3),
                        "_provenance": {
                            "collection": "documents",
                            "doc_id": row.get("doc_id"),
                            "page": row.get("page"),
                        },
                    })

        results.sort(key=lambda r: r["_relevance_score"], reverse=True)
        elapsed = round((time.perf_counter() - t0) * 1000, 2)

        return {
            "query": query,
            "results": results,
            "result_count": len(results),
            "sources_searched": sources,
            "execution_time_ms": elapsed,
            "provenance": {
                "usl_layer": "Zetaris Networked Data Platform v2.1",
                "search_mode": "keyword_semantic_simulation",
            },
        }

    # ── Helpers ────────────────────────────────────────────────────────────

    @staticmethod
    def _detect_source(sql: str) -> str:
        """Heuristic source detection from query string."""
        lower = sql.lower()
        if any(kw in lower for kw in ["select", "from", "where", "erp"]):
            return ZetarisClient.SOURCE_ERP
        if any(kw in lower for kw in ["slack", "email", "pagerduty", "git", "audit", "metric"]):
            return ZetarisClient.SOURCE_COMMS
        if any(kw in lower for kw in ["pdf", "invoice", "doc", "contract", "runbook"]):
            return ZetarisClient.SOURCE_DOCS
        return ZetarisClient.SOURCE_ERP
