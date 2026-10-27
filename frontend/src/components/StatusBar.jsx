export default function StatusBar({ data }) {
  const time = data?.processing_time_ms;
  const coverage = data?.evidence_coverage_pct;

  return (
    <div
      style={{
        height: '30px',
        background: '#09090b',
        borderTop: '1px solid #18181b',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 16px',
        flexShrink: 0,
        fontSize: '11px',
        fontFamily: 'ui-monospace, monospace',
        color: '#71717a',
      }}
    >
      <div>
        <span>VeriFact v1.0.0</span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {time && (
          <span>
            Computation: <span style={{ color: '#d4d4d8' }}>{time}ms</span>
          </span>
        )}
        {coverage !== undefined && (
          <span>
            Coverage: <span style={{ color: '#38bdf8' }}>{coverage}%</span>
          </span>
        )}
      </div>
    </div>
  );
}
