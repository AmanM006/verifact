import { useState } from 'react';
import { Search, Loader2, AlertTriangle, DollarSign, TrendingUp, ChevronRight } from 'lucide-react';
import { MOCK_SCENARIOS } from '../api/mockData';

export default function ScenarioPanel({ scenarios, selectedScenario, onSelectScenario, onInvestigate, loading }) {
  const [customQuery, setCustomQuery] = useState('');
  const SCENARIOS = scenarios || MOCK_SCENARIOS;

  const handleInvestigate = () => {
    onInvestigate(selectedScenario, customQuery);
  };

  return (
    <div
      style={{
        width: '280px',
        flexShrink: 0,
        background: '#0f1629',
        borderRight: '1px solid #1e2d4d',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      {/* Section Header */}
      <div
        style={{
          padding: '14px 16px 10px',
          borderBottom: '1px solid #1e2d4d',
          background: 'rgba(59,130,246,0.04)',
        }}
      >
        <div style={{ fontSize: '10px', color: '#64748b', fontFamily: 'monospace', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: '2px' }}>
          Investigation Scenarios
        </div>
        <div style={{ fontSize: '12px', color: '#e2e8f0' }}>
          Select or define a case
        </div>
      </div>

      {/* Scenario Cards */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '10px' }}>
        {SCENARIOS.map((scenario, idx) => (
          <ScenarioCard
            key={scenario.id}
            scenario={scenario}
            index={idx + 1}
            selected={selectedScenario === scenario.id}
            onClick={() => onSelectScenario(scenario.id)}
          />
        ))}

        {/* Custom Query */}
        <div style={{ marginTop: '12px' }}>
          <div
            style={{
              fontSize: '10px',
              color: '#64748b',
              fontFamily: 'monospace',
              letterSpacing: '0.12em',
              textTransform: 'uppercase',
              marginBottom: '6px',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
            }}
          >
            <ChevronRight size={10} color="#64748b" />
            Custom Query
          </div>
          <textarea
            value={customQuery}
            onChange={(e) => setCustomQuery(e.target.value)}
            placeholder="Or describe your own scenario..."
            rows={4}
            style={{
              width: '100%',
              background: '#0a0e1a',
              border: '1px solid #1e2d4d',
              borderRadius: '8px',
              padding: '10px',
              color: '#e2e8f0',
              fontSize: '12px',
              fontFamily: 'inherit',
              resize: 'vertical',
              outline: 'none',
              transition: 'border-color 0.2s',
              lineHeight: '1.5',
            }}
            onFocus={(e) => { e.target.style.borderColor = '#3b82f6'; }}
            onBlur={(e) => { e.target.style.borderColor = '#1e2d4d'; }}
          />
        </div>
      </div>

      {/* Investigate Button */}
      <div style={{ padding: '12px', borderTop: '1px solid #1e2d4d' }}>
        <button
          onClick={handleInvestigate}
          disabled={loading}
          style={{
            width: '100%',
            padding: '12px',
            background: loading
              ? 'rgba(59,130,246,0.3)'
              : 'linear-gradient(135deg, #3b82f6, #2563eb)',
            border: '1px solid rgba(59,130,246,0.5)',
            borderRadius: '8px',
            color: '#fff',
            fontFamily: 'monospace',
            fontWeight: 700,
            fontSize: '13px',
            letterSpacing: '0.1em',
            cursor: loading ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            transition: 'all 0.2s',
            boxShadow: loading ? 'none' : '0 0 20px rgba(59,130,246,0.4)',
          }}
          onMouseEnter={(e) => {
            if (!loading) {
              e.currentTarget.style.boxShadow = '0 0 30px rgba(59,130,246,0.7)';
              e.currentTarget.style.transform = 'translateY(-1px)';
            }
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.boxShadow = '0 0 20px rgba(59,130,246,0.4)';
            e.currentTarget.style.transform = 'translateY(0)';
          }}
        >
          {loading ? (
            <>
              <Loader2 size={15} style={{ animation: 'spin 1s linear infinite' }} />
              INVESTIGATING...
            </>
          ) : (
            <>
              <Search size={15} />
              INVESTIGATE
            </>
          )}
        </button>
        <div style={{ fontSize: '10px', color: '#64748b', textAlign: 'center', marginTop: '6px', fontFamily: 'monospace' }}>
          Powered by Zetaris · H-MEM · Nemotron
        </div>
      </div>
    </div>
  );
}

function ScenarioCard({ scenario, index, selected, onClick }) {
  return (
    <div
      onClick={onClick}
      style={{
        background: selected ? 'rgba(59,130,246,0.1)' : 'rgba(255,255,255,0.02)',
        border: selected ? '1px solid rgba(59,130,246,0.5)' : '1px solid #1e2d4d',
        borderRadius: '8px',
        padding: '12px',
        marginBottom: '8px',
        cursor: 'pointer',
        transition: 'all 0.2s',
        boxShadow: selected ? '0 0 16px rgba(59,130,246,0.2), inset 0 0 16px rgba(59,130,246,0.05)' : 'none',
      }}
      onMouseEnter={(e) => {
        if (!selected) {
          e.currentTarget.style.borderColor = '#3b82f6';
          e.currentTarget.style.background = 'rgba(59,130,246,0.05)';
        }
      }}
      onMouseLeave={(e) => {
        if (!selected) {
          e.currentTarget.style.borderColor = '#1e2d4d';
          e.currentTarget.style.background = 'rgba(255,255,255,0.02)';
        }
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', marginBottom: '6px' }}>
        <div
          style={{
            background: selected ? '#3b82f6' : '#1e2d4d',
            borderRadius: '4px',
            padding: '2px 6px',
            fontSize: '10px',
            color: selected ? '#fff' : '#64748b',
            fontFamily: 'monospace',
            fontWeight: 700,
            flexShrink: 0,
            transition: 'all 0.2s',
          }}
        >
          #{String(index).padStart(2, '0')}
        </div>
        <div style={{ fontSize: '12px', color: '#e2e8f0', fontWeight: 600, lineHeight: 1.3 }}>
          {scenario.title}
        </div>
      </div>
      <div style={{ fontSize: '11px', color: '#64748b', lineHeight: 1.5, marginBottom: '8px' }}>
        {scenario.description}
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
        {scenario.tags.map((tag) => (
          <span
            key={tag}
            style={{
              background: 'rgba(6,182,212,0.1)',
              border: '1px solid rgba(6,182,212,0.25)',
              borderRadius: '3px',
              padding: '1px 6px',
              fontSize: '9px',
              color: '#06b6d4',
              fontFamily: 'monospace',
              letterSpacing: '0.05em',
            }}
          >
            {tag}
          </span>
        ))}
        <span
          style={{
            background: 'rgba(239,68,68,0.1)',
            border: '1px solid rgba(239,68,68,0.25)',
            borderRadius: '3px',
            padding: '1px 6px',
            fontSize: '9px',
            color: '#ef4444',
            fontFamily: 'monospace',
            fontWeight: 600,
          }}
        >
          {scenario.impact}
        </span>
      </div>
    </div>
  );
}
