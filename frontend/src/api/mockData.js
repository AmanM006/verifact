export const MOCK_SCENARIOS = [
  {
    id: "procurement_fraud",
    title: "Apex Supplies Procurement Fraud",
    description: "A $94,750 disbursement went to an unverified vendor IBAN. CFO approval references missing email thread #4471. Invoice address mismatches SEC EDGAR records.",
    tags: ["Track 02", "Explain Why"],
    impact: "$52,750 leaked",
    track: "02"
  },
  {
    id: "sla_breach_coverup",
    title: "Cloud SLA Breach Coverup",
    description: "p99 latency spiked to 8,200ms following an unauthorized connection pool hotfix. PagerDuty alert was delayed by 16s. 23-minute SLA violation covered up.",
    tags: ["Track 02", "Infrastructure"],
    impact: "$5,750 penalty",
    track: "02"
  },
  {
    id: "supply_chain_ghosting",
    title: "Supply Chain Ghost Inventory",
    description: "13,800 units went missing across transit checkpoints. Full $2.3M payment cleared before shipping, followed by a drastically underreported insurance claim.",
    tags: ["Track 02", "Forensic"],
    impact: "$2.3M exposed",
    track: "02"
  }
];

export const MOCK_INVESTIGATION = {
  investigation_id: "INV-20261027-001",
  scenario_id: "procurement_fraud",
  status: "complete",
  summary: "Multi-vector procurement fraud detected. IBAN substitution combined with forged CFO approval enabled unauthorized transfer of $52,750. Evidence from 3 independent silos confirms coordinated social engineering attack.",
  root_causes: [
    "IBAN substitution on vendor record (confidence: 0.97)",
    "Missing email thread #4471 breaks authorization chain (confidence: 0.91)",
    "Address mismatch with SEC EDGAR registry confirms identity fraud (confidence: 0.89)"
  ],
  contradiction_matrix: [
    { claim_a_id: "CLM-001", claim_b_id: "CLM-002", score: 0.94, type: "value_discrepancy", description: "ERP PO: $42,000 vs Ledger dispatch: $94,750" },
    { claim_a_id: "CLM-002", claim_b_id: "CLM-003", score: 0.87, type: "identity_conflict", description: "IBAN ending 8821 (ERP) vs IBAN ending 3304 (Ledger)" },
    { claim_a_id: "CLM-004", claim_b_id: "CLM-005", score: 0.91, type: "authorization_gap", description: "CFO approval references missing email #4471" }
  ],
  evidence_coverage_pct: 87.3,
  causal_chain_depth: 4,
  financial_impact: "$52,750",
  recommendations: [
    "Freeze all transactions to IBAN ending 3304 immediately",
    "Initiate forensic audit of email archive for thread #4471",
    "Alert compliance team — vendor identity verification failed at 2 checkpoints",
    "Review authorization workflow for IBAN change requests"
  ],
  claims: [
    {
      claim_id: "CLM-001",
      text: "ERP Purchase Order authorized for $42,000 to Apex Supplies Ltd (IBAN: ...8821)",
      source_type: "sql",
      source_ref: { table: "erp_transactions", row_id: 42, column: "amount" },
      confidence: 0.99,
      timestamp: "2026-10-15T09:23:00Z",
      entity_mentions: ["Apex Supplies Ltd", "$42,000", "IBAN ...8821"],
      claim_type: "financial"
    },
    {
      claim_id: "CLM-002",
      text: "SQL Ledger dispatched $94,750 to Apex Supplies Ltd (IBAN: ...3304)",
      source_ref: { table: "payment_ledger", row_id: 87, column: "amount" },
      confidence: 0.99,
      source_type: "sql",
      timestamp: "2026-10-17T14:41:00Z",
      entity_mentions: ["Apex Supplies Ltd", "$94,750", "IBAN ...3304"],
      claim_type: "financial"
    },
    {
      claim_id: "CLM-003",
      text: "CFO Slack message approves vendor IBAN change referencing email thread #4471",
      source_type: "comms",
      source_ref: { channel: "finance-approvals", message_id: "msg_0041", timestamp: "2026-10-16T11:22:00Z" },
      confidence: 0.85,
      timestamp: "2026-10-16T11:22:00Z",
      entity_mentions: ["CFO", "email thread #4471", "IBAN change"],
      claim_type: "authorization"
    },
    {
      claim_id: "CLM-004",
      text: "Email thread #4471 is absent from corporate email archive",
      source_type: "document",
      source_ref: { archive: "corporate_email", query: "thread_id:4471", result: "NOT_FOUND" },
      confidence: 0.99,
      timestamp: "2026-10-27T00:00:00Z",
      entity_mentions: ["email thread #4471"],
      claim_type: "identity"
    },
    {
      claim_id: "CLM-005",
      text: "SEC EDGAR: address '55 Water St Suite 400 New York' registered to TechNova LLC, not Apex Supplies Ltd",
      source_type: "document",
      source_ref: { registry: "SEC_EDGAR", entity: "TechNova LLC", address: "55 Water St Suite 400 New York" },
      confidence: 0.97,
      timestamp: "2026-10-27T00:00:00Z",
      entity_mentions: ["TechNova LLC", "Apex Supplies Ltd", "55 Water St"],
      claim_type: "identity"
    }
  ],
  graph: {
    nodes: [
      { id: "CLM-001", label: "ERP PO\n$42,000", type: "evidence", confidence: 0.99 },
      { id: "CLM-002", label: "Ledger\n$94,750", type: "evidence", confidence: 0.99 },
      { id: "CLM-003", label: "CFO Approval\nSlack", type: "evidence", confidence: 0.85 },
      { id: "CLM-004", label: "Email #4471\nMISSING", type: "gap", confidence: 0.99 },
      { id: "CLM-005", label: "EDGAR\nMismatch", type: "evidence", confidence: 0.97 },
      { id: "CONTR-001", label: "IBAN\nSwap", type: "contradiction", confidence: 0.94 },
      { id: "CONTR-002", label: "Auth\nGap", type: "contradiction", confidence: 0.91 },
      { id: "ROOT-001", label: "Social Eng.\nAttack", type: "root_cause", confidence: 0.93 },
      { id: "OUT-001", label: "$52,750\nLeaked", type: "outcome", confidence: 0.99 }
    ],
    edges: [
      { source: "CLM-001", target: "CONTR-001", weight: 0.94, label: "contradicts" },
      { source: "CLM-002", target: "CONTR-001", weight: 0.94, label: "contradicts" },
      { source: "CLM-003", target: "CONTR-002", weight: 0.91, label: "references" },
      { source: "CLM-004", target: "CONTR-002", weight: 0.91, label: "missing" },
      { source: "CLM-005", target: "ROOT-001", weight: 0.89, label: "indicates" },
      { source: "CONTR-001", target: "ROOT-001", weight: 0.93, label: "caused_by" },
      { source: "CONTR-002", target: "ROOT-001", weight: 0.91, label: "enabled_by" },
      { source: "ROOT-001", target: "OUT-001", weight: 0.99, label: "resulted_in" }
    ]
  },
  hmem_session_id: "SES-20261027-001",
  processing_time_ms: 1847,
  sponsor_stack: {
    zetaris: "USL query across 3 sources (ERP, Comms, Documents)",
    meterless_hmem: "5 evidence entries stored, 3 contradictions indexed",
    meterless_nightshift: "Active background monitoring",
    nvidia_nemotron: "nvidia/nemotron-3.5-bolt-e4b (or local fallback)"
  }
};
