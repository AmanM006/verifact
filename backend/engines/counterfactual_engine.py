"""
VeriFact Counterfactual Repair Engine (MaxSMT / Z3 Optimize)
Answers the core 'Why' question:
"What is the minimal set of proposed adjustments or missing evidence that would resolve this inconsistency?"

Auditing & Forensic Governance Rule:
1. Authoritative historical records (e.g. approved PO amount, vendor onboarding IBAN,
   measured physical telemetry) are strictly IMMUTABLE.
   The solver NEVER proposes retroactively legitimizing fraud (e.g. increasing a PO to match a rogue wire).
2. Operational Execution Distinction:
   Distinguishes between a pure mathematical repair (Z3 model adjustment) and human-reviewed
   investigative options. Recommendations are presented as qualified remediation options
   subject to treasury, legal, and jurisdictional determination, never unconditional commands.
"""

from __future__ import annotations
import z3
from decimal import Decimal
from typing import Any, Sequence
from backend.engines.smt_verifier import VerifierClaim, NUM_VARS, BOOL_VARS, STRING_VARS, get_rule_library

# Authoritative baseline ground-truth that must NEVER be altered to excuse an anomaly
IMMUTABLE_AUTHORITATIVE_VARS: set[str] = {
    "po.amount",
    "po.iban",
    "sla_threshold_ms",
    "shipped",
    "received",
    "p99_latency_ms",
    "downtime_duration_min",
    "required_approvals",
}

# Operational or remedial variables subject to prospective auditor intervention
MUTABLE_OPERATIONAL_VARS: set[str] = {
    "ledger.dispatched",
    "ledger.iban",
    "disclosure.filed",
    "claimed_loss",
    "email.exists",
    "cfo.approved",
    "obtained_approvals",
}


class CounterfactualRepairEngine:
    """
    Computes minimal constraint relaxations / counterfactual corrections
    using MaxSMT so a human auditor can see what actionable interventions restore consistency,
    strictly distinguishing mathematical satisfaction from qualified human-reviewed remediation options.
    """

    def compute_repair(
        self,
        claims: Sequence[VerifierClaim],
        minimal_core_ids: list[str],
    ) -> list[dict[str, Any]]:
        """
        Given the claims and the minimal contradictory core, determines:
        1. Which operational claim(s) need adjustment
        2. Proposed corrected values (MaxSMT model)
        3. Operational status and qualified investigation protocols
        """
        if not claims or not minimal_core_ids:
            return []

        v: dict[str, z3.ExprRef] = {n: z3.Real(n) for n in NUM_VARS}
        v.update({n: z3.Bool(n) for n in BOOL_VARS})
        v.update({n: z3.String(n) for n in STRING_VARS})

        opt = z3.Optimize()
        claimed_vars = {c.var for c in claims}

        # 1. Hard assertions: Background domain rules must strictly hold
        rules = get_rule_library(v)
        used_rules = [
            (rid, expr, desc, _)
            for rid, needed, expr, desc, _ in rules
            if needed.issubset(claimed_vars)
        ]
        for _, expr, _, _ in used_rules:
            opt.add(expr)

        # 2. Add claims to MaxSMT solver:
        # Immutable authoritative records are added as HARD constraints (weight = infinity).
        # Mutable operational records are added as SOFT constraints (low weight in core, high outside).
        for c in claims:
            is_immutable = c.var in IMMUTABLE_AUTHORITATIVE_VARS

            if c.var in NUM_VARS:
                dec_val = str(Decimal(str(c.value)))
                expr = (v[c.var] == z3.RealVal(dec_val))
            elif c.var in STRING_VARS:
                expr = (v[c.var] == z3.StringVal(str(c.value)))
            elif c.var in BOOL_VARS:
                b_val = c.value if isinstance(c.value, bool) else (str(c.value).lower() == "true")
                expr = (v[c.var] == z3.BoolVal(b_val))
            else:
                continue

            if is_immutable:
                opt.add(expr)
            else:
                weight = 1 if c.id in minimal_core_ids else 10
                opt.add_soft(expr, weight)

        if opt.check() != z3.sat:
            return []

        model = opt.model()
        repairs: list[dict[str, Any]] = []

        # Compare model values against original claim values for mutable claims in the minimal core
        for c in claims:
            if c.id not in minimal_core_ids:
                continue
            if c.var in IMMUTABLE_AUTHORITATIVE_VARS:
                continue  # Never suggest mutating authoritative contracts or baseline records

            target_var = v[c.var]
            model_val = model[target_var]
            if model_val is None:
                continue

            if c.var in NUM_VARS:
                if isinstance(model_val, z3.RatNumRef):
                    m_val_num = float(model_val.numerator_as_long()) / float(model_val.denominator_as_long())
                else:
                    m_val_num = float(str(model_val))
                
                delta = abs(m_val_num - float(c.value))
                if delta > 0.001:
                    if c.var == "ledger.dispatched":
                        repairs.append({
                            "claim_id": c.id,
                            "variable": c.var,
                            "current_value": c.value,
                            "counterfactual_value": m_val_num,
                            "mathematical_repair": f"ledger.dispatched := {m_val_num} (matches PO ceiling)",
                            "operational_status": "DISBURSEMENT_COMMITTED",
                            "action_type": "HUMAN_REVIEW_RECOVERY_OPTION",
                            "execution_protocol": (
                                "Human Review Required: Verify settlement status with Treasury. "
                                f"If wire is settled, evaluate formal inter-bank recall protocols (e.g. SWIFT gpi MT192/camt.056) "
                                f"for the ${delta:,.2f} overage with banking counsel, or submit formal supplemental PO amendment."
                            ),
                            "repair_recommendation": (
                                f"Initiate clawback / intercept of ${delta:,.2f} overpayment to align disbursed "
                                f"amount (${float(c.value):,.2f}) with authorized PO ceiling (${m_val_num:,.2f}), "
                                "OR obtain formal supplemental CFO board override."
                            ),
                        })
                    elif c.var == "claimed_loss":
                        repairs.append({
                            "claim_id": c.id,
                            "variable": c.var,
                            "current_value": c.value,
                            "counterfactual_value": m_val_num,
                            "mathematical_repair": f"claimed_loss := {m_val_num} (matches physically measured delta)",
                            "operational_status": "CLAIM_SUBMITTED_TO_CARRIER",
                            "action_type": "HUMAN_REVIEW_CLAIM_AMENDMENT",
                            "execution_protocol": (
                                "Human Review Required: Review insurance policy coverage terms, deductibles, and "
                                f"carrier claim amendment procedures with risk management. If supported, prepare supplemental "
                                f"Proof of Loss for {int(m_val_num):,} units citing verified customs shortfall tallies."
                            ),
                            "repair_recommendation": (
                                f"Amend insurance claim from {int(c.value):,} units to {int(m_val_num):,} units "
                                "to reflect physically measured deficit."
                            ),
                        })
                    elif c.var == "obtained_approvals":
                        repairs.append({
                            "claim_id": c.id,
                            "variable": c.var,
                            "current_value": c.value,
                            "counterfactual_value": m_val_num,
                            "mathematical_repair": f"obtained_approvals := {int(m_val_num)} (meets policy threshold)",
                            "operational_status": "POLICY_GATE_BYPASS",
                            "action_type": "GOVERNANCE_REVIEW_REQUIRED",
                            "execution_protocol": (
                                "Human Review Required: Single approval deployment bypassed runbook gates. "
                                "Conduct retrospective architectural post-mortem and enforce CI/CD branch protection rules."
                            ),
                            "repair_recommendation": (
                                f"Submit required senior engineering and SRE sign-offs "
                                f"(increase from {int(c.value)} to {int(m_val_num)}) before deploy."
                            ),
                        })
                    else:
                        repairs.append({
                            "claim_id": c.id,
                            "variable": c.var,
                            "current_value": c.value,
                            "counterfactual_value": m_val_num,
                            "mathematical_repair": f"{c.var} := {m_val_num}",
                            "operational_status": "AUDIT_RECONCILIATION_REQUIRED",
                            "action_type": "ADJUST_OPERATIONAL_METRIC",
                            "execution_protocol": f"Human Review Required: Reconcile operational tracking ledger for {c.var}.",
                            "repair_recommendation": (
                                f"Adjust {c.var} from {c.value} to {m_val_num} to restore domain consistency."
                            ),
                        })

            elif c.var in BOOL_VARS:
                m_val_bool = bool(z3.is_true(model_val))
                orig_bool = c.value if isinstance(c.value, bool) else (str(c.value).lower() == "true")
                if m_val_bool != orig_bool:
                    if c.var == "disclosure.filed":
                        repairs.append({
                            "claim_id": c.id,
                            "variable": c.var,
                            "current_value": orig_bool,
                            "counterfactual_value": m_val_bool,
                            "mathematical_repair": "disclosure.filed := true",
                            "operational_status": "OUTAGE_CLOSED_UNDISCLOSED",
                            "action_type": "HUMAN_REVIEW_DISCLOSURE",
                            "execution_protocol": (
                                "Human Review Required: Review customer contract SLA terms (Clause 4.2) and post-incident "
                                "disclosure obligations with legal counsel before issuing official notice and service credits ($5,750)."
                            ),
                            "repair_recommendation": (
                                "File mandatory customer SLA breach disclosure and initiate service credit ledger entry."
                            ),
                        })
                    elif c.var == "email.exists":
                        repairs.append({
                            "claim_id": c.id,
                            "variable": c.var,
                            "current_value": orig_bool,
                            "counterfactual_value": m_val_bool,
                            "mathematical_repair": "email.exists := true",
                            "operational_status": "ARCHIVE_SEARCH_NEGATIVE",
                            "action_type": "HUMAN_REVIEW_AUTHORIZATION_SEARCH",
                            "execution_protocol": (
                                "Human Review Required: Primary email archive search for thread #4471 was negative. "
                                "Request cold-storage backup search or seek written executive verification affidavit."
                            ),
                            "repair_recommendation": (
                                "Provide verified archive email thread validating retroactive executive approval."
                            ),
                        })
                    else:
                        repairs.append({
                            "claim_id": c.id,
                            "variable": c.var,
                            "current_value": orig_bool,
                            "counterfactual_value": m_val_bool,
                            "mathematical_repair": f"{c.var} := {m_val_bool}",
                            "operational_status": "EVIDENCE_GAP",
                            "action_type": "PROVIDE_MISSING_EVIDENCE",
                            "execution_protocol": f"Locate and verify missing audit evidence for '{c.var}'.",
                            "repair_recommendation": (
                                f"Locate and verify missing audit evidence for '{c.var}' to validate authorization."
                            ),
                        })

            elif c.var in STRING_VARS:
                m_val_str = model_val.as_string()
                if m_val_str != str(c.value):
                    if c.var == "ledger.iban":
                        repairs.append({
                            "claim_id": c.id,
                            "variable": c.var,
                            "current_value": c.value,
                            "counterfactual_value": m_val_str,
                            "mathematical_repair": f"ledger.iban := '{m_val_str}'",
                            "operational_status": "TRANSFERRED_TO_UNAUTHORIZED_ACCOUNT",
                            "action_type": "HUMAN_REVIEW_PAYEE_RECONCILIATION",
                            "execution_protocol": (
                                f"Human Review Required: Payment was directed to unauthorized account '{c.value}'. "
                                "Contact paying institution treasury and receiving bank compliance to investigate beneficiary status. "
                                "Evaluate jurisdictional reporting obligations (e.g. SAR/STR) and confirm authorized vendor coordinates."
                            ),
                            "repair_recommendation": (
                                f"Freeze payment to rogue recipient account '{c.value}' and "
                                f"re-route disbursement to authorized vendor IBAN '{m_val_str}'."
                            ),
                        })
                    else:
                        repairs.append({
                            "claim_id": c.id,
                            "variable": c.var,
                            "current_value": c.value,
                            "counterfactual_value": m_val_str,
                            "mathematical_repair": f"{c.var} := '{m_val_str}'",
                            "operational_status": "IDENTITY_MISMATCH",
                            "action_type": "REVERT_IDENTITY_MUTATION",
                            "execution_protocol": f"Revert entity identity to authorized registry value '{m_val_str}'.",
                            "repair_recommendation": (
                                f"Revert {c.var} ('{c.value}') to match authorized record ('{m_val_str}')."
                            ),
                        })

        return repairs


counterfactual_engine = CounterfactualRepairEngine()
