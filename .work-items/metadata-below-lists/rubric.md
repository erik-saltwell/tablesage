# Quality rubric: detail-screen metadata and creation dialogs

**Status: approved** (2026-09-28). Dimensions, anchors, and the calibration check below are settled.

## Subject and intended effect

Judges changes to how Player, Campaign, and Session metadata is captured and edited in the TUI. The intended effect: the Campaign, Player, and Session Detail screens no longer open with a metadata text input focused (which swallows every key binding until Esc is pressed), because all of an item's metadata is collected up front in its creation dialog, and metadata editing on the detail screen moves out of the first-focus position (either below the lists, or read-only with a single edit binding that reopens the creation-style dialog; the choice is still open).

## Scale

Every dimension uses a shared 0–10 scale where higher is better. Reasoned intermediate scores are allowed. Dimensions are scored independently; there is no total, weighting, target, or pass/fail threshold.

## Dimensions

### 1. Bindings on arrival

How usable the screen's shortcuts are the moment it opens.

- **0:** Opens with a text input focused. No shortcut works until Esc (today's behavior).
- **3:** Focus starts outside any input but not on the main list. Row actions like E/D/Enter need a Tab or arrow press first, or the footer is incomplete.
- **6:** Opening from the list lands on the main list with every shortcut working. But some other entry route drops focus back into an input: create-then-open, returning from a dialog or child screen, or switching tabs.
- **8:** Every entry route lands on the list with the full footer. One minor gap remains, such as an empty list leaving focus somewhere unhelpful.
- **10:** Every entry route, including an empty list, lands on the primary list with all shortcuts live and shown in the footer.

### 2. Complete creation

Whether the creation dialog captures all of the item's metadata in one pass without becoming tedious.

- **0:** The dialog asks only for the name. Other metadata can only be set later on the detail screen.
- **3:** All fields are present, but an error closes the dialog or loses what was typed (for example, a bad date shows a toast and you start over).
- **6:** All fields are present and errors show inside the dialog. But it has friction: optional fields must be filled in, there's no date default, or Enter doesn't submit from every field.
- **8:** Complete, optional fields can be skipped, errors appear in the dialog with entries kept, and the date has a sensible default. One rough edge remains, such as odd tab order, or the folder-collision prompt afterward losing the entries.
- **10:** One pass. The name field is focused first, optional fields are marked, the date defaults to today but can be changed, and Enter submits from any field. Invalid names or dates and folder collisions never lose what was typed.

### 3. Later editing

How discoverable, cheap, and safe it is to correct metadata after creation.

Deliberately does not reward in-place editing (typing directly into a field shown on the detail screen) over a dialog-based edit: this dimension counts keystrokes and safety, not the editing surface, since in-place editing at first focus is exactly what causes today's bindings-on-arrival problem (see the contrast check below).

- **0:** Metadata can't be changed after creation, or only through an obscure path away from the detail screen.
- **3:** Editing is possible but hidden (not in the footer, reached only by tabbing through unrelated widgets), or ordinary browsing keys can change data by accident.
- **6:** Editing is discoverable and works. But its validation differs from creation, or it's unclear whether Esc cancels or saves.
- **8:** One visible binding or a single focus move starts editing. Validation matches creation and Esc discards changes. Minor friction remains, such as editing one field at a time.
- **10:** Editing is shown in the footer and takes at most two keystrokes to start. It uses the same validation as creation, pre-filled with current values; Enter saves and Esc discards. No browsing key can change metadata.

### 4. Metadata visibility

Whether the current metadata can still be read at a glance on the detail screen.

- **0:** Metadata isn't shown on the detail screen, or can only be seen by scrolling or opening a dialog.
- **3:** Shown, but below the fold at 80×24, or visually blends into the list content.
- **6:** Visible at 80×24 without scrolling, but placed where it's easily overlooked (at the bottom, de-emphasized), or long values are cut off with no way to see them in full.
- **8:** Clearly labeled in a prominent, consistent spot that's visible on opening. Long values are shortened but can be seen in full elsewhere.
- **10:** All metadata can be read at a glance on opening, in the same spot on every screen, even at 80×24. Long values wrap or are shortened with a way to see them in full.

### 5. Cross-screen consistency

Whether Player, Campaign, and Session share the same creation dialog pattern, edit mechanism, placement, and Esc/commit behavior.

- **0:** Each screen uses a different creation pattern and a different way to edit.
- **3:** Creation dialogs match, but editing works differently (inline on one screen, a binding on another), or the same mechanism uses different keys.
- **6:** Same mechanism everywhere, but one screen differs in key, label, placement, or Esc/Enter behavior.
- **8:** Same dialog pattern, key, placement, and Esc behavior on all three screens. Small differences are justified by content.
- **10:** One shared dialog component, the same binding key and label, the same placement, and identical Esc/Enter behavior. The only difference is which fields each screen has.

## Calibration: contrasting outcomes

- **Version A, fields below the lists:** the inputs stay editable in place but move under the tables, and focus starts on the list.
  - Dimension 1 rewards it.
  - Dimension 4 marks it down: the fields sit at the bottom, and Session Detail is dense, so they may fall below the fold at 80×24.
  - Dimension 3 is middling: you reach the fields by tabbing, and blur-to-save means a stray Tab plus typing can change data.
- **Version B, read-only header plus edit binding:** metadata shows as plain text at the top, and a single key opens the creation dialog pre-filled.
  - Dimensions 1, 4, and 5 reward it.
  - Its Dimension 3 score depends on that binding being visible in the footer.

As anchored, the rubric generally favors B. The one thing A offers that the rubric does not reward is editing in place — fixing a typo right where you see it, with no dialog. This is deliberate (2026-09-28): Dimension 3 already counts keystrokes, and in-place editing at first focus is exactly what causes today's bindings-on-arrival problem, so rewarding it in Dimension 3 would work against Dimension 1.
