import React, { useState, useEffect } from 'react';
import { Modal } from './Modal';
import { Copy, Check, Search } from 'lucide-react';

export const DataModal = ({ isOpen, onClose, data, nodeId, functionName, type = 'Data' }) => {
    const [copiedItems, setCopiedItems] = useState(new Set());
    const [searchTerm, setSearchTerm] = useState('');

    // Reset search term when modal opens/closes
    useEffect(() => {
        if (!isOpen) {
            setSearchTerm('');
        }
    }, [isOpen]);

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
                onClick={() => copyToClipboard(text, itemKey)}
                className={`p-2 hover:bg-gray-100 rounded transition-colors ${className}`}
                title={isCopied ? "Copied!" : "Copy to clipboard"}
            >
                {isCopied ? (
                    <Check className="w-4 h-4 text-green-500" />
                ) : (
                    <Copy className="w-4 h-4 text-gray-500 hover:text-gray-700" />
                )}
            </button>
        );
    };

    // Highlight search terms in JSON
    const highlightJSON = (jsonString) => {
        if (!jsonString || !searchTerm) return jsonString || '';
        
        const regex = new RegExp(`(${searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
        return jsonString.split(regex).map((part, index) =>
            regex.test(part) ? (
                <mark key={index} className="bg-yellow-200">{part}</mark>
            ) : part
        );
    };

    const title = `${type} - ${functionName || 'Node'}`;
    const jsonString = data ? JSON.stringify(data, null, 2) : '';
    const placeholder = `Search ${type.toLowerCase()}...`;

    return (
        <Modal isOpen={isOpen} onClose={onClose} title={title} size="xl">
            <div className="space-y-2">
                {/* Header */}
                <div className="flex items-center justify-between pb-2 border-b ">
                    <div className="text-xs text-gray-500 ">
                        Node ID: {nodeId} 
                    </div>
                    <div className='flex gap-x-2'>
                        <div className="relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                        <input
                        type="text"
                        placeholder={placeholder}
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                        />
                    </div>
                    <CopyButton 
                            text={jsonString} 
                            itemKey={`all-${type.toLowerCase()}-${nodeId}`} 
                            className="bg-blue-100 hover:bg-blue-200"
                        />
                    </div>
                </div>
 

                {/* Content */}
                <div className="bg-gray-50 rounded-lg p-2">
                    <pre className="text-sm font-mono whitespace-pre-wrap overflow-auto max-h-[60vh]">
                        {jsonString ? highlightJSON(jsonString) : 'No data available'}
                    </pre>
                </div>
            </div>
        </Modal>
    );
};