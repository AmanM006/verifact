import { useState, useRef, useCallback, useEffect } from 'react';
import { X, ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';

// ─── Layout helpers ──────────────────────────────────────────────────────────

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
  ids.forEach((id) => { if (!sorted.includes(id)) sorted.push(id); });
  return sorted;
}

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

function computeLayout(nodes, edges, width, height) {
  const PADDING_X = 80;
  const PADDING_Y = 60;

  const layers = assignLayers(nodes, edges);
  const maxLayer = Math.max(...Object.values(layers), 0);

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

// ─── Clean High-Contrast Nodes ──────────────────────────────────────────────

const NODE_CONFIG = {
  evidence:      { color: '#38bdf8', border: '#0284c7', labelColor: '#ffffff', tag: 'EVIDENCE' },
  contradiction: { color: '#f59e0b', border: '#d97706', labelColor: '#ffffff', tag: 'CONTRADICTION' },
  root_cause:    { color: '#a855f7', border: '#7e22ce', labelColor: '#ffffff', tag: 'ROOT CAUSE' },
  outcome:       { color: '#ef4444', border: '#b91c1c', labelColor: '#ffffff', tag: 'OUTCOME' },
  gap:           { color: '#71717a', border: '#3f3f46', labelColor: '#d4d4d8', tag: 'GAP' },
};

function NodeShape({ node, pos, selected, onClick }) {
  const cfg = NODE_CONFIG[node.type] || NODE_CONFIG.evidence;
  const lines = (node.label || node.id).split('\n');

  return (
    <g
      className="graph-node"
      style={{ cursor: 'pointer' }}
      onClick={(e) => {
        e.stopPropagation();
        onClick(node);
      }}
    >
      {/* Node selection indicator ring */}
      {selected && (
        <rect
          x={pos.x - 48}
          y={pos.y - 30}
          width="96"
          height="60"
          rx="8"
          fill="none"
          stroke="#ffffff"
          strokeWidth="2"
        />
      )}

      {/* Node Box */}
      <rect
        x={pos.x - 44}
        y={pos.y - 26}
        width="88"
        height="52"
        rx="6"
        fill="#121215"
        stroke={selected ? '#ffffff' : cfg.border}
        strokeWidth={selected ? 2 : 1.5}
      />

      {/* Type badge on top border */}
      <rect
        x={pos.x - 44}
        y={pos.y - 26}
        width="88"
        height="14"
        rx="5"
        fill={`${cfg.color}25`}
      />
      <text
        x={pos.x}
        y={pos.y - 16}
        textAnchor="middle"
        fill={cfg.color}
        fontSize="8"
        fontWeight="700"
        fontFamily="ui-monospace, monospace"
      >
        {cfg.tag}
      </text>

      {/* Node text content */}
      <text
        x={pos.x}
        y={pos.y + 4}
        textAnchor="middle"
        fill="#ededed"
        fontSize="11"
        fontWeight="600"
      >
        {lines[0]}
      </text>
      {lines[1] && (
        <text
          x={pos.x}
          y={pos.y + 17}
          textAnchor="middle"
          fill="#a1a1aa"
          fontSize="10"
          fontFamily="ui-monospace, monospace"
        >
          {lines[1]}
        </text>
      )}
    </g>
  );
}

function Edge({ edge, positions }) {
  const src = positions[edge.source];
  const tgt = positions[edge.target];
  if (!src || !tgt) return null;

  const dx = tgt.x - src.x;
  const dy = tgt.y - src.y;
  const dist = Math.sqrt(dx * dx + dy * dy);
  if (dist === 0) return null;

  const x1 = src.x + (dx / dist) * 44;
  const y1 = src.y + (dy / dist) * 26;
  const x2 = tgt.x - (dx / dist) * 46;
  const y2 = tgt.y - (dy / dist) * 28;

  const mx = (x1 + x2) / 2;
  const my = (y1 + y2) / 2;

  return (
    <g>
      <defs>
        <marker
          id={`arrow-${edge.source}-${edge.target}`}
          markerWidth="7"
          markerHeight="7"
          refX="6"
          refY="3.5"
          orient="auto"
        >
          <polygon points="0 0, 7 3.5, 0 7" fill="#52525b" />
        </marker>
      </defs>
      <line
        x1={x1}
        y1={y1}
        x2={x2}
        y2={y2}
        stroke="#3f3f46"
        strokeWidth="1.5"
        markerEnd={`url(#arrow-${edge.source}-${edge.target})`}
      />
      {edge.label && (
        <g transform={`translate(${mx}, ${my})`}>
          <rect
            x="-28"
            y="-9"
            width="56"
            height="15"
            rx="3"
            fill="#09090b"
            stroke="#27272a"
            strokeWidth="1"
          />
          <text
            x="0"
            y="2"
            textAnchor="middle"
            fill="#a1a1aa"
            fontSize="8.5"
            fontFamily="ui-monospace, monospace"
          >
            {edge.label}
          </text>
        </g>
      )}
    </g>
  );
}

// ─── Detail Drawer ────────────────────────────────────────────────────────────

function NodeDetail({ node, data, onClose }) {
  const claim = data?.claims?.find((c) => c.claim_id === node.id);
  const cfg = NODE_CONFIG[node.type] || NODE_CONFIG.evidence;

  return (
    <div
      style={{
        position: 'absolute',
        right: 0,
        top: 0,
        bottom: 0,
        width: '320px',
        background: '#09090b',
        borderLeft: '1px solid #27272a',
        zIndex: 20,
        overflowY: 'auto',
        padding: '16px',
        boxShadow: '-8px 0 24px rgba(0,0,0,0.7)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span
            style={{
              background: `${cfg.color}20`,
              color: cfg.color,
              border: `1px solid ${cfg.border}`,
              padding: '2px 7px',
              borderRadius: '4px',
              fontSize: '10px',
              fontFamily: 'ui-monospace, monospace',
              fontWeight: 700,
            }}
          >
            {cfg.tag}
          </span>
          <span style={{ fontSize: '13px', fontWeight: 600, color: '#ffffff' }}>
            {node.id}
          </span>
        </div>
        <button
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            color: '#71717a',
            cursor: 'pointer',
            padding: '4px',
          }}
        >
          <X size={16} />
        </button>
      </div>

      <div style={{ marginBottom: '16px' }}>
        <div style={{ fontSize: '11px', color: '#71717a', marginBottom: '4px', fontFamily: 'ui-monospace, monospace' }}>
          Confidence
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ flex: 1, background: '#18181b', borderRadius: '3px', height: '6px', overflow: 'hidden' }}>
            <div
              style={{
                width: `${node.confidence * 100}%`,
                height: '100%',
                background: cfg.color,
              }}
            />
          </div>
          <span style={{ fontSize: '12px', color: '#ededed', fontFamily: 'ui-monospace, monospace', fontWeight: 600 }}>
            {Math.round(node.confidence * 100)}%
          </span>
        </div>
      </div>

      {claim ? (
        <>
          <div style={{ marginBottom: '16px' }}>
            <div style={{ fontSize: '11px', color: '#71717a', marginBottom: '6px', fontFamily: 'ui-monospace, monospace' }}>
              Extracted Claim
            </div>
            <div
              style={{
                background: '#121215',
                border: '1px solid #27272a',
                borderRadius: '6px',
                padding: '12px',
                fontSize: '12px',
                color: '#ededed',
                lineHeight: '1.5',
              }}
            >
              {claim.text}
            </div>
          </div>

          <div style={{ marginBottom: '16px' }}>
            <div style={{ fontSize: '11px', color: '#71717a', marginBottom: '6px', fontFamily: 'ui-monospace, monospace' }}>
              Source Provenance
            </div>
            <div
              style={{
                background: '#121215',
                border: '1px solid #27272a',
                borderRadius: '6px',
                padding: '10px',
                fontSize: '11px',
                fontFamily: 'ui-monospace, monospace',
                color: '#38bdf8',
              }}
            >
              <div style={{ fontWeight: 600, marginBottom: '6px', color: '#ffffff' }}>
                {claim.source_type.toUpperCase()}
              </div>
              {claim.source_ref &&
                Object.entries(claim.source_ref).map(([k, v]) => (
                  <div key={k} style={{ color: '#a1a1aa', margin: '2px 0' }}>
                    <span style={{ color: '#71717a' }}>{k}: </span>
                    {String(v)}
                  </div>
                ))}
            </div>
          </div>

          {claim.entity_mentions?.length > 0 && (
            <div>
              <div style={{ fontSize: '11px', color: '#71717a', marginBottom: '6px', fontFamily: 'ui-monospace, monospace' }}>
                Entity Mentions
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
                {claim.entity_mentions.map((e) => (
                  <span
                    key={e}
                    style={{
                      background: '#18181b',
                      border: '1px solid #27272a',
                      borderRadius: '4px',
                      padding: '2px 7px',
                      fontSize: '11px',
                      color: '#d4d4d8',
                    }}
                  >
                    {e}
                  </span>
                ))}
              </div>
            </div>
          )}
        </>
      ) : (
        <div
          style={{
            background: '#121215',
            border: '1px solid #27272a',
            borderRadius: '6px',
            padding: '12px',
            fontSize: '12px',
            color: '#ededed',
            lineHeight: '1.5',
          }}
        >
          {node.label}
        </div>
      )}
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function EvidenceGraph({ data }) {
  const containerRef = useRef(null);
  const [selectedNode, setSelectedNode] = useState(null);
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

  // Intercept wheel events locally on the container so the whole page doesn't zoom
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const onWheelHandler = (e) => {
      e.preventDefault();
      e.stopPropagation();
      const zoomFactor = e.deltaY > 0 ? 0.92 : 1.08;
      setTransform((t) => ({
        ...t,
        scale: Math.min(2.5, Math.max(0.4, t.scale * zoomFactor)),
      }));
    };

    el.addEventListener('wheel', onWheelHandler, { passive: false });
    return () => el.removeEventListener('wheel', onWheelHandler);
  }, []);

  const graph = data?.graph;
  const graphWidth = dimensions.width - (selectedNode ? 320 : 0) - 40;
  const graphHeight = dimensions.height - 40;

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

  const resetZoom = () => setTransform({ x: 0, y: 0, scale: 1 });
  const zoomIn = () => setTransform((t) => ({ ...t, scale: Math.min(2.5, t.scale * 1.15) }));
  const zoomOut = () => setTransform((t) => ({ ...t, scale: Math.max(0.4, t.scale * 0.85) }));

  return (
    <div
      ref={containerRef}
      style={{
        flex: 1,
        position: 'relative',
        overflow: 'hidden',
        background: '#000000',
        cursor: isPanning ? 'grabbing' : 'grab',
        userSelect: 'none',
      }}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      {/* Subtle Dot Grid */}
      <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', opacity: 0.12, pointerEvents: 'none' }}>
        <defs>
          <pattern id="dotgrid" width="24" height="24" patternUnits="userSpaceOnUse">
            <circle cx="2" cy="2" r="1" fill="#71717a" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#dotgrid)" />
      </svg>

      {/* Main SVG Graph */}
      {graph && (
        <svg style={{ width: '100%', height: '100%', display: 'block' }}>
          <g transform={`translate(${transform.x},${transform.y}) scale(${transform.scale})`}>
            {graph.edges.map((edge, i) => (
              <Edge key={i} edge={edge} positions={positions} />
            ))}
            {graph.nodes.map((node) => (
              <NodeShape
                key={node.id}
                node={node}
                pos={positions[node.id] || { x: 100, y: 100 }}
                selected={selectedNode?.id === node.id}
                onClick={setSelectedNode}
              />
            ))}
          </g>
        </svg>
      )}

      {/* Floating Controls Bar */}
      <div
        style={{
          position: 'absolute',
          bottom: '12px',
          right: selectedNode ? '332px' : '12px',
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          background: '#121215',
          border: '1px solid #27272a',
          borderRadius: '6px',
          padding: '3px',
          zIndex: 10,
        }}
      >
        <button
          onClick={zoomIn}
          style={{ background: 'none', border: 'none', color: '#a1a1aa', padding: '5px', cursor: 'pointer', borderRadius: '4px' }}
          title="Zoom in"
        >
          <ZoomIn size={14} />
        </button>
        <button
          onClick={zoomOut}
          style={{ background: 'none', border: 'none', color: '#a1a1aa', padding: '5px', cursor: 'pointer', borderRadius: '4px' }}
          title="Zoom out"
        >
          <ZoomOut size={14} />
        </button>
        <button
          onClick={resetZoom}
          style={{ background: 'none', border: 'none', color: '#a1a1aa', padding: '5px', cursor: 'pointer', borderRadius: '4px' }}
          title="Reset"
        >
          <RotateCcw size={14} />
        </button>
        <span style={{ fontSize: '10px', color: '#71717a', padding: '0 6px', fontFamily: 'ui-monospace, monospace' }}>
          {Math.round(transform.scale * 100)}%
        </span>
      </div>

      {/* Selected Node Drawer */}
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
