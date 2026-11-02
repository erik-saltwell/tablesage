---
name: "System prompt caching"
status: complete
---

# System Prompt Caching

Reduce repeated system-prompt processing costs during campaign-wide output regeneration without adding cache-write costs to ordinary Session processing.

The agreed [intent](intent.md) enables explicit system-prefix caching when at least three Sessions need the same prompt and model during Regenerate All Outputs: Anthropic defaults to one hour, and OpenAI GPT-5.6+ to 30 minutes. Ordinary modern OpenAI calls use explicit-only mode without breakpoints. Gemini and older OpenAI models retain implicit caching. Backchannel caching and explicit Gemini cache objects are excluded.

Implemented and extended on 2026-10-29; see the completed [plan](plan.md) and [verification record](progress.md). All 63 existing targeted tests, Ruff checks and type checks passed. Native OpenAI/Gemini HTTP request and JSON/SSE conversion were verified offline with the installed LiteLLM/SDK; no dependency upgrade was needed. Provider minimum prefix sizes still apply. Live provider hits and billing savings were not measured. No quality rubric or numerical evaluation was defined; the user explicitly requested implementation.
