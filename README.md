# Agentic Coding Talk — ATLS 4214

Materials for a guest lecture on agentic coding for the University of Colorado ATLAS program, [ATLS 4214: Big Data Architecture](https://www.colorado.edu/atlas/academics/undergraduate/bs-ctd-focus-electives).

## What's here

This repo contains two things built concurrently:

- **`slides/`** — the slide deck for the talk
- **`project/`** — a toy log analytics pipeline, used as a live demo

The project is built *using* the techniques described in the talk: a top-down planning loop paired with bottom-up implementation driven by an AI coding agent.

## The toy project

`project/` is a small CLI tool called `logpipe` that ingests web server logs and lets you query aggregated metrics — error rates, request counts, latency percentiles.

It's intentionally simple, but built the way a real project should be: **black-box integration tests written first**, implementation second. The tests are the contract; the agent's job is to make them pass.

See [`project/README.md`](project/README.md) for setup and usage instructions.

## The talk

The core argument: agentic coding tools don't change *what* good software looks like — clear interfaces, fast feedback loops, readable code. They change *how fast* you can get there, and *where* you spend your attention.

Topics covered:

1. What "agentic coding" actually means (vs. autocomplete)
2. Top-down planning with an AI agent
3. Bottom-up implementation driven by tests
4. Where agents excel and where they still need you
5. Live demo: building `logpipe` from scratch

## Repo layout

```
├── README.md          # you are here
├── AGENT.md           # context for the AI coding agent working in this repo
├── slides/            # slide deck
└── project/           # logpipe — the toy demo project
```
