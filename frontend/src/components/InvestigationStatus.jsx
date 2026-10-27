export default function InvestigationStatus({ data }) {
  if (!data) return null;

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

      {/* Root Causes List */}
      <div>
        <div style={{ fontSize: '11px', color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600, marginBottom: '8px' }}>
          Identified Root Causes
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {data.root_causes?.map((rc, i) => (
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
              {rc}
            </div>
          ))}
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
