# TableSage TUI screens

This is an inventory of implemented screens and navigation. Domain/storage responsibilities are in [architecture](system_architecture.md); product capabilities are in [use cases](tablesage_use_cases.md). Actual bindings are declared under [screens/](../apps/tablesage-tui/src/tablesage_tui/screens/).

## Shared interaction patterns

Collection screens use tables; entity screens combine inline CommittingInput metadata with child tables. Campaign Detail has Roster/Sessions/Glossary tabs; Player and Session Detail do not.

N generally creates, E/Enter opens or edits a selected row, and D/Delete removes a selection. Entity/clip deletion and destructive cleanup ask for confirmation. Manual Review and proposal-review deletion edit a transient working copy and need not prompt per row.

C is contextual: orphan cleanup on collections, unused-clip cleanup on Player Detail, Clean Session on Session Detail, and Apply & Continue in spelling suggestions. It is not globally reserved for one operation.

F5 reloads live state without regeneration, can discard uncommitted inline edits, and is hidden where no refresh applies. Escape usually returns/cancels, with flow-specific discard handling. Ctrl-Q quits; the command palette is disabled. Consult the footer and each screen's enabled-action checks rather than assuming every key is universal.

FileOpen, FileSave and SelectDirectory use shared application wrappers. Existing text/confirmation, roster role/player, attendee and glossary dialogs are reused. These are implemented controls, not future widget work.

## Landing and Settings

Landing is always home, even in an empty workspace: C Campaigns, P Players, S Settings. Required first-run/settings-version review disables ordinary navigation until a valid Settings Save. Credentials need not be populated just to save setup.

Settings has LLM and Keys sections. It edits three model selectors (including custom IDs) and personal credentials; other YAML fields are preserved, not exposed or reset. Ctrl-S saves. Dirty exit offers Save/Discard/Cancel; provider tests require saving edits first. See [Settings](../.scratch/settings/design.md).

## Campaigns List

Columns are Campaign (name and description), Game System and Last Session date. N creates, E/Enter opens, D deletes the database campaign after confirmation, C cleans orphan campaign folders, and I imports a campaign ZIP. There is no separate inactive/archive view.

## Campaign Detail

Inline name/description/game-system fields sit above R Roster, S Sessions (initial tab), G Glossary. N/E/D apply to the active child collection.

- Roster adds existing global players and default GM/character roles. Removing membership leaves the player intact.
- Sessions creates/opens Session Detail. Deleting a Session removes its database record; C on this tab cleans orphan numbered folders. New attendance derives from the previous Session or roster.
- Glossary adds/edits terms and descriptions and confirms deletion.
- I imports glossary entries from legacy settings; X exports the campaign ZIP.
- O Regenerate All Outputs runs the campaign-wide regeneration operation.
- V Create Previously On and P Generate Opportunities launch the implemented preparation flows below.

#### Generate Opportunities

Requires current, valid, complete Scene Breakdowns for every Session. The screen
shows the Campaign ending situation and a required editable upcoming-session prompt.
Ctrl-G generates up to five short pitches from the complete Campaign Scene Recap;
successful regeneration replaces the displayed set, while failures preserve it.
Each pitch has a title, From the Campaign, and Opportunity, without source citations
or expansion controls. An empty set invites revising the prompt.

Ctrl-S saves the entire displayed set and its original generating prompt as Markdown
outside managed Campaign data, confirming replacement of existing files. Saving
stays on the screen. Escape returns to Campaign Detail; there is no persisted draft
or suggestion history. See the [feature proposal](../.scratch/reincorporation-assistant/proposal.md).

#### Create Previously On

This ephemeral workflow requires a current, valid, complete Scene Breakdown for every
Session. The action stays available; invoking it reports all affected Sessions and directs
the GM to **Regenerate All Outputs** if the requirement fails. No regeneration starts automatically.

After a progress dialog generates source-backed ingredients, a split-pane quick-entry view
shows editable starting situation and upcoming-session notes on the left, and four ingredient
categories on the right. Starting situation is the highest-sequence Session's `ending_situation`.
Each category has up to five unselected suggestions; focus shows supporting Scenes. Space or
Enter selects ingredients. Notes or at least one ingredient are required to **Find Scenes** (`Ctrl-N`).

The scout opens a complete chronological Session → Scene tree. Recommendations are marked
and preselected; only their Sessions start expanded. Space or Enter toggles Scenes or expands
Sessions. Every recorded Scene is selectable, with no count limits. Focus shows its full record
and private scout rationale. Per-Session and total selected counts remain visible; at least one
Scene is required to save. **Back** preserves quick-entry inputs; scouting again replaces all
prior Scene choices with the new recommendations.

**Save Markdown…** opens a home-directory file picker suggesting
`<campaign-name>-<max-session-sequence-plus-one:03d>-previously-on.md`. The destination must be
a Markdown file outside managed Campaign folders. Replacing an existing file requires confirmation
before generation. Canceling the picker preserves selection. The recap writer sees selected
Scenes, starting situation, and glossary only. Success returns directly to Campaign detail;
the GM reviews the file externally. Provider or save failures preserve inputs, choices, and
destination for manual retry. Leaving or quitting after edits or Scene review confirms discard.

See [the full proposal](../.scratch/campaign-aware-previously-on/proposal.md) for scope and deferred work.


## Players List

Columns show player name, centroid sample count and centroid status. N creates a named player, E/Enter opens, D deletes and C cleans orphan player folders. A From Audio runs the standalone multi-speaker import wizard; S From Session enhances attendees from a selected transcribed Session. I/X import/export player ZIP archives.

See [audio import](import_players_from_audio_file.md) and [session enhancement](enhance_players_from_session.md). Neither is a stub or a Player Detail S action.

## Player Detail

Inline name plus read-only centroid metadata/total duration, then WAV filename/duration rows. F imports from a directory, D deletes a selected clip with confirmation, R recomputes and C removes unused duplicates/outliers after confirmation. No per-clip edit action or session-import binding. See [Player Detail](player_detail_screen.md).

## Session Detail and review screens

[Session Detail](session_detail_screen.md) provides A Import Audio, V Review Transcript, G Generate Outputs, R Regenerate Artifact, B Benchmark, L Extract Glossary, X Export and C Clean Session. N/E/D are attendance-focus-scoped. Indicators report Current/Stale/Missing rather than presence alone; some utility gates (export and glossary extraction) still use presence.

[Manual Review](speaker_review_screen.md) has spelling suggestions followed by speaker/text review, sharing one unsaved working copy. Glossary Review similarly edits proposals before committing; Artifact Export copies one chosen visible artifact at a time. The From Audio wizard has pre-step, speaker-resolution and final-summary screens sharing transient run state.

The former deferred Session Detail generation, From Audio, directory import and unused-clip cleanup features are implemented. Public documentation/site work remains separately [captured](../.work-items/public-documentation/item.md).
