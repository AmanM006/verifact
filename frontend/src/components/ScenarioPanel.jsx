import { useState } from 'react';
import { Search, Loader2 } from 'lucide-react';
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
        background: '#09090b',
        borderRight: '1px solid #18181b',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '14px 16px',
          borderBottom: '1px solid #18181b',
        }}
      >
        <div style={{ fontSize: '11px', color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
          Investigation Scenarios
        </div>
      </div>

      {/* Scenario List */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {SCENARIOS.map((scenario) => {
          const isSelected = selectedScenario === scenario.id;
          return (
            <div
              key={scenario.id}
              onClick={() => onSelectScenario(scenario.id)}
              style={{
                background: isSelected ? '#18181b' : '#0e0e11',
                border: isSelected ? '1px solid #3f3f46' : '1px solid #18181b',
                borderRadius: '6px',
                padding: '12px',
                cursor: 'pointer',
                transition: 'border-color 0.15s ease',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                <span style={{ fontSize: '12.5px', fontWeight: 600, color: isSelected ? '#ffffff' : '#d4d4d8' }}>
                  {scenario.title}
                </span>
                {scenario.impact && (
                  <span style={{ fontSize: '10px', color: '#ef4444', fontFamily: 'ui-monospace, monospace' }}>
                    {scenario.impact}
                  </span>
                )}
              </div>
              <div style={{ fontSize: '11.5px', color: '#71717a', lineHeight: '1.45' }}>
                {scenario.description}
              </div>
            </div>
          );
        })}

        {/* Custom Query Box */}
        <div style={{ marginTop: '12px' }}>
          <div style={{ fontSize: '11px', color: '#71717a', marginBottom: '6px', fontWeight: 500 }}>
            Custom Case Query
          </div>
          <textarea
            value={customQuery}
            onChange={(e) => setCustomQuery(e.target.value)}
            placeholder="E.g., Trace unauthorized transfers over $50k in September..."
            rows={3}
            style={{
              width: '100%',
              background: '#0e0e11',
              border: '1px solid #18181b',
              borderRadius: '6px',
              padding: '8px 10px',
              fontSize: '11.5px',
              color: '#ededed',
              resize: 'none',
              outline: 'none',
              fontFamily: 'inherit',
            }}
          />
        </div>
      </div>

      {/* Action Footer */}
      <div style={{ padding: '12px', borderTop: '1px solid #18181b' }}>
        <button
          onClick={handleInvestigate}
          disabled={loading}
          style={{
            width: '100%',
            height: '38px',
            background: '#ffffff',
            color: '#000000',
            border: 'none',
            borderRadius: '6px',
            fontWeight: 600,
            fontSize: '13px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.7 : 1,
            transition: 'opacity 0.15s ease',
          }}
        >
          {loading ? (
            <>
              <Loader2 size={15} className="animate-spin" />
              <span>Analyzing Causal Graph...</span>
            </>
          ) : (
            <>
              <Search size={15} />
              <span>Investigate</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
