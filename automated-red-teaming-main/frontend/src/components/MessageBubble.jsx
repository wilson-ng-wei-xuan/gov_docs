import { useId, useMemo, useState } from "react";
import { Loader2, Check, X, ChevronRight } from "lucide-react";
import MarkdownRenderer from "./MarkdownRenderer";

function isEmptyMetadata(data) {
    if (data == null) return true;
    if (Array.isArray(data)) return data.length === 0;
    if (typeof data === "object") return Object.keys(data).length === 0;
    // primitives exist -> treat as non-empty to allow visibility
    return false;
}

function stringifyMetadata(data) {
    try {
        if (typeof data === "string") return data;
        return JSON.stringify(data, null, 2);
    } catch {
        return String(data);
    }
}

function formatInputs(inputs) {
    if (!inputs || typeof inputs !== 'object') return null;
    
    return Object.entries(inputs).map(([key, value]) => (
        <div key={key} className="mb-1">
            <span className="font-medium text-neutral-900 text-xs">{key}:</span>{' '}
            <span className="text-neutral-700 text-xs">
                {typeof value === 'string' ? value : JSON.stringify(value)}
            </span>
        </div>
    ));
}

function CollapsibleSection({ title, children, defaultOpen = false }) {
    const [isOpen, setIsOpen] = useState(defaultOpen);
    const sectionId = useId();
    
    return (
        <div className="border-b border-neutral-200 last:border-b-0">
            <button
                type="button"
                onClick={() => setIsOpen(!isOpen)}
                className="w-full flex items-center justify-between py-2 text-left text-xs"
                aria-expanded={isOpen}
                aria-controls={sectionId}
            >
                <span className="font-medium text-neutral-800">{title}</span>
                <ChevronRight className={`h-3 w-3 transition-transform duration-300 ${isOpen ? 'rotate-90' : ''}`} />
            </button>
            {isOpen && (
                <div id={sectionId} className="pb-2">
                    {children}
                </div>
            )}
        </div>
    );
}

function FunctionBubble({ text, metadata, status, isDiagnostic }) {
    const [open, setOpen] = useState(false);
    const panelId = useId();

    // Support both tool and diagnostic naming conventions
    const name = isDiagnostic ? metadata?.diagnostic_name : metadata?.tool_name;
    const inputKey = isDiagnostic ? "inputs" : "tool_args";
    const outputKey = isDiagnostic ? "final_output" : "tool_output";

    // Determine what to show based on status
    const displayText = useMemo(() => {
        if (status === "running") {
            return (
                <div className="flex items-center justify-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin text-neutral-400" />
                    <span>Running {name} {isDiagnostic ? "" : "tool"}</span>
                </div>
            );
        } else if (status === "completed") {
            return (
                <div className="flex items-center justify-center gap-2">
                    <Check className="h-4 w-4 text-green-600" />
                    <span>Completed {name} {isDiagnostic ? "" : "tool"}</span>
                </div>
            );
        } else if (status === "failed") {
            return (
                <div className="flex items-center justify-center gap-2">
                    <X className="h-4 w-4 text-red-500" />
                    <span>Failed {name} {isDiagnostic ? "" : "tool"}</span>
                </div>
            );
        }
        return <span>{name}</span>; 
    }, [name, status, isDiagnostic]);

    const hasMetadata = metadata !== null && (metadata?.[inputKey] || metadata?.[outputKey]);

    const structuredContent = useMemo(() => {
        if (!metadata) return null;

        const relevantMetadata = { ...metadata };

        // Remove unwanted fields
        delete relevantMetadata.session_id;
        delete relevantMetadata.node_id;
        delete relevantMetadata.run_id;
        delete relevantMetadata.tool_name;
        delete relevantMetadata.diagnostic_name;
        delete relevantMetadata.status;

        const inputs = relevantMetadata[inputKey];
        const output = relevantMetadata[outputKey];
        delete relevantMetadata[inputKey];
        delete relevantMetadata[outputKey];

        return (
            <div className="space-y-0">
                {inputs && (
                    <CollapsibleSection title="Inputs">
                        <pre className="text-xs font-mono whitespace-pre-wrap break-words text-neutral-800 bg-neutral-50 p-2 rounded border overflow-auto max-h-60">
                            {formatInputs(inputs)}
                        </pre>
                    </CollapsibleSection>
                )}

                {output && (
                    <CollapsibleSection title="Output">
                        <pre className="text-xs font-mono whitespace-pre-wrap break-words text-neutral-800 bg-neutral-50 p-2 rounded border overflow-auto max-h-60">
                            {stringifyMetadata(output)}
                        </pre>
                    </CollapsibleSection>
                )}

                {Object.keys(relevantMetadata).length > 0 && (
                    <CollapsibleSection title="Additional Metadata">
                        <pre className="text-xs font-mono whitespace-pre-wrap break-words text-neutral-800 bg-neutral-50 p-2 rounded border overflow-auto max-h-60">
                            {stringifyMetadata(relevantMetadata)}
                        </pre>
                    </CollapsibleSection>
                )}
            </div>
        );
    }, [metadata, inputKey, outputKey]);

    return (
        <div className="w-full flex flex-col items-center">
            {/* Tool/Diagnostic call bubble (centered) */}
            <div className="relative w-[50%]">
                <div className={`px-4 py-2 text-xs font-mono whitespace-pre-wrap bg-neutral-300 text-neutral-700 ${hasMetadata && open ? 'rounded-t-xl' : 'rounded-xl'}`}>
                    {/* clickable link if backend sent one */}
                      {hasMetadata && metadata?.novnc_url && (
                        <a
                          href={metadata.novnc_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-2 px-3 py-1 rounded-lg bg-blue-50 text-blue-700 hover:bg-blue-100 underline"
                        >
                          Open noVNC
                          <svg width="14" height="14" viewBox="0 0 24 24" aria-hidden>
                            <path d="M14 3h7v7h-2V6.41l-9.29 9.3-1.42-1.42 9.3-9.29H14V3z"></path>
                            <path d="M5 5h5V3H3v7h2V5z"></path>
                          </svg>
                        </a>
                      )}
                    <div className="break-words text-center">
                        {displayText}
                    </div>
                </div>

                {/* Icon-only toggle button at the right end of the bubble */}
                {hasMetadata && (
                    <button
                        type="button"
                        aria-expanded={open}
                        aria-controls={panelId}
                        aria-label="Toggle metadata"
                        onClick={() => setOpen(v => !v)}
                        className="absolute top-4 -translate-y-1/2 right-[-24px] inline-flex items-center justify-center "
                    >
                        <ChevronRight
                            className={`h-3.5 w-3.5 transition-transform duration-300 ${open ? "rotate-90" : ""}`}
                            aria-hidden="true"
                        />
                    </button>
                )}
                {/* Expandable metadata section - attached to main bubble */}
                {hasMetadata && open && (
                    <div
                        id={panelId}
                        className={`bg-neutral-200 text-neutral-700 rounded-b-xl border-t border-neutral-400 px-4 py-2`}
                    >
                        {structuredContent}
                    </div>
                )}
            </div>
        </div>
    );
}

export default function MessageBubble({
    role,
    text,
    isError,
    metadata,
    status,
}) {
    const isUser = role === "user";
    const isSystem = role === "system";
    const isTool = role === "tool" ;
    const isDiagnostic = role === "diagnostic";
    

    if (isSystem) {
        return (
            <div className="flex flex-col items-center justify-center">
                <div
                    className={`${isError ? "bg-red-700 text-white" : "bg-neutral-300 text-neutral-700"
                        } w-[50%] text-xs font-mono whitespace-pre-wrap px-4 py-2 rounded-xl text-center break-all`}
                >
                    {text}
                </div>
            </div>
        );
    }

    if (isTool || isDiagnostic) {
        // Centered tool call with right-end toggle and below-bubble metadata
        return <FunctionBubble 
            text={text} 
            metadata={metadata}
            status={status}
            isDiagnostic={isDiagnostic}
        />;
    }

    // user/assistant messages
    return (
        <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
            <div
                className={`max-w-[60%] px-4 py-2 rounded-2xl shadow-sm text-[15px] leading-6 ${isUser
                    ? "bg-neutral-900 text-white rounded-br-md"
                    : "bg-white border border-neutral-200 text-neutral-900 rounded-bl-md"
                    }`}
            >
                <div className="break-words">
                    {isUser ? text : <MarkdownRenderer text={text} />}
                </div>
            </div>
        </div>
    );
}
