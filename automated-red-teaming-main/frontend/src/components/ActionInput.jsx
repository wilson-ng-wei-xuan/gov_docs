import { useState, useEffect } from "react";
import { Play } from "lucide-react";

export function ActionInput({ onSubmit, ttl }) {
    const [value, setValue] = useState("");
    const [timeLeft, setTimeLeft] = useState(ttl);

    useEffect(() => {
        if (!ttl || ttl <= 0) return;

        setTimeLeft(ttl);

        const interval = setInterval(() => {
            setTimeLeft((prev) => {
                const newTime = prev - 100; // Update every 100ms for smooth animation
                return newTime <= 0 ? 0 : newTime;
            });
        }, 100);

        return () => clearInterval(interval);
    }, [ttl]);

    const onKeyDown = (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            onSubmit(value);
        }
    };

    // Calculate progress percentage (1 = full circle, 0 = empty)
    const progress = ttl > 0 ? timeLeft / ttl : 0;

    // SVG circle parameters
    const radius = 16;
    const circumference = 2 * Math.PI * radius;
    const strokeDashoffset = circumference * (1 - progress);

    return (
        <div className="flex items-center max-h-64 m-3 bg-neutral-100 border border-neutral-300 rounded-3xl overflow-hidden">
            <textarea
                className="flex-1 resize-none p-4 text-sm placeholder-neutral-400 focus:outline-none bg-transparent"
                placeholder="User response required"
                value={value}
                onKeyDown={onKeyDown}
                onChange={(e) => setValue(e.target.value)}
            />
            <div className="relative mr-3 flex items-center justify-center w-10 h-10">
                {/* Circular progress indicator */}
                {ttl > 0 && (
                    <svg
                        className="absolute inset-0 w-full h-full -rotate-90"
                        width="40"
                        height="40"
                        viewBox="0 0 40 40"
                    >
                        {/* Background circle */}
                        <circle
                            cx="20"
                            cy="20"
                            r={radius}
                            stroke="rgb(212 212 212)" // neutral-300
                            strokeWidth="2"
                            fill="none"
                            opacity="0.3"
                        />
                        {/* Progress circle */}
                        <circle
                            cx="20"
                            cy="20"
                            r={radius}
                            stroke={progress > 0.2 ? "rgb(34 197 94)" : "rgb(239 68 68)"} // green-500 or red-500
                            strokeWidth="2"
                            fill="none"
                            strokeDasharray={circumference}
                            strokeDashoffset={strokeDashoffset}
                            strokeLinecap="round"
                            className="transition-all duration-100 ease-linear"
                        />
                    </svg>
                )}

                {/* Submit button - now perfectly centered */}
                <button
                    type="button"
                    className="relative z-10 flex items-center justify-center w-8 h-8 rounded-full hover:bg-neutral-200 transition-colors"
                    aria-label="Submit"
                    onClick={() => onSubmit(value)}
                >
                    <Play size={18} />
                </button>
            </div>
        </div>
    );
}