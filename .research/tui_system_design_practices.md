# TUI System Design Practices

A reference of design patterns distilled from studying influential TUIs in `awesome_tuis.md` — including lazygit, k9s, helix, yazi, btop++, fzf, harlequin, posting, and the major frameworks (Textual, Ratatui, Bubble Tea / Lipgloss).

This document is organized by **design concern**, not by tool. Each section ends with concrete examples and rules of thumb.

---

## 1. Foundational Principles

These five principles recur across every well-designed TUI studied:

1. **Keyboard is the primary input.** Every interaction must be reachable without a mouse. Mouse support is a nice-to-have, not a substitute. (btop++, k9s, helix all hold to this.)
2. **The terminal grid is a constraint, not a limitation.** Treat fixed-width cells, limited color, and no animation as design features that force clarity. Don't fight the medium by simulating GUI affordances.
3. **State must be visible.** Modes, focus, selection, async progress, and errors must be expressed in the chrome at all times — the user should never have to guess "what mode am I in?" or "is something happening?"
4. **Predictability beats cleverness.** A keybinding that works the same way across every panel is worth more than ten contextual shortcuts that surprise users.
5. **Progressive disclosure.** Surface the 5 things a user needs now; hide the 50 they might need eventually behind `?`, `:`, or a command palette.

---

## 2. Layout & Spatial Design

### 2.1 The canonical layouts

| Layout | When to use | Examples |
|---|---|---|
| **Single-pane + status bar** | Single-purpose tools, fuzzy finders, viewers | fzf, glow, less |
| **Two-pane (master/detail)** | List → detail navigation | gitui, mutt, ncspot |
| **Three-pane (miller columns)** | Hierarchical data, file managers | yazi, ranger, lf |
| **Dashboard (multi-panel grid)** | Monitoring, multi-stream data | btop++, lazygit, bottom |
| **Editor + sidebars** | Editing with context | helix, harlequin, posting |
| **Tabbed workspace** | Multiple parallel contexts | k9s, yazi tabs, tmux |

**Rule of thumb:** if a user has to switch panels more than ~3 times to complete a common task, the layout is wrong.

### 2.2 Spatial conventions

- **Top-left is "where you start."** Primary content, current focus, or first-class navigation goes here.
- **Bottom row is reserved for status and contextual help.** Never put primary content in the last row — terminals truncate it, ssh sessions lose it on resize.
- **Right edge is for ephemeral / supplementary info.** Preview panes, hints, scrollbars.
- **Borders carry semantic weight.** A bordered region = a focusable widget. An unbordered region = passive chrome. Don't draw borders for decoration.
- **Leave breathing room.** Single-cell padding inside borders dramatically improves readability vs. flush-against-border text.

### 2.3 Sizing

- Use **fractional sizing** (`1fr`, percentages, Ratatui `Constraint::Percentage`) for adaptable widgets and **fixed sizing** only for chrome (status bars, headers, prompts).
- Define a **minimum usable size** and gracefully degrade below it. btop++ collapses panels at narrow widths; harlequin hides the schema viewer. Don't render garbage at 80×24.
- The **golden ratio of TUI dashboards** is roughly: 60–70% content, 20–25% navigation/list, 10–15% chrome (header + status).

---

## 3. Navigation & Input Model

### 3.1 The three navigation paradigms

1. **Spatial** — arrow keys / hjkl move within a focused widget; Tab moves between widgets. Best for editors, file managers (helix, yazi).
2. **Modal** — keybindings change meaning based on mode (normal/insert/visual). Best for editors and complex apps (helix, kakoune, vim).
3. **Command-driven** — a `:` prompt or palette executes named actions. Best for resource-heavy tools where users know what they want (k9s, vim ex-mode, Textual command palette).

The strongest TUIs **combine all three**: spatial navigation for the common case, modal for power editing, command palette for everything else (posting, k9s, harlequin all do this).

### 3.2 Focus management

- **Exactly one widget is focused at a time.** Show focus with a brighter border, accent color, or background tint — never just text color (insufficient contrast for many users).
- **Tab cycles forward, Shift+Tab cycles backward.** Universal expectation; don't reinvent it.
- **Esc returns to the parent context.** Closes overlays, exits modes, dismisses pickers. Esc should never be destructive.
- **Provide a "jump mode"** for apps with ≥4 focusable regions. Posting uses Ctrl+O to overlay single-letter labels on every focusable area — like vim-easymotion for widgets. Vastly faster than tab-cycling.

### 3.3 Selection-first vs. action-first

- **Action-first (vim):** `dw` = delete word. The verb comes first, then the noun.
- **Selection-first (helix, kakoune):** select the word, then press `d`. The noun is visible before the verb commits.

Selection-first is more discoverable and more forgiving (you see what you're about to act on). Action-first is faster for experts but punishes mistakes. **Default to selection-first** unless your users are vim natives.

---

## 4. Keybindings & Discoverability

### 4.1 The keybinding hierarchy

Every TUI should layer keybindings in this order of accessibility:

1. **Single-letter mnemonics** for the top 10 actions per context. (lazygit: `b` branches, `c` commit, `p` push.)
2. **Modifier combos** (Ctrl/Alt) for global actions that work in any mode. (Ctrl+P palette, Ctrl+Q quit.)
3. **Multi-key sequences** for less-frequent actions. (yazi: `cd` = copy directory path.)
4. **Command palette** for everything else.

### 4.2 Conventions you must not break

| Key | Expected behavior |
|---|---|
| `q` | Quit current view / app |
| `?` | Help overlay |
| `/` | Search / filter |
| `:` | Command mode |
| `Esc` | Cancel / back / dismiss |
| `Enter` | Confirm / drill in |
| `Tab` / `Shift+Tab` | Cycle focus |
| `g` / `G` | Top / bottom of list |
| `j` / `k` | Down / up (vim-style) |
| `Ctrl+C` | Hard exit (always honor it) |
| `Ctrl+P` | Command palette (modern convention) |

Break these only with a very good reason. Users assume them.

### 4.3 Discoverability patterns

- **Persistent footer hints.** lazygit and k9s show the 4–8 most relevant keys at the bottom of every panel, changing based on context. This is the single highest-leverage UX feature in a TUI. **Build this first.**
- **`?` opens a full keymap overlay.** Group keys by function, not alphabetically. Show the keys you can press *right now* given the current focus.
- **Leader-key menu (helix's `Space`).** Pressing a leader key opens a popup showing the next valid keys with descriptions. Removes the "memorize everything" tax.
- **Command palette with fuzzy search.** The escape hatch for actions you can't remember the binding for. Textual ships this for free; Charm has `huh`. Always include it.
- **Echo unrecognized keys.** When a user mashes a key that does nothing, briefly flash "key not bound" in the status bar. Silent failure is the worst UX outcome.

---

## 5. Visual Hierarchy

### 5.1 Establishing hierarchy without typography

Terminals have no font sizes, weights, or families to work with. Hierarchy comes from:

- **Color saturation.** Bright = important, dim = secondary, gray = disabled.
- **Position.** Top-left > center > bottom-right.
- **Borders and boxing.** A boxed region reads as a unit.
- **Density.** A spaced-out title above a dense table reads as a heading.
- **Symbols / icons.** Nerd Font glyphs (or ASCII fallbacks) give instant category recognition (file types, branch icons, status markers).
- **Reverse video / inverse.** Use sparingly for selection only — never for headings.

### 5.2 Selection vs. focus vs. hover

These are three distinct states and should look different:

- **Focus** (the widget receiving keyboard input): accent border or accent background on the whole widget.
- **Selection** (the item within a widget that's "current"): inverse video or distinctive background on the row.
- **Hover** (mouse over): subtle background change, dimmer than selection.

A common mistake: making focus and selection look identical. Then users lose track of "is this list focused, or am I just looking at where the cursor last was?"

### 5.3 The status indicator hierarchy

In order of severity, with corresponding visual treatment:

| State | Color | Icon | Persistence |
|---|---|---|---|
| Success | green | `✓` / `✔` | Brief flash, then fade |
| Info | blue / cyan | `i` / `•` | Status bar, fades |
| Warning | yellow / orange | `!` / `⚠` | Status bar, requires acknowledge |
| Error | red | `✗` / `✖` | Modal or persistent banner |
| In progress | accent + spinner | `⠋⠙⠹⠸...` | Animated until done |

---

## 6. Color & Theming

### 6.1 The semantic color system (from Textual)

Define colors by *role*, not by hue. A good theme defines ~10 semantic slots:

- `primary` — brand / accent
- `secondary` — supporting accent
- `background` — main canvas
- `surface` — panels/cards
- `panel` — secondary panels
- `foreground` — body text
- `text-muted` — secondary text
- `text-disabled` — inactive text
- `success` / `warning` / `error` — status

Then **generate variants algorithmically** (3 lighter, 3 darker, muted versions). This is how Textual themes work and why a single `primary` color is often enough.

### 6.2 Theming rules

- **Ship light and dark variants.** Don't assume dark terminals. Many devs use Solarized Light, Alabaster, etc.
- **Degrade gracefully.** Detect terminal capability (TrueColor → 256 → 16 → mono) and downsample. Lipgloss does this automatically; do it manually in Ratatui.
- **Respect the user's terminal background.** Don't hardcode a background color; let the terminal show through where possible. This is how the app blends with tmux, alacritty themes, etc.
- **Allow user overrides.** A config file with `theme = catppuccin-mocha` covers 80% of customization desire. btop++ even reads themes from predecessor projects (bashtop, bpytop) for community portability.
- **Never use color alone to encode meaning.** Pair color with an icon, glyph, or position. ~8% of users have color vision deficiency.

### 6.3 What "Charm aesthetic" actually is

Studying Bubble Tea / Lipgloss apps, the aesthetic is:

- **Generous padding** (1–2 cells inside every border)
- **Rounded borders** as default
- **A single saturated accent color** (often pink, purple, or teal) used sparingly
- **Muted body text** with the accent reserved for state, headings, and CTAs
- **Subtle gradients** on prompts and dividers
- **Spinners and progress for any operation >100ms**
- **Restraint** — every screen has ≤2 colors doing semantic work; the rest is monochrome

You can copy this aesthetic in any framework, not just Bubble Tea.

---

## 7. Information Density

### 7.1 The density dial

Different users want different density. Build a **density toggle** (k9s does this with "Narrow / Wide" view):

- **Comfortable** — generous padding, single-line rows, more whitespace
- **Compact** — tight rows, minimal padding, more rows per screen
- **Dense** — multi-column rows, no padding, maximum info per cell

Persist the user's choice. Default to comfortable.

### 7.2 Progressive disclosure techniques

- **Folding / collapsing.** Tree views collapse by default. lazygit's commit list folds details until you press enter.
- **Detail panes.** Don't show all fields in the list; show key fields and reveal the rest in a detail pane on selection (gitui, k9s).
- **Modal popups for confirmations and forms.** Don't expand the layout to fit a "are you sure?" prompt — overlay it.
- **Tabs for orthogonal views.** Yazi tabs for parallel directories, harlequin tabs for parallel queries.
- **Filtering > pagination.** TUIs should never paginate. Make `/` filter the visible list down to what fits.

### 7.3 Tables done well

- **Right-align numeric columns**, left-align text, center small status icons.
- **Truncate with ellipsis** (`…`) and show the full value on hover/focus.
- **Sticky headers** when the table scrolls.
- **Allow column reordering and hiding** (k9s does this per-resource).
- **Sortable columns** with `s` + column index, or click on the header.

---

## 8. Feedback & State Communication

### 8.1 The 100ms rule

- **<100ms:** No feedback needed; the action feels instant.
- **100–1000ms:** Show a spinner. Disable the trigger key.
- **1–10s:** Spinner + progress text ("Fetching 124 of 500…").
- **>10s:** Progress bar with ETA. Allow cancellation (Esc/Ctrl+C).

Never block input. Even during long operations, the UI must remain responsive to navigation and Esc.

### 8.2 Async patterns

- **Optimistic UI.** Stage changes locally and reconcile when the network responds (lazygit does this for many git operations).
- **Background refresh.** btop++ refreshes data on a background timer without blocking menus. Patterns: separate render loop from data loop.
- **Error toasts that don't steal focus.** A failed request should appear as a bottom-right banner, not a modal that hijacks the keyboard.

### 8.3 Empty states

Never show an empty rectangle. When a list is empty, render:

- A short message ("No branches yet")
- A hint at the next action ("Press `n` to create one")
- Optionally a small ASCII illustration

### 8.4 Destructive action confirmations

- **Single-key actions are reversible only.** Deleting a row should require `d` + confirm, never just `d`.
- **Spell-out confirmations** for irrecoverable actions. Type `delete` to confirm — not `y/n` — when force-pushing or dropping a table (rainfrog does this).
- **Always offer undo for stack-like operations** (lazygit's `z` undo). Stash before deleting; let the user roll back.

---

## 9. Search, Filter, and Fuzzy Finding

The fzf paradigm is the single most-copied pattern in TUIs. Internalize it:

### 9.1 The fzf model

1. **Type to filter** — incremental, fuzzy by default.
2. **Arrow keys move the highlight**, Enter selects.
3. **Preview pane on the right** — updates as the highlight moves. Configurable command on the current line.
4. **Multi-select with Tab**, Shift+Tab to deselect.
5. **Esc cancels, Enter commits.**

### 9.2 When to embed fzf-style finding

Whenever a list has >20 items. Whenever a user might know what they want but not where it is. Examples in the awesome list:

- File pickers (helix `Space f`)
- Branch / commit pickers (lazygit, gitui)
- Resource pickers (k9s)
- Command palettes (Textual, posting, harlequin)
- Snippet / template selectors (nap)

### 9.3 Filtering vs. searching

- **Filter** = hide non-matching rows. Use `/`. Persists until cleared.
- **Search** = jump to next match, others stay visible. Use `n` / `N` to advance. Use for in-document search.

Don't conflate them. Both are useful; both have keyboard conventions.

---

## 10. Mode Indicators (when going modal)

If your app is modal:

- **Show the mode in the status bar** at all times. Helix shows `NOR`, `INS`, `SEL`. The status bar color often changes with the mode.
- **Cursor shape conveys mode.** Block in normal, bar in insert, underline in select. Most terminals support `CSI Ps SP q`.
- **Mode-specific keybindings appear in the footer.** When you enter insert mode, the footer shows `Esc: normal` and not `j/k: navigate`.
- **Avoid >3 modes.** Each mode is a memory tax. Normal + Insert + Visual is the ceiling.

---

## 11. Mouse Support

Mouse support is optional but, when implemented:

- **Click to focus / select.** Same as keyboard arrows landing on the row.
- **Scroll wheel scrolls the focused widget.** Not the whole screen.
- **Drag for selection** in text areas (posting allows this for response bodies).
- **Right-click for context menu** — but only as an accelerator for an existing keyboard action. Never make it the only way.
- **Always test without a mouse.** If the app is unusable keyboard-only, you have not built a TUI.

---

## 12. Performance

### 12.1 The frame budget

- **Render in <16ms** to feel smooth at 60fps for animations.
- **For static UIs, render only on input or data change.** Don't re-render at 60fps if nothing moved — burns battery and CPU.
- **Diff renders, don't redraw the screen.** Ratatui and Textual both do this; if you're using ncurses, use `wnoutrefresh` + `doupdate`.

### 12.2 Async I/O

- Network, disk, and subprocess calls **must not block the render loop**. Use channels (Go, Rust), threads, or async/await (Python).
- Yazi's async I/O is the gold standard: file previews load in the background without blocking navigation.
- Show partial data as it arrives — don't wait for a full result set to render the first row.

### 12.3 Large data

- **Virtualize long lists.** Render only the visible rows + a buffer. Both Ratatui's `List` and Textual's `DataTable` do this.
- **Stream logs and outputs.** Append rows as they arrive; cap memory with a ring buffer.
- **Index for search.** Don't grep N rows on every keystroke; build a trigram or substring index once.

---

## 13. Framework-Specific Notes

### 13.1 Textual (Python)

- **Use CSS for all styling.** Resist the urge to set styles in Python — separation of concerns is the framework's whole pitch.
- **Reactive attributes drive re-renders.** Mutate a reactive and the bound widgets update automatically.
- **Compose with Containers.** `Horizontal`, `Vertical`, `Grid`, and `dock` cover 95% of layouts.
- **Use the dev tools.** `textual run --dev` enables live CSS reload — iterate visuals at GUI speed.
- **The command palette is free.** Register actions with descriptions; users get a Ctrl+P palette automatically.
- **Themes use 11 semantic colors.** Define `primary` and let the framework generate variants.

### 13.2 Ratatui (Rust)

- **Pick one architecture and commit:** TEA (Elm-style) is easiest to reason about for small apps; component architecture scales better for large ones.
- **`Constraint::*` is your layout vocabulary.** Mix `Length`, `Percentage`, and `Min` to express adaptive layouts.
- **Build a `widgets::*` module** for app-specific reusable widgets — don't keep inlining `Block::default().borders(...)`.
- **Use `tui-input` or similar** for text editing — rolling your own is painful.
- **Separate state, view, and event handling** into distinct modules from day one.

### 13.3 Bubble Tea / Lipgloss (Go)

- **Embrace the Elm architecture.** Model + Update + View. Resist adding mutable state outside the model.
- **Use `tea.Cmd` for side effects.** Network calls, timers, file I/O return a `tea.Msg` to the update loop.
- **Lipgloss styles are values, not functions.** Define them once at package level; reuse everywhere.
- **Compose with `lipgloss.JoinHorizontal` / `JoinVertical`.** They handle ANSI-aware width correctly.
- **Use Bubbles components** (textinput, viewport, spinner, list, table) rather than reinventing.

### 13.4 Curses-family (ncurses, urwid, blessed)

- **Lower-level, more control, less polish.** Best when you need to support ancient terminals or have a non-standard rendering model.
- **Beware of resize handling.** SIGWINCH must redraw; many curses apps break on resize.
- **No built-in theming.** You'll build it yourself.

---

## 14. Anti-Patterns to Avoid

Patterns observed failing in the wild, or missing from poorly-designed TUIs:

1. **Silent key presses.** A user mashes keys and nothing happens. No echo, no message, no visual change. They assume the app is broken.
2. **Stealing terminal state.** Not restoring the cursor, leaving the alternate screen on exit, or eating Ctrl+C. Always restore on signal.
3. **Hardcoded 80×24 assumption.** Modern users have ultrawide monitors. Lay out responsively.
4. **Color-only state encoding.** Red = error is fine; red without an icon and dim red is "is this an error or just dim text?"
5. **Modals that you can't escape with Esc.** Trapping users in confirmations they didn't mean to open.
6. **Mouse-only features.** Drag-to-resize panes with no keyboard equivalent.
7. **Logs / output without scroll.** Always allow pageup/pagedown through historical output.
8. **Footer with no hints.** The bottom row is reserved real estate; don't waste it on a static "powered by X" message.
9. **Unicode without ASCII fallback.** Nerd Font icons are great, but the app must remain legible without them (option flag or auto-detect).
10. **Reactive lag.** Filtering a 10k-row table on every keystroke without debouncing. Debounce, virtualize, or index.
11. **Inconsistent navigation across panels.** `j` scrolls in panel A and switches focus in panel B. Pick one and stick with it.
12. **Help overlays that don't reflect current context.** Showing every key in the app instead of the keys you can press *right now*.

---

## 15. Pattern Catalog (Quick Reference)

Patterns observed across multiple TUIs, with the canonical exemplar:

| Pattern | Description | Exemplar |
|---|---|---|
| Contextual footer | Bottom bar shows keys valid for current focus | lazygit, k9s |
| Help overlay (`?`) | Full keymap, grouped by function, dismiss with Esc | helix, lazygit |
| Command palette (Ctrl+P) | Fuzzy search over all actions | Textual, posting, harlequin |
| Command mode (`:`) | Vim-style line for typed commands | k9s, helix |
| Leader menu | Press leader key, popup shows next valid keys | helix (Space), Spacemacs |
| Jump mode | Single-letter overlays on every focusable region | posting, vim-easymotion |
| Picker | Fuzzy-filterable list + preview pane | fzf, helix, k9s |
| Miller columns | Parent / current / preview side-by-side | yazi, ranger |
| Master/detail | List on left, full content on right | mutt, gitui, ncspot |
| Dashboard | Grid of independently-updating panels | btop++, bottom, lazygit |
| Tabs | Numbered (1–9) or named workspaces | yazi, k9s, tmux |
| Status bar with mode | Mode indicator + filename + position | helix, vim |
| Toast notifications | Non-blocking bottom-corner status | posting, modern Textual apps |
| Spinner + ETA | Async operation feedback | every Charm app |
| Folded/tree views | Expand on Enter, collapse on left | gitui, lazygit |
| Density toggle | Compact/comfortable/dense modes | k9s |
| Themes from config | Named themes selectable at runtime | btop++, every Charm app |
| Sticky preview | Preview pane follows highlight | fzf, yazi, helix picker |
| Two-step destructive | Confirm with typed word or second keypress | rainfrog, lazygit |
| Undo stack | `z` / `Shift+z` for reversible operations | lazygit |

---

## 16. Design Checklist (Use Before Shipping)

A practical pre-flight for any TUI:

**Layout**
- [ ] Renders correctly at 80×24, 120×40, and 200×60
- [ ] Bottom row reserved for status / hints
- [ ] At most one widget focused at any time, visibly
- [ ] Adapts gracefully when too narrow (collapse panels, hide chrome)

**Keybindings**
- [ ] `q`, `?`, `/`, `:`, `Esc`, `Enter`, `Tab` all do conventional things
- [ ] `Ctrl+C` exits cleanly and restores terminal
- [ ] Contextual footer shows ≤8 most-relevant keys
- [ ] `?` opens grouped help overlay
- [ ] Command palette (Ctrl+P) covers all actions
- [ ] No silent key presses — unknown keys produce visible feedback

**Visuals**
- [ ] Focus, selection, and hover are visually distinct
- [ ] Color paired with icon/glyph everywhere it carries meaning
- [ ] Light and dark themes both supported
- [ ] Degrades to 16-color and monochrome
- [ ] Unicode glyphs have ASCII fallbacks

**Feedback**
- [ ] Spinner appears for any operation >100ms
- [ ] Long operations show progress and are cancellable
- [ ] Errors are non-blocking and dismissible
- [ ] Empty states show a message + next-action hint
- [ ] Destructive actions require confirmation (typed for irrecoverable)

**Performance**
- [ ] Long lists are virtualized
- [ ] Network/disk I/O is async; UI stays responsive
- [ ] No re-render at 60fps when idle
- [ ] Resize (SIGWINCH) redraws correctly

**Mouse (if supported)**
- [ ] Every mouse action has a keyboard equivalent
- [ ] Scroll wheel scrolls the focused widget
- [ ] Click focuses + selects

---

## 17. Recommended Reading by Tool

The TUIs in `awesome_tuis.md` most worth studying for specific patterns:

- **Layout & dashboard:** btop++, bottom, lazygit, gh-dash
- **Navigation & focus:** helix, kakoune, yazi
- **Command palette / picker:** fzf, helix, harlequin, posting
- **Theming & polish:** glow, slides, gum, charm's catalog
- **Information density:** k9s, visidata, tabiew
- **Async / streaming:** mitmproxy, termshark, lazyjournal
- **Forms & input:** posting, slumber, ATAC
- **Modal editing:** helix, vis, kakoune
- **Multi-pane editing:** harlequin, lazygit
- **Charts & data viz:** btop++, bottom, gping, glances
