# VeriFact: Autonomous Cross-Silo Forensic Causality & Evidence Provenance Agent

[![Hackathon Track](https://img.shields.io/badge/Track_02-The_Agent_That_Can_Explain_Why-blue.svg?style=for-the-badge)](https://hackathon.genai.works/event/open-agent-hackathon-2026)
[![Formal Prover](https://img.shields.io/badge/Verification-Z3_SMT_Deletion--Minimized_MUS-purple.svg?style=for-the-badge)](https://github.com/Z3Prover/z3)
[![MaxSMT Repair](https://img.shields.io/badge/Repair_Engine-Z3_Optimize_MaxSMT-008080.svg?style=for-the-badge)](https://github.com/Z3Prover/z3)
[![In-Kind Target](https://img.shields.io/badge/NVIDIA_Prize-Best_Use_of_NVIDIA_Nemotron-76B900.svg?style=for-the-badge&logo=nvidia)](https://hackathon.genai.works/event/open-agent-hackathon-2026)
[![Tests Passing](https://img.shields.io/badge/Tests-9_Passed-brightgreen.svg?style=for-the-badge)](./tests)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](./LICENSE)

> **"An LLM that generates narrative text does not explain why. An agent that extracts typed proposition variables across fragmented silos, calculates true deletion-minimized UNSAT cores, produces offline-reproducible SMT-LIB2 proofs, and derives prospective counterfactual repairs under strict governance rules does."**

Built for the **Open Agent Hackathon 2026** (Track 02: *The Agent That Can Explain Why*), **VeriFact** is an enterprise forensic causality agent. When silent procurement fraud, cloud SLA violations, or supply chain inventory leaks occur, VeriFact:
1. Queries fragmented enterprise silos via the **Zetaris Universal Semantic Layer (USL)** pattern.
2. Deconstructs unstructured evidence into typed proposition variables using **NVIDIA Nemotron 3.5 Bolt**.
3. Employs the **Z3 SMT Theorem Prover** to mathematically calculate a **True Deletion-Minimized UNSAT Core** (the minimal irreducible subset of contradictory enterprise assertions).
4. Generates a **Self-Contained SMT-LIB2 Proof Certificate** downloadable for independent offline verification in standalone `z3` and `cvc5`.
5. Uses **MaxSMT (Z3 Optimize)** to compute **Counterfactual Repairs** (*"What would resolve this?"*) while strictly respecting governance boundaries—authoritative purchase orders and contracts are immutable historical facts, presenting qualified operational remediation options subject to human review.
6. Retains and invalidates refuted evidence in **Meterless H-MEM** while scheduling continuous watchers via **Meterless Nightshift**.

---

## 🌐 Live Public Cloudflare Endpoints (Zero Interstitial Warning)

The system is deployed over official **Cloudflare Tunnels** (`trycloudflare.com`) on Cloudflare's global edge network—accessible from any browser without interstitial screens or bypass headers:
- **Interactive UI Dashboard:** [https://ripe-defensive-beginning-hospitals.trycloudflare.com](https://ripe-defensive-beginning-hospitals.trycloudflare.com)
- **Live REST API Base:** [https://cups-arrangements-processing-hoped.trycloudflare.com](https://cups-arrangements-processing-hoped.trycloudflare.com)
- **API Health Check:** `curl -s https://cups-arrangements-processing-hoped.trycloudflare.com/`
- **Execute Live Investigation Over Cloudflare:**
  ```bash
  curl -s -X POST -H "Content-Type: application/json" \
    -d '{"scenario_id": "procurement_fraud"}' \
    https://cups-arrangements-processing-hoped.trycloudflare.com/investigate
  ```

*(Secondary localtunnel fallbacks: Dashboard: `https://six-spoons-care.loca.lt`, API: `https://clean-pets-hide.loca.lt` with header `bypass-tunnel-reminder: 1`)*

---

## 🔬 Formal Verification vs Heuristic LLM Guesswork

In typical agent architectures, "detecting a contradiction" means prompting an LLM: *"Do these two documents clash?"* 
This approach is non-deterministic, hallucinates on complex arithmetic, and cannot produce formal mathematical proof.

VeriFact solves this by converting claims into **Typed Variables & First-Order Background Invariants in Z3**:
$$\text{DisbursementLimit}: \text{ledger.dispatched} > \text{po.amount} \implies \text{email.exists} = \text{True}$$
$$\text{PayeeIdentityMatch}: \text{ledger.iban} = \text{po.iban}$$
$$\text{InventoryConservation}: \text{claimed\_loss} = \text{shipped} - \text{received}$$
$$\text{SLAPenaltyDisclosure}: (\text{p99} > \text{threshold} \land \text{downtime} > 2\text{min}) \implies \text{disclosure.filed} = \text{True}$$

### 1. Deletion-Based Core Minimization (True MUS)
Standard `solver.unsat_core()` calls can contain redundant tracking literals. VeriFact implements **iterative deletion-based minimization**:
For each literal $l \in \text{Core}$, if $\text{Core} \setminus \{l\} \models \bot$, literal $l$ is pruned. The resulting set is guaranteed to be a **Minimal Unsatisfiable Subset (MUS)**:
- Retracting or correcting any single claim in this subset resolves that specific contradiction.
- If no background rules match the extracted variables, the verifier explicitly reports `NO_APPLICABLE_RULES` (with `is_consistent = None`) rather than a vacuous green pass.

### 2. Forensic Governance: Preserving Authoritative Records
A naive solver might attempt to resolve an unauthorized $94,750 payment against a $42,000 PO by proposing: *"Increase the PO amount to $94,750."*
In financial and legal forensics, that is retroactively legitimizing fraud!
VeriFact distinguishes **Authoritative Invariants** from **Operational Knobs**:
- **Authoritative Baselines (Immutable / Hard Constraints):** `po.amount`, `po.iban`, `sla_threshold_ms`, `shipped`, `received`.
- **Actionable Remediations (Mutable / Soft Optimization):** 
  - `ledger.dispatched` $\to$ Propose immediate clawback/intercept of overpayment down to PO ceiling ($52,750 recovery), or obtain formal supplemental board override.
  - `ledger.iban` $\to$ Freeze disbursement to unauthorized account and re-route to vendor's authorized IBAN.
  - `disclosure.filed` $\to$ File mandatory incident breach disclosure and process service credits.
  - `claimed_loss` $\to$ Amend insurance claim to align with verified physical deficit.

### 3. Qualified Human-Reviewed Investigation & Remediation Options
VeriFact does not emit categorical legal commands; all counterfactual outputs are qualified as **Human-Reviewed Investigation Options** subject to institutional, jurisdictional, and contractual verification:
- *Overpayment Option:* Verify settlement status with Treasury. If wire is cleared, evaluate formal inter-bank recall protocols (e.g. SWIFT gpi MT192/camt.056) or submit formal supplemental PO amendment.
- *IBAN Mismatch Option:* Contact paying institution treasury and receiving bank compliance to investigate beneficiary status. Evaluate jurisdictional reporting obligations (e.g. SAR/STR) and confirm authorized vendor coordinates.
- *SLA Breach Option:* Review customer contract SLA terms (Clause 4.2) and post-incident disclosure obligations with legal counsel before issuing official notice and service credits ($5,750).
- *Insurance Shortfall Option:* Verify insurance policy limits, deductible thresholds, and carrier claim amendment guidelines with risk management before submitting supplemental loss documentation.

### 4. Self-Contained Offline SMT-LIB2 Proof Certificates
Every detected contradiction outputs a standalone `.smt2` document asserting claims directly with `:named` tracking labels:
```smt2
; VeriFact SMT-LIB2 Proof Certificate (Z3 v5.3.2.0)
(set-option :produce-unsat-cores true)
(set-logic ALL)
(declare-fun |po.iban| () String)
(declare-fun |ledger.iban| () String)
(assert (= |ledger.iban| |po.iban|))
(assert (! (= |po.iban| "8821") :named |CLM-001::po.iban|))
(assert (! (= |ledger.iban| "3304") :named |CLM-002::ledger.iban|))
(check-sat)
(get-unsat-core)
```
Executing `z3 proof.smt2` or `cvc5 proof.smt2` in an offline terminal evaluates to `unsat` and outputs `(|CLM-001::po.iban| |CLM-002::ledger.iban|)`, completely eliminating reliance on cloud APIs for proof verification.

---

## 📊 Decoupled Blind Benchmark Evaluation (n=30)

To avoid circularity, the benchmark evaluates **30 unseen enterprise cases** across 12 distinct commercial entities, decoupled into separate evaluation stages with no conflation between inconclusive cases and verified controls:

### Stage 1: Extraction Performance (Text $\to$ Typed Claims)
- **Precision:** **1.0000** *(95% CI: 0.9586 – 1.0)*
- **Recall:** **0.9674** *(95% CI: 0.9085 – 0.9888)*
- **F1-Score:** **0.9834**

### Stage 2: Binary SMT Verdict on Applicable Domain Cases ($n=25$)
Evaluated strictly on cases with applicable domain invariants (15 anomalies + 10 controls):
- **Precision:** **1.0000** *(95% CI: 0.7961 – 1.0)*
- **Recall:** **1.0000** *(95% CI: 0.7961 – 1.0)*
- **F1-Score:** **1.0000**
- **Accuracy:** **1.0000** *(95% CI: 0.8668 – 1.0)*
- **Confusion Matrix:** TP=15, FP=0, TN=10, FN=0

### Stage 3: Out-of-Domain & Unconstrained Telemetry Routing ($n=5$)
Evaluated on out-of-domain telemetry (e.g. CPU temps, marketing clicks, unconstrained logs):
- **Routing Accuracy to `NO_APPLICABLE_RULES`:** **1.0000 (5/5)** *(95% CI: 0.5655 – 1.0)*
- **Vacuous Pass / False Alarm Rate:** **0.0000**

### Stage 4: Full 3x3 Multi-Class Confusion Matrix ($n=30$)
| Actual \ Predicted | INCONSISTENT | CONSISTENT | NO_APPLICABLE_RULES |
|---|:---:|:---:|:---:|
| **INCONSISTENT ($n=15$)** | **15** | 0 | 0 |
| **CONSISTENT ($n=10$)** | 0 | **10** | 0 |
| **NO_APPLICABLE_RULES ($n=5$)** | 0 | 0 | **5** |

*Overall 3-Class Accuracy: **1.0000** (95% CI: 0.8865 – 1.0)*

*Run one-line command to reproduce locally:*
```bash
python -m backend.eval.blind_eval
```

---

## 🔬 Full-Pipeline Evaluation on Unfamiliar Entity Records

To evaluate end-to-end performance on records outside the scenario dataset, VeriFact includes a dedicated multi-silo ingestion harness (`backend/eval/full_pipeline_eval.py`). It ingests brand-new records for **Helios Solar Tech** spanning ERP SQL, banking wire dispatches, and email archive search queries:
```bash
python -m backend.eval.full_pipeline_eval
```
*Output: In 10.63ms, executes raw text parsing, verbatim grounding checks, H-MEM persistence, Z3 MUS core extraction (`CLM-001`, `CLM-002`), and MaxSMT recovery recommendations with human-review protocols.*

---

## 🚀 Preloaded Real-World Scenarios

| Scenario | Cross-Silo Data Sources | Z3 SMT Formal Inconsistency | Minimal UNSAT Core | Counterfactual Governance Repair & Operational Protocol |
|---|---|---|---|---|
| **01. Silent Procurement Fraud** | ERP Table `row 1001`, SQL Wire Ledger `row 2047`, Slack Audit, SEC EDGAR | Dispatched (\$94,750) > PO limit (\$42,000) requires archive email; archive confirms email missing; payment sent to unapproved IBAN ...3304. | `CLM-001`, `CLM-002` | **Remedy:** Clawback \$52,750 overpayment to restore authorized PO cap (\$42,000); freeze payment to ...3304 and re-route to approved IBAN ...8821.<br>**Protocol (Human Review):** Treasury evaluates SWIFT gpi recall (MT192) and bank compliance investigates beneficiary account. |
| **02. Cloud SLA Breach Coverup** | Grafana Telemetry, Prometheus p99, Git Commits, SLA Contract | Telemetry p99 (8,200ms) for 23min strictly breaches contract clause 4.2 (limit 500ms for >2min); triggers mandatory disclosure; disclosure log is absent. | `CLM-002`, `CLM-004`, `CLM-006` | **Remedy:** File mandatory customer SLA incident breach disclosure.<br>**Protocol (Human Review):** Legal reviews contract clause 4.2 and issues \$5,750 credit memo. |
| **03. Supply Chain Ghost Inventory** | Shipping Manifest, Customs Clearance, Warehouse Receipt, Insurance | Conservation of physical mass violated: Manifest shows 45,000 shipped, warehouse received 31,200 (deficit 13,800), but insurance filing claims only 2,100 units. | `CLM-003`, `CLM-005`, `CLM-006` | **Remedy:** Amend insurance claim from 2,100 units to 13,800 units.<br>**Protocol (Human Review):** Risk management prepares supplemental Proof of Loss citing customs shortfall tallies. |

---

## 🛠️ Quickstart

### Prerequisites
- Python 3.10+
- Node.js 18+

### 1. Install Dependencies & Run Tests
```bash
# Clone
git clone https://github.com/AmanM006/verifact.git
cd verifact

# Python environment
pip install -r backend/requirements.txt
pip install z3-solver pytest

# Run the formal verification test suite
python -m pytest tests/ -v
# (9 passed in ~0.77s — validates MUS minimality, payee IBAN matching, counterfactual governance invariance, unfamiliar entity pipeline)
```

### 2. Launch Backend API
```bash
python -m uvicorn backend.main:app --port 8000 --reload
```
*Interactive Swagger Documentation: `http://localhost:8000/docs`*

### 3. Launch Frontend Dashboard
```bash
cd frontend
npm install
npm run dev
```
*Open `http://localhost:5173` to explore the interactive evidence canvas, contradiction matrix, and one-click SMT-LIB2 proof download.*

---

## ⚖️ System Disclosures, Conformance & Sponsor Architecture Boundaries

We adhere strictly to hackathon submission transparency guidelines:
- **Zetaris USL Integration:** Implemented following the Zetaris Universal Semantic Layer pattern with multi-source schema federation (`backend/engines/zetaris_client.py`). Implemented as an in-memory SQL/dictionary federated adapter across 3 simulated silos (ERP SQLite, Comms, Documents) to ensure 100% deterministic local judging evaluation.
- **Meterless State Engine:** Implements the `H-MEM` specification for hierarchical session indexing and evidence refutation (`backend/engines/meterless_hmem.py`), alongside `MeterlessNightshift` task dispatch.
- **AI Inference:** The reasoner client defines the full API schema for `nvidia/nemotron-3.5-bolt-e4b` through the Meterless Nightshift endpoint (`https://api.nightshift.meterless.io/v1/chat/completions`). When `NIGHTSHIFT_API_KEY` is not present, it routes to a local deterministic extractor to guarantee continuous judging evaluation without network failure.
- **SMT Scope & Limitations:** Z3 proves **logical and arithmetic inconsistency between asserted claims and domain invariants**; it does not independently verify whether real-world events occurred or prove legal intent. Upstream extraction represents the primary real-world bottleneck, which is why VeriFact includes a verbatim Claim Grounding Gate.

---

## 👥 Authors
Built for the **Open Agent Hackathon 2026** (Track 02 & Best Use of NVIDIA Nemotron).  
Repository: [https://github.com/AmanM006/verifact](https://github.com/AmanM006/verifact)  
Licensed under the **MIT License**.
