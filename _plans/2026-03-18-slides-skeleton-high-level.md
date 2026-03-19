# Slides Skeleton — High-Level Plan

## Starting Prompt

slides: I want to use a tool to either display the slides in my terminal, or in a browser. The content of the slides should be markdown (or something similar) that you can edit directly for me. This plan is just for setting up the "skeleton" of the slides/ directory

---

## § High-Level Plan

### Tool Recommendation: Marp

**Marp** (`@marp-team/marp-cli`) is the right fit:

- Slides are a single Markdown file, `---` separates slides — trivially editable
- `marp --preview slides.md` opens a live-reloading browser view
- `marp slides.md -o slides.html` exports a self-contained HTML file (shareable with students, no install needed)
- VS Code extension gives split-pane live preview while editing
- npm install, no heavy framework (no Vue, no build step)

For terminal viewing: `patat` (`brew install patat`) reads the same Markdown file with minimal config. Worth noting in the README as an optional alternative for SSH/headless environments.

---

### Directory Layout

```
slides/
├── slides.md          # all slide content — the only file that changes day-to-day
├── theme.css          # optional custom CSS overrides (colors, fonts)
├── package.json       # pins marp-cli version, defines npm scripts
└── README.md          # how to view: browser (marp), terminal (patat), export to HTML
```

---

### `package.json` scripts

```json
{
  "scripts": {
    "dev":    "marp --preview slides.md",
    "build":  "marp slides.md -o dist/slides.html",
    "pdf":    "marp slides.md -o dist/slides.pdf"
  },
  "devDependencies": {
    "@marp-team/marp-cli": "^4"
  }
}
```

`npm run dev` → live browser preview
`npm run build` → `dist/slides.html` (self-contained, shareable)

---

### `slides.md` skeleton structure

```markdown
---
marp: true
theme: default
paginate: true
---

<!-- Title slide -->
# Agentic Coding
### How AI agents change the way we build software
ATLS 4214 — Big Data Architecture

---

<!-- Section marker pattern -->
# Part 1: What is agentic coding?

---

<!-- Content slide pattern -->
## Slide title

- Bullet
- Bullet

---
```

Slides are separated by `---`. YAML frontmatter at the top configures Marp globally. Per-slide directives go in HTML comments.

---

### Data/UX Flow

```
slides.md  ──(marp --preview)──▶  browser (live reload)
           ──(marp -o)──────────▶  dist/slides.html  (static)
           ──(marp -o)──────────▶  dist/slides.pdf

slides.md  ──(patat)────────────▶  terminal (optional, brew install patat)
```

---

### Talk outline for initial slide stubs

Stubs (titles only, no content) for these sections:

1. Title
2. What is agentic coding? (vs. autocomplete)
6. Live demo: building `logpipe`
7. Q&A / Resources

---

### Documentation impact

| File | Change |
|---|---|
| `README.md` (root) | Update `slides/` description to mention Marp + `npm run dev` |
| `slides/README.md` | New — student-facing setup instructions |

---

### Feedback Log

> **Line 114** — on the talk outline stubs list:
> `^^ for the stubs, lets use just keep 1, 2, 6, & 7 ^^`
> → Removed stubs 3 (dual workflow), 4 (where agents excel), 5 (where you still need a human) from the initial skeleton. Keeping only: Title, What is agentic coding?, Live demo, Q&A.
