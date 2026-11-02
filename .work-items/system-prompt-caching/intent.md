# Selective System Prompt Caching

## Outcome and Usage

TableSage sends fixed system instructions followed by variable user inputs through LiteLLM. Cache the processed system prefix when campaign regeneration will reuse it enough to justify the initial write premium. Each request must still process its current user inputs and generate a fresh response.

The expected production user processes approximately one Session per week. Code inspection found that most prompts run once successfully per Session; retries and backchannel batches are exceptions. Production frequencies have not been measured. Weekly calls are too far apart to benefit from a one-hour cache, so global explicit caching would often increase costs.

## Agreed Scope

The user approved the following refinements after reviewing an initial proposal to cache both backchannels and campaign regeneration:

- Keep explicit caching off during ordinary Session processing.
- During **Regenerate All Outputs**, enable system-prompt caching for a prompt when at least three Sessions need that same prompt. Anthropic uses one hour by default; the approved OpenAI extension uses 30 minutes. Count work actually needed, rather than all Sessions in the Campaign: current outputs are skipped.
- Apply caching only to supported providers. Do not send Anthropic-specific controls to other providers or imply that every provider supports a one-hour TTL.
- Keep `prompt_caching.ttl` for Anthropic, defaulting to one hour, and add independent `prompt_caching.openai_ttl`, defaulting to `30m` (the only supported value for the current Chat Completions transport).
- Log cache reads and writes so actual reuse and savings can be assessed, including streamed responses.
- Allow matching cache entries to be reused across regeneration runs. Do not add application-version or per-run identifiers to force fresh entries.
- Exclude explicit backchannel caching for now. Do not lengthen the prompt merely to qualify for caching.

The feature should remain simple. The user subsequently authorized implementation of both the initial policy and the extension below.

### Approved OpenAI and Gemini Extension

The user subsequently approved the researched extension and explicitly requested implementation on 2026-10-29:

- Direct OpenAI GPT-5.6+ calls use explicit-only caching. Eligible regeneration calls place a breakpoint after the fixed system instructions. Ordinary calls use explicit-only mode with no breakpoints, preventing implicit writes of changing user inputs.
- Older OpenAI models retain implicit caching; model-family checks prevent unsupported controls being sent to them. No global LiteLLM settings are changed.
- Gemini retains implicit caching; verify cached-token reporting for streamed and nonstreamed responses. Do not create explicit cache objects or introduce their storage costs. Gemini explicit caching is deferred.
- Verify installed LiteLLM/SDK request translation and upgrade only if needed. Verification found the existing OpenAI `extra_body` pass-through sufficient; no dependency upgrade is necessary.

OpenAI's documented 30-minute writes cost 1.25× ordinary input and generally read at 0.1×, making the existing three-Session threshold conservative. Gemini explicit storage pricing means three uses is not a reliable break-even rule there. Provider controls are intentionally not represented by one universal TTL. References: [OpenAI Prompt Caching](https://developers.openai.com/api/docs/guides/prompt-caching), [Gemini Context Caching](https://ai.google.dev/gemini-api/docs/generate-content/caching), and [Gemini Pricing](https://ai.google.dev/gemini-api/docs/pricing).

## Why These Boundaries

Research checked on 2026-10-29 found that Anthropic requires identical cached prefixes, supports five-minute and one-hour TTLs, refreshes lifetime on hits from the request start, and offers neither indefinite retention nor manual flushing. Changed system instructions therefore cannot reuse the old full prefix; changed user inputs can reuse an unchanged system prefix. Cache reuse does not reuse an answer. See [Anthropic Prompt Caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching).

For configured Sonnet 4.5 and Haiku 4.5, a one-hour write costs 2× ordinary input pricing and reads cost 0.1×. One write plus two hits costs 2.2× the prefix's ordinary single-call cost, compared with 3× without caching. Two calls cost 2.1× with caching versus 2× without. Thus three total calls is a useful simple eligibility threshold, assuming successful reuse before expiry. This is not a guarantee of savings for every run. User-input and output costs remain additional.

The backchannel system prompt measured 2,255 characters and approximately 510 tokens with LiteLLM's local token counter. Haiku 4.5 requires a 4,096-token cached prefix. Marking this short system prompt would silently skip caching. These estimates do not establish exact provider token counts, but the gap is substantial. See the same provider documentation for minimum lengths and pricing.

## Existing Code and Constraints

- [Shared tools client](../../packages/tablesage-tools/src/tablesage_tools/llm/client.py) constructs separate system and user messages and calls `litellm.acompletion`; the lockfile inspected uses LiteLLM 1.99.0. [LiteLLM Prompt Caching](https://docs.litellm.ai/docs/completion/prompt_caching) documents system content-block annotations and normalized cache usage.
- [Application prompt helper](../../packages/tablesage-application/src/tablesage_application/llm/llm_helper.py) renders fixed system prompts and variable user templates before invoking the transport.
- [Campaign Detail](../../apps/tablesage-tui/src/tablesage_tui/screens/campaign_detail.py) currently processes eligible reviewed audio Sessions sequentially through `generate_outputs`. Regenerate All Outputs is stale-aware, rather than an unconditional rebuild.
- [Backchannel classification](../../packages/tablesage-application/src/tablesage_application/session_pipeline/remove_backchannels.py) batches candidates; batching alone does not overcome the system-prefix size limit.
- TTL must originate in deployed TUI settings, with a packaged default in [settings.yaml](../../apps/tablesage-tui/src/tablesage_tui/resources/settings.yaml) and validation in [AppSettings](../../packages/tablesage-model/src/tablesage_model/settings/app_settings.py). Pass plain values into `tablesage-tools`; do not make that package depend on application settings.

## Observable Behavior and Remaining Design Work

An ordinary processing request must not opt into explicit cache reads or writes under this feature. Regeneration must apply the policy only to qualifying repeated prompts, leave variable user inputs outside the cache breakpoint, and restore ordinary behavior after completion, failure, or cancellation. A matching entry from an earlier run may be reused; a changed prompt must be sent intact. Usage logging must distinguish an actual hit or write from merely requesting caching.

Implementation uses the existing generation plans, which propagate stale dependencies, and counts distinct Sessions by exact system text and model. Direct Anthropic and modern OpenAI calls support explicit system-prefix caching; Gemini and older OpenAI calls retain implicit caching. Providers enforce minimum prefix sizes. Repeated uses may be separated by other generation work; the interval between uses of each prefix must fit the TTL for savings to materialize. Provider controls were rechecked during implementation on 2026-10-29. See [progress](progress.md) for verification and limitations.

The user approved this intent and explicitly requested implementation. The completed [plan](plan.md) records that work. No rubric or numerical quality evaluation was produced; verification used direct offline checks and existing tests, lint and type checks, without creating or expanding unit tests.
