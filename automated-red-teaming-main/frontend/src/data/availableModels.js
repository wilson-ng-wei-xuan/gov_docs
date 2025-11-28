export const availableModels = {
  "Claude 3.7 Sonnet":
    import.meta.env.VITE_CLAUDE_3_7_SONNET || "litellm_proxy/apac.anthropic.claude-3-7-sonnet-20250219-v1:0",
  "Claude 4 Sonnet":
    import.meta.env.VITE_CLAUDE_4_SONNET || "litellm_proxy/csg.anthropic.claude-sonnet-4-20250514-v1:0",
  "GPT-5": import.meta.env.VITE_GPT_5 || "litellm_proxy/azure/gpt-5-eastus2",
  "Gemini-2.5-Pro": import.meta.env.VITE_GEMINI_2_5_PRO || "litellm_proxy/gemini-2.5-pro",
  "GPT-4o-mini": import.meta.env.VITE_GPT_4O_MINI || "litellm_proxy/azure/gpt-4o-mini",
};
