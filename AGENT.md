# Agentic Coding Talk — ATLS 4214

## Project Overview

This repo supports a guest lecture on agentic coding for the University of Colorado ATLAS program, ATLS 4214 (Big Data Architecture). It contains:

- **Slide deck** — covering agentic coding concepts, workflows, and tooling
- **Toy project** — a hands-on demonstration project built using agentic coding techniques

## Development Approach

This project is being built using a dual workflow:

- **Bottom-up**: [entire.io](https://entire.io) records work as it happens
- **Top-down**: Claude Code `plan` → `process-feedback` → `implement` skill loop

## Audience

Undergraduate students in a Big Data Architecture course. Assume familiarity with:
- General programming (Python likely primary language)
- Data pipelines and storage concepts
- Some exposure to cloud services

## Repo Structure

```
/                  # root
├── AGENT.md       # this file
├── slides/        # slide deck source
└── project/       # toy project
```

## Talk Goals

- Demonstrate how agentic coding tools (Claude Code, Cursor, etc.) change the developer workflow
- Show the interplay between top-down planning and bottom-up implementation
- Give students a mental model for working *with* AI agents, not just prompting them
- Live-code or replay a realistic development session
