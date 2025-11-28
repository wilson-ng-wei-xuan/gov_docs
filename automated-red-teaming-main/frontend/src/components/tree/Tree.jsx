import React, { useCallback, useMemo, useState } from 'react';
import ReactFlow, {
    MiniMap,
    Controls,
    Background,
    useNodesState,
    useEdgesState,
    addEdge,
    Panel,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Shield, Minus, Plus } from 'lucide-react';
import { useApiContext } from '../../hooks/useApiContext';
import { VulnAnalysisNode } from './Node';
import { DataModal } from '../modal/DataModal';
import { ChatModal } from '../modal/ChatModal';

const nodeTypes = {
    vulnAnalysisNode: VulnAnalysisNode,
};

export const VulnAnalysisTree = ({ analysisData }) => {
    const [collapsedNodes, setCollapsedNodes] = useState(new Set());
    const [expandedNodes, setExpandedNodes] = useState(new Map()); // Track which nodes have expanded sections
    
    // Modal state management
    const [modalOpen, setModalOpen] = useState(false);
    const [selectedNodeData, setSelectedNodeData] = useState(null);
    const [modalType, setModalType] = useState(''); // 'inputs' or 'results'

    const getDescendantIds = useCallback((nodeId, allNodes) => {
        const descendants = new Set();
        const nodeData = allNodes?.find(n => n?.node_id === nodeId);
        if (nodeData?.children) {
            nodeData.children.forEach(child => {
                if (child?.node_id) {
                    descendants.add(child.node_id);
                    const childDescendants = getDescendantIds(child.node_id, allNodes);
                    childDescendants.forEach(id => descendants.add(id));
                }
            });
        }
        return descendants;
    }, []);

    const countChildren = useCallback((node) => {
        if (!node?.children?.length) return 0;
        let count = node.children.length;
        node.children.forEach(child => {
            count += countChildren(child);
        });
        return count;
    }, []);

    const toggleNodeCollapse = useCallback((nodeId) => {
        setCollapsedNodes(prev => {
            const newCollapsed = new Set(prev);
            newCollapsed.has(nodeId) ? newCollapsed.delete(nodeId) : newCollapsed.add(nodeId);
            return newCollapsed;
        });
    }, []);

    // Handle node expansion state changes
    const handleExpansionChange = useCallback((nodeId, section, isExpanded) => {
        setExpandedNodes(prev => {
            const newExpanded = new Map(prev);
            const nodeExpansions = newExpanded.get(nodeId) || {};
            newExpanded.set(nodeId, {
                ...nodeExpansions,
                [section]: isExpanded
            });
            return newExpanded;
        });
    }, []);

    // Modal handlers
    const openChatModal = useCallback((nodeData) => {
        setSelectedNodeData(nodeData);
        setModalType('chat');
        setModalOpen(true);
    }, []);

    const openInputsModal = useCallback((nodeData) => {
        setSelectedNodeData(nodeData);
        setModalType('inputs');
        setModalOpen(true);
    }, []);

    const openResultsModal = useCallback((nodeData) => {
        setSelectedNodeData(nodeData);
        setModalType('results');
        setModalOpen(true);
    }, []);

    const closeModal = useCallback(() => {
        setModalOpen(false);
        setSelectedNodeData(null);
        setModalType('');
    }, []);

    // Calculate additional height for expanded sections
    const getNodeExtraHeight = useCallback((nodeId) => {
        const expansions = expandedNodes.get(nodeId);
        if (!expansions) return 0;

        let extraHeight = 0;
        if (expansions.inputs) extraHeight += 160; // Height of expanded inputs section
        if (expansions.results) extraHeight += 160; // Height of expanded results section
        return extraHeight;
    }, [expandedNodes]);

    const { nodes: initialNodes, edges: initialEdges } = useMemo(() => {
        const nodes = [];
        const edges = [];
        const allTreeNodes = [];

        if (!analysisData?.tree) return { nodes, edges };

        const collectNodes = (node) => {
            if (!node) return;
            allTreeNodes.push(node);
            node.children?.forEach(collectNodes);
        };
        collectNodes(analysisData.tree);

        const shouldShowNode = (nodeId, path = []) => {
            if (path.length === 0) return true;
            return !path.some(pid => collapsedNodes.has(pid));
        };

        const calculatePosition = (level, siblingIndex, totalSiblings, siblingHeights = []) => {
            // Dynamic level width based on node content and level
            const baseWidth = 400;
            const levelWidth = baseWidth + (level * 50); // Increase spacing for deeper levels
            
            // Dynamic spacing based on node heights
            const baseSpacing = 60;
            const currentNodeHeight = siblingHeights[siblingIndex] || 200;
            const prevNodeHeight = siblingIndex > 0 ? siblingHeights[siblingIndex - 1] : 200;
            
            // Use larger spacing for taller nodes
            const dynamicSpacing = Math.max(baseSpacing, (currentNodeHeight + prevNodeHeight) * 0.15);

            // Calculate Y position based on accumulated heights of previous siblings
            let yPosition = 0;
            for (let i = 0; i < siblingIndex; i++) {
                const spacing = i === 0 ? baseSpacing : 
                    Math.max(baseSpacing, (siblingHeights[i] + siblingHeights[i - 1]) * 0.15);
                yPosition += siblingHeights[i] + spacing;
            }

            // Center the entire group with dynamic spacing
            let totalGroupHeight = siblingHeights.reduce((sum, height) => sum + height, 0);
            for (let i = 0; i < siblingHeights.length - 1; i++) {
                const spacing = Math.max(baseSpacing, (siblingHeights[i] + siblingHeights[i + 1]) * 0.15);
                totalGroupHeight += spacing;
            }
            const startY = -totalGroupHeight / 2;

            return {
                x: level * levelWidth,
                y: startY + yPosition
            };
        };

        const processNode = (node, level = 0, siblingIndex = 0, totalSiblings = 1, parentId = null, path = []) => {
            if (!node) return;
            const nodeId = node.node_id;
            const currentPath = [...path, nodeId];

            if (!shouldShowNode(nodeId, path)) return;

            // Calculate heights for all siblings at this level first
            const siblingNodes = parentId ?
                allTreeNodes.find(n => n.node_id === parentId)?.children || [] :
                [analysisData.tree];

            const siblingHeights = siblingNodes.map(sibling => {
                // Calculate more accurate base height based on content
                let baseHeight = 180; // Minimum base height
                
                // Add height for target URL
                if (sibling.inputs?.tag_recon_info?.url || sibling.inputs?.target) {
                    baseHeight += 40;
                }
                
                // Add height for parameters
                if (sibling.inputs?.tag_recon_info?.vuln_param) {
                    baseHeight += 35;
                }
                
                // Add height for metrics
                const metricsCount = [
                    sibling.result?.endpoints?.length > 0,
                    sibling.result?.assessments?.[0]?.vuln_param_sets?.length > 0
                ].filter(Boolean).length;
                baseHeight += metricsCount * 20;
                
                // Add height for test results
                if (sibling.result?.final_param_result_list) {
                    baseHeight += 45;
                }
                
                // Add height for collapsed children indicator
                if (collapsedNodes.has(sibling.node_id) && sibling.children?.length > 0) {
                    baseHeight += 30;
                }
                
                const extraHeight = getNodeExtraHeight(sibling.node_id);
                return baseHeight + extraHeight;
            });

            let nodeType = 'vuln_test';
            let functionName = node.function?.replace('run_', '').replace('_', ' ').toUpperCase() || node.label || 'UNKNOWN';

            if (node.function === 'run_katana') {
                nodeType = 'root';
                functionName = 'KATANA SCAN';
            } else if (node.function === 'run_recon_agent') {
                nodeType = 'recon';
                functionName = 'RECON AGENT';
            }

            const vulnType = node.inputs?.tag_recon_info?.tag;
            const targetUrl = node.inputs?.tag_recon_info?.url || node.inputs?.target;
            const parameter = node.inputs?.tag_recon_info?.vuln_param;

            const metrics = [];
            if (node.result?.endpoints?.length) {
                metrics.push({
                    label: 'Endpoints',
                    value: node.result.endpoints.length,
                    className: 'text-blue-600 font-medium',
                });
            }
            if (node.result?.assessments?.[0]?.vuln_param_sets?.length) {
                metrics.push({
                    label: 'Vuln Params',
                    value: node.result.assessments[0].vuln_param_sets.length,
                    className: 'text-orange-600 font-medium',
                });
            }

            let testResults = null;
            const paramResultList = node.result?.final_param_result_list;
            if (paramResultList && typeof paramResultList === 'object') {
                const allTests = [];
                Object.values(paramResultList).forEach(paramTests => {
                    paramTests?.forEach(testGroup => {
                        const tests = testGroup?.param_result_list?.param_result_list ?? [];
                        allTests.push(...tests);
                    });
                });
                testResults = {
                    totalTests: allTests.length,
                    vulnerableCount: allTests.filter(test => test?.potentially_vulnerable).length
                };
            }

            const reactFlowNode = {
                id: nodeId,
                type: 'vulnAnalysisNode',
                position: calculatePosition(level, siblingIndex, totalSiblings, siblingHeights),
                data: {
                    nodeType,
                    functionName,
                    status: node.status,
                    vulnType,
                    targetUrl,
                    parameter,
                    inputs: node.inputs,
                    results: node.result,
                    metrics: metrics.length ? metrics : null,
                    testResults,
                    hasChildren: Array.isArray(node.children) && node.children.length > 0,
                    isCollapsed: collapsedNodes.has(nodeId),
                    childrenCount: countChildren(node),
                    onToggleCollapse: toggleNodeCollapse,
                    onExpansionChange: handleExpansionChange,
                    onOpenInputsModal: openInputsModal,
                    onOpenResultsModal: openResultsModal,
                    onOpenChatModal: openChatModal,
                },
            };
            nodes.push(reactFlowNode);

            if (parentId) {
                edges.push({
                    id: `${parentId}-${nodeId}`,
                    source: parentId,
                    target: nodeId,
                    type: 'smoothstep',
                    animated: ['in_progress', 'initialized'].includes(node.status),
                    style: {
                        stroke: node.status === 'completed' ? '#10b981' : '#f59e0b',
                        strokeWidth: 2
                    }
                });
            }

            if (reactFlowNode.data.hasChildren && !reactFlowNode.data.isCollapsed) {
                node.children.forEach((child, idx) => {
                    processNode(child, level + 1, idx, node.children.length, nodeId, currentPath);
                });
            }
        };

        processNode(analysisData.tree);
        return { nodes, edges };
    }, [analysisData?.tree, collapsedNodes, toggleNodeCollapse, countChildren, getNodeExtraHeight, handleExpansionChange]);

    const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
    const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

    React.useEffect(() => {
        setNodes(initialNodes);
        setEdges(initialEdges);
    }, [initialNodes, initialEdges, setNodes, setEdges]);

    const onConnect = useCallback(
        (params) => setEdges((eds) => addEdge(params, eds)),
        [setEdges]
    );

    const collapseAll = useCallback(() => {
        const allNodeIds = new Set();
        const collect = (node) => {
            if (!node) return;
            if (Array.isArray(node.children) && node.children.length > 0) {
                allNodeIds.add(node.node_id);
                node.children.forEach(collect);
            }
        };
        collect(analysisData?.tree);
        setCollapsedNodes(allNodeIds);
    }, [analysisData]);

    const expandAll = useCallback(() => {
        setCollapsedNodes(new Set());
    }, []);

    const { fetchState } = useApiContext();
    const [sid, setSID] = useState('');

    const handleClick = () => {
        if (sid?.trim()) {
            fetchState(sid.trim());
        }
    };

    return (
        <div className="w-full h-[90vh] bg-gray-50">
            
            {/* For debugging */}
            {/* <div className="p-2">
                <label>Retrieve session: </label>
                <input
                    className="bg-white w-64 border-black border rounded-md"
                    onChange={(e) => setSID(e.target.value)}
                />
                <button
                    className="p-1 ml-2 bg-neutral-500 text-sm rounded-xl"
                    onClick={handleClick}
                >
                    Submit
                </button>
            </div> */}

            {!analysisData?.tree ? (
                <div className="p-4 text-center text-gray-500">
                    No analysis data available.
                </div>
            ) : (
                <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                    onConnect={onConnect}
                    nodeTypes={nodeTypes}
                    fitView
                    fitViewOptions={{ padding: 0.3, maxZoom: 0.8 }}
                    defaultViewport={{ x: 0, y: 0, zoom: 0.3 }}
                    minZoom={0.2}
                    maxZoom={2}
                    nodesDraggable={true}
                    nodesConnectable={false}
                    elementsSelectable={true}
                    selectNodesOnDrag={false}
                >
                    <Controls position="top-left" />
                    <MiniMap
                        position="top-right"
                        nodeColor={(node) => {
                            switch (node.data?.nodeType) {
                                case "root":
                                    return "#3b82f6";
                                case "recon":
                                    return "#10b981";
                                case "vuln_test":
                                    return "#8b5cf6";
                                default:
                                    return "#6b7280";
                            }
                        }}
                        className="bg-white/0 border border-gray-300 rounded"
                    />
                    <Background variant="dots" gap={20} size={1} />

                    <Panel
                        position="bottom-right"
                        className="bg-white p-2 rounded-lg shadow-lg border"
                    >
                        <div className="flex items-center space-x-2">
                            <button
                                onClick={expandAll}
                                className="px-3 py-1 bg-green-100 text-green-800 rounded hover:bg-green-200 transition-colors text-sm flex items-center space-x-1"
                            >
                                <Plus className="w-3 h-3" />
                                <span>Expand All</span>
                            </button>
                            <button
                                onClick={collapseAll}
                                className="px-3 py-1 bg-blue-100 text-blue-800 rounded hover:bg-blue-200 transition-colors text-sm flex items-center space-x-1"
                            >
                                <Minus className="w-3 h-3" />
                                <span>Collapse All</span>
                            </button>
                        </div>
                    </Panel>

                    <Panel
                        position="bottom-left"
                        className="group relative bg-white rounded-lg shadow-lg overflow-hidden transition-all duration-400 ease-out w-10 h-10 hover:w-56 hover:h-28 opacity-70 hover:opacity-100"
                    >
                        {/* Simple i icon - visible when collapsed */}
                        <div className="absolute inset-0 flex items-center justify-center transition-opacity duration-150 group-hover:opacity-0 group-hover:delay-0 delay-200">
                            <span className="text-gray-500 font-medium text-sm">i</span>
                        </div>
                        
                        {/* Content - visible when expanded */}
                        <div className="p-4 opacity-0 group-hover:opacity-100 transition-opacity duration-150 delay-300 group-hover:delay-300">
                            <div className="space-y-2 text-sm">
                                <div className="text-xs font-semibold text-gray-700">
                                    Controls:
                                </div>
                                <div className="text-xs text-gray-600 space-y-1">
                                    <div>
                                        • Click{" "}
                                        <Plus className="w-3 h-3 inline mx-1" />/
                                        <Minus className="w-3 h-3 inline mx-1" /> to
                                        expand/collapse
                                    </div>
                                    <div>• Drag nodes to reposition</div>
                                    <div>• Mouse wheel to zoom</div>
                                </div>
                            </div>
                        </div>
                    </Panel>
                </ReactFlow>
            )}
            
            {/* Modals */}
            <DataModal
                isOpen={modalOpen && modalType !== 'chat'}
                onClose={closeModal}
                data={modalType === 'inputs' ? selectedNodeData?.inputs : selectedNodeData?.results}
                nodeId={selectedNodeData?.nodeId}
                functionName={selectedNodeData?.functionName}
                type={modalType === 'inputs' ? 'Inputs' : 'Results'}
            />
            <ChatModal
                isOpen={modalOpen && modalType === 'chat'}
                onClose={closeModal}
                node={selectedNodeData}
            />
        </div>
    );
}
