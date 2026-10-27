"""
VeriFact — FastAPI Application
Autonomous Cross-Silo Forensic Causality Agent
Open Agent Hackathon 2026 | Track 02: "The Agent That Can Explain Why"
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.data.scenarios import list_scenarios
from backend.engines.meterless_hmem import hmem, nightshift
from backend.engines.graph_solver import graph_solver
from backend.pipeline.investigator import investigator

# ──────────────────────────────────────────────────────────────────────────────
# App setup
# ──────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="VeriFact API",
    description=(
        "Autonomous Cross-Silo Forensic Causality Agent. "
        "Powered by Nemotron (Meterless Nightshift) + NetworkX causal graph + "
        "Zetaris USL + Meterless H-MEM."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory investigation store (keyed by investigation_id)
_investigations: dict[str, dict[str, Any]] = {}


# ──────────────────────────────────────────────────────────────────────────────
# Request / Response Models
# ──────────────────────────────────────────────────────────────────────────────

class InvestigateRequest(BaseModel):
    scenario_id: str = Field(
        ...,
        description="ID of the scenario to investigate",
        examples=["procurement_fraud", "sla_breach_coverup", "supply_chain_ghosting"],
    )
    custom_query: str | None = Field(
        default=None,
        description="Optional free-text query to cross-search across all data sources",
    )


class HMemStoreRequest(BaseModel):
    key: str = Field(..., description="Evidence key")
    value: dict[str, Any] = Field(..., description="Evidence value payload")
    session_id: str = Field(
        default_factory=lambda: f"SESS-{uuid.uuid4().hex[:8].upper()}",
        description="H-MEM session namespace",
    )
    provenance: dict[str, Any] = Field(
        default_factory=dict,
        description="Provenance metadata (source, row_id, etc.)",
    )


class HMemRecallRequest(BaseModel):
    query: str = Field(..., description="Keyword query for similarity recall")
    session_id: str = Field(..., description="H-MEM session namespace")
    top_k: int = Field(default=5, ge=1, le=50, description="Max results to return")


# ──────────────────────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Health check — confirms API is live."""
    return {"status": "ok", "version": "1.0.0"}


@app.get("/scenarios", tags=["Scenarios"])
async def get_scenarios() -> dict[str, Any]:
    """Return the list of 3 preloaded investigation scenarios."""
    scenarios = list_scenarios()
    return {
        "scenarios": scenarios,
        "count": len(scenarios),
    }


@app.post("/investigate", tags=["Investigation"])
async def run_investigation(request: InvestigateRequest) -> dict[str, Any]:
    """
    Run a full VeriFact investigation pipeline.

    Steps:
    1. Zetaris USL: federated query across ERP, comms, and document sources
    2. Nemotron: extract structured evidence claims
    3. H-MEM: persist evidence ledger
    4. Graph Solver: build causal DAG, score contradictions, find root causes
    5. Narrative: generate 'Why' explanation + counterfactuals
    """
    valid_ids = {"procurement_fraud", "sla_breach_coverup", "supply_chain_ghosting"}
    if request.scenario_id not in valid_ids:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown scenario_id '{request.scenario_id}'. Valid IDs: {sorted(valid_ids)}",
        )

    try:
        result = await investigator.investigate(
            scenario_id=request.scenario_id,
            custom_query=request.custom_query,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Investigation failed: {exc}") from exc

    # Persist for retrieval
    _investigations[result["investigation_id"]] = result

    return result


@app.get("/investigate/{investigation_id}", tags=["Investigation"])
async def get_investigation(investigation_id: str) -> dict[str, Any]:
    """Retrieve a previously-run investigation result by ID."""
    result = _investigations.get(investigation_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Investigation '{investigation_id}' not found. Run POST /investigate first.",
        )
    return result


@app.get("/graph/{investigation_id}", tags=["Graph"])
async def get_investigation_graph(investigation_id: str) -> dict[str, Any]:
    """
    Return the NetworkX causal graph as JSON nodes+edges for frontend visualization.
    Suitable for D3.js / vis.js / Cytoscape rendering.
    """
    result = _investigations.get(investigation_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Investigation '{investigation_id}' not found.",
        )
    graph = result.get("graph", {})
    return {
        "investigation_id": investigation_id,
        "scenario_id": result.get("scenario_id"),
        "scenario_title": result.get("scenario_title"),
        **graph,
    }


@app.post("/hmem/store", tags=["H-MEM"])
async def hmem_store(request: HMemStoreRequest) -> dict[str, Any]:
    """Store an evidence entry to the Meterless H-MEM ledger."""
    result = hmem.write(
        key=request.key,
        value=request.value,
        session_id=request.session_id,
        provenance=request.provenance,
    )
    return result


@app.get("/hmem/recall", tags=["H-MEM"])
async def hmem_recall(
    query: str,
    session_id: str,
    top_k: int = 5,
) -> dict[str, Any]:
    """
    Recall evidence from H-MEM by keyword similarity.

    Args:
        query: Keyword search query
        session_id: H-MEM session namespace
        top_k: Maximum results to return (default 5)
    """
    results = hmem.recall_similar(query=query, session_id=session_id, top_k=top_k)
    return {
        "query": query,
        "session_id": session_id,
        "results": results,
        "result_count": len(results),
    }


@app.get("/hmem/ledger/{session_id}", tags=["H-MEM"])
async def hmem_ledger(session_id: str) -> dict[str, Any]:
    """Return the full evidence ledger for a session."""
    return hmem.get_full_ledger(session_id)


@app.get("/nightshift/tasks", tags=["Nightshift"])
async def nightshift_tasks() -> dict[str, Any]:
    """List all Meterless Nightshift background tasks."""
    tasks = nightshift.list_tasks()
    return {"tasks": tasks, "count": len(tasks)}


@app.get("/nightshift/tasks/{task_id}", tags=["Nightshift"])
async def nightshift_task_status(task_id: str) -> dict[str, Any]:
    """Get status of a specific Nightshift background task."""
    return nightshift.get_task_status(task_id)


@app.get("/investigations", tags=["Investigation"])
async def list_investigations() -> dict[str, Any]:
    """List all investigations run in the current session."""
    summaries = [
        {
            "investigation_id": inv_id,
            "scenario_id": inv.get("scenario_id"),
            "scenario_title": inv.get("scenario_title"),
            "status": inv.get("status"),
            "completed_at": inv.get("completed_at"),
            "evidence_coverage_pct": inv.get("evidence_coverage_pct"),
            "financial_impact": inv.get("financial_impact"),
            "severity": inv.get("severity"),
        }
        for inv_id, inv in _investigations.items()
    ]
    return {"investigations": summaries, "count": len(summaries)}
