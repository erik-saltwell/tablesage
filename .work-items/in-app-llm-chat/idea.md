# In-App LLM Chat: Research and Working Direction

Research saved on 2026-10-11. This captures feasibility findings and proposals for an embedded TableSage chat; it is not an implementation plan or a finalized design.

## User Requirements

- Allow skills to be made available and used during chat. Skills describe common tasks, such as creating a Previously On recap.
- Allow Python tools and/or MCP servers to be made available during chat. Tools provide data and actions, such as retrieving a Campaign’s Glossary.
- Allow switching between TableSage’s configured High, Medium, and Low models while continuing the same conversation.
- Make exposing an additional skill straightforward after the initial integration is built.

## UI Package Candidate

[`textual-chat`](https://pypi.org/project/textual-chat/) provides an embeddable Textual widget backed by LiteLLM, with streaming, Python function tools, MCP connections, and a model selector. TableSage already depends on Textual and LiteLLM, making it a plausible fit. Textual’s own [Markdown widget](https://textual.textualize.io/widgets/markdown/) provides a lower-level rendering option if a custom chat screen proves preferable.

The published `textual-chat` 0.1.4 wheel was downloaded and inspected in memory without installing it or changing the app. Findings from the inspected implementation:

- `Chat` accepts functions and MCP server configurations through `tools`, and offers a `tool` decorator for registering Python functions.
- MCP connections use FastMCP, discover server tools, and wrap their calls for the chat tool loop.
- There is no dedicated skill discovery/catalog/loading mechanism in the inspected package; TableSage would provide that integration.
- The model selection handler creates a fresh backend conversation. Switching models while preserving history requires additional work; the built-in selector alone does not satisfy the requirement.
- MCP wrappers accept generic keyword arguments. Verify that the resulting model-facing tools preserve each server tool’s argument schema before relying on this integration.
- The widget enables automatic app introspection by default. Choose explicit TableSage tools and decide whether introspection belongs in this feature.

These are source-level findings, not proof of compatibility with TableSage’s deployed Textual version or configured models. Package adoption remains unresolved.

## Existing TableSage Plumbing

- [AppSettings](../../packages/tablesage-model/src/tablesage_model/settings/app_settings.py) already exposes `llm_model_high`, `llm_model`, and `llm_model_lite`, corresponding to High, Medium, and Low.
- The [tools LLM client](../../packages/tablesage-tools/src/tablesage_tools/llm/client.py) uses LiteLLM but constructs one system message and one user message, returning a final text response. It does not provide a chat history or agent tool loop. Its internal streaming path assembles the completed response rather than exposing incremental UI updates.
- The [application prompt helper](../../packages/tablesage-application/src/tablesage_application/llm/llm_helper.py) renders task prompts and delegates to that client. Chat needs a separate conversation/tool execution layer or an appropriate extension; reusing credentials and settings does not supply that layer automatically.
- Chat configuration must follow the project’s settings boundary: application/TUI code reads deployed settings and supplies plain values to `tablesage-tools`.

## Proposed Skills Integration

A skill supplies the process and instructions for a task; tools supply the data and actions needed to carry it out. For example, a Previously On skill could instruct the LLM to gather relevant scene logs, consult the Glossary, select events, and compose the recap. That illustrative sequence is not yet a settled recap contract.

Use the [Agent Skills integration approach](https://agentskills.io/client-implementation/adding-skills-support): discover `SKILL.md` files, disclose names and descriptions in a compact catalog, and load instructions and referenced resources when a skill is activated. A dedicated activation tool can supply instructions without giving the model general filesystem access.

The proposed explicit UI flow is:

1. Add a skill directory containing its instructions to a configured skills folder and enable it for chat.
2. Expose the skill in a picker or slash command, such as `/previously-on`.
3. Selecting the skill loads its instructions into the ongoing conversation.
4. The LLM follows those instructions using the tools available to that conversation.

The picker, slash command, enablement mechanism, and optional automatic model-driven activation are proposals. Once discovery and activation exist, adding another instruction-only skill should largely consist of adding its Markdown file. Skills that require missing tools, script execution, or special resources require those capabilities to be implemented too; instructions alone do not enable them.

For TableSage’s own operations, direct Python tools are the proposed simplest starting point. MCP is useful when connecting external services or exposing operations for reuse across apps. Whether TableSage should itself expose an MCP server is outside the settled scope.

## Rough Effort Estimates

These are preliminary engineering estimates for a usable first version, assuming folder/configuration-based skill and MCP setup. They are not measured delivery commitments, and the increments overlap.

- Basic embedded chat UI: roughly 1–3 engineering days for embedding, credentials/settings, cancellation, and error handling. Saved conversation management adds scope.
- Skills integration: roughly 2–4 additional days for discovery, catalog disclosure, activation, and referenced-file access. Arbitrary executable skills are outside this estimate.
- Python tool framework: roughly 1–2 additional days for connecting functions and showing tool activity/results. Each actual tool needs its own implementation or adapter.
- MCP integration: roughly 3–5 additional days for configuration, connection lifecycle, schema handling, and failures. Interactive authentication can increase effort.
- High/Medium/Low switching with retained history: roughly half a day to one and a half additional days for the settings-backed selector, preserving conversation and active capabilities, and handling provider options/context differences. The proposed switch takes effect on the next turn.

A rough combined range discussed was 1–2 working weeks for a first integrated version, subject to a successful package trial and limited scope. In-app installers/editors for skills and MCP configuration, extensive authentication, and arbitrary script execution expand the scope.

## Open Choices and Suggested Trial

No final choice has been made about the package, persistence, skill activation UI, configuration UI, or breadth of supported MCP servers. Conversation history must remain valid across models with different context limits and tool-message conventions; preservation of active skills and tools also needs verification.

The agent’s recommendation is a short integration trial of `textual-chat` with one real TableSage tool and history-preserving switching between the three configured tiers. Also verify MCP tool schemas and how TableSage’s existing credentials, model options, and diagnostics fit the package’s backend. The trial has not been authorized or performed by this save request.
