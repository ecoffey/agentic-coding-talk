# Entire.io

## What is Entire.io?

Entire is a **Git-native session recorder** for AI coding agents. It captures the full context of an agent session — conversation transcript, code changes, token usage, reasoning — and stores it permanently as versioned data in Git alongside your commits.

## Data Model

- **Session** — one complete agent interaction (start → finish). Nested sessions are captured when agents spawn sub-agents (e.g., Claude Code's Task tool). Contains transcript, tool calls, token usage, and line attribution.
- **Checkpoint** — a snapshot tied to a Git commit. The checkpoint ID is embedded as a commit message trailer (`Entire-Checkpoint: a3b2c4d5e6f7`). Two types:
  - *Temporary* — live snapshots on shadow branches (`entire/<sessionID>-<worktreeID>`) during active sessions. Let you rewind mid-session.
  - *Committed* — permanent metadata stored on `entire/checkpoints/v1` branch and synced to GitHub.
- **Repository** — a connected GitHub repo with the Git hook installed.

Sessions and checkpoints have a flexible many-to-many relationship: one commit can span multiple agent sessions; one session can produce multiple commits.

## How Entire.io is Being Used in This Repo

This repo demonstrates a dual agentic coding workflow: **top-down planning** via `_plans/` documents, and **bottom-up recording** via Entire.

**Capturing real sessions alongside plans.** Each feature — slides skeleton, logpipe ingest, query/WHERE filtering — has a corresponding plan in `_plans/` and a committed Entire checkpoint. Together they tell the full story: the plan shows *intent*, the session shows *execution*.

**Nested sessions as a teaching artifact.** Claude Code uses sub-agents (the Task tool) for complex work. Entire captures these as nested sessions within the parent, producing a concrete artifact that illustrates multi-agent orchestration — something that can be shown directly to students during the talk.

**Permanent session history in Git.** The `entire/checkpoints/v1` branch stores all session metadata and syncs to GitHub. The reasoning behind every commit in this repo is reviewable, permanent, and part of the repo's history — a live example of "show your work."

**Token usage as a real data point.** Entire tracks per-checkpoint token costs. These numbers are available as concrete evidence when discussing the economics of agentic coding in the slides.

**Live demo material.** The Entire web app lets you browse session transcripts with tool calls and file diffs. An actual session from building logpipe can be pulled up during the talk to show students what agent reasoning looks like in practice.
