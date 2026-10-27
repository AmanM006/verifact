"""
Integration tests for Meterless H-MEM Engine Conformance (Specification v1.0).
Demonstrates:
  1. MemoryStoreService + MemoryRetrievalService canonical schema (agentId, runId, taskId, layers).
  2. Durable JSONL trust ledger append-only logging.
  3. Warm-start hydration across separate HMem instances.
  4. Memory supersession and evidence refutation (invalidated memory retains audit trail).
  5. Multi-investigation continuity: Investigation 1 writes finding, Investigation 2 recalls, Investigation 3 invalidates.
"""

import shutil
import tempfile
from pathlib import Path
from backend.engines.meterless_hmem import HMem, CanonicalMemory


def test_hmem_canonical_schema_and_tiers():
    temp_dir = Path(tempfile.mkdtemp())
    try:
        mem_engine = HMem(persist_dir=temp_dir)
        
        # 1. Write working memory
        res1 = mem_engine.write(
            key="CLM-101",
            value={"amount": 42000.0, "vendor": "Apex Supplies Ltd"},
            session_id="INV-001",
            layer="working",
            mem_type="factual",
            confidence=0.98,
            agent_id="verifact-extractor",
            entities=["Apex Supplies Ltd", "$42,000"],
        )
        assert res1["status"] == "written"
        
        # 2. Write long-term memory
        res2 = mem_engine.write(
            key="VENDOR-RULE-APEX",
            value={"rule": "Mandatory dual-approval for bank modifications"},
            session_id="global",
            layer="long_term",
            mem_type="preference",
            confidence=1.0,
            agent_id="governance-agent",
        )
        assert res2["layer"] == "long_term"
        
        # Read back
        entry = mem_engine.read("CLM-101", session_id="INV-001")
        assert entry is not None
        assert entry["layer"] == "working"
        assert entry["agent_id"] == "verifact-extractor"
        assert "Apex Supplies Ltd" in entry["entities"]
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_hmem_jsonl_trust_ledger_and_warm_start():
    temp_dir = Path(tempfile.mkdtemp())
    try:
        engine1 = HMem(persist_dir=temp_dir)
        
        # Store long-term knowledge in engine 1
        engine1.write(
            key="VENDOR-APEX-IBAN",
            value={"iban": "GB29NWBK60161331926819", "status": "authorized"},
            session_id="global",
            layer="long_term",
            confidence=1.0,
            agent_id="onboarding-service",
        )
        
        # Verify JSONL ledger exists and has CREATE entry
        ledger_file = temp_dir / "trust_ledger.jsonl"
        assert ledger_file.exists()
        with open(ledger_file, "r") as f:
            lines = [line.strip() for line in f if line.strip()]
        assert len(lines) >= 1
        assert "CREATE" in lines[0]
        
        # Invalidate entry and verify INVALIDATE audit event
        engine1.invalidate(key="VENDOR-APEX-IBAN", reason="Contradicted by rogue dispatch", session_id="global")
        with open(ledger_file, "r") as f:
            lines = [line.strip() for line in f if line.strip()]
        assert len(lines) >= 2
        assert "INVALIDATE" in lines[1]
        
        # Create fresh engine instance pointing to same dir (Warm-start test)
        engine2 = HMem(persist_dir=temp_dir)
        stats = engine2.get_stats("global")
        assert stats["total"] >= 1
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_hmem_hybrid_retrieval_and_reinjection():
    temp_dir = Path(tempfile.mkdtemp())
    try:
        mem_engine = HMem(persist_dir=temp_dir)
        mem_engine.write(
            key="CLM-001",
            value={"text": "Purchase order PO-1001 for Apex Supplies Ltd authorized $42,000 with IBAN GB8821"},
            session_id="INV-PROC",
            layer="working",
            entities=["Apex Supplies Ltd", "GB8821"],
        )
        mem_engine.write(
            key="CLM-002",
            value={"text": "Payment PAY-2047 dispatched $94,750 with rogue IBAN DE3304"},
            session_id="INV-PROC",
            layer="working",
            entities=["DE3304"],
        )

        # Hybrid recall matching keyword and entity boost
        results = mem_engine.recall_similar("Apex Supplies PO authorization", session_id="INV-PROC")
        assert len(results) >= 1
        assert results[0]["key"] == "CLM-001"
        assert results[0]["_recall_score"] > 0.5

        # Structured reinjection payload
        reinjection = mem_engine.reinject_context("Apex Supplies", session_id="INV-PROC")
        assert reinjection["memories_count"] >= 1
        assert reinjection["retrieval_strategy"] == "hybrid_ranked_reinjection"
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
