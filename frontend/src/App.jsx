import { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import ScenarioPanel from './components/ScenarioPanel';
import InvestigationStatus from './components/InvestigationStatus';
import EvidenceGraph from './components/EvidenceGraph';
import ContradictionMatrix from './components/ContradictionMatrix';
import StatusBar from './components/StatusBar';
import { getScenarios, runInvestigation } from './api/client';
import { MOCK_INVESTIGATION, MOCK_SCENARIOS } from './api/mockData';

export default function App() {
  const [selectedScenario, setSelectedScenario] = useState('procurement_fraud');
  const [scenarios, setScenarios] = useState(MOCK_SCENARIOS);
  const [investigationData, setInvestigationData] = useState(MOCK_INVESTIGATION);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getScenarios()
      .then(res => {
        const list = res.data?.scenarios || (Array.isArray(res.data) ? res.data : null);
        if (list && list.length > 0) {
          setScenarios(list.map(s => ({
            id: s.id,
            title: s.title,
            description: s.description,
            tags: ["Track 02", s.severity || "Critical"],
            impact: s.financial_impact ? `${s.financial_impact} impact` : "High",
            track: "02"
          })));
        }
      })
      .catch(() => {
        // Fallback to MOCK_SCENARIOS
      });
  }, []);

  const handleInvestigate = useCallback(async (scenarioId, customQuery) => {
    setLoading(true);
    try {
      const res = await runInvestigation(scenarioId, customQuery);
      setInvestigationData(res.data);
    } catch (err) {
      // Backend not available — use mock data with a short delay for demo effect
      await new Promise((r) => setTimeout(r, 1800));
      setInvestigationData({ ...MOCK_INVESTIGATION, scenario_id: scenarioId || 'procurement_fraud' });
    } finally {
      setLoading(false);
    }
  }, []);

  return (
    <div
      style={{
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        background: '#0a0e1a',
        color: '#e2e8f0',
        overflow: 'hidden',
      }}
    >
      <Header />

      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Left Sidebar */}
        <ScenarioPanel
          scenarios={scenarios}
          selectedScenario={selectedScenario}
          onSelectScenario={setSelectedScenario}
          onInvestigate={handleInvestigate}
          loading={loading}
        />

        {/* Main Content */}
        <div style={{ flex: 1, display: 'flex', overflow: 'hidden', gap: 0 }}>
          {/* Panel 1: Investigation Status */}
          <Panel
            title="Investigation Status"
            width="300px"
            borderRight
            badge={investigationData ? 'ACTIVE' : 'STANDBY'}
            badgeColor={investigationData ? '#10b981' : '#64748b'}
          >
            <InvestigationStatus data={investigationData} />
          </Panel>

          {/* Panel 2: Evidence Graph — visual centerpiece */}
          <Panel
            title="Evidence Causality Graph"
            flex={1}
            borderRight
            badge={
              investigationData
                ? `${investigationData.graph.nodes.length} nodes · ${investigationData.graph.edges.length} edges`
                : 'EMPTY'
            }
            badgeColor="#06b6d4"
          >
            <EvidenceGraph data={investigationData} />
          </Panel>

          {/* Panel 3: Contradiction Matrix + Claims */}
          <Panel
            title="Contradiction Matrix"
            width="360px"
            badge={investigationData ? `${investigationData.contradiction_matrix.length} conflicts` : 'NONE'}
            badgeColor="#f59e0b"
          >
            <ContradictionMatrix data={investigationData} />
          </Panel>
        </div>
      </div>

      <StatusBar data={investigationData} />
    </div>
  );
}

function Panel({ title, children, width, flex, borderRight, badge, badgeColor }) {
  return (
    <div
      style={{
        width: width,
        flex: flex,
        display: 'flex',
        flexDirection: 'column',
        borderRight: borderRight ? '1px solid #1e2d4d' : 'none',
        overflow: 'hidden',
        minWidth: 0,
      }}
    >
      {/* Panel header */}
      <div
        style={{
          height: '36px',
          background: '#0a0e1a',
          borderBottom: '1px solid #1e2d4d',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 14px',
          flexShrink: 0,
        }}
      >
        <span
          style={{
            fontSize: '10px',
            color: '#64748b',
            fontFamily: 'monospace',
            letterSpacing: '0.1em',
            textTransform: 'uppercase',
          }}
        >
          {title}
        </span>
        {badge && (
          <span
            style={{
              fontSize: '9px',
              color: badgeColor,
              background: `${badgeColor}18`,
              border: `1px solid ${badgeColor}40`,
              borderRadius: '3px',
              padding: '1px 6px',
              fontFamily: 'monospace',
              fontWeight: 700,
            }}
          >
            {badge}
          </span>
        )}
      </div>

      {/* Panel content */}
      <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        {children}
      </div>
    </div>
  );
}
