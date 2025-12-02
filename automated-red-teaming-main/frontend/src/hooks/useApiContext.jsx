import { useContext } from "react";
import { ApiContext } from "../context/ApiContext";

export function useApiContext() {
    const context = useContext(ApiContext);
    if (!context) throw new Error("useApiContext must be used within ApiContextProvider");
    return context;
}
