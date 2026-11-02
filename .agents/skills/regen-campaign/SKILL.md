---
name: regen-campaign
description: Regenerate a TableSage campaign's outputs through the Textual MCP server in this repo's deployment workspace. Defaults to Brandonsford when no campaign is supplied.
---

# Regen Campaign

Use the campaign name supplied with the invocation, or **Brandonsford** if none is provided. Treat the whole supplied name as the campaign name, including spaces.

1. Use the **Textual MCP server** to enter the real TableSage app in this repository's `deployment/` workspace. Reuse a running MCP session only if it uses that workspace; otherwise launch one with `cwd` set to the absolute deployment path. The app must load `deployment/.tablesage/settings.yaml` and the configured credentials, as normal startup does; a bare `TableSageApp()` uses default settings instead. Do not use screenshot fixtures or a temporary campaign.
2. Inspect the app, navigate to the Campaigns List, and open the requested Campaign. Confirm its name on Campaign Detail before proceeding.
3. From Campaign Detail, open **Other actions** (`slash` or `question_mark`), then select **Regenerate All Outputs** (`o`). Drive the UI through Textual MCP rather than invoking generation functions or CLI regeneration commands directly.
4. Observe progress until completion or a reported failure. Report the Campaign name and the app's result, including skipped Sessions or blockers. Do not automatically restart a failed run. Keep the MCP app session alive while generation is running.

If the Campaign is absent or the app requires setup or transcript review, report that blocker. Do not create a Campaign or change settings to work around it.
