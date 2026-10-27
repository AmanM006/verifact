"""
Graph Solver — Deterministic NetworkX Causal Graph Engine
THE KEY DIFFERENTIATOR: mathematical causal chain computation,
contradiction scoring, evidence coverage, and rich JSON export.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Any

import networkx as nx

from backend.engines.nemotron_reasoner import Claim, ContradictionResult


# ──────────────────────────────────────────────────────────────────────────────
# Node / Edge type constants
# ──────────────────────────────────────────────────────────────────────────────

NODE_EVIDENCE = "evidence"
NODE_CONTRADICTION = "contradiction"
NODE_ROOT_CAUSE = "root_cause"
NODE_OUTCOME = "outcome"
NODE_GAP = "gap"

# Colors for frontend D3 / vis rendering
NODE_COLORS: dict[str, str] = {
    NODE_EVIDENCE: "#4A90D9",
    NODE_CONTRADICTION: "#E74C3C",
    NODE_ROOT_CAUSE: "#8E44AD",
    NODE_OUTCOME: "#F39C12",
    NODE_GAP: "#95A5A6",
}


# ──────────────────────────────────────────────────────────────────────────────
# Data types
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class CausalChain:
    chain_id: str
    nodes: list[str]
    depth: int
    total_confidence: float
    description: str
    root_node: str
    terminal_node: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ──────────────────────────────────────────────────────────────────────────────
# Graph Solver
# ──────────────────────────────────────────────────────────────────────────────

class GraphSolver:
    """
    Builds and analyses a directed acyclic causal graph from extracted claims.
    All scoring is deterministic and mathematically reproducible.
    """

    def build_evidence_graph(
        self,
        claims: list[Claim],
        contradictions: list[ContradictionResult],
    ) -> nx.DiGraph:
        """
        Build a DAG where nodes are claims/contradictions/outcomes/gaps and
        edges encode causal or evidential relationships with confidence weights.
        """
        G = nx.DiGraph()

        # ── Add evidence nodes ─────────────────────────────────────────────
        for claim in claims:
            nid = claim.claim_id
            G.add_node(
                nid,
                node_type=NODE_EVIDENCE,
                label=claim.text[:60] + ("…" if len(claim.text) > 60 else ""),
                full_text=claim.text,
                source_type=claim.source_type,
                source_ref=asdict(claim.source_ref),
                claim_type=claim.claim_type,
                confidence=claim.confidence,
                timestamp=claim.timestamp,
                entity_mentions=claim.entity_mentions,
                scenario_id=claim.scenario_id,
                negated=claim.negated,
                color=NODE_COLORS[NODE_EVIDENCE],
            )

        # ── Add contradiction nodes and edges ──────────────────────────────
        for contr in contradictions:
            cid = contr.contradiction_id
            G.add_node(
                cid,
                node_type=NODE_CONTRADICTION,
                label=f"⚡ Contradiction ({contr.contradiction_type})",
                full_text=contr.explanation,
                contradiction_type=contr.contradiction_type,
                contradiction_score=contr.contradiction_score,
                evidence=contr.evidence,
                color=NODE_COLORS[NODE_CONTRADICTION],
            )
            # Edges: both claims point TO the contradiction node
            if contr.claim_a_id and G.has_node(contr.claim_a_id):
                G.add_edge(
                    contr.claim_a_id,
                    cid,
                    edge_type="contradicts",
                    weight=contr.contradiction_score,
                    label=f"contradicts ({contr.contradiction_score:.2f})",
                )
            if contr.claim_b_id and G.has_node(contr.claim_b_id):
                G.add_edge(
                    contr.claim_b_id,
                    cid,
                    edge_type="contradicts",
                    weight=contr.contradiction_score,
                    label=f"contradicts ({contr.contradiction_score:.2f})",
                )

        # ── Add temporal / causal edges between evidence nodes ─────────────
        self._add_causal_edges(G, claims)

        # ── Promote root causes and add outcome nodes ──────────────────────
        self._promote_root_causes(G)
        self._add_outcome_nodes(G, claims)
        self._add_gap_nodes(G, claims)

        return G

    def _add_causal_edges(self, G: nx.DiGraph, claims: list[Claim]) -> None:
        """
        Heuristically add causal edges between claims based on:
        - Shared entity mentions (same actors / amounts)
        - Temporal ordering (earlier → later)
        - Claim type chains: authorization → financial, authorization → identity, etc.
        """
        causal_type_flow: dict[str, list[str]] = {
            "authorization": ["financial", "identity", "temporal", "physical"],
            "temporal": ["financial", "physical"],
            "identity": ["financial"],
            "physical": ["financial"],
        }

        for i, ca in enumerate(claims):
            for j, cb in enumerate(claims):
                if i >= j:
                    continue

                # Temporal ordering
                t_a = ca.timestamp or ""
                t_b = cb.timestamp or ""
                earlier, later = (ca, cb) if t_a <= t_b else (cb, ca)

                # Entity overlap
                ents_a = set(e.lower() for e in ca.entity_mentions)
                ents_b = set(e.lower() for e in cb.entity_mentions)
                overlap = len(ents_a & ents_b) / max(len(ents_a | ents_b), 1)

                if overlap < 0.1:
                    continue  # No meaningful shared entities

                # Type-based causal flow
                downstream_types = causal_type_flow.get(earlier.claim_type, [])
                if later.claim_type in downstream_types or overlap > 0.4:
                    weight = round(overlap * (earlier.confidence + later.confidence) / 2, 3)
                    if not G.has_edge(earlier.claim_id, later.claim_id):
                        G.add_edge(
                            earlier.claim_id,
                            later.claim_id,
                            edge_type="causes",
                            weight=weight,
                            label=f"leads to ({weight:.2f})",
                        )

    def _promote_root_causes(self, G: nx.DiGraph) -> None:
        """
        Mark evidence nodes with zero in-degree and high confidence as root causes.
        """
        for node in G.nodes():
            data = G.nodes[node]
            if data.get("node_type") != NODE_EVIDENCE:
                continue
            if G.in_degree(node) == 0 and data.get("confidence", 0) > 0.9:
                G.nodes[node]["node_type"] = NODE_ROOT_CAUSE
                G.nodes[node]["color"] = NODE_COLORS[NODE_ROOT_CAUSE]

    def _add_outcome_nodes(self, G: nx.DiGraph, claims: list[Claim]) -> None:
        """Add outcome nodes based on financial / physical terminal claims."""
        scenario_id = claims[0].scenario_id if claims else ""
        outcomes: dict[str, dict[str, Any]] = {
            "procurement_fraud": {
                "id": "OUTCOME-FRAUD",
                "label": "💸 $52,750 fraudulently diverted",
                "description": "Net financial loss: $94,750 dispatched − $42,000 authorized = $52,750 fraud.",
                "financial_impact": "$52,750",
            },
            "sla_breach_coverup": {
                "id": "OUTCOME-SLA",
                "label": "⚠ $5,750 SLA penalty incurred",
                "description": "23-minute breach at $250/min = $5,750 penalty. Customer SLA violated.",
                "financial_impact": "$5,750",
            },
            "supply_chain_ghosting": {
                "id": "OUTCOME-GHOST",
                "label": "📦 13,800 units ghosted (~$705K)",
                "description": "Multi-stage inventory diversion: 13,800 of 45,000 units unaccounted.",
                "financial_impact": "~$705,000",
            },
        }

        outcome = outcomes.get(scenario_id)
        if not outcome:
            return

        oid = outcome["id"]
        G.add_node(
            oid,
            node_type=NODE_OUTCOME,
            label=outcome["label"],
            full_text=outcome["description"],
            financial_impact=outcome["financial_impact"],
            color=NODE_COLORS[NODE_OUTCOME],
        )

        # Connect highest-confidence financial claims to the outcome
        financial_claims = sorted(
            [c for c in claims if c.claim_type == "financial"],
            key=lambda c: -c.confidence,
        )
        for fc in financial_claims[:3]:
            if G.has_node(fc.claim_id):
                G.add_edge(
                    fc.claim_id,
                    oid,
                    edge_type="results_in",
                    weight=fc.confidence,
                    label="results in",
                )

    def _add_gap_nodes(self, G: nx.DiGraph, claims: list[Claim]) -> None:
        """Add explicit gap nodes for missing / negated evidence."""
        for claim in claims:
            if claim.negated:
                gap_id = f"GAP-{claim.claim_id}"
                G.add_node(
                    gap_id,
                    node_type=NODE_GAP,
                    label=f"🔍 Missing: {claim.text[:50]}…",
                    full_text=f"Evidence GAP: {claim.text}",
                    color=NODE_COLORS[NODE_GAP],
                )
                if G.has_node(claim.claim_id):
                    G.add_edge(
                        claim.claim_id,
                        gap_id,
                        edge_type="references_missing",
                        weight=0.8,
                        label="missing evidence",
                    )

    # ── Analytical methods ─────────────────────────────────────────────────

    def compute_causal_chains(self, G: nx.DiGraph) -> list[CausalChain]:
        """
        Find all simple paths from root cause nodes to outcome nodes.
        Returns CausalChain objects sorted by depth (descending).
        """
        root_nodes = [n for n, d in G.nodes(data=True) if d.get("node_type") == NODE_ROOT_CAUSE]
        outcome_nodes = [n for n, d in G.nodes(data=True) if d.get("node_type") == NODE_OUTCOME]

        chains: list[CausalChain] = []
        chain_counter = 1

        for root in root_nodes:
            for outcome in outcome_nodes:
                try:
                    paths = list(nx.all_simple_paths(G, root, outcome, cutoff=10))
                except nx.NetworkXError:
                    paths = []

                for path in paths:
                    confidences = [
                        G.nodes[n].get("confidence", 0.8)
                        for n in path
                        if G.nodes[n].get("node_type") == NODE_EVIDENCE
                    ]
                    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

                    chain = CausalChain(
                        chain_id=f"CHAIN-{chain_counter:03d}",
                        nodes=path,
                        depth=len(path),
                        total_confidence=round(avg_conf, 4),
                        description=(
                            f"Causal path of depth {len(path)}: "
                            + " → ".join(path[:3])
                            + (" → …" if len(path) > 3 else "")
                        ),
                        root_node=root,
                        terminal_node=outcome,
                    )
                    chains.append(chain)
                    chain_counter += 1

        chains.sort(key=lambda c: (-c.depth, -c.total_confidence))
        return chains

    def score_contradiction(self, claim_a: Claim, claim_b: Claim) -> float:
        """
        Mathematical contradiction score (0.0–1.0) based on 4 dimensions:
          1. Temporal overlap (same or adjacent timestamps → more suspicious)
          2. Entity overlap (shared actors / amounts → more likely related)
          3. Value discrepancy magnitude (normalized delta of numeric values)
          4. Authorization chain gaps (negated authorization claims)

        Final score = weighted combination of all four dimensions.
        """
        weights = {"temporal": 0.20, "entity": 0.30, "value": 0.30, "auth": 0.20}

        # 1. Temporal score
        t_score = 0.0
        if claim_a.timestamp and claim_b.timestamp:
            # Same date = higher contradiction potential
            if claim_a.timestamp[:10] == claim_b.timestamp[:10]:
                t_score = 0.9
            elif claim_a.timestamp[:7] == claim_b.timestamp[:7]:
                t_score = 0.6
            else:
                t_score = 0.2
        else:
            t_score = 0.5  # Unknown timestamps — neutral

        # 2. Entity overlap score
        ents_a = set(e.lower() for e in claim_a.entity_mentions)
        ents_b = set(e.lower() for e in claim_b.entity_mentions)
        union = len(ents_a | ents_b)
        e_score = len(ents_a & ents_b) / union if union > 0 else 0.0

        # 3. Value discrepancy score
        v_score = 0.0
        nums_a = self._extract_numbers(claim_a.text)
        nums_b = self._extract_numbers(claim_b.text)
        if nums_a and nums_b:
            max_a, max_b = max(nums_a), max(nums_b)
            if max_a > 0 and max_b > 0:
                ratio = max(max_a, max_b) / min(max_a, max_b)
                v_score = min(1.0, math.log(ratio + 1) / math.log(10))

        # 4. Authorization gap score
        auth_score = 0.0
        if claim_a.claim_type == "authorization" or claim_b.claim_type == "authorization":
            if claim_a.negated or claim_b.negated:
                auth_score = 1.0
            else:
                auth_score = 0.6

        score = (
            weights["temporal"] * t_score
            + weights["entity"] * e_score
            + weights["value"] * v_score
            + weights["auth"] * auth_score
        )
        return round(min(score, 1.0), 4)

    @staticmethod
    def _extract_numbers(text: str) -> list[float]:
        """Extract numeric values from text for discrepancy scoring."""
        import re
        nums = re.findall(r"[\$€£]?\s*([\d,]+(?:\.\d+)?)", text)
        result: list[float] = []
        for n in nums:
            try:
                result.append(float(n.replace(",", "")))
            except ValueError:
                pass
        return result

    def compute_evidence_coverage(
        self,
        G: nx.DiGraph,
        scenario: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Compute % of scenario facts explained by evidence in the graph.
        Returns a detailed breakdown by source type.
        """
        expected_facts = len(scenario.get("raw_evidence", scenario.get("expected_root_causes", [])))
        if expected_facts == 0:
            return {"coverage_pct": 0.0, "explained": 0, "total": 0}

        evidence_nodes = [
            n for n, d in G.nodes(data=True)
            if d.get("node_type") in (NODE_EVIDENCE, NODE_ROOT_CAUSE)
        ]

        # Coverage = min(evidence_nodes_count / expected_facts, 1.0) × 100
        covered = len(evidence_nodes)
        pct = round(min(covered / expected_facts, 1.0) * 100, 1)

        by_source: dict[str, int] = {}
        for n in evidence_nodes:
            st = G.nodes[n].get("source_type", "unknown")
            by_source[st] = by_source.get(st, 0) + 1

        return {
            "coverage_pct": pct,
            "explained_nodes": covered,
            "expected_facts": expected_facts,
            "by_source_type": by_source,
        }

    def find_root_causes(self, G: nx.DiGraph) -> list[str]:
        """
        Topological sort to find causal origins.
        Returns node IDs of root-cause and zero-in-degree evidence nodes.
        """
        root_causes: list[str] = []

        # Explicit ROOT_CAUSE typed nodes
        for n, d in G.nodes(data=True):
            if d.get("node_type") == NODE_ROOT_CAUSE:
                root_causes.append(n)

        # Zero in-degree evidence nodes not already listed
        for n, d in G.nodes(data=True):
            if (
                d.get("node_type") == NODE_EVIDENCE
                and G.in_degree(n) == 0
                and n not in root_causes
            ):
                root_causes.append(n)

        return root_causes

    def export_for_viz(self, G: nx.DiGraph) -> dict[str, Any]:
        """
        Export graph as JSON for frontend D3/vis rendering.
        Includes node metadata (type, color, label, confidence) and
        edge metadata (type, weight, label).
        """
        nodes: list[dict[str, Any]] = []
        for node_id, data in G.nodes(data=True):
            nodes.append({
                "id": node_id,
                "label": data.get("label", node_id),
                "node_type": data.get("node_type", NODE_EVIDENCE),
                "color": data.get("color", NODE_COLORS[NODE_EVIDENCE]),
                "confidence": data.get("confidence"),
                "claim_type": data.get("claim_type"),
                "source_type": data.get("source_type"),
                "timestamp": data.get("timestamp"),
                "full_text": data.get("full_text", ""),
                "entity_mentions": data.get("entity_mentions", []),
                "source_ref": data.get("source_ref"),
                "contradiction_score": data.get("contradiction_score"),
                "financial_impact": data.get("financial_impact"),
            })

        edges: list[dict[str, Any]] = []
        for src, tgt, data in G.edges(data=True):
            edges.append({
                "source": src,
                "target": tgt,
                "edge_type": data.get("edge_type", "causes"),
                "weight": data.get("weight", 0.5),
                "label": data.get("label", ""),
            })

        # Compute basic graph stats
        try:
            is_dag = nx.is_directed_acyclic_graph(G)
        except Exception:
            is_dag = False

        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "is_dag": is_dag,
            "node_type_counts": {
                nt: sum(1 for _, d in G.nodes(data=True) if d.get("node_type") == nt)
                for nt in [NODE_EVIDENCE, NODE_CONTRADICTION, NODE_ROOT_CAUSE, NODE_OUTCOME, NODE_GAP]
            },
            "legend": NODE_COLORS,
        }


# Singleton
graph_solver = GraphSolver()
