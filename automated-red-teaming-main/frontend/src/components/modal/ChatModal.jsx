import React, { useState, useEffect } from 'react';
import { Modal } from './Modal';
import { Copy, Check, Search } from 'lucide-react';
import { useApiContext } from '../../hooks/useApiContext';
import MessageBubble from '../MessageBubble';       

export const ChatModal = ({ isOpen, onClose, node }) => {
    function filterMessagesByNodeId(messages, nodeId) {
        return messages.filter(message => message.metadata?.node_id === nodeId);
    }
    
    const { messages } = useApiContext();
    let filteredMessages = filterMessagesByNodeId(messages, node?.nodeId);

    return (
        <Modal isOpen={isOpen} onClose={onClose} title={`Logs for ${node?.functionName}`} size="xl">
            <div className="w-full mx-auto space-y-4">
                    {filteredMessages.map((m, i) => (
                        <MessageBubble 
                            key={i} 
                            role={m.role} 
                            text={m.text} 
                            isError={m.isError ?? false} 
                            metadata={m.metadata}
                            status={m.status}
                        />
                    ))}
                </div>
        </Modal>
    );
};