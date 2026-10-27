"""
VeriFact Counterfactual Repair Engine (MaxSMT / Z3 Optimize)
Answers the core 'Why' question:
"What is the minimal set of proposed adjustments or missing evidence that would resolve this inconsistency?"
"""

from __future__ import annotations
import z3
from decimal import Decimal
from typing import Any, Sequence
from backend.engines.smt_verifier import VerifierClaim, NUM_VARS, BOOL_VARS, STRING_VARS, get_rule_library


class CounterfactualRepairEngine:
    """
    Computes minimal constraint relaxations / counterfactual corrections
    using MaxSMT so a human auditor can see what must change to restore consistency.
    """

    def compute_repair(
        self,
        claims: Sequence[VerifierClaim],
        minimal_core_ids: list[str],
    ) -> list[dict[str, Any]]:
        """
        Given the claims and the minimal contradictory core, determines:
        1. Which claim(s) need adjustment
        2. Proposed corrected values (MaxSMT model)
        3. Human-readable auditor explanation (e.g. 'Supply missing authorization' or 'Reduce wire amount')
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

            # 2. Soft assertions: Maximize keeping non-core claims unchanged (weight 10).
            # For core claims, target values that restore legitimacy:
            # - po.iban is authoritative ground-truth; ledger.iban is the mutable target
            for c in claims:
                weight = 1 if c.id in minimal_core_ids else 10
                if c.var == "po.iban":
                    # po.iban is authoritative
                    opt.add_soft(v[c.var] == z3.StringVal(str(c.value)), 100)
                elif c.var in NUM_VARS:
                    dec_val = str(Decimal(str(c.value)))
                    opt.add_soft(v[c.var] == z3.RealVal(dec_val), weight)
                elif c.var in STRING_VARS:
                    opt.add_soft(v[c.var] == z3.StringVal(str(c.value)), weight)
                elif c.var in BOOL_VARS:
                    b_val = c.value if isinstance(c.value, bool) else (str(c.value).lower() == "true")
                    opt.add_soft(v[c.var] == z3.BoolVal(b_val), weight)

        if opt.check() != z3.sat:
            return []

        model = opt.model()
        repairs: list[dict[str, Any]] = []

        # Compare model values against original claim values for claims in the minimal core
        for c in claims:
            if c.id not in minimal_core_ids:
                continue

            target_var = v[c.var]
            model_val = model[target_var]
            if model_val is None:
                continue

            # Convert model value to readable string
            if c.var in NUM_VARS:
                if isinstance(model_val, z3.RatNumRef):
                    m_val_num = float(model_val.numerator_as_long()) / float(model_val.denominator_as_long())
                else:
                    m_val_num = float(str(model_val))
                
                # Check delta
                if abs(m_val_num - float(c.value)) > 0.001:
                    repairs.append({
                        "claim_id": c.id,
                        "variable": c.var,
                        "current_value": c.value,
                        "counterfactual_value": m_val_num,
                        "action_type": "REDUCE_AMOUNT" if m_val_num < float(c.value) else "ADJUST_METRIC",
                        "repair_recommendation": (
                            f"Adjust {c.var} from {c.value} to {m_val_num} (matches upper threshold)."
                        ),
                    })
            elif c.var in BOOL_VARS:
                m_val_bool = bool(z3.is_true(model_val))
                if m_val_bool != bool(c.value):
                    repairs.append({
                        "claim_id": c.id,
                        "variable": c.var,
                        "current_value": c.value,
                        "counterfactual_value": m_val_bool,
                        "action_type": "PROVIDE_MISSING_EVIDENCE",
                        "repair_recommendation": (
                            f"Locate and verify missing audit evidence for '{c.var}' to validate authorization."
                        ),
                    })
            elif c.var in STRING_VARS:
                m_val_str = model_val.as_string()
                if m_val_str != str(c.value):
                    repairs.append({
                        "claim_id": c.id,
                        "variable": c.var,
                        "current_value": c.value,
                        "counterfactual_value": m_val_str,
                        "action_type": "REVERT_IDENTITY_MUTATION",
                        "repair_recommendation": (
                            f"Revert {c.var} ('{c.value}') to match authorized record ('{m_val_str}')."
                        ),
                    })

        return repairs


counterfactual_engine = CounterfactualRepairEngine()
