'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { getStandardGraph, DependencyGraph } from '@/lib/api';
import { Panel } from '@/components/ui/Panel';
import { LoadingSkeleton } from '@/components/ui/LoadingSkeleton';

interface GraphViewProps {
  initialStandardId?: string;
  onExploreStandard?: (standardId: string) => void;
  onToast: (message: string, type?: 'success' | 'error' | 'info') => void;
}

const PRESET_STANDARDS = [
  'IS 12615:2018',
  'IS 694:2010',
  'IS 732:2019',
  'IS 10500:2012',
  'IS 3043:2018',
  'IS 15652:2006',
];

interface PositionedNode {
  id: string;
  label: string;
  title?: string;
  type?: string;
  group?: string;
  x: number;
  y: number;
  isRoot?: boolean;
}

export const GraphView: React.FC<GraphViewProps> = ({
  initialStandardId = 'IS 12615:2018',
  onExploreStandard,
  onToast,
}) => {
  const [standardId, setStandardId] = useState(initialStandardId);
  const [activeRoot, setActiveRoot] = useState(initialStandardId);
  const [maxDepth, setMaxDepth] = useState(2);
  const [direction, setDirection] = useState('both');
  const [isLoading, setIsLoading] = useState(false);
  const [graphData, setGraphData] = useState<DependencyGraph | null>(null);
  const [selectedNode, setSelectedNode] = useState<PositionedNode | null>(null);

  const svgRef = useRef<SVGSVGElement>(null);

  const fetchGraph = async (stdId: string, depth = maxDepth, dir = direction) => {
    if (!stdId.trim()) return;
    setIsLoading(true);
    setSelectedNode(null);
    try {
      const data = await getStandardGraph(stdId.trim(), depth, dir);
      setGraphData(data);
      setActiveRoot(stdId.trim());
      onToast(`Loaded topology for ${stdId.trim()} (${data.nodes?.length || 0} nodes, ${data.edges?.length || 0} edges)`, 'info');
    } catch (err: any) {
      onToast(err.message || 'Failed to load standards graph.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (initialStandardId) {
      setStandardId(initialStandardId);
      fetchGraph(initialStandardId);
    }
  }, [initialStandardId]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchGraph(standardId, maxDepth, direction);
  };

  // Layout calculation: place root at center, child nodes in concentric rings
  const positionedNodes: PositionedNode[] = React.useMemo(() => {
    if (!graphData || !graphData.nodes || graphData.nodes.length === 0) return [];
    const width = 800;
    const height = 500;
    const centerX = width / 2;
    const centerY = height / 2;

    const rootId = graphData.root_standard || activeRoot;
    const otherNodes = graphData.nodes.filter((n) => n.id !== rootId);

    const result: PositionedNode[] = [];
    // Root node
    const rootItem = graphData.nodes.find((n) => n.id === rootId) || {
      id: rootId,
      label: rootId,
      title: 'Active Root Standard',
    };
    result.push({
      ...rootItem,
      x: centerX,
      y: centerY,
      isRoot: true,
    });

    // Other nodes in radial layout
    const count = otherNodes.length;
    const radius = count > 8 ? 190 : 150;

    otherNodes.forEach((node, i) => {
      const angle = (2 * Math.PI * i) / count - Math.PI / 2;
      const x = centerX + radius * Math.cos(angle);
      const y = centerY + radius * Math.sin(angle);
      result.push({
        ...node,
        x,
        y,
        isRoot: false,
      });
    });

    return result;
  }, [graphData, activeRoot]);

  const nodeMap = React.useMemo(() => {
    const map = new Map<string, PositionedNode>();
    positionedNodes.forEach((n) => map.set(n.id, n));
    return map;
  }, [positionedNodes]);

  const getNodeColor = (node: PositionedNode) => {
    if (node.isRoot) return 'var(--accent-primary)';
    const type = (node.type || node.group || '').toLowerCase();
    if (type.includes('testing')) return 'var(--accent-cyan)';
    if (type.includes('safety')) return 'var(--accent-amber)';
    if (type.includes('supersede')) return 'var(--status-danger)';
    return '#6366f1';
  };

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
      <Panel
        title="Knowledge Graph & Relationship Topology"
        subtitle="Deterministic graph traversal exploring normative references, testing methods, safety standards, and supersession lineage."
        badge="Knowledge Graph"
      >
        {/* Search & Traversal Controls */}
        <form onSubmit={handleSubmit} style={{ marginBottom: '18px' }}>
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
            <div style={{ flex: 1, minWidth: '240px' }}>
              <input
                type="text"
                value={standardId}
                onChange={(e) => setStandardId(e.target.value)}
                placeholder="Enter IS Standard identifier (e.g. IS 12615:2018)..."
                required
              />
            </div>

            <div style={{ minWidth: '130px' }}>
              <select
                value={maxDepth}
                onChange={(e) => {
                  const d = parseInt(e.target.value, 10);
                  setMaxDepth(d);
                  fetchGraph(standardId, d, direction);
                }}
              >
                <option value={1}>Depth 1 (Direct)</option>
                <option value={2}>Depth 2 (Allied)</option>
                <option value={3}>Depth 3 (Extended)</option>
              </select>
            </div>

            <div style={{ minWidth: '130px' }}>
              <select
                value={direction}
                onChange={(e) => {
                  setDirection(e.target.value);
                  fetchGraph(standardId, maxDepth, e.target.value);
                }}
              >
                <option value="both">Both Directions</option>
                <option value="outbound">Outbound (Referenced)</option>
                <option value="inbound">Inbound (Referencing)</option>
              </select>
            </div>

            <button type="submit" disabled={isLoading} className="btn-primary" style={{ padding: '11px 22px' }}>
              {isLoading ? 'Traversing...' : '🕸️ Traverse Graph'}
            </button>
          </div>
        </form>

        {/* Quick presets */}
        <div>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: '8px', fontWeight: 600 }}>
            Inspect Benchmark Topologies:
          </span>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {PRESET_STANDARDS.map((std) => (
              <button
                key={std}
                type="button"
                onClick={() => {
                  setStandardId(std);
                  fetchGraph(std);
                }}
                style={{
                  padding: '5px 12px',
                  borderRadius: 'var(--radius-full)',
                  background: standardId === std ? 'var(--accent-primary-subtle)' : '#f8fafc',
                  border: `1px solid ${standardId === std ? 'var(--accent-primary)' : 'var(--border-subtle)'}`,
                  color: standardId === std ? 'var(--accent-primary-dark)' : 'var(--text-secondary)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.76rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                {std}
              </button>
            ))}
          </div>
        </div>
      </Panel>

      {/* Loading Skeleton */}
      {isLoading && (
        <Panel title="Loading Graph Topology...">
          <LoadingSkeleton height="350px" />
        </Panel>
      )}

      {/* Interactive Graph Canvas */}
      {!isLoading && graphData && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.35 }}>
          <div
            className="glass-panel"
            style={{
              padding: '24px',
              marginBottom: '20px',
              background: '#ffffff',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
              <div>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                  Graph Topology: {graphData.root_standard || activeRoot}
                </h3>
                <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  {positionedNodes.length} Verified Nodes · {graphData.edges?.length || 0} Grounded Edges
                </span>
              </div>

              {/* Legend */}
              <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', fontSize: '0.75rem', fontWeight: 600 }}>
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
                  <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: 'var(--accent-primary)' }} />
                  Root Standard
                </span>
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
                  <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: 'var(--accent-cyan)' }} />
                  Testing
                </span>
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
                  <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: 'var(--accent-amber)' }} />
                  Safety
                </span>
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
                  <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#6366f1' }} />
                  Normative
                </span>
              </div>
            </div>

            {/* SVG Visualizer */}
            <div
              style={{
                background: '#f8fafc',
                borderRadius: 'var(--radius-md)',
                border: '1px solid #e2e8f0',
                overflow: 'hidden',
                position: 'relative',
              }}
            >
              <svg
                ref={svgRef}
                viewBox="0 0 800 500"
                style={{ width: '100%', height: 'auto', maxHeight: '520px', display: 'block' }}
              >
                <defs>
                  <marker
                    id="arrowhead"
                    markerWidth="8"
                    markerHeight="6"
                    refX="22"
                    refY="3"
                    orient="auto"
                  >
                    <polygon points="0 0, 8 3, 0 6" fill="#94a3b8" />
                  </marker>
                </defs>

                {/* Edges */}
                {graphData.edges?.map((edge, i) => {
                  const source = nodeMap.get(edge.source);
                  const target = nodeMap.get(edge.target);
                  if (!source || !target) return null;

                  const isSupersede = edge.relationship_type.toLowerCase().includes('supersede');

                  return (
                    <g key={i}>
                      <line
                        x1={source.x}
                        y1={source.y}
                        x2={target.x}
                        y2={target.y}
                        stroke={isSupersede ? 'var(--status-danger)' : '#cbd5e1'}
                        strokeWidth={isSupersede ? 2 : 1.5}
                        strokeDasharray={isSupersede ? '4 3' : edge.is_unresolved ? '3 3' : undefined}
                        markerEnd="url(#arrowhead)"
                      />
                      {/* Edge Label */}
                      <text
                        x={(source.x + target.x) / 2}
                        y={(source.y + target.y) / 2 - 4}
                        fill="#64748b"
                        fontSize="9"
                        fontFamily="var(--font-mono)"
                        textAnchor="middle"
                        fontWeight="600"
                      >
                        {edge.relationship_type}
                      </text>
                    </g>
                  );
                })}

                {/* Nodes */}
                {positionedNodes.map((node) => {
                  const isSelected = selectedNode?.id === node.id;
                  const color = getNodeColor(node);

                  return (
                    <g
                      key={node.id}
                      onClick={() => setSelectedNode(node)}
                      style={{ cursor: 'pointer' }}
                    >
                      {/* Glow halo for root or selected */}
                      {(node.isRoot || isSelected) && (
                        <circle
                          cx={node.x}
                          cy={node.y}
                          r={node.isRoot ? 32 : 26}
                          fill={color}
                          opacity={0.18}
                        />
                      )}

                      <circle
                        cx={node.x}
                        cy={node.y}
                        r={node.isRoot ? 24 : 18}
                        fill="#ffffff"
                        stroke={color}
                        strokeWidth={isSelected ? 3 : 2}
                      />

                      <text
                        cx={node.x}
                        cy={node.y}
                        x={node.x}
                        y={node.y + 4}
                        fill={color}
                        fontSize={node.isRoot ? '12' : '10'}
                        fontWeight="800"
                        textAnchor="middle"
                      >
                        {node.isRoot ? '★' : '●'}
                      </text>

                      {/* Label Text below node */}
                      <text
                        x={node.x}
                        y={node.y + (node.isRoot ? 38 : 30)}
                        fill="var(--text-primary)"
                        fontSize="10"
                        fontWeight="700"
                        fontFamily="var(--font-mono)"
                        textAnchor="middle"
                      >
                        {node.label || node.id}
                      </text>
                    </g>
                  );
                })}
              </svg>
            </div>

            {/* Selected Node Details Drawer */}
            {selectedNode && (
              <div
                style={{
                  marginTop: '16px',
                  padding: '16px 20px',
                  background: '#f8fafc',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid #e2e8f0',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  flexWrap: 'wrap',
                  gap: '12px',
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 800, fontSize: '1rem', color: 'var(--text-primary)' }}>
                      {selectedNode.id}
                    </span>
                    {selectedNode.isRoot && <span className="badge badge-indigo">Root Node</span>}
                    {selectedNode.type && <span className="badge badge-cyan">{selectedNode.type}</span>}
                  </div>
                  {selectedNode.title && (
                    <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                      {selectedNode.title}
                    </p>
                  )}
                </div>

                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    onClick={() => {
                      setStandardId(selectedNode.id);
                      fetchGraph(selectedNode.id);
                    }}
                    className="btn-secondary"
                    style={{ fontSize: '0.78rem', padding: '6px 14px' }}
                  >
                    Center on this Node 🎯
                  </button>

                  {onExploreStandard && (
                    <button
                      onClick={() => onExploreStandard(selectedNode.id)}
                      className="btn-primary"
                      style={{ fontSize: '0.78rem', padding: '6px 14px' }}
                    >
                      View in Explorer ↗
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        </motion.div>
      )}
    </div>
  );
};
