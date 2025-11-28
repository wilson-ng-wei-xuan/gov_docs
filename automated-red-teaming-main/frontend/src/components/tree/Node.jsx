import React, { useState } from 'react';
import { Handle, Position } from 'reactflow';
import { 
    Shield,
    Database, 
    FileText, 
    ExternalLink, 
    CheckCircle, 
    Clock, 
    AlertCircle, 
    Plus, 
    Minus, 
    ChevronDown, 
    Loader2, 
    Copy, 
    Check, 
    Maximize2,
    MessagesSquare 
    } from 'lucide-react';

/// Custom node component for vulnerability analysis nodes
export const VulnAnalysisNode = ({ data = {}, id }) => {
    const [inputsExpanded, setInputsExpanded] = useState(false);
    const [resultsExpanded, setResultsExpanded] = useState(false);
    const [copiedItems, setCopiedItems] = useState(new Set());

    // Copy to clipboard utility function
    const copyToClipboard = async (text, itemKey) => {
        try {
            await navigator.clipboard.writeText(text);
            setCopiedItems(prev => new Set([...prev, itemKey]));
            // Clear the copied state after 2 seconds
            setTimeout(() => {
                setCopiedItems(prev => {
                    const newSet = new Set(prev);
                    newSet.delete(itemKey);
                    return newSet;
                });
            }, 2000);
        } catch (err) {
            console.error('Failed to copy text: ', err);
        }
    };

    // Copy button component
    const CopyButton = ({ text, itemKey, className = "" }) => {
        const isCopied = copiedItems.has(itemKey);
        return (
            <button
                onClick={(e) => {
                    e.stopPropagation();
                    copyToClipboard(text, itemKey);
                }}
                className={`p-1 hover:bg-gray-200 rounded transition-colors ${className}`}
                title={isCopied ? "Copied!" : "Copy to clipboard"}
            >
                {isCopied ? (
                    <Check className="w-3 h-3 text-green-500" />
                ) : (
                    <Copy className="w-3 h-3 text-gray-500 hover:text-gray-700" />
                )}
            </button>
        );
    };

    const ChatButton = ({ nodeId, className = "" }) => {
        return (
            <button
                onClick={(e) => {
                    e.stopPropagation();
                    data?.onOpenChatModal?.({
                        nodeId: id,
                        functionName: data.functionName
                    });
                }}
                className={`p-1 hover:bg-gray-200 rounded transition-colors ${className}`}
                title={`View chat logs`}
            >
                <MessagesSquare className="w-3 h-3 text-gray-500 hover:text-gray-700" />
            </button>
        );
    };

    // Notify parent when expansion state changes
    const handleInputsToggle = () => {
        const newState = !inputsExpanded;
        setInputsExpanded(newState);
        data?.onExpansionChange?.(id, 'inputs', newState);
    };

    const handleResultsToggle = () => {
        const newState = !resultsExpanded;
        setResultsExpanded(newState);
        data?.onExpansionChange?.(id, 'results', newState);
    };
    const getStatusIcon = () => {
        switch (data?.status) {
            case 'completed':
                return <CheckCircle className="w-4 h-4 text-green-500" />;
            case 'in_progress':
                return <Clock className="w-4 h-4 text-blue-500" />;
            case 'initialized':
                return <Clock className="w-4 h-4 text-yellow-500" />;
            default:
                return <AlertCircle className="w-4 h-4 text-gray-500" />;
        }
    };

    const getBorderColor = () => {
        switch (data?.nodeType) {
            case 'root':
                return 'border-blue-500';
            case 'recon':
                return 'border-blue-500';
            case 'vuln_test':
                return 'border-red-500';
            default:
                return 'border-gray-300';
        }
    };

    const handleCollapseToggle = (e) => {
        e.stopPropagation();
        data?.onToggleCollapse?.(id);
    };

    return (
        <div className={`px-4 py-3 shadow-lg rounded-lg bg-white border-l-4 ${getBorderColor()} min-w-[250px] max-w-[350px] relative transition-all duration-300 ease-in-out group`}>
            {/* Input Handle */}
            <Handle
                type="target"
                position={Position.Left}
                className="w-3 h-3 !bg-gray-400 !border-2 !border-white"
            />

            {/* Header with collapse button */}
            <div className="flex items-center justify-between mb-1">
                <div className="flex items-center space-x-2">
                    {getStatusIcon()}
                    <div className="flex items-center space-x-1">
                        <span className="font-semibold text-gray-800 text-sm pr-1">
                            {data?.functionName ?? 'Unnamed Node'}
                        </span>
                        <CopyButton 
                            text={data?.functionName ?? 'Unnamed Node'} 
                            itemKey={`function-${id}`}
                            className="opacity-0 group-hover:opacity-100 transition-opacity"
                        />
                        <ChatButton 
                            nodeId={id}
                            className="opacity-0 group-hover:opacity-100 transition-opacity"
                        />
                    </div>
                </div>

                <div className="flex items-center space-x-2">
                    {/* Spinner for in-progress status */}
                    {data?.status === 'in_progress' && (
                        <Loader2 className="w-3 h-3 text-blue-500 animate-spin" />
                    )}
                    
                    <span className={`px-2 py-1 text-xs rounded-full ${data?.status === 'completed'
                        ? 'bg-green-100 text-green-800'
                        : data?.status === 'in_progress'
                            ? 'bg-blue-100 text-blue-800'
                            : data?.status === 'initialized'
                                ? 'bg-yellow-100 text-yellow-800'
                                : 'bg-gray-100 text-gray-800'
                        }`}>
                        {data?.status ?? 'unknown'}
                    </span>
                    
                    

                    {/* Collapse/Expand Button */}
                    {data?.hasChildren && (
                        <button
                            onClick={handleCollapseToggle}
                            className="p-1 hover:bg-gray-100 rounded-full transition-colors"
                            title={data?.isCollapsed ? 'Expand children' : 'Collapse children'}
                        >
                            {data?.isCollapsed ? (
                                <Plus className="w-4 h-4 text-gray-600" />
                            ) : (
                                <Minus className="w-4 h-4 text-gray-600" />
                            )}
                        </button>
                    )}
                </div>
            </div>

            {/* Node ID */}
            <div className='text-[10px] text-gray-400 mb-2'>
                ID: {id}
            </div>

            {/* Collapsed indicator */}
            {data?.isCollapsed && data?.hasChildren && (
                <div className="mb-2 p-1 bg-yellow-50 border border-yellow-200 rounded text-xs text-yellow-700 text-center">
                    {data?.childrenCount ?? 0} child nodes hidden
                </div>
            )}

            {/* Target URL */}
            {data?.targetUrl && (
                <div className="mb-2 p-2 bg-gray-50 rounded text-xs">
                    <div className="flex items-center justify-between mb-1">
                        <span className="text-gray-600">Target:</span>
                        <CopyButton 
                            text={data.targetUrl} 
                            itemKey={`url-${id}`}
                        />
                    </div>
                    <div className="font-mono text-blue-600 break-all">{data.targetUrl}</div>
                </div>
            )}

            {/* Inputs - Collapsible */}
            {data?.inputs && (
                <div className="mb-2 bg-gray-50 rounded text-xs">
                    <button
                        onClick={handleInputsToggle}
                        className="w-full flex items-center justify-between p-2 hover:bg-gray-100 transition-colors"
                    >
                        <span className="text-gray-600">Inputs:</span>
                        <div className="flex items-center space-x-2">
                            {inputsExpanded && (
                                <>
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            data?.onOpenInputsModal?.({
                                                inputs: data.inputs,
                                                nodeId: id,
                                                functionName: data.functionName
                                            });
                                        }}
                                        className="p-1 hover:bg-blue-100 rounded transition-colors"
                                        title="Open in full view"
                                    >
                                        <Maximize2 className="w-3 h-3 text-blue-500" />
                                    </button>
                                    <CopyButton 
                                        text={JSON.stringify(data.inputs, null, 2)} 
                                        itemKey={`inputs-${id}`}
                                    />
                                </>
                            )}
                            <ChevronDown className={`w-4 h-4 text-gray-500 transition-transform duration-200 ${inputsExpanded ? 'rotate-0' : '-rotate-90'
                                }`} />
                        </div>
                    </button>
                    <div className={`overflow-hidden transition-all duration-200 ease-in-out ${inputsExpanded ? 'max-h-40 opacity-100' : 'max-h-0 opacity-0'
                        }`}>
                        <div className="p-2 pt-0">
                            <div className="font-mono text-blue-600 bg-white border rounded p-2 max-h-32 overflow-auto">
                                <pre>{JSON.stringify(data.inputs, null, 2)}</pre>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Results - Collapsible */}
            {data?.results && (
                <div className="mb-2 bg-gray-50 rounded text-xs">
                    <button
                        onClick={handleResultsToggle}
                        className="w-full flex items-center justify-between p-2 hover:bg-gray-100 transition-colors"
                    >
                        <span className="text-gray-600">Results:</span>
                        <div className="flex items-center space-x-2">
                            {resultsExpanded && (
                                <>
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            data?.onOpenResultsModal?.({
                                                results: data.results,
                                                nodeId: id,
                                                functionName: data.functionName
                                            });
                                        }}
                                        className="p-1 hover:bg-blue-100 rounded transition-colors"
                                        title="Open in full view"
                                    >
                                        <Maximize2 className="w-3 h-3 text-blue-500" />
                                    </button>
                                    <CopyButton 
                                        text={JSON.stringify(data.results, null, 2)} 
                                        itemKey={`results-${id}`}
                                    />
                                </>
                            )}
                            <ChevronDown className={`w-4 h-4 text-gray-500 transition-transform duration-200 ${resultsExpanded ? 'rotate-0' : '-rotate-90'
                                }`} />
                        </div>
                    </button>
                    <div className={`overflow-hidden transition-all duration-200 ease-in-out ${resultsExpanded ? 'max-h-40 opacity-100' : 'max-h-0 opacity-0'
                        }`}>
                        <div className="p-2 pt-0">
                            <div className="font-mono text-blue-600 bg-white border rounded p-2 max-h-32 overflow-auto">
                                <pre>{JSON.stringify(data.results, null, 2)}</pre>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Parameter */}
            {data?.parameter && (
                <div className="mb-2 p-2 bg-blue-50 rounded text-xs">
                    <div className="flex items-center justify-between mb-1">
                        <span className="text-gray-600">Parameter:</span>
                        <CopyButton 
                            text={data.parameter} 
                            itemKey={`param-${id}`}
                        />
                    </div>
                    <code className="bg-white px-2 py-1 rounded border block">{data.parameter}</code>
                </div>
            )}

            {/* Metrics */}
            {Array.isArray(data?.metrics) && data.metrics.map((metric, idx) => (
                <div key={idx} className="flex justify-between text-xs">
                    <span className="text-gray-600">{metric.label}:</span>
                    <span className={metric.className || 'text-gray-800'}>{metric.value}</span>
                </div>
            ))}

            {/* Test results */}
            {data?.testResults && (
                <div className="mt-2 p-2 rounded text-xs border">
                    <div className="flex items-center justify-between mb-1">
                        <span className="font-medium">Payloads Tested:</span>
                        <span>{data.testResults.totalTests ?? 0}</span>
                    </div>
                    <div className="flex items-center justify-between">
                        <span className="font-medium">Potential Vulnerabilities:</span>
                        <span className={`font-medium ${(data.testResults.vulnerableCount ?? 0) > 0
                            ? 'text-red-600'
                            : 'text-green-600'
                            }`}>
                            {data.testResults.vulnerableCount ?? 0}
                        </span>
                    </div>
                </div>
            )}

            {/* Handles */}
            {data?.hasChildren && !data?.isCollapsed && (
                <Handle
                    type="source"
                    position={Position.Right}
                    className="w-3 h-3 !bg-gray-400 !border-2 !border-white"
                />
            )}

            {data?.hasChildren && data?.isCollapsed && (
                <Handle
                    type="source"
                    position={Position.Right}
                    className="w-3 h-3 !bg-yellow-400 !border-2 !border-white"
                />
            )}
        </div>
    );
};