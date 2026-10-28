"""
VeriFact — Synthetic Investigation Scenarios
Three rich, realistic cross-silo forensic investigation scenarios.
"""

from typing import Any

SCENARIOS: list[dict[str, Any]] = [
    {
        "id": "procurement_fraud",
        "title": "Apex Supplies Procurement Fraud",
        "subtitle": "IBAN Swap + Social Engineering (Track 01 + 02)",
        "description": (
            "A $94,750 disbursement went to a vendor IBAN that was never formally authorized. "
            "The CFO approval references an email thread that does not exist in the archive. "
            "The invoice address belongs to an entirely different SEC-registered entity."
        ),
        "severity": "CRITICAL",
        "financial_impact": "$52,750",
        "tags": ["procurement", "fraud", "iban-swap", "social-engineering"],
        "data_sources": ["erp_transactions", "comms_audit", "documents"],
        "expected_root_causes": [
            "IBAN substitution on vendor banking record",
            "Forged CFO approval referencing non-existent email thread #4471",
            "Invoice address mismatch — SEC EDGAR shows different legal entity",
        ],
        "raw_evidence": [
            {
                "source": "erp_transactions",
                "record_type": "purchase_order",
                "row_id": 1001,
                "content": (
                    "PO-2024-1001 | Vendor: Apex Supplies Ltd | IBAN: GB29NWBK60161331926819 "
                    "(ending 8821) | Amount: $42,000.00 | Status: Authorized | "
                    "Authorized by: CFO-jenkins | Date: 2024-09-14"
                ),
            },
            {
                "source": "erp_transactions",
                "record_type": "payment_dispatch",
                "row_id": 2047,
                "content": (
                    "PAY-2024-2047 | Vendor: Apex Supplies Ltd | IBAN: DE89370400440532013304 "
                    "(ending 3304) | Amount: $94,750.00 | Status: Dispatched | "
                    "Dispatched by: AP-system | Date: 2024-09-19"
                ),
            },
            {
                "source": "comms_audit",
                "record_type": "slack_message",
                "message_id": "SLK-4471",
                "content": (
                    "[Slack #finance-approvals | 2024-09-18 11:42 UTC] CFO-jenkins: "
                    "'Approved vendor change per email thread #4471 — updated banking details for Apex. "
                    "Proceed with payment.' | Reactions: 2"
                ),
            },
            {
                "source": "comms_audit",
                "record_type": "email_thread",
                "thread_id": "EMAIL-4471",
                "content": (
                    "[EMAIL ARCHIVE QUERY] Thread #4471 — NOT FOUND. "
                    "Archive search returned 0 results for thread ID 4471. "
                    "Thread may have been deleted or never existed."
                ),
            },
            {
                "source": "documents",
                "record_type": "invoice_pdf",
                "doc_id": "INV-APEX-2024-09",
                "page": 1,
                "bbox": [72, 180, 540, 220],
                "content": (
                    "INVOICE | Apex Supplies Ltd | Suite 400, 55 Water St, New York, NY 10041 | "
                    "Invoice #: INV-7821 | Date: 2024-09-17 | Amount Due: $94,750.00 | "
                    "IBAN: DE89370400440532013304"
                ),
            },
            {
                "source": "documents",
                "record_type": "sec_edgar_lookup",
                "doc_id": "EDGAR-55WATER-ST",
                "content": (
                    "SEC EDGAR Entity Search | Address: Suite 400, 55 Water St, New York, NY 10041 | "
                    "Registered Entity: TechNova LLC | EIN: 83-4421109 | "
                    "NOT Apex Supplies Ltd — address belongs to a different legal entity."
                ),
            },
        ],
    },
    {
        "id": "sla_breach_coverup",
        "title": "Cloud SLA Breach Coverup",
        "subtitle": "Unauthorized Config Change → Cascading Failure (Track 02)",
        "description": (
            "A hotfix commit disabling connection pool limits caused p99 latency to spike to 8,200ms — "
            "16 seconds before PagerDuty even fired an alert. The 23-minute SLA breach triggered a "
            "$5,750 penalty. The runbook violation (single engineer approval) was not disclosed."
        ),
        "severity": "HIGH",
        "financial_impact": "$5,750",
        "tags": ["sla", "incident", "config-change", "runbook-violation", "coverup"],
        "data_sources": ["erp_transactions", "comms_audit", "documents"],
        "expected_root_causes": [
            "Unauthorized connection pool config change by j.malik at 14:21:33 UTC",
            "Runbook violation: only 1 of 2 required senior engineer approvals obtained",
            "Latency degraded 16 seconds BEFORE alert fired — monitoring gap",
            "23-minute p99 breach at $15,000/hour = $5,750 SLA penalty",
        ],
        "raw_evidence": [
            {
                "source": "comms_audit",
                "record_type": "pagerduty_incident",
                "incident_id": "PD-2024-8821",
                "content": (
                    "[PagerDuty] ALERT FIRED at 14:23:07 UTC | Service: payments-api | "
                    "Severity: P1 | Title: High latency detected | "
                    "Assigned to: oncall-sre-team | Acknowledged: 14:27:33 UTC"
                ),
            },
            {
                "source": "comms_audit",
                "record_type": "grafana_metric",
                "metric_id": "GRF-PAYMENTS-P99",
                "content": (
                    "[Grafana metrics export] Service: payments-api | Metric: http_request_duration_p99 | "
                    "14:22:45 UTC: 45ms (baseline) | "
                    "14:22:51 UTC: 8,200ms (spike onset — 16s BEFORE PagerDuty alert) | "
                    "14:23:07 UTC: 9,400ms (alert fires) | "
                    "14:46:02 UTC: 52ms (resolved)"
                ),
            },
            {
                "source": "comms_audit",
                "record_type": "git_commit",
                "commit_sha": "a7f3c19",
                "content": (
                    "[Git log] commit a7f3c19 | Author: j.malik | "
                    "Timestamp: 2024-10-15T14:21:33Z | "
                    "Message: 'hotfix: disable connection pool limits temporarily' | "
                    "Files changed: config/payments-api/pool.yaml (+1/-3) | "
                    "Approvals: 1 (engineer: r.chen) | Required: 2"
                ),
            },
            {
                "source": "documents",
                "record_type": "sla_contract",
                "doc_id": "SLA-PAYMENTS-2024",
                "page": 4,
                "bbox": [72, 310, 540, 380],
                "content": (
                    "SLA Contract v3.2 — Section 4.1: payments-api p99 latency SLA = 500ms. "
                    "Penalty clause 4.1(b): breach duration >2 minutes triggers penalty of $15,000 per hour "
                    "(pro-rated per minute). Breach window measured from first metric exceedance to recovery."
                ),
            },
            {
                "source": "documents",
                "record_type": "runbook",
                "doc_id": "RB-CONN-POOL-007",
                "page": 2,
                "bbox": [72, 140, 540, 200],
                "content": (
                    "Runbook RB-007: Connection Pool Configuration Changes. "
                    "MANDATORY: All changes to connection pool parameters require approval from "
                    "2 (two) senior engineers before deployment to production. "
                    "Single approvals are insufficient and constitute a policy violation. "
                    "Escalate to: SRE Lead + Engineering Manager."
                ),
            },
            {
                "source": "comms_audit",
                "record_type": "audit_log",
                "log_id": "AUDIT-DEPLOY-14213",
                "content": (
                    "[Audit Log] Deployment: payments-api config update | "
                    "Deployed by: j.malik | Time: 14:21:33 UTC | "
                    "Approval count: 1 | Approver(s): r.chen (Senior Engineer) | "
                    "Second approval: NOT OBTAINED | "
                    "Deployment proceeded despite incomplete approval chain."
                ),
            },
        ],
    },
    {
        "id": "supply_chain_ghosting",
        "title": "Supply Chain Ghosting",
        "subtitle": "Multi-Stage Inventory Skimming + Insurance Fraud (Track 03)",
        "description": (
            "45,000 units of SKU-7821 were ordered and fully paid ($2.3M, pre-shipment). "
            "Shipping, customs, and warehouse receipts show a progressive 13,800-unit loss "
            "with no loss declarations. An insurance claim for only 2,100 units was filed — "
            "vastly underreporting the discrepancy."
        ),
        "severity": "CRITICAL",
        "financial_impact": "$2,300,000",
        "tags": ["supply-chain", "inventory", "fraud", "insurance", "collusion"],
        "data_sources": ["erp_transactions", "comms_audit", "documents"],
        "expected_root_causes": [
            "6,500 units missing at customs with no loss/damage declaration",
            "Additional 7,300 units missing between customs and warehouse receipt",
            "Insurance claim filed for only 2,100 units — 11,700 units unaccounted",
            "Full $2.3M payment made to Horizon Manufacturing BEFORE shipment (Oct 8 vs Oct 12)",
            "Possible multi-party collusion across customs, logistics, and warehouse",
        ],
        "raw_evidence": [
            {
                "source": "erp_transactions",
                "record_type": "purchase_order",
                "row_id": 3301,
                "content": (
                    "PO-2024-3301 | Vendor: Horizon Manufacturing | "
                    "SKU: SKU-7821 | Quantity Ordered: 45,000 units | "
                    "Unit Price: $51.11 | Total: $2,300,000.00 | "
                    "Order Date: 2024-10-01 | Expected Delivery: 2024-10-25"
                ),
            },
            {
                "source": "erp_transactions",
                "record_type": "payment",
                "row_id": 3401,
                "content": (
                    "PAY-2024-3401 | Vendor: Horizon Manufacturing | "
                    "Amount: $2,300,000.00 | Payment Date: 2024-10-08 | "
                    "Status: CLEARED | Note: Full pre-payment per contract clause 7b | "
                    "Payment made BEFORE shipment departed (Oct 12)"
                ),
            },
            {
                "source": "documents",
                "record_type": "shipping_manifest",
                "doc_id": "SHIP-SHANGHAI-OCT12",
                "page": 1,
                "bbox": [72, 200, 540, 260],
                "content": (
                    "Shipping Manifest | Vessel: MV Horizon Star | "
                    "Port of Departure: Shanghai Yangshan, China | "
                    "Departure Date: 2024-10-12 | "
                    "Cargo: SKU-7821 | Quantity: 45,000 units | "
                    "Weight: 135,000 kg | Seal #: SHNG-77821-X"
                ),
            },
            {
                "source": "documents",
                "record_type": "customs_clearance",
                "doc_id": "CUSTOMS-LA-OCT22",
                "page": 1,
                "bbox": [72, 300, 540, 360],
                "content": (
                    "US Customs and Border Protection | Port: Los Angeles | "
                    "Clearance Date: 2024-10-22 | "
                    "SKU-7821 | Quantity Cleared: 38,500 units | "
                    "Discrepancy: -6,500 units vs manifest | "
                    "Loss/Damage Declaration: NONE FILED | "
                    "CBP Officer: ID-4421 | Note: No explanation provided for shortfall."
                ),
            },
            {
                "source": "erp_transactions",
                "record_type": "warehouse_receipt",
                "row_id": 3501,
                "content": (
                    "Warehouse Receipt | Facility: LA-WEST-07 | "
                    "Received Date: 2024-10-24 | "
                    "SKU-7821 | Quantity Received: 31,200 units | "
                    "Expected (post-customs): 38,500 units | "
                    "Discrepancy: -7,300 units | "
                    "Receiver: W. Okonkwo | No damage report filed."
                ),
            },
            {
                "source": "documents",
                "record_type": "insurance_claim",
                "doc_id": "INS-CLAIM-2024-1188",
                "page": 1,
                "bbox": [72, 150, 540, 220],
                "content": (
                    "Insurance Claim #INS-1188 | Claimant: Horizon Manufacturing | "
                    "Policy: Marine Cargo CMC-44210 | "
                    "Claimed Loss: 2,100 units of SKU-7821 | "
                    "Claimed Value: $107,331.00 | "
                    "Filed Date: 2024-10-25 | "
                    "Note: Actual discrepancy = 13,800 units — claim is vastly underreported."
                ),
            },
        ],
    },
]


def get_scenario(scenario_id: str) -> dict[str, Any] | None:
    """Return a scenario by ID, or None if not found."""
    return next((s for s in SCENARIOS if s["id"] == scenario_id), None)


def list_scenarios() -> list[dict[str, Any]]:
    """Return lightweight scenario summaries for the /scenarios endpoint."""
    return [
        {
            "id": s["id"],
            "title": s["title"],
            "subtitle": s["subtitle"],
            "description": s["description"],
            "severity": s["severity"],
            "financial_impact": s["financial_impact"],
            "tags": s["tags"],
        }
        for s in SCENARIOS
    ]
