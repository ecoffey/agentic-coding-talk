# Slides Content — Implementation Detail

## § Implementation Detail

No tests. One file changes: `slides/slides.md` is replaced in full.

---

### Step 1 — Replace `slides/slides.md`

**File:** `slides/slides.md` (full replacement)

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

Not autocomplete. Not a search engine.

An agent that can **read your codebase**, **write files**, **run tests**, and **iterate** — with you in the loop.

> "LLM tooling can be a multiplier for your effectiveness — you just have to make sure you are bringing a value greater than 1 to multiply by."

---

# Theme 1: LLMs are a tool

- They shift the engineer's role toward **design**, **requirements**, and **testing**
- Tell it *what* you want, not *how* to do it
  - Describe the outcome, constraints, and context
  - Leave implementation to the tool unless the "how" is critical
- The tool leverages the "language" you've already put in place

---

# Fundamentals still matter

- Wrestling with problems builds understanding — that understanding is what lets you direct the tool well
- *"These tools are great at removing accidental friction, but not all friction is bad."*
- Open question: how do we ensure new engineers still build foundational experience?

---

# Theme 2: Show your work

LLMs strongly incentivize **solo work** — resist this.

- Pairing builds shared context and surfaces what you didn't know you didn't know
- Code review builds collective ownership
- The goal: a team with a **shared reality** of what they own and operate

Process and tooling should shift focus: not just *generating* artifacts, but running them through that shared reality.

---

# Workflows that capture intent

Concrete practices:

- **Generate artifacts to react to** — a plan or writeup sidesteps the blank page problem; editing is easier than creating from nothing
- **Stage changes between chunks** — the working diff always shows what the agent is currently doing
- **Review before it lands** — never be surprised by a commit

---

# Top-down: plan → implement

The `plan` → `process-feedback` → `implement` loop:

- Write a high-level plan *before* touching code — iterate your thinking cheaply
- Share the plan for early feedback **before any code exists**
- Plan files live in the repo: future you (and future LLM sessions) can read them
- Forces you to articulate *what* and *why*, not just let the agent decide *how*

---

# Bottom-up: entire.io

[entire.io](https://entire.io) records your coding session as it happens:

- Captures the *actual* sequence of decisions — not a cleaned-up post-hoc summary
- Complements the plan: **the plan is the intent, the recording is the reality**
- Useful for your own review, async teammates, and future LLM sessions

Top-down + bottom-up = a workflow where the work is **legible to others**

---

# Theme 3: Give the agent a feedback loop

LLMs do well with **objective measures of correctness** they can react to.

- A running test suite is the tightest feedback loop you can give an agent
- Integration tests > unit tests
  - Harder to "fake"
  - Cast a wider net across the system

---

# Black-box integration tests

Virtuous cycle:

```
write seed tests → agent makes them pass
               ↓
        agent writes more tests
               ↓
      better coverage + honest signal
```

For `logpipe`: feed in raw log lines, assert on query output — **no mocking internals**.

---

# This talk, built with these tools

This presentation and `logpipe` were built using the exact workflows just described:

- **Top-down**: `plan` → `process-feedback` → `implement` — plan files are in `_plans/` in this repo
- **Bottom-up**: entire.io recorded the sessions — you can watch how the work unfolded

The talk is its own demo. You don't have to take my word for any of this.

---

# Live demo: building `logpipe`

<!-- TODO: content -->

---

# Q&A / Resources

- Blog post: [eoinisawesome.com/2026/02/16/agentic-coding.html](https://eoinisawesome.com/2026/02/16/agentic-coding.html)
- This repo: <!-- TODO: add repo URL when published -->
- [Marp](https://marp.app/) — slide tool used for this deck
- [entire.io](https://entire.io) — bottom-up session recording
```

---

### Files changed summary

| File | Action |
|---|---|
| `slides/slides.md` | Full replacement — 4 stubs → 13 slides with content |
