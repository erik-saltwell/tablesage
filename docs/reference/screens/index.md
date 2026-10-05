# Screen Reference

This section documents every screen in TableSage: what it shows, every key it responds to, the secondary actions tucked behind its **Other actions** menu, and the dialogs it opens. Use it to look up what a key does or why an action is unavailable. For step-by-step help with a task, start from the [Guides](../../guides/index.md). For the ideas powering the application, see the [Concepts](../../concepts/index.md).

Start with [Common UI Patterns](ui-patterns.md). It covers the conventions every screen shares: going back with **Esc**, quitting with **Ctrl+Q**, the **New**, **Edit**, and **Delete** keys on lists, secondary actions and the **?** menu, unavailable actions, and the common dialogs.

The screenshots use a fictional sample workspace: the *Iron Pact* Campaign, its Players Alice Chen, Bob Martinez, Priya Patel, and Jordan Lee, and a Session called *The Flooded Cistern*. Most were captured in a 140 × 44 terminal; the Player Detail playback and Review Outliers captures use 160 × 44 so the added controls are visible. Those clip review captures use synthetic audio and illustrative similarity scores. In a narrower terminal, some footer labels can be cut off.

## Screens

| Screen | How you reach it | Page |
|---|---|---|
| *All screens* | | [Common UI Patterns](ui-patterns.md) |
| Welcome | Shown when TableSage starts | [Welcome and Settings](welcome-and-settings.md) |
| Settings | **S** on the Welcome screen | [Welcome and Settings](welcome-and-settings.md#settings) |
| Campaigns | **C** on the Welcome screen | [Campaigns](campaigns.md) |
| Campaign Detail | **E** or **Enter** on a Campaign | [Campaigns](campaigns.md#campaign-detail) |
| Players | **P** on the Welcome screen | [Players](players.md) |
| Player Detail | **E** or **Enter** on a Player | [Players](players.md#player-detail) |
| Review Outliers | **V** on Player Detail | [Players](players.md#review-outliers) |
| Session Detail | **E** or **Enter** on a Session in Campaign Detail | [Session Detail](session-detail.md) |
| Export Artifact | **X** on Session Detail | [Session Detail](session-detail.md#export-artifact) |
| Process Session | **P** on Session Detail | [Process Session](process-session.md) |
| Processing review screens | Opened by Process Session as it reaches each review step | [Processing Review Screens](processing-review-screens.md) |
| Create Previously On | **V** in Campaign Detail's Other actions | [Previously On and Opportunities](previously-on-and-opportunities.md) |
| Generate Opportunities | **Y** in Campaign Detail's Other actions | [Previously On and Opportunities](previously-on-and-opportunities.md#generate-opportunities) |

The screens nest like this. **Esc** takes you back up one level.

```text
Welcome
├── Settings
├── Campaigns
│   └── Campaign Detail
│       ├── Session Detail
│       │   ├── Export Artifact
│       │   └── Process Session
│       │       └── review screens (one per review step)
│       ├── Create Previously On
│       └── Generate Opportunities
└── Players
    └── Player Detail
        └── Review Outliers
```
