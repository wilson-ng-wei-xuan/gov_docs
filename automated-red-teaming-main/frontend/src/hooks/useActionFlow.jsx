import { useRef, useState } from "react";

export function useActionFlow() {
    const [actionRequired, setActionRequired] = useState(false);
    const [pendingAction, setPendingAction] = useState(null);
    const actionDeferredRef = useRef(null);
    const timeoutRef = useRef(null);
    const [actionRemainingTime, setActionRemainingTime] = useState(null);

    const clearAction = () => {
        setActionRequired(false);
        setPendingAction(null);
        actionDeferredRef.current = null;
        if (timeoutRef.current) {
            clearTimeout(timeoutRef.current);
            timeoutRef.current = null;
        }
    };

    const sendAction = (actionId, prompt, ttl) => {
        const ttlMs = ttl * 1000

        return new Promise((resolve, reject) => {
            setPendingAction({ actionId, prompt });
            setActionRequired(true);
            actionDeferredRef.current = { resolve, reject };

            // set timeout if ttl is provided
            if (ttlMs) {
                setActionRemainingTime(ttlMs);
                timeoutRef.current = setTimeout(() => {
                    reject(new Error("Action timed out"));
                    clearAction();
                    setActionRemainingTime(null);
                }, ttlMs);
            }
        });
    };
    const resolveAction = (userResponse) => {
        actionDeferredRef.current?.resolve({ userResponse });
        clearAction();
    };

    const rejectAction = (reason) => {
        actionDeferredRef.current?.reject(reason || new Error("Action cancelled"));
        clearAction();
    };

    return {
        actionRequired,
        pendingAction,
        actionRemainingTime,
        sendAction,
        resolveAction,
        rejectAction,
    };
}
