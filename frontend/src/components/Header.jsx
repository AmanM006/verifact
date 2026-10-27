import { Shield, Radio } from 'lucide-react';

export default function Header() {
  return (
    <header
      style={{
        background: '#0f1629',
        borderBottom: '1px solid #1e2d4d',
        padding: '0 24px',
        height: '56px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexShrink: 0,
        zIndex: 10,
        boxShadow: '0 1px 0 #1e2d4d, 0 4px 20px rgba(0,0,0,0.4)',
      }}
    >
      {/* Left: Logo + Title */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div
          style={{
            background: 'linear-gradient(135deg, #3b82f6, #06b6d4)',
            borderRadius: '8px',
            padding: '6px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 16px rgba(59,130,246,0.5)',
          }}
        >
          <Shield size={20} color="#fff" />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
            <span
              style={{
                fontWeight: 800,
                fontSize: '18px',
                color: '#e2e8f0',
                letterSpacing: '0.05em',
                fontFamily: 'monospace',
              }}
            >
              VERI<span style={{ color: '#3b82f6' }}>FACT</span>
            </span>
            <span
              style={{
                fontSize: '11px',
                color: '#06b6d4',
                fontFamily: 'monospace',
                letterSpacing: '0.1em',
              }}
            >
              Autonomous Cross-Silo Forensic Causality Engine
            </span>
          </div>
        </div>
      </div>

      {/* Center: Sponsor Pills */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <SponsorBadge label="ZETARIS" color="#3b82f6" />
        <SponsorBadge label="METERLESS H-MEM" color="#06b6d4" />
        <SponsorBadge label="NVIDIA NEMOTRON" color="#10b981" />
      </div>

      {/* Right: Track badge + LIVE */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div
          style={{
            background: 'rgba(139,92,246,0.15)',
            border: '1px solid rgba(139,92,246,0.4)',
            borderRadius: '6px',
            padding: '4px 10px',
            fontSize: '11px',
            color: '#8b5cf6',
            fontFamily: 'monospace',
            letterSpacing: '0.08em',
            fontWeight: 600,
          }}
        >
          Track 02 · Explain Why
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <div style={{ position: 'relative', width: '8px', height: '8px' }}>
            <div
              style={{
                position: 'absolute',
                inset: 0,
                borderRadius: '50%',
                background: '#10b981',
              }}
            />
            <div
              className="pulse-ring"
              style={{ position: 'absolute', inset: 0, borderRadius: '50%' }}
            />
          </div>
          <span
            style={{
              fontSize: '11px',
              color: '#10b981',
              fontFamily: 'monospace',
              fontWeight: 700,
              letterSpacing: '0.1em',
            }}
            className="animate-blink"
          >
            LIVE
          </span>
        </div>
        <Radio size={14} color="#64748b" />
      </div>
    </header>
  );
}

function SponsorBadge({ label, color }) {
  return (
    <div
      style={{
        background: `rgba(${hexToRgb(color)}, 0.1)`,
        border: `1px solid rgba(${hexToRgb(color)}, 0.3)`,
        borderRadius: '4px',
        padding: '3px 8px',
        fontSize: '10px',
        color: color,
        fontFamily: 'monospace',
        fontWeight: 700,
        letterSpacing: '0.08em',
        whiteSpace: 'nowrap',
      }}
    >
      {label}
    </div>
  );
}

function hexToRgb(hex) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result
    ? `${parseInt(result[1], 16)},${parseInt(result[2], 16)},${parseInt(result[3], 16)}`
    : '255,255,255';
}
