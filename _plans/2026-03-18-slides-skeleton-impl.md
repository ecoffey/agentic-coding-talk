# Slides Skeleton — Implementation Detail

## § Implementation Detail

No tests apply here (pure static content + config). Steps are sequential.

---

### Step 1 — Create `slides/package.json`

**File:** `slides/package.json` (new)

```json
{
  "name": "agentic-coding-talk-slides",
  "private": true,
  "scripts": {
    "dev":   "marp --preview slides.md",
    "build": "marp slides.md -o dist/slides.html",
    "pdf":   "marp slides.md -o dist/slides.pdf"
  },
  "devDependencies": {
    "@marp-team/marp-cli": "^4"
  }
}
```

---

### Step 2 — Create `slides/.gitignore`

**File:** `slides/.gitignore` (new)

```
node_modules/
dist/
```

---

### Step 3 — Create `slides/slides.md`

**File:** `slides/slides.md` (new)

```markdown
---
marp: true
theme: default
paginate: true
---

# Agentic Coding
### How AI agents change the way we build software

ATLS 4214 — Big Data Architecture

---

# What is agentic coding?

<!-- TODO: content -->

---

# Live demo: building `logpipe`

<!-- TODO: content -->

---

# Q&A / Resources

<!-- TODO: content -->
```

---

### Step 4 — Create `slides/README.md`

**File:** `slides/README.md` (new)

```markdown
# Slides

Built with [Marp](https://marp.app/) — slides are plain Markdown in `slides.md`.

## Prerequisites

- [Node.js](https://nodejs.org/) (v18+)

## Setup

```bash
cd slides
npm install
```

## View in browser (live preview)

```bash
npm run dev
```

Opens a live-reloading browser window. Edit `slides.md` and the browser updates automatically.

## Export to HTML

```bash
npm run build
# → dist/slides.html  (self-contained, shareable — no install needed to view)
```

## Export to PDF

```bash
npm run pdf
# → dist/slides.pdf
```

## Terminal viewing (optional)

If you prefer a terminal presentation, install [patat](https://github.com/jaspervdj/patat):

```bash
brew install patat   # macOS
patat slides.md
```

patat reads the same `slides.md` file with no extra config.

## Editing tips

- Slides are separated by `---`
- YAML frontmatter at the top of the file configures Marp globally
- Per-slide directives go in HTML comments: `<!-- _class: lead -->`
- VS Code users: install the [Marp for VS Code](https://marketplace.visualstudio.com/items?itemName=marp-team.marp-vscode) extension for a split-pane live preview
```

---

### Step 5 — Update root `README.md`

**File:** `README.md` (existing)

In the `## Repo layout` section, update the `slides/` line:

**Before:**
```
├── slides/            # slide deck
```

**After:**
```
├── slides/            # slide deck (Marp — run `npm run dev` to preview)
```

---

### Files created/modified summary

| File | Action |
|---|---|
| `slides/package.json` | Create |
| `slides/.gitignore` | Create |
| `slides/slides.md` | Create |
| `slides/README.md` | Create |
| `README.md` | Update `## Repo layout` slides line |
