import { useState, useRef, useCallback, useEffect } from 'react';
import { X, Shield, AlertTriangle, GitBranch, Circle, Square } from 'lucide-react';

// ─── Layout helpers ──────────────────────────────────────────────────────────

/** Topological sort returning an array of node ids in order */
function topoSort(nodes, edges) {
  const ids = nodes.map((n) => n.id);
  const inDeg = Object.fromEntries(ids.map((id) => [id, 0]));
  const adj = Object.fromEntries(ids.map((id) => [id, []]));

  edges.forEach(({ source, target }) => {
    if (inDeg[target] !== undefined) inDeg[target]++;
    if (adj[source]) adj[source].push(target);
  });

  const queue = ids.filter((id) => inDeg[id] === 0);
  const sorted = [];
  while (queue.length) {
    const cur = queue.shift();
    sorted.push(cur);
    adj[cur].forEach((nb) => {
      inDeg[nb]--;
      if (inDeg[nb] === 0) queue.push(nb);
    });
  }
  // Append any remaining (cycles)
  ids.forEach((id) => { if (!sorted.includes(id)) sorted.push(id); });
  return sorted;
}

/** Assign each node to a layer (0 = leftmost/topmost) */
function assignLayers(nodes, edges) {
  const sorted = topoSort(nodes, edges);
  const layer = Object.fromEntries(sorted.map((id) => [id, 0]));

  sorted.forEach((id) => {
    edges
      .filter((e) => e.source === id)
      .forEach((e) => {
        if (layer[e.target] !== undefined) {
          layer[e.target] = Math.max(layer[e.target], layer[id] + 1);
        }
      });
  });
  return layer;
}

/** Compute (x, y) positions for all nodes in a DAG layout */
function computeLayout(nodes, edges, width, height) {
  const PADDING_X = 90;
  const PADDING_Y = 70;

  const layers = assignLayers(nodes, edges);
  const maxLayer = Math.max(...Object.values(layers));

  // Group nodes by layer
  const byLayer = {};
  nodes.forEach((n) => {
    const l = layers[n.id] ?? 0;
    if (!byLayer[l]) byLayer[l] = [];
    byLayer[l].push(n.id);
  });

  const layerCount = maxLayer + 1;
  const layerXStep = layerCount > 1 ? (width - PADDING_X * 2) / (layerCount - 1) : 0;

  const positions = {};
  for (let l = 0; l <= maxLayer; l++) {
    const group = byLayer[l] || [];
    const count = group.length;
    const x = PADDING_X + l * layerXStep;
    group.forEach((id, i) => {
      const yStep = count > 1 ? (height - PADDING_Y * 2) / (count - 1) : 0;
      const y = count === 1 ? height / 2 : PADDING_Y + i * yStep;
      positions[id] = { x, y };
    });
  }
  return positions;
}

// ─── Node renderers ──────────────────────────────────────────────────────────

const NODE_CONFIG = {
  evidence:     { color: '#06b6d4', shape: 'circle',   r: 28 },
  contradiction:{ color: '#f59e0b', shape: 'diamond',  r: 28 },
  root_cause:   { color: '#8b5cf6', shape: 'hexagon',  r: 30 },
  outcome:      { color: '#ef4444', shape: 'circle',   r: 30 },
  gap:          { color: '#64748b', shape: 'circle',   r: 24, dashed: true },
};

function hexagonPoints(cx, cy, r) {
  return Array.from({ length: 6 }, (_, i) => {
    const angle = (Math.PI / 3) * i - Math.PI / 6;
    return `${cx + r * Math.cos(angle)},${cy + r * Math.sin(angle)}`;
  }).join(' ');
}

function NodeShape({ node, pos, selected, onClick, onHover }) {
  const cfg = NODE_CONFIG[node.type] || NODE_CONFIG.evidence;
  const { x, y } = pos;
  const label = node.label.replace('\n', '\n');
  const lines = label.split('\n');
  const glowFilter = `drop-shadow(0 0 8px ${cfg.color}88)`;

  const commonProps = {
    fill: `${cfg.color}18`,
    stroke: selected ? cfg.color : `${cfg.color}88`,
    strokeWidth: selected ? 2.5 : 1.5,
    strokeDasharray: cfg.dashed ? '5,3' : undefined,
    style: { cursor: 'pointer', filter: selected ? glowFilter : undefined, transition: 'all 0.2s' },
    onClick: () => onClick(node),
    onMouseEnter: (e) => onHover(node, e),
    onMouseLeave: () => onHover(null, null),
  };

  const labelEls = (
    <>
      {lines.map((line, i) => (
        <text
          key={i}
          x={x}
          y={y + (i - (lines.length - 1) / 2) * 13}
          textAnchor="middle"
          dominantBaseline="middle"
          fill={cfg.color}
          fontSize="9"
          fontFamily="monospace"
          fontWeight="600"
          style={{ pointerEvents: 'none', userSelect: 'none' }}
        >
          {line}
        </text>
      ))}
    </>
  );

  if (cfg.shape === 'circle') {
    return (
      <g className="graph-node">
        <circle cx={x} cy={y} r={cfg.r} {...commonProps} />
        {labelEls}
      </g>
    );
  }
  if (cfg.shape === 'diamond') {
    const d = cfg.r;
    return (
      <g className="graph-node">
        <polygon
          points={`${x},${y - d} ${x + d},${y} ${x},${y + d} ${x - d},${y}`}
          {...commonProps}
        />
        {labelEls}
      </g>
    );
  }
  if (cfg.shape === 'hexagon') {
    return (
      <g className="graph-node">
        <polygon points={hexagonPoints(x, y, cfg.r)} {...commonProps} />
        {labelEls}
      </g>
    );
  }
  return null;
}

// ─── Edge ────────────────────────────────────────────────────────────────────

function Edge({ edge, positions }) {
  const src = positions[edge.source];
  const tgt = positions[edge.target];
  if (!src || !tgt) return null;

  const dx = tgt.x - src.x;
  const dy = tgt.y - src.y;
  const dist = Math.sqrt(dx * dx + dy * dy);
  const r = 30;
  const x1 = src.x + (dx / dist) * r;
  const y1 = src.y + (dy / dist) * r;
  const x2 = tgt.x - (dx / dist) * r;
  const y2 = tgt.y - (dy / dist) * r;

  const mx = (x1 + x2) / 2;
  const my = (y1 + y2) / 2;

  const opacity = 0.4 + edge.weight * 0.5;
  const strokeWidth = 0.5 + edge.weight * 2;

  return (
    <g>
      <defs>
        <marker
          id={`arrow-${edge.source}-${edge.target}`}
          markerWidth="6"
          markerHeight="6"
          refX="5"
          refY="3"
          orient="auto"
        >
          <path d="M0,0 L0,6 L6,3 z" fill={`rgba(99,132,255,${opacity})`} />
        </marker>
      </defs>
      <path
        d={`M${x1},${y1} Q${mx},${my - 20} ${x2},${y2}`}
        fill="none"
        stroke={`rgba(99,132,255,${opacity})`}
        strokeWidth={strokeWidth}
        strokeDasharray="6,3"
        markerEnd={`url(#arrow-${edge.source}-${edge.target})`}
        className="animated-edge"
        style={{ animationDuration: `${1 + (1 - edge.weight)}s` }}
      />
      {/* Edge label */}
      <text
        x={mx}
        y={my - 25}
        textAnchor="middle"
        fill="rgba(100,116,139,0.8)"
        fontSize="8"
        fontFamily="monospace"
        style={{ pointerEvents: 'none', userSelect: 'none' }}
      >
        {edge.label}
      </text>
    </g>
  );
}

// ─── Detail Drawer ────────────────────────────────────────────────────────────

function NodeDetail({ node, data, onClose }) {
  const claim = data?.claims?.find((c) => c.claim_id === node.id);
  const cfg = NODE_CONFIG[node.type] || NODE_CONFIG.evidence;

  const sourceIcon = { sql: '🗄️', comms: '💬', document: '📄' };

  return (
    <div
      style={{
        position: 'absolute',
        right: 0,
        top: 0,
        bottom: 0,
        width: '260px',
        background: '#0f1629',
        borderLeft: `2px solid ${cfg.color}`,
        zIndex: 20,
        overflow: 'auto',
        padding: '16px',
        animation: 'fadeIn 0.2s ease-out',
        boxShadow: `-8px 0 24px rgba(0,0,0,0.5)`,
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
        <div>
          <div
            style={{
              fontFamily: 'monospace',
              fontSize: '11px',
              fontWeight: 700,
              color: cfg.color,
              marginBottom: '4px',
            }}
          >
            {node.id}
          </div>
          <div
            style={{
              fontSize: '10px',
              color: '#64748b',
              fontFamily: 'monospace',
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
            }}
          >
            {node.type.replace('_', ' ')}
          </div>
        </div>
        <button
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            color: '#64748b',
            cursor: 'pointer',
            padding: '2px',
          }}
        >
          <X size={14} />
        </button>
      </div>

      {/* Confidence bar */}
      <div style={{ marginBottom: '12px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
          <span style={{ fontSize: '10px', color: '#64748b', fontFamily: 'monospace' }}>Confidence</span>
          <span style={{ fontSize: '10px', color: cfg.color, fontFamily: 'monospace', fontWeight: 700 }}>
            {Math.round(node.confidence * 100)}%
          </span>
        </div>
        <div style={{ background: '#1e2d4d', borderRadius: '2px', height: '4px' }}>
          <div
            style={{
              width: `${node.confidence * 100}%`,
              height: '100%',
              background: cfg.color,
              borderRadius: '2px',
              boxShadow: `0 0 8px ${cfg.color}`,
              transition: 'width 0.8s ease',
            }}
          />
        </div>
      </div>

      {claim ? (
        <>
          <div
            style={{
              background: 'rgba(255,255,255,0.03)',
              border: '1px solid #1e2d4d',
              borderRadius: '6px',
              padding: '10px',
              fontSize: '11px',
              color: '#94a3b8',
              lineHeight: '1.6',
              marginBottom: '10px',
            }}
          >
            {claim.text}
          </div>

          {/* Source provenance */}
          <div
            style={{
              background: 'rgba(6,182,212,0.06)',
              border: '1px solid rgba(6,182,212,0.2)',
              borderRadius: '6px',
              padding: '8px',
              fontSize: '10px',
              fontFamily: 'monospace',
              color: '#06b6d4',
              marginBottom: '10px',
            }}
          >
            <div style={{ color: '#64748b', marginBottom: '4px' }}>Source Provenance</div>
            <div>{sourceIcon[claim.source_type] || '📋'} {claim.source_type.toUpperCase()}</div>
            {Object.entries(claim.source_ref).map(([k, v]) => (
              <div key={k} style={{ color: '#94a3b8', marginLeft: '12px' }}>
                <span style={{ color: '#475569' }}>{k}:</span> {String(v)}
              </div>
            ))}
          </div>

          {/* Entity mentions */}
          {claim.entity_mentions?.length > 0 && (
            <div>
              <div style={{ fontSize: '10px', color: '#64748b', fontFamily: 'monospace', marginBottom: '5px', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                Entity Mentions
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                {claim.entity_mentions.map((e) => (
                  <span
                    key={e}
                    style={{
                      background: 'rgba(139,92,246,0.12)',
                      border: '1px solid rgba(139,92,246,0.3)',
                      borderRadius: '3px',
                      padding: '1px 6px',
                      fontSize: '9px',
                      color: '#c4b5fd',
                      fontFamily: 'monospace',
                    }}
                  >
                    {e}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div style={{ marginTop: '10px', fontSize: '10px', color: '#475569', fontFamily: 'monospace' }}>
            {new Date(claim.timestamp).toLocaleString()}
          </div>
        </>
      ) : (
        <div
          style={{
            background: 'rgba(255,255,255,0.03)',
            border: '1px solid #1e2d4d',
            borderRadius: '6px',
            padding: '10px',
            fontSize: '11px',
            color: '#94a3b8',
            lineHeight: '1.6',
          }}
        >
          {node.label.replace('\n', ' ')}
        </div>
      )}
    </div>
  );
}

// ─── Legend ───────────────────────────────────────────────────────────────────

function Legend() {
  const items = [
    { type: 'evidence', label: 'Evidence', color: '#06b6d4' },
    { type: 'contradiction', label: 'Contradiction', color: '#f59e0b' },
    { type: 'root_cause', label: 'Root Cause', color: '#8b5cf6' },
    { type: 'outcome', label: 'Outcome', color: '#ef4444' },
    { type: 'gap', label: 'Evidence Gap', color: '#64748b' },
  ];

  return (
    <div
      style={{
        position: 'absolute',
        top: '12px',
        right: '12px',
        background: 'rgba(15,22,41,0.9)',
        border: '1px solid #1e2d4d',
        borderRadius: '8px',
        padding: '10px 12px',
        zIndex: 5,
        backdropFilter: 'blur(4px)',
      }}
    >
      <div style={{ fontSize: '9px', color: '#64748b', fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '8px' }}>
        Node Types
      </div>
      {items.map(({ type, label, color }) => (
        <div key={type} style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
          <div
            style={{
              width: '10px',
              height: '10px',
              borderRadius: type === 'contradiction' ? '0' : '50%',
              background: `${color}20`,
              border: `1.5px solid ${color}`,
              flexShrink: 0,
              transform: type === 'contradiction' ? 'rotate(45deg)' : 'none',
            }}
          />
          <span style={{ fontSize: '10px', color: '#94a3b8', fontFamily: 'monospace' }}>{label}</span>
        </div>
      ))}
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function EvidenceGraph({ data }) {
  const svgRef = useRef(null);
  const containerRef = useRef(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [tooltip, setTooltip] = useState(null);
  const [transform, setTransform] = useState({ x: 0, y: 0, scale: 1 });
  const [isPanning, setIsPanning] = useState(false);
  const panStart = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 600, height: 400 });

  useEffect(() => {
    if (!containerRef.current) return;
    const ro = new ResizeObserver((entries) => {
      const { width, height } = entries[0].contentRect;
      setDimensions({ width: Math.max(400, width), height: Math.max(300, height) });
    });
    ro.observe(containerRef.current);
    return () => ro.disconnect();
  }, []);

  const graph = data?.graph;
  const graphWidth = dimensions.width - (selectedNode ? 260 : 0) - 24;
  const graphHeight = dimensions.height - 24;

  const positions = graph
    ? computeLayout(graph.nodes, graph.edges, graphWidth, graphHeight)
    : {};

  const handleMouseDown = useCallback((e) => {
    if (e.target.closest('.graph-node')) return;
    setIsPanning(true);
    panStart.current = { x: e.clientX - transform.x, y: e.clientY - transform.y };
  }, [transform]);

  const handleMouseMove = useCallback((e) => {
    if (!isPanning || !panStart.current) return;
    setTransform((t) => ({
      ...t,
      x: e.clientX - panStart.current.x,
      y: e.clientY - panStart.current.y,
    }));
  }, [isPanning]);

  const handleMouseUp = useCallback(() => {
    setIsPanning(false);
    panStart.current = null;
  }, []);

  const handleWheel = useCallback((e) => {
    e.preventDefault();
    const factor = e.deltaY > 0 ? 0.9 : 1.1;
    setTransform((t) => ({
      ...t,
      scale: Math.min(3, Math.max(0.3, t.scale * factor)),
    }));
  }, []);

  const handleNodeHover = useCallback((node, e) => {
    if (!node || !e) {
      setTooltip(null);
      return;
    }
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;
    setTooltip({
      node,
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    });
  }, []);

  if (!graph) {
    return (
      <div
        ref={containerRef}
        style={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* Grid background */}
        <svg
          style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', opacity: 0.3 }}
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e2d4d" strokeWidth="0.5" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>
        <div style={{ textAlign: 'center', zIndex: 1, padding: '24px' }}>
          <div
            style={{
              width: '48px',
              height: '48px',
              background: 'rgba(59,130,246,0.1)',
              border: '1px solid rgba(59,130,246,0.3)',
              borderRadius: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 12px',
            }}
          >
            <GitBranch size={24} color="#3b82f6" />
          </div>
          <div style={{ color: '#e2e8f0', fontSize: '13px', fontWeight: 600, marginBottom: '6px' }}>
            Evidence Causality Graph
          </div>
          <div style={{ color: '#64748b', fontSize: '11px', fontFamily: 'monospace' }}>
            Run an investigation to see the causality graph
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      style={{
        flex: 1,
        position: 'relative',
        overflow: 'hidden',
        cursor: isPanning ? 'grabbing' : 'grab',
      }}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      onWheel={handleWheel}
    >
      {/* Background grid */}
      <svg
        style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', opacity: 0.15 }}
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <pattern id="grid2" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e2d4d" strokeWidth="0.5" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid2)" />
      </svg>

      {/* Main graph SVG */}
      <svg
        ref={svgRef}
        style={{ width: '100%', height: '100%', display: 'block' }}
        xmlns="http://www.w3.org/2000/svg"
      >
        <g transform={`translate(${transform.x},${transform.y}) scale(${transform.scale})`}>
          {/* Edges first (behind nodes) */}
          {graph.edges.map((edge, i) => (
            <Edge key={i} edge={edge} positions={positions} />
          ))}
          {/* Nodes */}
          {graph.nodes.map((node) => (
            <NodeShape
              key={node.id}
              node={node}
              pos={positions[node.id] || { x: 100, y: 100 }}
              selected={selectedNode?.id === node.id}
              onClick={setSelectedNode}
              onHover={handleNodeHover}
            />
          ))}
        </g>
      </svg>

      {/* Legend */}
      <Legend />

      {/* Zoom hint */}
      <div
        style={{
          position: 'absolute',
          bottom: '10px',
          left: '12px',
          fontSize: '9px',
          color: '#475569',
          fontFamily: 'monospace',
        }}
      >
        Scroll to zoom · Drag to pan · Click node for details
      </div>

      {/* Tooltip */}
      {tooltip && (
        <div
          style={{
            position: 'absolute',
            left: tooltip.x + 14,
            top: tooltip.y - 10,
            background: '#0f1629',
            border: `1px solid ${NODE_CONFIG[tooltip.node.type]?.color || '#3b82f6'}60`,
            borderRadius: '6px',
            padding: '6px 10px',
            fontSize: '10px',
            color: '#e2e8f0',
            fontFamily: 'monospace',
            pointerEvents: 'none',
            zIndex: 30,
            boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
          }}
        >
          <div style={{ color: NODE_CONFIG[tooltip.node.type]?.color || '#3b82f6', fontWeight: 700 }}>
            {tooltip.node.id}
          </div>
          <div style={{ color: '#64748b' }}>{tooltip.node.type.replace('_', ' ')}</div>
          <div>Confidence: {Math.round(tooltip.node.confidence * 100)}%</div>
        </div>
      )}

      {/* Node detail drawer */}
      {selectedNode && (
        <NodeDetail
          node={selectedNode}
          data={data}
          onClose={() => setSelectedNode(null)}
        />
      )}
    </div>
  );
}
