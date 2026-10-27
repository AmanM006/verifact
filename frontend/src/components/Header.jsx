import { Shield } from 'lucide-react';

export default function Header() {
  return (
    <header
      style={{
        background: '#09090b',
        borderBottom: '1px solid #18181b',
        padding: '0 20px',
        height: '50px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexShrink: 0,
        zIndex: 10,
      }}
    >
      {/* Left: Brand + Purpose */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div
          style={{
            background: '#ffffff',
            borderRadius: '6px',
            padding: '5px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Shield size={16} color="#000000" />
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span
            style={{
              fontWeight: 700,
              fontSize: '15px',
              color: '#ffffff',
              letterSpacing: '-0.02em',
            }}
          >
            VeriFact
          </span>
          <span style={{ color: '#27272a' }}>/</span>
          <span
            style={{
              fontSize: '13px',
              color: '#71717a',
              fontWeight: 400,
            }}
          >
            Autonomous Forensic Causality Engine
          </span>
        </div>
      </div>

      {/* Right: Technical Stack Pill Indicators */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <TechPill label="Zetaris USL" status="SIMULATED FEDERATION" />
        <TechPill label="H-MEM Local Ledger" status="IN-MEMORY ENGINE" />
        <TechPill label="NVIDIA Nemotron" status="EXTRACTION PARSER" />
      </div>
    </header>
  );
}

function TechPill({ label, status }) {
  return (
    <div
      style={{
        background: '#121215',
        border: '1px solid #27272a',
        borderRadius: '4px',
        padding: '3px 8px',
        fontSize: '11px',
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        fontFamily: 'ui-monospace, monospace',
      }}
    >
      <span style={{ color: '#ffffff', fontWeight: 600 }}>{label}</span>
      {status && (
        <span
          style={{
            fontSize: '9px',
            color: '#a1a1aa',
            background: '#18181b',
            border: '1px solid #27272a',
            padding: '1px 4px',
            borderRadius: '2px',
          }}
        >
          {status}
        </span>
      )}
    </div>
  );
}
