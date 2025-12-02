import { createContext, useState } from "react";
import useAPI from "../hooks/useApi";

export const ApiContext = createContext();

export function ApiContextProvider({ children }) {
  // existing
  const [target, setTarget] = useState("");
  const [goal, setGoal] = useState("");
  const [model, setModel] = useState("");

  // NEW fields
  const [verifyUrl, setVerifyUrl] = useState("");
  const [verifyStr, setVerifyStr] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const { messages, data, isStreaming, sendPrompt, stopStreaming, actions, showResume, isResuming, resumeSession, novncURL, fetchState } = useAPI({
    target,
    goal,
    model,
    verifyUrl,
    verifyStr,
    username,
    password,
  });

  return (
    <ApiContext.Provider
      value={{
        // values
        target,
        goal,
        model,
        verifyUrl,
        verifyStr,
        username,
        password,
        // setters
        setTarget,
        setGoal,
        setModel,
        fetchState,
        setVerifyUrl,
        setVerifyStr,
        setUsername,
        setPassword,
        // api surface
        messages,
        data,
        isStreaming,
        sendPrompt,
        stopStreaming,
        actions,
          showResume, isResuming, resumeSession, novncURL
      }}
    >
      {children}
    </ApiContext.Provider>
  );
}
