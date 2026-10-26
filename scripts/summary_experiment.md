# Session Summary Experiment

Run the utility from the checkout with `uv run python scripts/summary_experiment.py --workspace ~/data/tablesage_summary_test <command>`. Use `--help` after any command for its arguments. Narrative evidence stays outside the checkout; candidate runs never replace canonical Session summaries.

## User Handoff

The prepared workspace is `/home/eriksalt/data/tablesage_summary_test`. Launch it with:

```sh
/home/eriksalt/data/tablesage_summary_test/launch-tablesage.sh
```

The launcher selects the workspace even when invoked from another directory. It uses this checkout's virtual environment, so keep that environment installed. Configure provider credentials locally through the normal Settings flow if needed; never include credentials in reference files or chat.

1. Create the test Campaign and set its game system, Players, attendance/Roles, and useful Glossary entries.
2. Create the earlier Session and import its recording. Complete human speaker, terminology, and transcript review, then finish normal processing and output generation.
3. Create the current Session in the same Campaign with a strictly later date. Import and review its recording, then finish processing. Its recap should come from the earlier Session.
4. Keep the original good and poor summaries and available transcripts/Ledgers untouched. Tell the agent their locations and any known generation dates, models, or application revisions.
5. Tell the agent when both Sessions are ready. The agent finds their IDs, checks currentness, and freezes the inputs after processing has stopped.

No historical reference files or existing Player/Glossary data have been imported yet. The user chooses any production data to reuse.

## Agent Operations

- `init`: initialize a new external workspace through normal application setup, deploy settings/help, create evidence directories, and write a launcher. Existing destinations are refused.
- `status`: list Campaigns/Sessions, IDs, dates, and required artifact freshness.
- `freeze --prior UUID --current UUID --output PATH`: require current outputs, ordered dates, correct prior-recap provenance, and introductions ownership; copy narrative artifacts, exact input/composition data, and a consistent SQLite backup into a new snapshot. Close TableSage before freezing.
- `prompt --snapshot PATH --revision REV --compatibility-note TEXT --output PATH`: extract both prompt files from Git without changing the checkout and render against frozen inputs. Inspect Ledger format and semantics before supplying the compatibility note; structural validation cannot prove semantic compatibility. Incompatible historical pipelines belong in a separate comparison.
- `run --snapshot PATH --prompt PATH --model MODEL --options JSON --output PATH`: report two planned calls without generation. Add `--execute` for two independent provider generations. Use identical explicit model/options/timeout for both prompt versions. An offline `--response-file PATH` exercises composition without a provider.
- `packet --runs PATH1 PATH2 PATH3 PATH4 --name ROUND`: require two successful repetitions per prompt with matching controls, shuffle into neutral candidate files and observation forms, and store the mapping separately.
- `reveal --name ROUND --review-complete`: show the mapping only after observations have been recorded. This flag is a declaration, not an access-control mechanism.

Snapshot, prompt, and run outputs must be new directories under their respective `summary_experiment/` subdirectories. Hash verification rejects changed or missing evidence. Hashes detect accidental changes; they are not tamper-proof signatures. A failed command can leave a partial directory: retain it and use a new destination.

Each generation preserves raw attempts and composed output, timings, effective requested settings, and separate word counts for body, recap, introductions, and complete summary. Invalid summary output gets at most three recorded attempts; provider errors stop the run. A failed repetition is retained and stops further generations. Token usage/cost is unavailable through the shared text-only interface; consult provider records. No seed is imposed by default, so repeated calls are independent.

Blind packets contain summaries and observation forms without provenance. Give them to a fresh reviewer context that has not seen prompt identities or run mappings. The preparing agent cannot claim a blind review in its informed conversation. Review word counts after qualitative observations; shorter is not automatically better.
