import { useState } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';

export default function ContradictionMatrix({ data }) {
  const [selectedConflict, setSelectedConflict] = useState(null);
  const [expandedClaim, setExpandedClaim] = useState(null);

  if (!data) return null;

  const { contradiction_matrix: matrix = [], claims = [] } = data;

  return (
    <div
      style={{
        height: '100%',
        overflowY: 'auto',
        padding: '16px',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
        background: '#09090b',
        borderLeft: '1px solid #18181b',
      }}
    >
      {/* Contradiction Matrix Header */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
          <div style={{ fontSize: '11px', color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
            Cross-Silo Contradictions
          </div>
          <span style={{ fontSize: '10px', color: '#f59e0b', background: '#f59e0b15', border: '1px solid #f59e0b35', padding: '1px 5px', borderRadius: '3px', fontFamily: 'ui-monospace, monospace' }}>
            {matrix.length} DETECTED
          </span>
        </div>

        {/* Conflict List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {matrix.map((c, i) => (
            <div
              key={i}
              onClick={() => setSelectedConflict(selectedConflict === i ? null : i)}
              style={{
                background: selectedConflict === i ? '#18181b' : '#121215',
                border: selectedConflict === i ? '1px solid #f59e0b' : '1px solid #18181b',
                borderRadius: '6px',
                padding: '9px 11px',
                cursor: 'pointer',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '3px' }}>
                <span style={{ fontSize: '10.5px', color: '#f59e0b', fontFamily: 'ui-monospace, monospace', fontWeight: 600 }}>
                  {c.claim_a_id} ⚡ {c.claim_b_id}
                </span>
                <span style={{ fontSize: '10px', color: '#71717a', fontFamily: 'ui-monospace, monospace' }}>
                  {Math.round(c.score * 100)}% score
                </span>
              </div>
              <div style={{ fontSize: '11.5px', color: '#d4d4d8', lineHeight: '1.4' }}>
                {c.description}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Claims Explorer Accordion */}
      <div>
        <div style={{ fontSize: '11px', color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600, marginBottom: '8px' }}>
          Atomic Claims ({claims.length})
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {claims.map((claim) => {
            const isExpanded = expandedClaim === claim.claim_id;
            return (
              <div
                key={claim.claim_id}
                style={{
                  background: '#121215',
                  border: isExpanded ? '1px solid #38bdf8' : '1px solid #18181b',
                  borderRadius: '6px',
                  overflow: 'hidden',
                }}
              >
                <div
                  onClick={() => setExpandedClaim(isExpanded ? null : claim.claim_id)}
                  style={{
                    padding: '8px 10px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    cursor: 'pointer',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0 }}>
                    <span style={{ fontSize: '10.5px', color: '#38bdf8', fontFamily: 'ui-monospace, monospace', fontWeight: 600 }}>
                      {claim.claim_id}
                    </span>
                    <span style={{ fontSize: '11.5px', color: '#d4d4d8', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {claim.text}
                    </span>
                  </div>
                  {isExpanded ? <ChevronDown size={14} color="#71717a" /> : <ChevronRight size={14} color="#71717a" />}
                </div>

                {isExpanded && (
                  <div style={{ padding: '10px', borderTop: '1px solid #18181b', background: '#0e0e11', fontSize: '11px' }}>
                    <div style={{ color: '#ededed', marginBottom: '8px', lineHeight: '1.5' }}>
                      {claim.text}
                    </div>
                    <div style={{ fontFamily: 'ui-monospace, monospace', color: '#71717a', marginBottom: '4px' }}>
                      Provenance Source: <span style={{ color: '#38bdf8' }}>{claim.source_type}</span>
                    </div>
                    {claim.source_ref && (
                      <div style={{ fontFamily: 'ui-monospace, monospace', color: '#a1a1aa' }}>
                        {Object.entries(claim.source_ref).map(([k, v]) => (
                          <div key={k}>
                            {k}: {String(v)}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
