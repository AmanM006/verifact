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
      .then((res) => {
        const list = res.data?.scenarios || (Array.isArray(res.data) ? res.data : null);
        if (list && list.length > 0) {
          setScenarios(
            list.map((s) => ({
              id: s.id,
              title: s.title,
              description: s.description,
              impact: s.financial_impact || 'Impacted',
            }))
          );
        }
      })
      .catch(() => {
        // Fallback
      });
  }, []);

  const handleInvestigate = useCallback(async (scenarioId, customQuery) => {
    setLoading(true);
    try {
      const res = await runInvestigation(scenarioId, customQuery);
      setInvestigationData(res.data);
    } catch (err) {
      await new Promise((r) => setTimeout(r, 800));
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
        background: '#000000',
        color: '#ededed',
        overflow: 'hidden',
      }}
    >
      <Header />

      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Left Column: Scenarios (280px) */}
        <ScenarioPanel
          scenarios={scenarios}
          selectedScenario={selectedScenario}
          onSelectScenario={setSelectedScenario}
          onInvestigate={handleInvestigate}
          loading={loading}
        />

        {/* Middle-Left Column: Investigation Status & Root Causes (300px) */}
        <div style={{ width: '310px', flexShrink: 0, height: '100%' }}>
          <InvestigationStatus data={investigationData} />
        </div>

        {/* Center: Evidence Causality Graph (Flex 1) */}
        <EvidenceGraph data={investigationData} />

        {/* Right Column: Contradiction Matrix & Claims (310px) */}
        <div style={{ width: '310px', flexShrink: 0, height: '100%' }}>
          <ContradictionMatrix data={investigationData} />
        </div>
      </div>

      <StatusBar data={investigationData} />
    </div>
  );
}
