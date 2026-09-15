# Public Documentation Intent

## Intended outcome

TableSage RPG should have public documentation that lets a new game master
understand the product, install it, begin using it, and follow its core
campaign workflow without needing contributor or internal-design knowledge.

The documentation should be a polished, navigable website. Markdown committed
to this repository remains the source of truth, and GitHub Pages publishes the
site. MkDocs is the chosen site generator because it keeps the authoring model
Markdown-first and is a natural fit for the project's Python ecosystem.

## Audience and scope

The immediate audience is a game master evaluating or using TableSage for the
first time. Contributor and developer documentation are out of scope for the
public site for now. Any locally retained internal material remains separate from the
public navigation.

## Information architecture

The README is the concise front door. It should explain what TableSage is,
present the key features, provide installation and a short quick start, show a
small number of representative screenshots, and link into the full guide.

The full guide should be organized around GM tasks rather than mirroring the
application's screen layout. The proposed top-level journey is:

1. Start a campaign.
2. Record and process a session.
3. Review and export the campaign record.
4. Prepare the next session.

Reference material, such as settings, supported platforms, and troubleshooting,
should support those task guides rather than determine the site's primary
navigation.

## Screenshots

Screenshots should explain consequential moments: recognizing the right screen,
choosing an action, or confirming the expected result. They should not be added
to every routine instruction. Existing candidate mockups live in
[`apps/tablesage-tui/mockups/`](../../apps/tablesage-tui/mockups/); public
documentation assets should ultimately live in a stable documentation image
location and use repository-relative links.

## Proposed public source layout

```text
README.md
docs/
  index.md
  quick-start.md
  how-it-works.md
  guides/
    create-your-first-campaign.md
    record-and-process-a-session.md
    review-and-export.md
    prepare-the-next-session.md
  reference/
    supported-platforms.md
    settings.md
  troubleshooting.md
  images/
```

This structure is a working proposal, not a settled set of individual pages.

## Decisions made

- Publish user-facing documentation as a GitHub Pages site generated with
  MkDocs.
- Keep repository Markdown as the documentation source of truth.
- Make the README a brief landing page that directs users to deeper guides.
- Prioritize first-time GMs, not contributors or developers.
- Organize primary navigation by user tasks and campaign workflow, not by TUI
  screens or a feature inventory.
- Use screenshots selectively to clarify important steps and outcomes.

## Open questions

- What is the smallest useful quick-start journey, and which real campaign
  scenario should demonstrate it?
- Which task guides belong in the first public release versus a later pass?
- Should screenshots be refreshed from the running application, or can the
  existing mockups be adapted for initial publication?
- What visual and editorial style should distinguish quick-start material from
  deeper reference material?
