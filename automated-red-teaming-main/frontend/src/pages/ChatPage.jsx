import Chat from "../components/Chat";
import { Workflow, MessageCircle } from "lucide-react";
import { useState } from 'react';
import { Dashboard } from "../components/Dashboard";
import { useApiContext } from "../hooks/useApiContext.jsx";
import { VulnAnalysisTree } from "../components/tree/Tree.jsx";
export default function ChatPage() {


    const { messages, data } = useApiContext();

    const [viewChat, setViewChat] = useState(true);

    function toggleViewRaw() {
        setViewChat(!viewChat);
    }

    return (
        <div
            className={`
                flex min-h-screen overflow-hidden
                ${messages.length > 0 ? "items-start justify-center" : "items-center justify-center"}
                ${viewChat ? "mt-2" : "mt-0"}
            `}
        >
            {viewChat ?
                <div className="w-full max-w-5xl px-4">
                    <Chat />
                </div> : <VulnAnalysisTree analysisData={data} />
            }
            <Dashboard togglebutton={<button
                className='w-full flex items-center justify-center gap-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 hover:text-indigo-800 p-2 rounded-lg border border-indigo-200 text-sm font-medium transition-colors duration-200'
                onClick={toggleViewRaw}>
                {viewChat ? <Workflow className="h-4 w-4" /> : <MessageCircle className="h-4 w-4" />}
                {viewChat ? 'Workflow View' : 'Chat View'}
            </button>} />
        </div>
    );
}
