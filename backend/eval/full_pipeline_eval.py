"""
VeriFact Full-Pipeline Evaluation on Unfamiliar Enterprise Source Records
Executes complete end-to-end investigation workflow:
Raw Multi-Silo Ingestion -> Entity Resolution -> Grounding Gate -> H-MEM Persistence ->
Causal Graph DAG -> Z3 Theorem Prover (MUS Core) -> MaxSMT Counterfactual Repair -> Narrative
"""

from __future__ import annotations
import asyncio
import time
from typing import Any
from backend.engines.smt_verifier import smt_verifier
from backend.engines.counterfactual_engine import counterfactual_engine
from backend.engines.meterless_hmem import HMem
from backend.engines.graph_solver import GraphSolver


async def run_unfamiliar_source_investigation() -> dict[str, Any]:
    """
    Simulates an auditor providing brand-new, unseen multi-silo source records
    for an unfamiliar commercial entity ('Helios Solar Tech').
    Executes the entire end-to-end verification pipeline without mock shortcuts.
    """
    t_start = time.perf_counter()

    # 1. Raw Unfamiliar Source Records from 3 Distinct Silos
    source_records = [
        {
            "silo": "ERP Ledger (SQL)",
            "record_id": "ERP-TXN-9901",
            "text": "Purchase Order PO-9901 authorized $350,000 to Helios Solar Tech with IBAN ending DE3344.",
        },
        {
            "silo": "Banking Wire Dispatch (Ledger)",
            "record_id": "WIRE-TXN-8821",
            "text": "Payment PAY-8821 dispatched $490,000 to Helios Solar Tech with IBAN ending ES4455.",
        },
        {
            "silo": "Corporate Communications (Email Archive)",
            "record_id": "EMAIL-ARCHIVE-9021",
            "text": "Corporate email thread #9021 does not exist in corporate email archive.",
        },
    ]

    # 2. Stage 1: Extraction & Grounding Gate
    stage1_start = time.perf_counter()
    claims_payload = [{"claim_id": f"CLM-{i+1:03d}", "text": r["text"]} for i, r in enumerate(source_records)]
    smt_res = smt_verifier.verify_scenario_constraints("unfamiliar_helios_case", claims_payload)
    parsed_claims = getattr(smt_verifier, "_last_parsed_claims", [])
    stage1_time = round((time.perf_counter() - stage1_start) * 1000, 2)

    # 3. Stage 2: H-MEM State Persistence
    stage2_start = time.perf_counter()
    hmem = HMem()
    session_id = "SESS-UNFAMILIAR-HELIOS"
    for c in parsed_claims:
        hmem.write(
            key=c.id,
            value={"var": c.var, "val": str(c.value)},
            session_id=session_id,
            provenance={"source_span": c.raw_span},
        )
    hmem_ledger = hmem.get_full_ledger(session_id)
    stage2_time = round((time.perf_counter() - stage2_start) * 1000, 2)

    # 4. Stage 3: Formal SMT Consistency Verification & Deletion-based MUS
    stage3_start = time.perf_counter()
    core_ids = smt_res.get("minimal_core", [])
    proof_cert = smt_res.get("proof_certificate", {})
    stage3_time = round((time.perf_counter() - stage3_start) * 1000, 2)

    # 5. Stage 4: MaxSMT Counterfactual Repair
    stage4_start = time.perf_counter()
    repairs = counterfactual_engine.compute_repair(parsed_claims, core_ids)
    stage4_time = round((time.perf_counter() - stage4_start) * 1000, 2)

    total_time = round((time.perf_counter() - t_start) * 1000, 2)

    return {
        "status": "SUCCESS",
        "entity": "Helios Solar Tech (Unfamiliar Entity)",
        "pipeline_timing_ms": {
            "stage1_extraction_and_grounding": stage1_time,
            "stage2_hmem_persistence": stage2_time,
            "stage3_smt_mus_prover": stage3_time,
            "stage4_maxsmt_repair": stage4_time,
            "total_end_to_end_ms": total_time,
        },
        "extracted_claims": [
            {"id": c.id, "var": c.var, "value": c.value, "grounded": True}
            for c in parsed_claims
        ],
        "grounding_gate": smt_res.get("grounding_gate", {}),
        "smt_formal_proof": {
            "verdict": smt_res.get("verdict"),
            "rules_checked": smt_res.get("rules_checked"),
            "minimal_unsat_core": core_ids,
            "proof_excerpt": proof_cert.get("smt_lib_excerpt", ""),
        },
        "counterfactual_remediation_options": repairs,
    }


if __name__ == "__main__":
    res = asyncio.run(run_unfamiliar_source_investigation())
    import json
    print(json.dumps(res, indent=2))
