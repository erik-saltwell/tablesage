# System Prompt Caching Implementation

Implement the [agreed intent](intent.md). No rubric exists; the user explicitly requested implementation. No numerical quality assessment is claimed.

- [x] Add validated `prompt_caching.ttl` settings (default `1h`, accepting Anthropic's `5m` and `1h`) and an operation-scoped policy. Count distinct Session tasks from existing generation plans, including recursively stale dependencies, by model and exact system text. Enable only prefixes needed by at least three Sessions. Wrap Campaign Detail's existing regeneration loop without changing its artifact behavior.
- [x] Pass the selected TTL from the application prompt helper as a plain transport value. Support direct Anthropic calls initially with a system-only content-block breakpoint; leave other providers and ordinary processing unchanged. Let the provider enforce model-specific minimum prefix size. Log requested/applied caching and actual input, output, cached-read and cache-write tokens after streamed or nonstreamed completion.
- [x] Document settings and limitations. Verify settings validation, operation lifetime/isolation, plan counting, request translation and usage capture through direct offline execution; run existing relevant tests, Ruff and type checks. Do not add or expand unit tests. Record any limitations and finish tracking.

Inspected components: `Application.generation_plan`, recursive `ArtifactGraph.status`, Campaign Detail's sequential stale-aware regeneration loop, the shared application prompt helper, tools LiteLLM client, settings model and deployment loader. Caching controls do not affect artifact content/freshness and must not be added to generation fingerprints. First implementation supports Anthropic only; provider-enforced minimum lengths avoid estimates becoming correctness gates. Actual provider hits require a live paid request and will not be claimed from offline verification.

## Approved OpenAI and Gemini Extension

The user approved the researched proposal and requested implementation on 2026-10-29. Preserve the Anthropic behavior and expand the same work item; there is still no numerical rubric or assessment.

- [x] Add an independent OpenAI `30m` default and include documented GPT-5.6+ model families in regeneration eligibility. Keep the three-distinct-Session rule and exact prefix matching.
- [x] Send explicit-only OpenAI caching controls on modern models, adding a system-only breakpoint for qualifying regeneration calls and no breakpoint for ordinary calls. Preserve older OpenAI implicit caching and Gemini implicit caching. Validate installed LiteLLM/SDK translation through intercepted HTTP; upgrade only if required.
- [x] Normalize OpenAI cache-write counts and verify Gemini cached-token reporting for both ordinary and streamed responses. Request OpenAI streaming usage. Keep missing metrics unknown.
- [x] Update intent, public settings documentation and completion evidence. Run existing targeted tests, lint/type checks and offline behavior checks without creating or expanding unit tests. Do not make paid requests or claim measured savings.
