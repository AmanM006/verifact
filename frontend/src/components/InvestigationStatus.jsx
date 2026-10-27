import { AlertTriangle, Target, BarChart3, DollarSign, ChevronRight, Zap } from 'lucide-react';

export default function InvestigationStatus({ data }) {
  if (!data) return null;

  return (
    <div
      className="animate-fadeIn"
      style={{
        height: '100%',
        overflowY: 'auto',
        padding: '16px',
        display: 'flex',
        flexDirection: 'column',
        gap: '14px',
      }}
    >
      {/* Investigation ID + Summary */}
      <div
        style={{
          background: 'rgba(59,130,246,0.06)',
          border: '1px solid rgba(59,130,246,0.2)',
          borderRadius: '10px',
          padding: '14px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
          <span
            style={{
              fontFamily: 'monospace',
              fontSize: '11px',
              color: '#3b82f6',
              background: 'rgba(59,130,246,0.15)',
              padding: '2px 8px',
              borderRadius: '4px',
              fontWeight: 700,
            }}
          >
            {data.investigation_id}
          </span>
          <span
            style={{
              fontSize: '10px',
              color: '#10b981',
              background: 'rgba(16,185,129,0.1)',
              border: '1px solid rgba(16,185,129,0.3)',
              padding: '2px 6px',
              borderRadius: '4px',
              fontFamily: 'monospace',
              fontWeight: 700,
            }}
          >
            ✓ COMPLETE
          </span>
        </div>
        <p style={{ fontSize: '12px', color: '#94a3b8', lineHeight: '1.6', margin: 0 }}>
          {data.summary}
        </p>
      </div>

      {/* KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
        <KpiCard
          label="Evidence Coverage"
          value={`${data.evidence_coverage_pct}%`}
          icon={<BarChart3 size={14} />}
          color="#10b981"
          progress={data.evidence_coverage_pct}
        />
        <KpiCard
          label="Contradiction Score"
          value={`${Math.round(data.contradiction_matrix.reduce((s, c) => s + c.score, 0) / data.contradiction_matrix.length * 100)}%`}
          icon={<AlertTriangle size={14} />}
          color="#f59e0b"
          progress={Math.round(data.contradiction_matrix.reduce((s, c) => s + c.score, 0) / data.contradiction_matrix.length * 100)}
        />
        <KpiCard
          label="Causal Chain Depth"
          value={`${data.causal_chain_depth} hops`}
          icon={<ChevronRight size={14} />}
          color="#8b5cf6"
          progress={(data.causal_chain_depth / 6) * 100}
        />
        <KpiCard
          label="Financial Impact"
          value={data.financial_impact}
          icon={<DollarSign size={14} />}
          color="#ef4444"
          progress={100}
        />
      </div>

      {/* Root Causes */}
      <div>
        <SectionLabel icon={<Target size={11} />} label="Root Causes Identified" />
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {data.root_causes.map((cause, i) => (
            <div
              key={i}
              style={{
                background: 'rgba(139,92,246,0.08)',
                borderLeft: '3px solid #8b5cf6',
                borderRadius: '0 6px 6px 0',
                padding: '9px 12px',
                fontSize: '11px',
                color: '#c4b5fd',
                lineHeight: '1.5',
              }}
            >
              <span style={{ color: '#8b5cf6', fontFamily: 'monospace', fontWeight: 700 }}>
                RC-{String(i + 1).padStart(2, '0')} ›{' '}
              </span>
              {cause}
            </div>
          ))}
        </div>
      </div>

      {/* Sponsor Stack */}
      <div>
        <SectionLabel icon={<Zap size={11} />} label="Sponsor Stack Used" />
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
          {Object.entries(data.sponsor_stack).map(([key, val]) => (
            <div
              key={key}
              title={val}
              style={{
                background: 'rgba(6,182,212,0.08)',
                border: '1px solid rgba(6,182,212,0.2)',
                borderRadius: '5px',
                padding: '4px 8px',
                fontSize: '10px',
                color: '#06b6d4',
                fontFamily: 'monospace',
                cursor: 'help',
              }}
            >
              {SPONSOR_LABELS[key] || key}
            </div>
          ))}
        </div>
      </div>

      {/* Why Narrative */}
      <div>
        <SectionLabel icon={<ChevronRight size={11} />} label="Why This Happened" />
        <div
          style={{
            background: '#0a0e1a',
            border: '1px solid #1e2d4d',
            borderRadius: '8px',
            padding: '14px',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          <div
            className="scanlines"
            style={{
              position: 'absolute',
              inset: 0,
              borderRadius: '8px',
            }}
          />
          <div style={{ position: 'relative', zIndex: 1 }}>
            {data.recommendations.map((rec, i) => (
              <div
                key={i}
                style={{
                  fontSize: '11px',
                  color: '#94a3b8',
                  lineHeight: '1.7',
                  marginBottom: '8px',
                  paddingLeft: '12px',
                  borderLeft: '2px solid #1e2d4d',
                }}
              >
                <span style={{ color: '#f59e0b', fontFamily: 'monospace', fontSize: '10px' }}>
                  ACTION {i + 1} ·{' '}
                </span>
                {rec}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

const SPONSOR_LABELS = {
  zetaris: 'Zetaris USL',
  meterless_hmem: 'Meterless H-MEM',
  meterless_nightshift: 'Nightshift Agent',
  nvidia_nemotron: 'NVIDIA Nemotron',
};

function SectionLabel({ icon, label }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '5px',
        marginBottom: '8px',
        color: '#64748b',
        fontSize: '10px',
        fontFamily: 'monospace',
        letterSpacing: '0.1em',
        textTransform: 'uppercase',
      }}
    >
      {icon}
      {label}
    </div>
  );
}

function KpiCard({ label, value, icon, color, progress }) {
  return (
    <div
      style={{
        background: `rgba(${hexToRgb(color)}, 0.07)`,
        border: `1px solid rgba(${hexToRgb(color)}, 0.2)`,
        borderRadius: '8px',
        padding: '12px',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
        <div style={{ fontSize: '10px', color: '#64748b', fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
          {label}
        </div>
        <div style={{ color: color, opacity: 0.6 }}>{icon}</div>
      </div>
      <div
        style={{
          fontSize: '20px',
          fontWeight: 800,
          color: color,
          fontFamily: 'monospace',
          marginBottom: '8px',
          textShadow: `0 0 12px ${color}60`,
        }}
      >
        {value}
      </div>
      <div style={{ background: 'rgba(255,255,255,0.05)', borderRadius: '2px', height: '3px', overflow: 'hidden' }}>
        <div
          className="animate-grow"
          style={{
            height: '100%',
            width: `${Math.min(100, progress)}%`,
            background: `linear-gradient(90deg, ${color}88, ${color})`,
            borderRadius: '2px',
            boxShadow: `0 0 8px ${color}`,
          }}
        />
      </div>
    </div>
  );
}

function hexToRgb(hex) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result
    ? `${parseInt(result[1], 16)},${parseInt(result[2], 16)},${parseInt(result[3], 16)}`
    : '255,255,255';
}
