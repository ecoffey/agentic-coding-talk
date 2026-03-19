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
