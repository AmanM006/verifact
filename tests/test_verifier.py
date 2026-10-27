"""
Unit & Integration Test Suite for VeriFact
Validates:
  1. Deletion-based minimal UNSAT core extraction (true MUS)
  2. Generic rule-based consistency vs inconsistency vs NO_APPLICABLE_RULES
  3. Minimality property: removing any single core element makes remaining claims SAT or rule unapplicable
  4. Non-applicable rules reporting honesty (returns is_consistent=None, never vacuous True)
  5. Payee IBAN mismatch cross-silo identity verification
  6. SLA multi-source telemetry breach verification
  7. Offline reproducible SMT-LIB2 proof certificate verification
"""

import asyncio
import z3
from backend.engines.smt_verifier import smt_verifier, VerifierClaim
from backend.engines.meterless_hmem import HMem
from backend.pipeline.investigator import Investigator


def test_smt_generic_inconsistency_and_deletion_minimality():
    """Verify true deletion-based minimal unsatisfiable subset (MUS)."""
    # Over-disbursement without authorization
    claims = [
        VerifierClaim(id="CLM-001", var="po.amount", value=42000.0),
        VerifierClaim(id="CLM-002", var="ledger.dispatched", value=94750.0),
        VerifierClaim(id="CLM-003", var="email.exists", value=False),
        # Irrelevant distractor
        VerifierClaim(id="CLM-004", var="shipped", value=1000),
    ]
    res = smt_verifier.verify_claims(claims)
    assert res["verdict"] == "INCONSISTENT"
    assert res["is_consistent"] is False
    core = res["minimal_core"]
    
    assert set(core) == {"CLM-001", "CLM-002", "CLM-003"}
    assert "CLM-004" not in core
    assert res["minimal_conflict_size"] == 3


def test_smt_payee_iban_mismatch():
    """Verify payee IBAN substitution rule R_PAYEE_IBAN_MATCH."""
    claims = [
        VerifierClaim(id="CLM-001", var="po.iban", value="GB8821"),
        VerifierClaim(id="CLM-002", var="ledger.iban", value="DE3304"),
    ]
    res = smt_verifier.verify_claims(claims)
    assert res["verdict"] == "INCONSISTENT"
    assert set(res["minimal_core"]) == {"CLM-001", "CLM-002"}
    assert "R_PAYEE_IBAN_MATCH" in res["rules_checked"]


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
    """Ensure unconstrained input returns NO_APPLICABLE_RULES and is_consistent=None."""
    claims = [
        VerifierClaim(id="CLM-901", var="untracked.metric", value=123.45),
        VerifierClaim(id="CLM-902", var="random.counter", value=99),
    ]
    res = smt_verifier.verify_claims(claims)
    assert res["verdict"] == "NO_APPLICABLE_RULES"
    assert res["is_consistent"] is None
    assert len(res["rules_checked"]) == 0


def test_offline_proof_certificate_reproducibility():
    """Ensure generated SMT2 certificate evaluates to UNSAT in a fresh standalone Z3 solver."""
    claims = [
        VerifierClaim(id="CLM-001", var="po.amount", value=42000.0),
        VerifierClaim(id="CLM-002", var="ledger.dispatched", value=94750.0),
        VerifierClaim(id="CLM-003", var="email.exists", value=False),
    ]
    res = smt_verifier.verify_claims(claims)
    cert = res.get("proof_certificate")
    assert cert is not None
    assert "full_smt_lib2" in cert
    
    # Run in fresh solver instance
    offline_solver = z3.Solver()
    offline_solver.from_string(cert["full_smt_lib2"])
    assert offline_solver.check() == z3.unsat
    core = [str(x) for x in offline_solver.unsat_core()]
    assert any("CLM-001" in x for x in core)
    assert any("CLM-002" in x for x in core)


def test_full_investigation_pipeline_consistency_verdict():
    """Run full end-to-end investigation pipeline on procurement scenario."""
    inv = Investigator()
    res = asyncio.run(inv.investigate("procurement_fraud"))
    assert res["status"] == "complete"
    assert "smt_verification" in res
    assert res["smt_verification"]["verdict"] == "INCONSISTENT"
    assert len(res["smt_verification"]["minimal_core"]) > 0
    assert len(res["root_causes"]) > 0


def test_counterfactual_repair_authoritative_invariance():
    """Verify that MaxSMT never legitimizes fraud by increasing authoritative PO amount or changing PO IBAN."""
    from backend.engines.counterfactual_engine import counterfactual_engine

    claims = [
        VerifierClaim(id="CLM-001", var="po.amount", value=42000.0),
        VerifierClaim(id="CLM-001", var="po.iban", value="GB8821"),
        VerifierClaim(id="CLM-002", var="ledger.dispatched", value=94750.0),
        VerifierClaim(id="CLM-002", var="ledger.iban", value="DE3304"),
        VerifierClaim(id="CLM-003", var="email.exists", value=False),
    ]
    repairs = counterfactual_engine.compute_repair(claims, ["CLM-001", "CLM-002"])
    
    # Assert authoritative records are never mutated
    repair_vars = {r["variable"] for r in repairs}
    assert "po.amount" not in repair_vars
    assert "po.iban" not in repair_vars

    # Assert operational targets are remediated
    assert "ledger.dispatched" in repair_vars
    assert "ledger.iban" in repair_vars
    
    wire_repair = next(r for r in repairs if r["variable"] == "ledger.dispatched")
    assert wire_repair["counterfactual_value"] == 42000.0
    assert "HUMAN_REVIEW" in wire_repair["action_type"]
    assert "clawback" in wire_repair["repair_recommendation"].lower()

    iban_repair = next(r for r in repairs if r["variable"] == "ledger.iban")
    assert iban_repair["counterfactual_value"] == "GB8821"
    assert "HUMAN_REVIEW" in iban_repair["action_type"]


def test_counterfactual_sla_and_inventory_remediation():
    """Verify SLA disclosure and physical inventory counterfactual repairs."""
    from backend.engines.counterfactual_engine import counterfactual_engine

    # SLA scenario
    sla_claims = [
        VerifierClaim(id="CLM-002", var="p99_latency_ms", value=8200.0),
        VerifierClaim(id="CLM-004", var="sla_threshold_ms", value=500.0),
        VerifierClaim(id="CLM-006", var="downtime_duration_min", value=23.0),
        VerifierClaim(id="CLM-006", var="disclosure.filed", value=False),
    ]
    sla_repairs = counterfactual_engine.compute_repair(sla_claims, ["CLM-002", "CLM-004", "CLM-006"])
    disc_repair = next(r for r in sla_repairs if r["variable"] == "disclosure.filed")
    assert disc_repair["counterfactual_value"] is True
    assert "HUMAN_REVIEW" in disc_repair["action_type"]

    # Inventory scenario
    inv_claims = [
        VerifierClaim(id="CLM-003", var="shipped", value=45000),
        VerifierClaim(id="CLM-005", var="received", value=31200),
        VerifierClaim(id="CLM-006", var="claimed_loss", value=2100),
    ]
    inv_repairs = counterfactual_engine.compute_repair(inv_claims, ["CLM-003", "CLM-005", "CLM-006"])
    loss_repair = next(r for r in inv_repairs if r["variable"] == "claimed_loss")
    assert loss_repair["counterfactual_value"] == 13800.0
    assert "HUMAN_REVIEW" in loss_repair["action_type"]


def test_full_pipeline_unfamiliar_entity():
    """Verify complete end-to-end pipeline execution on unfamiliar enterprise records."""
    from backend.eval.full_pipeline_eval import run_unfamiliar_source_investigation
    res = asyncio.run(run_unfamiliar_source_investigation())
    assert res["status"] == "SUCCESS"
    assert res["smt_formal_proof"]["verdict"] == "INCONSISTENT"
    assert len(res["counterfactual_remediation_options"]) == 2

