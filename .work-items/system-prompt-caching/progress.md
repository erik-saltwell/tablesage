# Implementation and Verification

Completed 2026-10-29.

## Initial Anthropic Implementation

- Added `PromptCachingSettings` to `AppSettings` and packaged YAML, with `ttl: 1h` by default and `5m` also accepted. Existing deployed settings load the default without being rewritten.
- Campaign Detail enters `Application.cache_regeneration_prompts` inside its existing regeneration worker. Eligibility comes from deduplicated generation-plan tasks and graph-declared system files, grouped by exact model and system text, with at least three distinct Sessions required. Deterministic producers and ordinary processing do not opt in.
- A context-local policy passes into existing `asyncio.run` calls and resets in `finally`. Exact text matching prevents edited prompts from inheriting another prefix's eligibility. There are no version/run salts or global LiteLLM caching mutations.
- The application prompt helper forwards a plain TTL to the tools client for eligible prefixes. The client adds a direct Anthropic system-only content-block breakpoint. The provider enforces model-specific size limits. Unsupported providers retain their existing request shape.
- `call_llm` logs requested/applied TTL, prompt/completion tokens, normalized cached-read tokens and cache-write tokens after nonstreamed or assembled streamed responses. Missing usage stays unknown rather than being reported as a measured zero.
- Updated the public settings guide. Caching controls are excluded from content-freshness inputs, so changing TTL alone does not invalidate artifacts.

## Verification

- Existing tools-client, artifact-graph and Campaign Detail tests: `.venv/bin/pytest -q packages/tablesage-tools/tests/test_llm_client.py packages/tablesage-application/tests/session_pipeline/test_artifact_graph.py apps/tablesage-tui/tests/test_campaign_detail.py` — 47 passed.
- Existing helper and settings tests: `.venv/bin/pytest -q packages/tablesage-application/tests/llm/test_llm_helper.py packages/tablesage-model/tests/test_settings_setup.py packages/tablesage-model/tests/test_setup.py` — 16 passed.
- Ruff lint and format checks over all changed Python modules — passed.
- `.venv/bin/ty check packages apps/tablesage-tui` — passed.
- `git diff --check` — passed.
- Direct offline execution against a temporary database and Campaign verified current outputs excluded, cross-Session downstream staleness included, one/two Session prefixes excluded, three Session prefixes included, and duplicate plans/prior tasks deduplicated. Existing fixture helpers supplied artifact completion records; no tests were created or modified.
- Direct offline execution verified TTL defaults and invalid-value rejection, exact-prefix matching, context inheritance into asyncio, isolation from another worker thread, cancellation cleanup, and unsupported-provider behavior.
- Captured transport requests and ran the installed LiteLLM Anthropic request transformer to verify `ttl: 1h` survives native translation on the system block only. Verified application-helper forwarding and ordinary unannotated requests. Synthetic LiteLLM stream chunks verified response assembly, stream closure, and read/write usage logging. No paid requests were issued.

## Limits

Actual cache hits, provider token counts and billing savings remain unmeasured. Eligibility is a pre-execution forecast: a run can fail early, a prefix can be too short, a TTL can expire between uses, or unchanged rebuilt content can leave later outputs current. No rubric or numerical quality scores were defined.

## OpenAI and Gemini Extension

The user approved the researched extension and requested implementation on 2026-10-29.

- Added `prompt_caching.openai_ttl: 30m` independently of Anthropic's existing `ttl`. The current Chat Completions transport accepts only `30m`; it does not silently translate `1h` or introduce the Responses API's `12h` behavior.
- Added a documented GPT model-generation check for direct OpenAI GPT-5.6 and later, including the default GPT-6 Astra and dated/tier variants. Earlier GPT and o-series models retain implicit caching and receive no new explicit cache controls.
- Regeneration eligibility now includes modern OpenAI models with the same exact-prefix and three-distinct-Session rules. All modern OpenAI calls use explicit-only mode. Eligible calls annotate only the system block; ordinary calls include no breakpoint, avoiding implicit writes of variable user input.
- Verified installed LiteLLM 1.99.0 and the installed OpenAI SDK preserve both request-level controls through `extra_body` and system content-block breakpoints. No upgrade or new dependency is needed. Unrelated `extra_body` fields are preserved.
- Gemini still uses implicit caching with no explicit cache object or storage cost introduced. Native SSE verification exposed missing usage unless requested via `stream_options.include_usage`; the client now requests streaming usage for both OpenAI and Gemini.
- Cache-write logging recognizes OpenAI's normalized `prompt_tokens_details.cache_write_tokens` in addition to Anthropic's field. Gemini cache reads remain normalized as cached input tokens. Missing usage remains unknown.

### Extension Verification

- Re-ran all six existing targeted test files listed above together — 63 passed. No unit tests were created or changed.
- Ruff lint/format checks on changed Python modules, repository application/TUI type checks and `git diff --check` — passed.
- Direct offline execution against a temporary Campaign verified the OpenAI TTL default and invalid-value rejection, current outputs excluded, transitive stale dependencies included, duplicate task references deduplicated, two Sessions excluded and three included, and no content invalidation from caching-only settings changes. Verified thread isolation, asyncio inheritance and cleanup on cancellation, plus preservation of Anthropic and older OpenAI/Gemini policy behavior.
- Sent actual LiteLLM/OpenAI SDK requests through an HTTPX mock transport, exercising request serialization and native nonstream/SSE response conversion without contacting a provider. Verified system-only breakpoints and `30m`, ordinary explicit-only mode without breakpoints, preserved unrelated request fields, older-model request shape, and read/write usage after stream assembly.
- Sent actual LiteLLM Gemini requests through an HTTPX mock transport with native JSON/SSE responses. Verified cached input and input/output counts survive both response paths, with no `cachedContent` object or explicit caching annotation on outgoing requests.
- Actual live cache hits, discount eligibility and billing savings were not measured. Explicit Gemini caching remains deferred. The existing provider-enforced minimum-prefix caveat still applies.
