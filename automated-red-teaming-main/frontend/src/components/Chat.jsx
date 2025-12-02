import UserInput from "./UserInput";
import Messages from "./Messages";
import { useApiContext } from "../hooks/useApiContext.jsx";
import { ActionInput } from "./ActionInput.jsx";
import { useRef, useEffect, useState } from "react";
export default function Chat() {

    const { novncURL, messages, isStreaming, actions, showResume, resumeSession, isResuming } = useApiContext()
    const { actionRequired, resolveAction, rejectAction, actionRemainingTime } = actions
    const containerRef = useRef(null);
    const [isAtBottom, setIsAtBottom] = useState(true);

    useEffect(() => {
        const el = containerRef.current;
        if (!el) return;

        const onScroll = () => {
            const threshold = 100;
            const { scrollTop, scrollHeight, clientHeight } = el;
            const distanceFromBottom = scrollHeight - scrollTop - clientHeight;
            setIsAtBottom(distanceFromBottom < threshold);
        };

        el.addEventListener("scroll", onScroll, { passive: true });
        // run once so initial state is correct
        onScroll();
        return () => el.removeEventListener("scroll", onScroll);
    }, []);

    return (
        <div
            className={`flex flex-col h-full min-h-0 bg-neutral-50 border border-neutral-300 rounded-2xl shadow-lg 
                ${messages.length > 0 ? 'max-h-[85vh]' : ''}`}
        >

            {/* Input Section */}
            <div className={`w-full transition-all duration-500 ease-in-out bg-white ${messages.length > 0 ? 'rounded-t-2xl' : 'rounded-2xl hover:shadow-xl '}`}>
                <UserInput
                />
            </div>

            {/* Loading Bar */}
            {messages.length > 0 && (
                <div className="relative h-1 w-full overflow-hidden rounded-full bg-neutral-300">
                    {isStreaming && <div className="absolute inset-y-0 left-0 w-1/2 animate-slide-x bg-neutral-900 rounded-full" />}
                </div>
            )}

            {/* Resume Button */}
            {showResume && (
                <div className="flex items-center justify-between gap-3 px-3 py-2 bg-amber-50 border-y border-amber-200">
                  <span className="text-sm text-amber-900">
                      Manual login in progress (Playwright). Please visit{" "}
                      <a
                        href={`${novncURL}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="underline underline-offset-2 text-blue-700 hover:text-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-400 rounded"
                      >
                        this link
                      </a>{" "}
                      to access Chromium. Click <b>Resume</b> after you finish.
                </span>
                  <button
                    onClick={resumeSession}
                    disabled={isResuming}
                    className="px-3 py-1.5 rounded-lg bg-neutral-900 text-white hover:bg-neutral-800 disabled:opacity-60 hover:cursor-pointer"
                  >
                  {isResuming ? "Resuming..." : "Resume"}
                  </button>
                </div>
            )}

            {/* Messages */}
            <div className={`
                transition-all duration-500 ease-in-out overflow-y-auto min-h-0
                ${messages.length > 0 ? 'h-[80vh]  opacity-100' : 'h-0 opacity-0'}
            `}
                ref={containerRef}> {/* The auto-scroll ref must be attached to the scrollable container for it to work */}
                <Messages
                    isAtBottom={isAtBottom}
                />
            </div>
            {actionRequired && (
                <div
                    className="
                        origin-left
                        scale-x-100
                        transition-transform duration-300
                        "
                >
                    <ActionInput
                        onSubmit={(val) => resolveAction(val)}
                        onCancel={() => rejectAction()}
                        ttl={actionRemainingTime}
                    />
                </div>
            )}

        </div>
    );
}
