---
marp: true
theme: default
paginate: true
---

# Agentic Coding
### How AI agents change the way we build software

---

# What is agentic coding?

Not autocomplete. Not a search engine.

An agent that can **read your codebase**, **write files**, **run tests**, and **iterate** — with you in the loop.

> "LLM tooling can be a multiplier for your effectiveness — you just have to make sure you are bringing a value greater than 1 to multiply by."

---

# What is `logpipe`?

A CLI tool for parsing and querying web server access logs:

```bash
$ logpipe query "status >= 400 AND response_time > 1.0" access.log
```

- Reads Apache/nginx logs → structured records
- SQL-like filter, window, and aggregate pipeline
- Built live during this talk — every theme will point back to it

---

# Theme 1: LLMs are a tool

- They shift the engineer's role toward **design**, **requirements**, and **testing**
- Tell it *what* you want, not *how* to do it
  - Describe the outcome, constraints, and context
  - Leave implementation to the tool unless the "how" is critical
- What makes code legible to teammates makes it legible to LLMs too — naming, conventions, correct abstractions, tests all apply

<!--
"semantically compact language": the next slide has a concrete example from the logpipe plans (op: str → op: Op). Use that as the anchor.
The point to land here: there is a kernel of truth to "hardest part of software is naming". We wrestle with language and naming because the right
name helps point to the right concepts for other people to understand. An LLM doesn't "understand", but it has enough parameters to look like it
does — and that is good enough for getting it to make reasonable inferences.
-->

---

# Example: naming pays off immediately

From [`_plans/2026-03-21-querying-filtering-high-level.md`](_plans/2026-03-21-querying-filtering-high-level.md), inline comment on the plan:

> *"can we make this strong with a type instead of just str?"*

```python
# before — in the plan draft
op: str

# after — updated before a single line of code was written
Op = Literal["=", "!=", "<", ">", "<=", ">=", "~"]
op: Op
```

One observation on a plan doc. The improvement is obvious to both reviewer and LLM.

---

# Fundamentals still matter

- Wrestling with problems builds understanding — that understanding is what lets you direct the tool well
- *"These tools are great at removing accidental friction, but not all friction is bad."*
- Open question: how do we ensure new engineers still build foundational experience?

<!--
friction: "accidental friction is earned" — the struggle with a tool or concept is how it stops being opaque and becomes mechanical. Once it's mechanical,
it's no longer in your way; it's a building block for higher-level intent. You don't need to hand-tune a regex engine to use regexes well, but you do need
to have wrestled with them enough that the abstractions feel solid underfoot.

Analogy: being able to open the hood of a car and recognize the major moving pieces of the engine. You're not rebuilding it from scratch — but if something
goes wrong, or you want to modify something, you're not helpless either. That orientation is what lets you direct a tool rather than just be carried by it.

foundational experience: I'm still not sure what that looks like long term. I don't think we, as an industry, can just say "oh well juniors shouldn't use
these tools until they've struggled". But I do think we can do things like pair on the planning and prompting. Or have them manually implement a plan that
we helped them come up with.
-->

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

# Example: reshaping a design in the plan

From [`_plans/2026-03-21-querying-filtering-high-level.md`](_plans/2026-03-21-querying-filtering-high-level.md):

> *"I want to make a fundamental change: let's do something like SQL — FROM → WHERE → AGGREGATE → SELECT → HAVING"*

> *"let's just have query take a string, since we're going to make these more complex and combining multiple flags would be confusing"*

Both were comments on the plan doc. The agent updated the architecture and CLI design — **before any code existed**.

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

# Example: tests the agent can actually use

From [`_plans/2026-03-19-logpipe-skeleton-high-level.md`](_plans/2026-03-19-logpipe-skeleton-high-level.md):

> *"Tests invoke the CLI via subprocess against a real file or stdin. No mocking."*

The realization in [`project/tests/conftest.py`](project/tests/conftest.py) and [`project/tests/test_query.py`](project/tests/test_query.py):

```python
# conftest.py — runs the real CLI
result = subprocess.run([sys.executable, "-m", "logpipe", *args], ...)

# test_query.py — reads like a spec
def test_filter_status_eq(run, multi_log):
    stdout, _, code = run("query", "status = 200", str(multi_log))
    assert code == 0
```

The plan says *how to work*. The code is the audit — you can confirm the agent followed through.

---

# Live demo: building `logpipe`

*This talk was built with exactly these workflows — the `_plans/` are in the repo, entire.io recorded the sessions. You don't have to take my word for any of it.*

<!--
demo0
WHERE plans, demo1
WINDOW plans, demo2
AGGREGATE plans, demo3
-->

---

# Live demo: entire.io

<!--
screenshare entire.io for this repo and scroll around
-->

---

# Live demo: EasyPost intlb testing

<!--
switch to work laptop and show intlb presentation / live demo
-->

---

# Q&A / Resources

- Blog post: [eoinisawesome.com/2026/02/16/agentic-coding.html](https://eoinisawesome.com/2026/02/16/agentic-coding.html)
- Semantic Compression: [caseymuratori.com/blog_0015](https://caseymuratori.com/blog_0015)
- This repo: [github.com/ecoffey/agentic-coding-talk](https://github.com/ecoffey/agentic-coding-talk)
- [Marp](https://marp.app/) — slide tool used for this deck
- [entire.io](https://entire.io) — bottom-up session recording
