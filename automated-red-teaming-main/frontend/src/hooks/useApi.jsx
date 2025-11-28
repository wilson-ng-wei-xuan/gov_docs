import { useState, useRef, useEffect } from "react";
import { useActionFlow } from "../hooks/useActionFlow.jsx";

const POLL_MS = 5000;

export default function useAPI({ target, goal, model, verifyUrl, verifyStr, username, password }) {

    const [messages, setMessages] = useState([]);
    const [data, setData] = useState({});
    const [isStreaming, setIsStreaming] = useState(false);
    const [sessionId, setSessionId] = useState(null);
    const [showResume, setShowResume] = useState(false);
    const [isResuming, setIsResuming] = useState(false);
    const [novncURL, setNovncURL] = useState(false);

    const local_env = import.meta.env.VITE_ENV === "local";
    let backend = "api"; // assume to run on cloud
    if (local_env) {
        backend = "http://127.0.0.1:8000";
    }

    console.log(backend)
    
    const resumeSession = async () => {
        if (!sessionId) return;
        setIsResuming(true);
        try {
            const res = await fetch(`${backend}/sessions/${sessionId}/resume`, {
             method: "GET",
             headers: { "Content-Type": "application/json" },
           });
           if (!res.ok) throw new Error("Resume failed");
        } catch (e) {
            console.error(e);
        } finally {
            setIsResuming(false);
        }
    };

    const {
        actionRequired,
        pendingAction,
        actionRemainingTime,
        sendAction,
        resolveAction,
        rejectAction,
    } = useActionFlow();

    const streamRef = useRef(null); // ref for /stream event  
    const pollRef = useRef(null); // ref for /state polling interval

    // Immediately fetch once, then poll on an interval
    async function fetchState(sid) {
        try {
            const res = await fetch(`http://localhost:8000/sessions/${sid}/state`, {
                method: "GET",
                headers: { "Content-Type": "application/json" },
            });
            if (!res.ok) throw new Error("Failed to fetch session state");
            const json = await res.json();
            setData(json);
        } catch (err) {
            console.warn("State poll error:", err);
        }
    };

    const startPollingState = (sid) => {
        // Clear any old poller before starting a new one
        if (pollRef.current) {
            clearInterval(pollRef.current);
            pollRef.current = null;
        }

        // Fetch global state once before starting to poll
        fetchState(sid);
        pollRef.current = setInterval(() => fetchState(sid), POLL_MS);
    };

    const stopPollingState = () => {
        if (pollRef.current) {
            clearInterval(pollRef.current);
            pollRef.current = null;
        }
    };

    const sendPrompt = async () => {
        const trimmedTarget = target.trim();
        const trimmedGoal = goal.trim();
        const trimmedModel = model.trim();
        const trimmedVerifyUrl = verifyUrl.trim() || undefined;
        const trimmedVerifyStr = verifyStr.trim() || undefined;
        const trimmedUsername = username.trim() || undefined;
        const trimmedPassword = password.trim() || undefined;

        if (!trimmedTarget || !trimmedGoal || !trimmedModel) {
            alert("Pentest target, goal or model cannot be empty!");
            return;
        }
        if (isStreaming) return;

        const payload = {
            target: trimmedTarget,
            goal: trimmedGoal,
            model: trimmedModel,
            ...(trimmedVerifyUrl && { verify_url: trimmedVerifyUrl }),
            ...(trimmedVerifyStr && { verify_str: trimmedVerifyStr }),
            ...(trimmedUsername && { username: trimmedUsername }),
            ...(trimmedPassword && { password: trimmedPassword }),
          };

        console.log({ ...payload, password: payload.password ? "***" : undefined });

        /* NOTE: Uncomment below to allow frontend target validation (1/2 comments)*/
        // const error = validateTargetFrontend(target);
        // if (error) {
        //     alert(error);
        //     return;
        // }

        const text = (
            <p>
                Target: {trimmedTarget}
                <br />
                Goal: {trimmedGoal}
            </p>
        );

        // setMessages((prev) => [...prev, { role: "user", text }]);
        setMessages([{ role: "user", text }]);
        setData({}); // reset any previous run’s state

        try {
            // Creates session
            const res = await fetch(`${backend}/sessions`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });


            if (!res.ok) throw new Error("Failed to create session. Error: " + res.statusText);
            const data = await res.json();
            const sid = data.session_id;
            setSessionId(sid);

            // Executes session for provided session_id
            const runRes = await fetch(`${backend}/sessions/${sid}/run`, {
                method: "POST",
            });
            if (!runRes.ok) throw new Error("Failed to start run");

            streamSink(sid);
        } catch (err) {
            console.error("Failed to send prompt:", err);
            setMessages((prev) => [
                ...prev,
                { role: "system", text: "Error: " + err.message },
            ]);
        }
    };

    const streamSink = (sid) => {
        // Close any previous stream
        if (streamRef.current) {
            try {
                streamRef.current.close();
            } catch { }
            streamRef.current = null;
        }

        const es = new EventSource(`${backend}/sessions/${sid}/stream`);
        streamRef.current = es;
        setIsStreaming(true);
        setShowResume(false);

        // Start polling /state as soon as streaming begins
        startPollingState(sid);

        es.onmessage = async (event) => {
            try {
                const { type, data, metadata } = JSON.parse(event.data);

                if (type === "RunResponseContent") {
                    setMessages((prev) => {
                        const last = prev[prev.length - 1];
                        if (last?.role === "assistant") {
                            return [
                                ...prev.slice(0, -1),
                                { ...last, text: last.text + data, metadata: { ...last.metadata, ...metadata }},
                            ];
                        }
                        return [...prev, { role: "assistant", text: data, metadata }];
                    });

                } else if (type === "ToolCallStarted") {

                    if (metadata?.novnc_url) {
                        setNovncURL(metadata.novnc_url)
                        console.log(novncURL)
                    }

                    if (metadata?.tool_name === "Playwright.alogin_manual") {
                        setShowResume(true);
                    }


                    setMessages((prev) => [
                        ...prev,
                        { 
                            role: "tool", 
                            text: data, 
                            status: "running",
                            toolId: metadata?.tool_id,
                            metadata 
                        },
                    ]);

                } else if (type === "DiagnosticStart") {
                    setMessages((prev) => [
                        ...prev,
                        { 
                            role: "diagnostic", 
                            text: data, 
                            status: "running",
                            metadata 
                        },
                    ]);
                } else if (type === "ToolCallCompleted") {

                    if (metadata?.tool_name === "Playwright.alogin_manual") {
                        setShowResume(false);
                    }

                    // Update the existing tool call message to "completed" status
                    setMessages((prev) => {
                        const newMessages = [...prev];
                        // Find the most recent tool message with "running" status
                        for (let i = newMessages.length - 1; i >= 0; i--) {
                            if (newMessages[i].role === "tool" && newMessages[i].status === "running") {
                                newMessages[i] = {
                                    ...newMessages[i],
                                    status: metadata?.tool_call_error ? "failed" : "completed",
                                    completionText: data,
                                    metadata: { ...newMessages[i].metadata, ...metadata },
                                };
                                break;
                            }
                        }
                        return newMessages;
                    });

                } else if (type === "DiagnosticComplete") {
                    // Update the existing tool call message to "completed" status
                    setMessages((prev) => {
                        const newMessages = [...prev];
                        // Find the most recent tool message with "running" status
                        for (let i = newMessages.length - 1; i >= 0; i--) {
                            if (newMessages[i].role === "diagnostic" && newMessages[i].status === "running") {
                                newMessages[i] = {
                                    ...newMessages[i],
                                    status: metadata?.error ? "failed" : "completed",
                                    completionText: data,
                                    metadata: { ...newMessages[i].metadata, ...metadata },
                                };
                                break;
                            }
                        }
                        return newMessages;
                    });

                }else if (type === "ToolCallFailed" || type === "Error") {
                    // Update the existing tool call message to "failed" status or create new error message
                    setMessages((prev) => {
                        const newMessages = [...prev];
                        // Try to find a running tool call to update
                        let foundRunning = false;
                        for (let i = newMessages.length - 1; i >= 0; i--) {
                            if (newMessages[i].role === "tool" && newMessages[i].status === "running") {
                                newMessages[i] = {
                                    ...newMessages[i],
                                    status: "failed",
                                    completionText: data,
                                    metadata: { ...newMessages[i].metadata, ...metadata },
                                };
                                foundRunning = true;
                                break;
                            }
                        }
                        // If no running tool call found, create a new error message
                        if (!foundRunning) {
                            newMessages.push({
                                role: "system",
                                text: data,
                                isError: true,
                                metadata,
                            });
                        }
                        return newMessages;
                    });

                // } else if (type === "DiagnosticStart" || type === "DiagnosticComplete") {
                //     setMessages((prev) => [
                //         ...prev,
                //         { role: "diagnostic", text: data, isError: type === "Error", metadata },
                //     ]);

                } else if (type === "UserInput") {
                    const { action_id: actionId, TTL: ttl } = metadata;

                    setMessages((prev) => [
                        ...prev,
                        { role: "assistant", text: data, isError: type === "Error", metadata, type },
                    ]);

                    const { userResponse } = await sendAction(actionId, data, ttl);

                    setMessages((prev) => [
                        ...prev,
                        { role: "user", text: userResponse },
                    ]);

                    const payload = {
                        session_id: sid,
                        action_id: actionId,
                        message: userResponse,
                    }
                    try {
                        const actionRes = await fetch(`${backend}/actions`, {
                            headers: { "Content-Type": "application/json" },
                            method: "POST",
                            body: JSON.stringify(payload),
                        });
                        if (!actionRes.ok) throw new Error("Failed to submit action");
                    } catch (e) {
                        console.log(e);
                    }


                } else {
                    setMessages((prev) => [
                        ...prev,
                        { role: "system", text: data, isError: type === "Error", metadata },
                    ]);

                    if (type === "RunComplete") {
                        setIsStreaming(false);
                        setShowResume(false);

                        // final state poll
                        (async () => {
                            try {
                                const res = await fetch(`${backend}/sessions/${sid}/state`, {
                                    method: "GET",
                                    headers: { "Content-Type": "application/json" },
                                });
                                if (res.ok) {
                                    const json = await res.json();
                                    setData(json);
                                }
                            } catch (err) {
                                console.warn("Final state fetch failed:", err);
                            }
                        })();

                        stopPollingState();
                        streamRef.current?.close();
                        streamRef.current = null;
                    }
                }
            } catch (err) {
                console.error("Malformed SSE data:", event.data, err);
            }
        };

        es.onerror = () => {
            setMessages((prev) => [
                ...prev,
                { role: "system", text: "Connection error! Ending stream" },
            ]);
            setIsStreaming(false);
            setShowResume(false);
            stopPollingState();
            es.close();
            streamRef.current = null;
        };
    };

    const stopStreaming = async () => {
        if (!sessionId) return;

        try {
            await fetch(`${backend}/sessions/${sessionId}/stop`, {
                method: "POST",
            });
        } catch (e) {
            console.warn("Stop request failed:", e);
        }

        if (streamRef.current) {
            streamRef.current.close();
            streamRef.current = null;
        }

        stopPollingState();
        setIsStreaming(false);
        setShowResume(false);
        setMessages((prev) => [...prev, { role: "system", text: "Job cancelled!", isError: true }]);
    };

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            try {
                streamRef.current?.close();
            } catch (e) {
                // Silent catch
            }
            stopPollingState();
        };
    }, []);

    return {
        messages,
        data,
        isStreaming,
        sendPrompt,
        stopStreaming,
        fetchState: (sid) => fetchState(sid),
        showResume,
        isResuming,
        novncURL,
        resumeSession,
        actions: {
            actionRequired,
            pendingAction,
            actionRemainingTime,
            sendAction,
            resolveAction,
            rejectAction,
        }
    };
}

// Helper funcs
/* NOTE: Currently unused. Uncomment to allow frontend validation of target (2/2 comments) */
function validateTargetFrontend(url) {
    const trimmed = url.trim();

    if (!trimmed) {
        return "Target cannot be empty";
    }

    let parsed;
    try {
        parsed = new URL(trimmed); // built-in browser URL parser
    } catch {
        return "Invalid URL format";
    }

    // 1. Check scheme
    if (!["http:", "https:"].includes(parsed.protocol)) {
        return "URL must start with http:// or https://";
    }

    // 2. Check for host
    if (!parsed.hostname) {
        return "Invalid URL host";
    }

    // 3. Reject URLs with query string
    if (parsed.search) {
        return "URL contains query component";
    }

    // 4. Check if host is an IP
    const isIP = /^(\d{1,3}\.){3}\d{1,3}$/.test(parsed.hostname);
    if (isIP) {
        const parts = parsed.hostname.split(".").map(Number);
        for (const part of parts) {
            if (part < 0 || part > 255) {
                return "Invalid IPv4 address";
            }
        }
        return null; // valid IPv4
    }

    // 5. Domain regex check
    const DOMAIN_REGEX = /^([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,63}$/;
    if (!DOMAIN_REGEX.test(parsed.hostname)) {
        return "Host is malformed";
    }

    return null; // valid URL
}