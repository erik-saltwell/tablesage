---
name: "Chat with an LLM in the app"
status: ideating
---

# Chat with an LLM in the App

Provide an embedded chat in TableSage that can use task skills, call application tools and MCP tools, and switch between the app’s configured High, Medium, and Low models while preserving the conversation.

See [idea.md](idea.md) for the UI package research, requirements, proposed skills integration, rough effort estimates, and unresolved choices.

## Resume Note

Research was saved on 2026-10-11. `textual-chat` is a candidate, not an adopted dependency. Its published 0.1.4 code was inspected, but no integration trial or runtime compatibility checks were performed. No quality rubric has been defined; rubric definition is the next activity under the project workflow unless the user directs proceeding to a later stage. A proposed technical trial would check history-preserving model switching and one real TableSage tool before committing to the package. Implementation has not begun.
