export default function InvestigationStatus({ data }) {
  if (!data) return null;

  const downloadProofCertificate = () => {
    const smt2 = data.smt_verification?.proof_certificate?.full_smt_lib2;
    if (!smt2) return;
    const blob = new Blob([smt2], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `verifact_proof_${data.scenario_id || 'inconsistency'}.smt2`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div
      style={{
        height: '100%',
        overflowY: 'auto',
        padding: '16px',
        display: 'flex',
        flexDirection: 'column',
        gap: '14px',
        background: '#09090b',
        borderRight: '1px solid #18181b',
      }}
    >
      {/* Top Meta Line */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '11px', color: '#a1a1aa', fontFamily: 'ui-monospace, monospace' }}>
            {data.investigation_id}
          </span>
          <span style={{ fontSize: '10px', color: '#10b981', border: '1px solid #10b98140', padding: '1px 5px', borderRadius: '3px', fontFamily: 'ui-monospace, monospace' }}>
            RESOLVED
          </span>
        </div>
        {data.financial_impact && (
          <span style={{ fontSize: '11px', color: '#ef4444', fontFamily: 'ui-monospace, monospace', fontWeight: 600 }}>
            {data.financial_impact}
          </span>
        )}
      </div>

      {/* Summary Narrative */}
      <div
        style={{
          background: '#121215',
          border: '1px solid #18181b',
          borderRadius: '6px',
          padding: '12px',
          fontSize: '12.5px',
          color: '#d4d4d8',
          lineHeight: '1.55',
        }}
      >
        {data.summary}
      </div>

      {/* KPIs Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
        <div style={{ background: '#121215', border: '1px solid #18181b', borderRadius: '6px', padding: '10px' }}>
          <div style={{ fontSize: '10.5px', color: '#71717a', textTransform: 'uppercase', marginBottom: '4px' }}>
            Evidence Coverage
          </div>
          <div style={{ fontSize: '18px', fontWeight: 700, color: '#38bdf8', fontFamily: 'ui-monospace, monospace' }}>
            {data.evidence_coverage_pct}%
          </div>
        </div>
        <div style={{ background: '#121215', border: '1px solid #18181b', borderRadius: '6px', padding: '10px' }}>
          <div style={{ fontSize: '10.5px', color: '#71717a', textTransform: 'uppercase', marginBottom: '4px' }}>
            Causal Path Depth
          </div>
          <div style={{ fontSize: '18px', fontWeight: 700, color: '#a855f7', fontFamily: 'ui-monospace, monospace' }}>
            {data.causal_chain_depth} hops
          </div>
        </div>
      </div>

      {/* Formal SMT Mathematical Proof Badge (Z3 Solver) */}
      {data.smt_verification && (
        <div
          style={{
            background: data.smt_verification.is_consistent ? '#121215' : 'rgba(239, 68, 68, 0.08)',
            border: `1px solid ${data.smt_verification.is_consistent ? '#27272a' : 'rgba(239, 68, 68, 0.3)'}`,
            borderRadius: '6px',
            padding: '10px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
            <span style={{ fontSize: '10.5px', color: data.smt_verification.is_consistent ? '#10b981' : '#ef4444', fontWeight: 700, fontFamily: 'ui-monospace, monospace' }}>
              Z3 SMT VERIFIER: {data.smt_verification.verdict}
            </span>
            {data.smt_verification.grounding_gate && (
              <span style={{ fontSize: '9.5px', color: '#a1a1aa', fontFamily: 'ui-monospace, monospace' }}>
                Grounding Gate: {data.smt_verification.grounding_gate.grounded}/{data.smt_verification.grounding_gate.proposed} verified
              </span>
            )}
          </div>
          <div style={{ fontSize: '11px', color: '#d4d4d8', lineHeight: '1.45', marginBottom: '6px' }}>
            {data.smt_verification.formal_proof}
          </div>
          {data.smt_verification.minimal_core?.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
              <span style={{ fontSize: '10px', color: '#71717a', alignSelf: 'center', fontFamily: 'ui-monospace, monospace' }}>Minimal Core:</span>
              {data.smt_verification.minimal_core.map((c) => (
                <span
                  key={c}
                  style={{
                    background: '#18181b',
                    border: '1px solid rgba(239, 68, 68, 0.4)',
                    color: '#ef4444',
                    padding: '1px 5px',
                    borderRadius: '3px',
                    fontSize: '9.5px',
                    fontFamily: 'ui-monospace, monospace',
                  }}
                >
                  {c}
                </span>
              ))}
            </div>
          )}
          {data.smt_verification.proof_certificate?.full_smt_lib2 && (
            <div style={{ marginTop: '8px', paddingTop: '6px', borderTop: '1px solid rgba(255, 255, 255, 0.08)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '9px', color: '#71717a', fontFamily: 'ui-monospace, monospace' }}>
                Reproducible SMT-LIB2 ({data.smt_verification.proof_certificate.solver})
              </span>
              <button
                onClick={downloadProofCertificate}
                title="Download self-contained SMT-LIB2 benchmark to verify UNSAT offline in Z3/CVC5"
                style={{
                  background: 'rgba(239, 68, 68, 0.15)',
                  border: '1px solid rgba(239, 68, 68, 0.4)',
                  color: '#f87171',
                  borderRadius: '3px',
                  padding: '2px 7px',
                  fontSize: '9.5px',
                  cursor: 'pointer',
                  fontFamily: 'ui-monospace, monospace',
                  fontWeight: 600,
                  transition: 'background 0.15s ease',
                }}
              >
                ↓ Download proof.smt2
              </button>
            </div>
          )}
        </div>
      )}

      {/* Counterfactual Repair Proposals (MaxSMT / Z3 Optimize) */}
      {data.counterfactual_repairs?.length > 0 && (
        <div
          style={{
            background: 'rgba(56, 189, 248, 0.05)',
            border: '1px solid rgba(56, 189, 248, 0.25)',
            borderRadius: '6px',
            padding: '10px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
            <span style={{ fontSize: '10.5px', color: '#38bdf8', fontWeight: 700, fontFamily: 'ui-monospace, monospace' }}>
              WHAT WOULD RESOLVE THIS? (MaxSMT)
            </span>
            <span style={{ fontSize: '9px', color: '#71717a', fontFamily: 'ui-monospace, monospace' }}>
              Minimal Counterfactual
            </span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {data.counterfactual_repairs.map((repair, i) => (
              <div
                key={i}
                style={{
                  background: '#121215',
                  border: '1px solid #27272a',
                  borderRadius: '4px',
                  padding: '7px 9px',
                  fontSize: '11px',
                  lineHeight: '1.45',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '4px',
                }}
              >
                <div>
                  <span style={{ color: '#38bdf8', fontFamily: 'ui-monospace, monospace', fontWeight: 600 }}>
                    [{repair.action_type}]:
                  </span>{' '}
                  <span style={{ color: '#d4d4d8' }}>{repair.repair_recommendation}</span>
                </div>
                {repair.execution_protocol && (
                  <div style={{ fontSize: '10px', color: '#a1a1aa', borderTop: '1px solid #1c1c22', paddingTop: '4px', fontFamily: 'ui-monospace, monospace' }}>
                    <span style={{ color: '#f59e0b', fontWeight: 600 }}>Execution Protocol: </span>
                    {repair.execution_protocol}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Root Causes List */}
      <div>
        <div style={{ fontSize: '11px', color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600, marginBottom: '8px' }}>
          Identified Root Causes
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {data.root_causes?.map((rc, i) => {
            const text = typeof rc === 'string' ? rc : (rc?.description || rc?.label || rc?.node_id || JSON.stringify(rc));
            return (
              <div
                key={i}
                style={{
                  background: '#121215',
                  borderLeft: '2px solid #a855f7',
                  borderTop: '1px solid #18181b',
                  borderRight: '1px solid #18181b',
                  borderBottom: '1px solid #18181b',
                  borderRadius: '0 4px 4px 0',
                  padding: '8px 10px',
                  fontSize: '11.5px',
                  color: '#e4e4e7',
                  lineHeight: '1.45',
                }}
              >
                {text}
              </div>
            );
          })}
        </div>
      </div>

      {/* Recommended Remediation Actions */}
      {data.recommendations?.length > 0 && (
        <div>
          <div style={{ fontSize: '11px', color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600, marginBottom: '8px' }}>
            Remediation Actions
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
            {data.recommendations.map((rec, i) => (
              <div
                key={i}
                style={{
                  background: '#0e0e11',
                  border: '1px solid #18181b',
                  borderRadius: '4px',
                  padding: '7px 9px',
                  fontSize: '11px',
                  color: '#a1a1aa',
                  lineHeight: '1.4',
                }}
              >
                <span style={{ color: '#ffffff', fontWeight: 600, marginRight: '6px' }}>{i + 1}.</span>
                {rec}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
