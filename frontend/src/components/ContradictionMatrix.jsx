import { useState } from 'react';
import { ChevronDown, ChevronRight, AlertTriangle } from 'lucide-react';

function scoreColor(score) {
  if (score >= 0.8) return '#ef4444';
  if (score >= 0.5) return '#f59e0b';
  return '#10b981';
}

function scoreLabel(score) {
  if (score >= 0.8) return 'HIGH';
  if (score >= 0.5) return 'MED';
  return 'LOW';
}

const SOURCE_ICONS = {
  sql: '🗄️',
  comms: '💬',
  document: '📄',
};

export default function ContradictionMatrix({ data }) {
  const [selectedCell, setSelectedCell] = useState(null);
  const [expandedClaim, setExpandedClaim] = useState(null);

  if (!data) {
    return (
      <div
        style={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#64748b',
          fontSize: '12px',
          fontFamily: 'monospace',
          flexDirection: 'column',
          gap: '8px',
        }}
      >
        <AlertTriangle size={20} color="#1e2d4d" />
        No contradiction data yet
      </div>
    );
  }

  const { contradiction_matrix: matrix, claims } = data;
  const claimIds = [...new Set(matrix.flatMap((m) => [m.claim_a_id, m.claim_b_id]))];

  const getContradiction = (a, b) =>
    matrix.find(
      (m) =>
        (m.claim_a_id === a && m.claim_b_id === b) ||
        (m.claim_a_id === b && m.claim_b_id === a)
    );

  return (
    <div
      style={{
        flex: 1,
        overflowY: 'auto',
        padding: '12px',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
      }}
    >
      {/* Matrix */}
      <div>
        <div
          style={{
            fontSize: '10px',
            color: '#64748b',
            fontFamily: 'monospace',
            textTransform: 'uppercase',
            letterSpacing: '0.1em',
            marginBottom: '8px',
          }}
        >
          Contradiction Matrix
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table
            style={{
              borderCollapse: 'collapse',
              fontSize: '10px',
              fontFamily: 'monospace',
              width: '100%',
            }}
          >
            <thead>
              <tr>
                <th style={{ padding: '4px 6px', color: '#475569', textAlign: 'left', fontWeight: 400, borderBottom: '1px solid #1e2d4d' }}>
                  —
                </th>
                {claimIds.map((id) => (
                  <th
                    key={id}
                    style={{
                      padding: '4px 6px',
                      color: '#94a3b8',
                      fontWeight: 700,
                      borderBottom: '1px solid #1e2d4d',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {id}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {claimIds.map((rowId) => (
                <tr key={rowId}>
                  <td
                    style={{
                      padding: '4px 6px',
                      color: '#94a3b8',
                      fontWeight: 700,
                      borderRight: '1px solid #1e2d4d',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {rowId}
                  </td>
                  {claimIds.map((colId) => {
                    if (rowId === colId) {
                      return (
                        <td
                          key={colId}
                          style={{
                            padding: '4px 6px',
                            background: '#1e2d4d',
                            textAlign: 'center',
                          }}
                        >
                          <span style={{ color: '#475569' }}>—</span>
                        </td>
                      );
                    }
                    const contr = getContradiction(rowId, colId);
                    const color = contr ? scoreColor(contr.score) : '#10b981';
                    const isSelected =
                      selectedCell?.claim_a_id === contr?.claim_a_id &&
                      selectedCell?.claim_b_id === contr?.claim_b_id;
                    return (
                      <td
                        key={colId}
                        onClick={() => contr && setSelectedCell(isSelected ? null : contr)}
                        style={{
                          padding: '4px 6px',
                          textAlign: 'center',
                          cursor: contr ? 'pointer' : 'default',
                          background: contr
                            ? isSelected
                              ? `${color}25`
                              : `${color}0d`
                            : 'rgba(16,185,129,0.05)',
                          border: isSelected ? `1px solid ${color}` : '1px solid transparent',
                          transition: 'all 0.15s',
                        }}
                      >
                        {contr ? (
                          <span
                            style={{
                              color: color,
                              fontWeight: 700,
                              fontSize: '9px',
                            }}
                          >
                            {scoreLabel(contr.score)}
                          </span>
                        ) : (
                          <span style={{ color: '#10b98150', fontSize: '9px' }}>OK</span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Selected cell detail */}
        {selectedCell && (
          <ConflictDetail
            contradiction={selectedCell}
            claims={claims}
            onClose={() => setSelectedCell(null)}
          />
        )}
      </div>

      {/* Claims Explorer */}
      <div>
        <div
          style={{
            fontSize: '10px',
            color: '#64748b',
            fontFamily: 'monospace',
            textTransform: 'uppercase',
            letterSpacing: '0.1em',
            marginBottom: '8px',
          }}
        >
          Claims Explorer ({claims?.length || 0})
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {(claims || []).map((claim) => {
            const contradictions = matrix.filter(
              (m) => m.claim_a_id === claim.claim_id || m.claim_b_id === claim.claim_id
            );
            const isExpanded = expandedClaim === claim.claim_id;
            return (
              <ClaimCard
                key={claim.claim_id}
                claim={claim}
                contradictions={contradictions}
                isExpanded={isExpanded}
                onToggle={() => setExpandedClaim(isExpanded ? null : claim.claim_id)}
              />
            );
          })}
        </div>
      </div>
    </div>
  );
}

function ConflictDetail({ contradiction, claims, onClose }) {
  const claimA = claims?.find((c) => c.claim_id === contradiction.claim_a_id);
  const claimB = claims?.find((c) => c.claim_id === contradiction.claim_b_id);
  const color = scoreColor(contradiction.score);

  return (
    <div
      style={{
        marginTop: '10px',
        background: `rgba(${hexToRgb(color)},0.07)`,
        border: `1px solid ${color}40`,
        borderRadius: '8px',
        padding: '12px',
        animation: 'fadeIn 0.2s ease-out',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
        <span style={{ fontSize: '10px', color: color, fontFamily: 'monospace', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
          {contradiction.type.replace(/_/g, ' ')} · Score: {Math.round(contradiction.score * 100)}%
        </span>
        <button
          onClick={onClose}
          style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', fontSize: '14px', lineHeight: 1 }}
        >
          ×
        </button>
      </div>
      <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '10px', fontStyle: 'italic' }}>
        {contradiction.description}
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
        {[claimA, claimB].map((claim, i) => (
          claim && (
            <div
              key={i}
              style={{
                background: '#0a0e1a',
                border: '1px solid #1e2d4d',
                borderRadius: '6px',
                padding: '8px',
              }}
            >
              <div style={{ fontSize: '9px', color: '#64748b', fontFamily: 'monospace', marginBottom: '4px' }}>
                {claim.claim_id}
              </div>
              <div style={{ fontSize: '10px', color: '#e2e8f0', lineHeight: '1.5' }}>
                {claim.text}
              </div>
              <div style={{ marginTop: '6px', fontSize: '9px', color: '#3b82f6', fontFamily: 'monospace' }}>
                {SOURCE_ICONS[claim.source_type] || '📋'} {claim.source_type.toUpperCase()} ·{' '}
                {Object.entries(claim.source_ref)
                  .slice(0, 2)
                  .map(([k, v]) => `${k}:${v}`)
                  .join(' ')}
              </div>
            </div>
          )
        ))}
      </div>
    </div>
  );
}

function ClaimCard({ claim, contradictions, isExpanded, onToggle }) {
  const hasContradictions = contradictions.length > 0;
  const confidence = Math.round(claim.confidence * 100);

  return (
    <div
      style={{
        background: 'rgba(255,255,255,0.02)',
        border: `1px solid ${hasContradictions ? 'rgba(239,68,68,0.25)' : '#1e2d4d'}`,
        borderRadius: '7px',
        overflow: 'hidden',
        transition: 'all 0.2s',
      }}
    >
      <div
        onClick={onToggle}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '9px 10px',
          cursor: 'pointer',
        }}
      >
        <span style={{ color: '#64748b', flexShrink: 0 }}>
          {isExpanded ? <ChevronDown size={11} /> : <ChevronRight size={11} />}
        </span>
        <span
          style={{
            fontFamily: 'monospace',
            fontSize: '10px',
            color: '#3b82f6',
            fontWeight: 700,
            flexShrink: 0,
          }}
        >
          {claim.claim_id}
        </span>
        <span
          style={{
            fontSize: '11px',
            color: '#94a3b8',
            flex: 1,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {claim.text}
        </span>
        {/* Source chip */}
        <span
          style={{
            background: 'rgba(59,130,246,0.1)',
            border: '1px solid rgba(59,130,246,0.2)',
            borderRadius: '3px',
            padding: '1px 5px',
            fontSize: '9px',
            color: '#60a5fa',
            fontFamily: 'monospace',
            flexShrink: 0,
          }}
        >
          {SOURCE_ICONS[claim.source_type] || '📋'} {claim.source_type.toUpperCase()}
        </span>
        {/* Confidence */}
        <span
          style={{
            fontSize: '10px',
            color: confidence >= 90 ? '#10b981' : '#f59e0b',
            fontFamily: 'monospace',
            fontWeight: 700,
            flexShrink: 0,
          }}
        >
          {confidence}%
        </span>
      </div>

      {isExpanded && (
        <div
          style={{
            padding: '0 10px 10px 28px',
            borderTop: '1px solid #1e2d4d',
            paddingTop: '8px',
            animation: 'fadeIn 0.2s ease-out',
          }}
        >
          {/* Confidence bar */}
          <div style={{ background: '#1e2d4d', borderRadius: '2px', height: '3px', marginBottom: '8px' }}>
            <div
              style={{
                width: `${confidence}%`,
                height: '100%',
                background: confidence >= 90 ? '#10b981' : '#f59e0b',
                borderRadius: '2px',
                transition: 'width 0.8s ease',
              }}
            />
          </div>

          <div style={{ fontSize: '11px', color: '#94a3b8', lineHeight: '1.6', marginBottom: '8px' }}>
            {claim.text}
          </div>

          {/* Full source reference */}
          <div
            style={{
              background: '#0a0e1a',
              border: '1px solid #1e2d4d',
              borderRadius: '5px',
              padding: '6px 8px',
              fontSize: '10px',
              fontFamily: 'monospace',
              color: '#06b6d4',
              marginBottom: hasContradictions ? '6px' : 0,
            }}
          >
            {SOURCE_ICONS[claim.source_type] || '📋'} {claim.source_type.toUpperCase()}:{' '}
            {Object.entries(claim.source_ref)
              .map(([k, v]) => `${k}=${v}`)
              .join(' · ')}
          </div>

          {/* Contradiction warnings */}
          {contradictions.map((c) => {
            const otherId =
              c.claim_a_id === claim.claim_id ? c.claim_b_id : c.claim_a_id;
            return (
              <div
                key={otherId}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '5px',
                  fontSize: '10px',
                  color: '#ef4444',
                  fontFamily: 'monospace',
                  marginTop: '4px',
                }}
              >
                <AlertTriangle size={10} />
                Contradicted by: {otherId} ({Math.round(c.score * 100)}% conflict)
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function hexToRgb(hex) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result
    ? `${parseInt(result[1], 16)},${parseInt(result[2], 16)},${parseInt(result[3], 16)}`
    : '255,255,255';
}
