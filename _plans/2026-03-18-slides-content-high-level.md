# Slides Content — High-Level Plan

## Starting Prompt

lets use my agentic coding blog post to stub out the slides https://eoinisawesome.com/2026/02/16/agentic-coding.html. Things I want to highlight: 1.) LLMs are a tool, you still have to understand the fundamentals to use them to their full potential. 2.) adopt workflows that still capture "showing your work". This helps yourself, co-workers, and future LLM sessions. 3.) LLMs need a good feedback mechansim. Black-box integration tests are great for this.

---

## § High-Level Plan

### Source material

Blog post: `~/workspace/ecoffey.github.com/_posts/2026-02-16-agentic-coding.md`

Key passages mapped to the three themes:

| Theme | Blog section(s) |
|---|---|
| 1. LLMs are a tool / fundamentals matter | Intro ("bring a value greater than 1"), "Tell It What, Not How", "Looking Forward" |
| 2. Show your work | "Generating Artifacts to React To", "Stay in the Loop" |
| 3. Feedback mechanisms / integration tests | "Invest in Integration Tests" |

---

### Proposed slide structure

```
1.  [Title]               Agentic Coding — existing stub
2.  [Framing]             What is agentic coding?
3.  [Theme 1]             LLMs are a tool
4.  [Theme 1 cont.]       Fundamentals still matter
5.  [Theme 2]             Show your work
6.  [Theme 2 cont.]       Workflows that capture intent
7.  [Theme 2 cont.]       Top-down: the plan & implement workflow
8.  [Theme 2 cont.]       Bottom-up: entire.io
9.  [Theme 3]             Give the agent a feedback loop
10. [Theme 3 cont.]       Black-box integration tests
11. [Meta]                This talk, built with these tools
12. [Demo intro]          Live demo: building `logpipe` — existing stub
13. [Q&A]                 Q&A / Resources — existing stub
```

13 slides total. Theme 2 ("show your work") expands to 4 slides to cover both the top-down plan/implement workflow and the bottom-up entire.io capture. A meta slide (11) bridges the concepts section and the live demo by showing these workflows applied to building this talk itself.

---

### Slide-by-slide content outline

**Slide 1 — Title** *(existing, no change)*

---

**Slide 2 — What is agentic coding?**

Framing: not autocomplete, not a search engine. An agent that can read your codebase, write files, run tests, and iterate.

Key line from blog: *"LLM tooling can be a multiplier for your effectiveness — you just have to make sure you are bringing a value greater than 1 to multiply by."*

---

**Slide 3 — Theme 1: LLMs are a tool**

- They shift the engineer's role toward design, requirements, and testing
- Focus on *what* you want, not *how* — describe the outcome, constraints, and context
- Leave implementation to the tool unless the "how" is critical

---

**Slide 4 — Fundamentals still matter**

- The tool can leverage the "language" you've put in place in a codebase
- Wrestling with problems builds understanding; that understanding lets you direct the tool well
- Concern for new engineers: how do we ensure foundational experience is still built?

> *"These tools are great at removing accidental friction, but not all friction is bad."*

---

**Slide 5 — Theme 2: Show your work**

- LLMs strongly incentivize solo work — resist this
- Pairing, review, and onboarding build the team's "shared reality"
- Process and tooling need to shift focus: not just *generating* artifacts, but running them through the team's shared reality viewpoint

---

**Slide 6 — Workflows that capture intent**

Concrete practices:
- Generate plans/writeups first → something concrete to react to and edit
- Stage changes between chunks of work so the working diff always shows what the agent is currently doing
- Review everything before it lands — never be surprised by a commit

---

**Slide 7 — Top-down: the plan & implement workflow**

The `plan` → `process-feedback` → `implement` loop:
- Write a high-level plan *before* touching code — iterate your thinking cheaply
- Share the plan with teammates for early feedback before any code exists
- The plan file lives in the repo: future you (and future LLM sessions) can read it
- Forces you to articulate *what* and *why*, not just let the agent do *how*

Motivations: shows your work, keeps the team in the loop, maintains shared context

---

**Slide 8 — Bottom-up: entire.io**

[entire.io](https://entire.io) records your coding session as it happens:
- Captures the *actual* sequence of decisions, not a cleaned-up post-hoc summary
- Complements the plan: the plan is the intent, the recording is the reality
- Useful for your own review, async teammates, and future LLM sessions with full context

Together, top-down planning + bottom-up recording = a workflow where the work is legible to others.

---

**Slide 9 — Theme 3: Give the agent a feedback loop**

- LLMs do well with objective measures of correctness they can react to
- A running test suite is the tightest feedback loop you can give an agent
- Integration tests > unit tests: harder to "fake", cast a wider net

---

**Slide 10 — Black-box integration tests**

Virtuous cycle:
```
write seed tests → agent makes them pass
               ↓
        agent writes more tests
               ↓
      better coverage + honest signal
```

For `logpipe`: feed in raw log lines, assert on query output — no mocking internals.

---

**Slide 11 — This talk, built with these tools**

Meta: this presentation and `logpipe` were built using the exact workflows just described.

- **Top-down**: `plan` → `process-feedback` → `implement` skill loop — plan files are in `_plans/` in this repo, you can read them
- **Bottom-up**: entire.io recorded the sessions — you can watch how the work actually unfolded
- Both streams are in the repo: the intent (plans) and the reality (recording)

Punchline: *the talk is its own demo*. You don't have to take my word for any of this.

---

**Slide 12 — Live demo: building `logpipe`** *(existing stub, content TBD)*

---

**Slide 13 — Q&A / Resources** *(existing stub)*

Resources to add:
- Link to blog post
- Link to this repo

---

### Documentation impact

| File | Change |
|---|---|
| `slides/slides.md` | Replace 4-stub skeleton with 13-slide content outline above |
| Root `README.md` | No change needed |

---

### Feedback Log

> **Line 41** — after the original 10-slide structure:
> `^^ I also want a specific set of slides about the "top down" "plan & implement" skills, and their motivations (tl;dr shows your work, iterate your thinking before coding, can get early feedback from team mates, helps maintain shared context), and also entire.io and what its capturing ^^`
> → Added slides 7 (top-down: plan & implement workflow) and 8 (bottom-up: entire.io) within Theme 2. Total expanded from 10 to 12 slides.

> **Line 43** — after the 12-slide structure:
> `^^ I also want a set of slides about how I used the "plan & execute" skills + entire.io to build out this presentation and toy logpipe project itself. A bit of a "meta" slide. ^^`
> → Added slide 11 ("This talk, built with these tools") — a meta bridge between the concepts section and the live demo. References the `_plans/` files and entire.io recording in the repo as evidence. Total expanded from 12 to 13 slides.
