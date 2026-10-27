"""
VeriFact Investigation Pipeline
Orchestrates the full forensic investigation: Zetaris USL → Nemotron → H-MEM → Graph Solver.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Any

from backend.data.scenarios import get_scenario
from backend.engines.graph_solver import GraphSolver, graph_solver
from backend.engines.meterless_hmem import HMem, MeterlessNightshift, hmem, nightshift
from backend.engines.nemotron_reasoner import Claim, ContradictionResult, NemotronReasoner, reasoner
from backend.engines.zetaris_client import ZetarisClient


class Investigator:
    """
    Full investigation pipeline orchestrator.

    Steps:
      1. Load scenario data
      2. Query Zetaris USL for all relevant records
      3. Feed records to Nemotron → extract Claims
      4. Store Claims to H-MEM
      5. Run graph_solver: build DAG, detect contradictions, score, find root causes
      6. Generate final narrative from Nemotron
      7. Return full structured result
    """

    def __init__(
        self,
        zetaris: ZetarisClient | None = None,
        reasoner_inst: NemotronReasoner | None = None,
        hmem_inst: HMem | None = None,
        nightshift_inst: MeterlessNightshift | None = None,
        solver: GraphSolver | None = None,
    ) -> None:
        self._zetaris = zetaris or ZetarisClient()
        self._reasoner = reasoner_inst or reasoner
        self._hmem = hmem_inst or hmem
        self._nightshift = nightshift_inst or nightshift
        self._solver = solver or graph_solver

    async def investigate(
        self,
        scenario_id: str,
        custom_query: str | None = None,
    ) -> dict[str, Any]:
        """
        Run a full investigation and return a structured result.
        """
        t_start = time.perf_counter()
        investigation_id = f"INV-{uuid.uuid4().hex[:8].upper()}"
        session_id = f"SESS-{uuid.uuid4().hex[:8].upper()}"

        # ── Step 1: Load scenario ──────────────────────────────────────────
        scenario = get_scenario(scenario_id)
        if scenario is None:
            raise ValueError(f"Unknown scenario_id: '{scenario_id}'")

        # ── Step 2: Query Zetaris USL ──────────────────────────────────────
        self._zetaris.connect()
        zetaris_result = self._zetaris.query_scenario_all(scenario_id)

        # Optional custom semantic search
        custom_search_results: dict[str, Any] | None = None
        if custom_query:
            custom_search_results = self._zetaris.semantic_search(custom_query)

        # ── Step 3: Extract Claims via Nemotron ────────────────────────────
        # Combine all raw evidence text for extraction
        all_text = "\n".join(
            row.get("content", row.get("text", str(row)))
            for row in zetaris_result["rows"]
        )

        claims: list[Claim] = await self._reasoner.extract_claims(
            text=all_text,
            source_metadata=zetaris_result["provenance"],
            scenario_id=scenario_id,
        )

        # ── Step 4: Store Claims to H-MEM ─────────────────────────────────
        for claim in claims:
            self._hmem.write(
                key=claim.claim_id,
                value=claim.to_dict(),
                session_id=session_id,
                provenance={
                    "investigation_id": investigation_id,
                    "scenario_id": scenario_id,
                    "zetaris_query_id": zetaris_result.get("provenance", {}).get("usl_layer", ""),
                    "source_type": claim.source_type,
                    "source_ref": claim.source_ref.__dict__,
                },
            )

        # ── Step 5: Detect contradictions between claim pairs ──────────────
        contradictions: list[ContradictionResult] = []
        contradiction_matrix: list[dict[str, Any]] = []

        for i, ca in enumerate(claims):
            for j, cb in enumerate(claims):
                if j <= i:
                    continue
                score = self._solver.score_contradiction(ca, cb)
                if score >= 0.35:  # Threshold for noteworthy contradictions
                    contr = await self._reasoner.reason_contradiction(
                        ca.to_dict(), cb.to_dict()
                    )
                    # Use the mathematical score as ground truth
                    contr.contradiction_score = max(contr.contradiction_score, score)
                    contradictions.append(contr)
                    contradiction_matrix.append({
                        **contr.to_dict(),
                        "mathematical_score": score,
                    })

        # ── Step 5b: Build causal graph ────────────────────────────────────
        G = self._solver.build_evidence_graph(claims, contradictions)

        causal_chains = self._solver.compute_causal_chains(G)
        root_cause_ids = self._solver.find_root_causes(G)
        coverage = self._solver.compute_evidence_coverage(G, scenario)
        graph_json = self._solver.export_for_viz(G)

        # Attach scenario_id to graph for narrative generation
        graph_json["scenario_id"] = scenario_id

        # ── Step 6: Generate narrative & recommendations ───────────────────
        narrative_input = {
            "scenario_id": scenario_id,
            "root_causes": root_cause_ids,
            "evidence_coverage_pct": coverage["coverage_pct"],
            "contradiction_count": len(contradictions),
            "chain_depth": max((c.depth for c in causal_chains), default=0),
            "financial_impact": scenario.get("financial_impact", "Unknown"),
        }

        narrative = await self._reasoner.generate_causality_narrative(narrative_input)

        # ── Step 7: Schedule background monitoring ─────────────────────────
        nightshift_task_id = self._nightshift.schedule_task(
            fn=lambda sid: hmem.get_stats(sid),
            args=[session_id],
            delay_seconds=2.0,
        )

        # ── Build recommendations ──────────────────────────────────────────
        recommendations = self._build_recommendations(scenario_id, contradictions, coverage)

        # ── Assemble root cause descriptions ──────────────────────────────
        root_cause_descriptions = []
        for rc_id in root_cause_ids:
            node_data = G.nodes.get(rc_id, {})
            root_cause_descriptions.append({
                "node_id": rc_id,
                "description": node_data.get("full_text", node_data.get("label", rc_id)),
                "claim_type": node_data.get("claim_type"),
                "confidence": node_data.get("confidence"),
                "source_type": node_data.get("source_type"),
                "source_ref": node_data.get("source_ref"),
                "timestamp": node_data.get("timestamp"),
            })

        # ── Compute processing time ────────────────────────────────────────
        elapsed_ms = round((time.perf_counter() - t_start) * 1000, 2)

        # ── Assemble final result ──────────────────────────────────────────
        return {
            "investigation_id": investigation_id,
            "scenario_id": scenario_id,
            "scenario_title": scenario["title"],
            "status": "complete",
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "summary": narrative,
            "root_causes": root_cause_descriptions,
            "contradiction_matrix": contradiction_matrix,
            "evidence_coverage_pct": coverage["coverage_pct"],
            "evidence_coverage_detail": coverage,
            "causal_chain_depth": max((c.depth for c in causal_chains), default=0),
            "causal_chains": [c.to_dict() for c in causal_chains[:5]],  # Top 5
            "financial_impact": scenario.get("financial_impact", "Unknown"),
            "severity": scenario.get("severity", "UNKNOWN"),
            "recommendations": recommendations,
            "claims": [c.to_dict() for c in claims],
            "graph": graph_json,
            "hmem_session_id": session_id,
            "custom_query_results": custom_search_results,
            "processing_time_ms": elapsed_ms,
            "sponsor_stack": {
                "zetaris": f"USL query across 3 sources — {zetaris_result['row_count']} records retrieved",
                "zetaris_breakdown": zetaris_result["breakdown"],
                "meterless_hmem": f"{len(claims)} evidence entries stored in session {session_id}",
                "meterless_nightshift": f"active — monitoring task {nightshift_task_id}",
                "nvidia_nemotron": self._reasoner.model_info["mode"],
                "nemotron_model": self._reasoner.model_info["model"],
                "graph_engine": f"NetworkX DAG — {graph_json['node_count']} nodes, {graph_json['edge_count']} edges",
            },
        }

    def _build_recommendations(
        self,
        scenario_id: str,
        contradictions: list[ContradictionResult],
        coverage: dict[str, Any],
    ) -> list[str]:
        base: dict[str, list[str]] = {
            "procurement_fraud": [
                "IMMEDIATE: Freeze all payments to IBAN ending 3304 (DE89370400440532013304)",
                "Escalate to financial crime unit and law enforcement",
                "Audit all vendor banking changes in the past 90 days",
                "Implement mandatory dual-approval for IBAN modifications with out-of-band confirmation",
                "Restore email archive backup to verify thread #4471 existence",
                "Cross-reference invoice addresses against SEC EDGAR for all active vendors",
            ],
            "sla_breach_coverup": [
                "Enforce mandatory 2-engineer approval gate in CI/CD pipeline — block single-approver deploys",
                "Reduce PagerDuty alert sensitivity: trigger on 3-consecutive-second p99 > 200ms",
                "Conduct formal post-incident review naming the runbook violation",
                "Disclose SLA breach and $5,750 penalty to customer per contract clause 4.3",
                "Add connection pool change to high-risk change category requiring SRE Lead sign-off",
                "Review j.malik's recent deployments for other policy violations",
            ],
            "supply_chain_ghosting": [
                "File amended insurance claim for full 13,800 units ($705,300 at unit cost)",
                "Refer to DOJ and CBP for customs fraud investigation",
                "Suspend Horizon Manufacturing as approved vendor pending investigation",
                "Audit warehouse operator W. Okonkwo and customs broker ID-4421",
                "Eliminate pre-payment clauses — require delivery-confirmed payment for all POs > $500K",
                "Implement IoT seal tracking for all international shipments to detect in-transit diversion",
            ],
        }
        recs = base.get(scenario_id, ["Review investigation findings and take appropriate remedial action."])
        if coverage["coverage_pct"] < 80:
            recs.append(f"Evidence coverage is {coverage['coverage_pct']:.1f}% — gather additional documentation to close evidence gaps.")
        if len(contradictions) > 3:
            recs.append(f"High contradiction density ({len(contradictions)} conflicts) — forensic accountant review recommended.")
        return recs


# Module-level investigator singleton
investigator = Investigator()
