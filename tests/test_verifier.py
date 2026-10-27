"""
Unit & Integration Test Suite for VeriFact
Validates:
  1. Deletion-based minimal UNSAT core extraction
  2. Generic rule-based consistency vs inconsistency vs NO_APPLICABLE_RULES
  3. Minimality property: removing any single core element makes remaining claims SAT
  4. Non-applicable rules reporting honesty (never vacuous SAT)
  5. Meterless H-MEM session persistence & refutation
"""

import asyncio
from backend.engines.smt_verifier import smt_verifier, VerifierClaim
from backend.engines.graph_solver import graph_solver
from backend.engines.meterless_hmem import HMem
from backend.engines.nemotron_reasoner import Claim
from backend.pipeline.investigator import Investigator


def test_smt_generic_inconsistency_and_deletion_minimality():
    """Verify true deletion-based minimal unsatisfiable subset (MUS)."""
    # Over-disbursement without authorization
    claims = [
        VerifierClaim(id="CLM-001", var="po.amount", value=42000.0),
        VerifierClaim(id="CLM-002", var="ledger.dispatched", value=94750.0),
        VerifierClaim(id="CLM-003", var="email.exists", value=False),
        # Irrelevant claim that should NOT be part of the minimal core
        VerifierClaim(id="CLM-004", var="shipped", value=1000),
    ]
    res = smt_verifier.verify_claims(claims)
    assert res["verdict"] == "INCONSISTENT"
    assert res["is_consistent"] is False
    core = res["minimal_core"]
    
    # Core must contain exactly the 3 conflicting claims, not CLM-004
    assert set(core) == {"CLM-001", "CLM-002", "CLM-003"}
    assert "CLM-004" not in core
    assert res["minimal_conflict_size"] == 3

    # Minimality property test: removing any one claim in core must make remaining SAT
    for removed_id in core:
        sub_claims = [c for c in claims if c.id != removed_id and c.id != "CLM-004"]
        sub_res = smt_verifier.verify_claims(sub_claims)
        # Without any one of the 3 axioms, the overage rule cannot prove inconsistency
        assert sub_res["verdict"] in ("CONSISTENT", "NO_APPLICABLE_RULES")


def test_smt_consistent_state():
    """Verify legitimate disbursements within PO bounds evaluate as CONSISTENT."""
    claims = [
        VerifierClaim(id="CLM-001", var="po.amount", value=50000.0),
        VerifierClaim(id="CLM-002", var="ledger.dispatched", value=48000.0),
        VerifierClaim(id="CLM-003", var="email.exists", value=False),
    ]
    res = smt_verifier.verify_claims(claims)
    assert res["verdict"] == "CONSISTENT"
    assert res["is_consistent"] is True
    assert len(res["minimal_core"]) == 0
    assert "R_DISBURSEMENT_LIMIT" in res["rules_checked"]


def test_smt_no_applicable_rules_honesty():
    """Ensure unconstrained input returns NO_APPLICABLE_RULES, never vacuous SAT."""
    claims = [
        VerifierClaim(id="CLM-901", var="untracked.metric", value=123.45),
        VerifierClaim(id="CLM-902", var="random.counter", value=99),
    ]
    res = smt_verifier.verify_claims(claims)
    assert res["verdict"] == "NO_APPLICABLE_RULES"
    assert len(res["rules_checked"]) == 0


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


def test_full_investigation_pipeline_consistency_verdict():
    """Run full end-to-end investigation pipeline on procurement scenario."""
    inv = Investigator()
    res = asyncio.run(inv.investigate("procurement_fraud"))
    assert res["status"] == "complete"
    assert "smt_verification" in res
    assert res["smt_verification"]["verdict"] == "INCONSISTENT"
    assert len(res["smt_verification"]["minimal_core"]) > 0
    assert len(res["root_causes"]) > 0
