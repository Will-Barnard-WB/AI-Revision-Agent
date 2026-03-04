# UI Polish Plan — Round 2

## Step 1 — Logo no-highlight
Remove the hover/active highlight effect from the RevisionAgent logo link in the sidebar.
- Add `no-highlight` class to the `<a>` tag wrapping the logo in `base.html`
- Add CSS rule in `style.css` to suppress sidebar hover/active styles on `.no-highlight`

## Step 2 — Full-width pages
Remove the `max-w-5xl` constraint from ambient, approvals, and history pages so they fill the full available width.
- `ambient.html`: change `<div class="p-6 max-w-5xl">` → `<div class="p-6">`
- `approvals.html`: same
- `history.html`: same

## Step 3 — History tab with Recent Files & preview modal
Rewrite `history.html` to include a **Recent Files** section that:
- Parses the 10 most recent `created`/`generated` entries from `/api/history`
- Extracts filenames from the description (e.g. `Eigenvalues_Study_Guide.md`)
- Displays them as clickable cards
- Opens a full-screen preview modal with:
  - Markdown rendering via `marked.parse()` (fetched from `/outputs/documents/<file>`)
  - PDF via `<iframe>` (same path pattern)
  - Close button (Escape key support)
