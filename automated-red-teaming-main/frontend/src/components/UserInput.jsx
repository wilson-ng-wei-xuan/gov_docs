import { ArrowUp, CircleX } from "lucide-react";
import { ApiContext } from "../context/ApiContext.jsx";
import { useApiContext } from "../hooks/useApiContext.jsx";
import { availableModels } from "../data/availableModels.js";

export default function UserInput() {
  const {
    target, setTarget,
    goal, setGoal,
    model, setModel,
    verifyUrl, setVerifyUrl,
    verifyStr, setVerifyStr,
    username, setUsername,
    password, setPassword,
    isStreaming, stopStreaming, sendPrompt
  } = useApiContext(ApiContext);

  const onKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendPrompt();
    }
  };

  const inputBase =
    "w-full px-3 py-2 bg-neutral-100 border border-neutral-300 rounded-3xl outline-none placeholder-neutral-400 text-[15px]";

  // label keeps natural width; no huge fixed w-XX
  const labelBase = "shrink-0 text-black";

  // pair = label + field; grows and wraps nicely
  const pair = "flex items-center gap-2 flex-1 min-w-[280px]";

  return (
    <div className="m-4 flex flex-col gap-y-4">
      {/* Row 1: Target / Goal / Model / Send */}
      <div className="flex flex-wrap items-center gap-3 w-full">
        <div className={pair}>
          <label className={labelBase}>Target:</label>
          <input
            className={inputBase}
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Enter pentest target"
            disabled={isStreaming}
            spellCheck={false}
          />
        </div>

        <div className={pair}>
          <label className={labelBase}>Goal:</label>
          <input
            className={inputBase}
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Enter pentest goal"
            disabled={isStreaming}
            spellCheck={false}
          />
        </div>

        <div className="flex items-center gap-2">
          <label className={labelBase}>Model:</label>
          <select
            className="bg-gray-300 rounded-lg p-1"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            disabled={isStreaming}
          >
            <option value="" disabled>
              Select option
            </option>
            {Object.entries(availableModels).map(([label, value], index) => (
              <option key={index} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={isStreaming ? stopStreaming : sendPrompt}
          disabled={(!target.trim() || !goal.trim() || !model.trim()) && !isStreaming}
          className="w-8 h-8 flex items-center justify-center rounded-full text-neutral-500 text-sm hover:text-black disabled:opacity-40 disabled:cursor-not-allowed hover:cursor-pointer"
          aria-label={isStreaming ? "Stop" : "Send"}
        >
          {isStreaming ? <CircleX className="size-5 text-red-600" /> : <ArrowUp className="size-5" />}
        </button>
      </div>

      {/* Row 2: Verify URL / Verify Str */}
      <div className="flex flex-wrap items-center gap-3 w-full">
        <div className={`${pair} basis-[60%]`}>
          <label className={labelBase}>Verify URL:</label>
          <input
            type="url"
            className={inputBase}
            value={verifyUrl ?? ""}
            onChange={(e) => setVerifyUrl(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Optional: expected post-login URL"
            disabled={isStreaming}
            spellCheck={false}
          />
        </div>

        <div className={`${pair} basis-[40%]`}>
          <label className={labelBase}>Verify Str:</label>
          <input
            className={inputBase}
            value={verifyStr ?? ""}
            onChange={(e) => setVerifyStr(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder='Optional: string to confirm (e.g., "Welcome", "Dashboard")'
            disabled={isStreaming}
            spellCheck={false}
          />
        </div>
      </div>

      {/* Row 3: Username / Password */}
      <div className="flex flex-wrap items-center gap-3 w-full">
        <div className={pair}>
          <label className={labelBase}>Username:</label>
          <input
            className={inputBase}
            value={username ?? ""}
            onChange={(e) => setUsername(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Optional: username"
            autoComplete="username"
            disabled={isStreaming}
            spellCheck={false}
          />
        </div>

        <div className={pair}>
          <label className={labelBase}>Password:</label>
          <input
            type="password"
            className={inputBase}
            value={password ?? ""}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Optional: password"
            autoComplete="current-password"
            disabled={isStreaming}
          />
        </div>
      </div>
    </div>
  );
}
