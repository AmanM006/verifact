"""
Unit & Integration Test Suite for VeriFact
Validates:
  1. Z3 SMT Formal Theorem Prover (UNSAT Core extraction)
  2. Directed Acyclic Graph (DAG) cycle prevention and topological sort
  3. Meterless H-MEM session storage and claim invalidation
  4. Investigation pipeline execution across all scenarios
"""

import asyncio
import networkx as nx
from backend.engines.smt_verifier import smt_verifier
from backend.engines.graph_solver import graph_solver
from backend.engines.meterless_hmem import HMem
from backend.engines.nemotron_reasoner import Claim
from backend.pipeline.investigator import Investigator


def test_smt_procurement_fraud_unsat():
    """Verify Z3 proves the procurement fraud contradiction as mathematically UNSAT."""
    res = smt_verifier.verify_scenario_constraints("procurement_fraud", [])
    assert res["is_consistent"] is False
    assert "UNSAT" in res["solver_verdict"]
    assert len(res["unsat_core"]) >= 2
    assert "CLM_001_PO_AUTH" in res["unsat_core"]
    assert "CLM_002_LEDGER_DISPATCH" in res["unsat_core"]


def test_smt_clean_scenario_sat():
    """Verify consistent generic claims return SAT with zero UNSAT core."""
    res = smt_verifier.verify_scenario_constraints("clean_scenario", [])
    assert res["is_consistent"] is True
    assert "SAT" in res["solver_verdict"]
    assert len(res["unsat_core"]) == 0


def test_graph_dag_topological_sort():
    """Ensure the causal graph builds a valid DAG and detects root causes."""
    claims = [
        Claim(
            claim_id="CLM-001",
            text="ERP PO created",
            confidence=0.95,
            source_type="sql",
            source_ref={"table": "erp"},
            timestamp="2026-10-15T09:00:00Z",
            entity_mentions=["PO-1001"],
            claim_type="financial"
        ),
        Claim(
            claim_id="CLM-002",
            text="Wire dispatched",
            confidence=0.90,
            source_type="sql",
            source_ref={"table": "ledger"},
            timestamp="2026-10-16T09:00:00Z",
            entity_mentions=["PAY-2001"],
            claim_type="financial"
        ),
    ]
    contradictions = []
    G = graph_solver.build_evidence_graph(claims, contradictions)
    root_causes = graph_solver.find_root_causes(G)
    assert len(root_causes) > 0
    # Graph must be acyclic
    assert nx.is_directed_acyclic_graph(G) is True


def test_hmem_storage_and_invalidation():
    """Test Meterless H-MEM memory retention and refutation tracking."""
    mem = HMem()
    session = "test_sess_001"
    mem.write("fact_1", {"amount": 5000}, session_id=session, provenance={"table": "erp"})
    
    val = mem.read("fact_1", session_id=session)
    assert val is not None
    assert val["value"]["amount"] == 5000
    assert val["valid"] is True

    # Invalidate claim
    res = mem.invalidate("fact_1", reason="Refuted by Z3 proof", session_id=session)
    assert res["status"] == "invalidated"
    invalidated_val = mem.read("fact_1", session_id=session)
    assert invalidated_val["valid"] is False
    assert invalidated_val["invalidation_reason"] == "Refuted by Z3 proof"


def test_full_investigation_pipeline():
    """Run full end-to-end investigation pipeline on procurement scenario."""
    inv = Investigator()
    res = asyncio.run(inv.investigate("procurement_fraud"))
    assert res["status"] == "complete"
    assert "smt_verification" in res
    assert res["smt_verification"]["is_consistent"] is False
    assert len(res["root_causes"]) > 0
    assert len(res["graph"]["nodes"]) > 0
