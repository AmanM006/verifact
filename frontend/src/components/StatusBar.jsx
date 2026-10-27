export default function StatusBar({ data }) {
  const stack = data?.sponsor_stack;
  const time = data?.processing_time_ms;
  const coverage = data?.evidence_coverage_pct;

  return (
    <div
      style={{
        height: '32px',
        background: '#070b15',
        borderTop: '1px solid #1e2d4d',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 16px',
        flexShrink: 0,
        fontSize: '10px',
        fontFamily: 'monospace',
        color: '#475569',
      }}
    >
      {/* Left */}
      <div>
        <span style={{ color: '#64748b' }}>VeriFact v1.0.0</span>
        <span style={{ color: '#1e2d4d', margin: '0 6px' }}>·</span>
        <span>Open Agent Hackathon 2026</span>
      </div>

      {/* Center */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <StackPill label="Zetaris USL" value={stack ? '3 sources' : 'idle'} color="#3b82f6" active={!!stack} />
        <StackPill label="H-MEM" value={stack ? 'active' : 'idle'} color="#06b6d4" active={!!stack} />
        <StackPill label="Nightshift" value={stack ? 'active' : 'idle'} color="#10b981" active={!!stack} />
        <StackPill label="Nemotron" value={stack ? 'nemotron-3.5-bolt-e4b' : 'idle'} color="#8b5cf6" active={!!stack} />
      </div>

      {/* Right */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {time && (
          <span>
            <span style={{ color: '#64748b' }}>⏱ </span>
            <span style={{ color: '#94a3b8' }}>{time.toLocaleString()}ms</span>
          </span>
        )}
        {coverage !== undefined && (
          <span>
            <span style={{ color: '#64748b' }}>Coverage: </span>
            <span style={{ color: '#10b981', fontWeight: 700 }}>{coverage}%</span>
          </span>
        )}
        {!data && (
          <span style={{ color: '#1e2d4d' }}>Awaiting investigation...</span>
        )}
      </div>
    </div>
  );
}

function StackPill({ label, value, color, active }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
      <div
        style={{
          width: '5px',
          height: '5px',
          borderRadius: '50%',
          background: active ? color : '#1e2d4d',
          boxShadow: active ? `0 0 6px ${color}` : 'none',
          transition: 'all 0.3s',
        }}
      />
      <span style={{ color: active ? '#64748b' : '#334155' }}>
        {label}:
      </span>
      <span style={{ color: active ? '#94a3b8' : '#334155' }}>
        {value}
      </span>
    </div>
  );
}
