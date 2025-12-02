import { useRef, useEffect } from "react";
import MessageBubble from "./MessageBubble";
import { useApiContext } from "../hooks/useApiContext.jsx";

export default function Messages({ isAtBottom }) {

    const { messages } = useApiContext()
    const listEndRef = useRef(null);

    useEffect(() => {
        if (!isAtBottom) return;
        listEndRef.current?.scrollIntoView({
            behavior: "smooth",
            block: "end",
        });
    }, [messages, isAtBottom]);

    return <div className="w-full mx-auto px-4 py-6 space-y-4">
        {messages.map((m, i) => (
            <MessageBubble 
                key={i} 
                role={m.role} 
                text={m.text} 
                isError={m.isError ?? false} 
                metadata={m.metadata}
                status={m.status}
            />
        ))}
        <div ref={listEndRef} className="h-1" />
    </div>
}