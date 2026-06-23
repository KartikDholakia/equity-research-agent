---
description: Active learning review after a coding task — surfaces non-obvious decisions, tests understanding with retrieval questions, suggests a hands-on modification.
---

Run a structured learning review on the coding task just completed.
Goal: make sure the user understands the *why* behind what was built, not just the *what*.

## Process

### Step 1 — Identify what to review
Look at the most recent code changes (git diff or files just written).
If the task involved multiple files, focus on the 1-2 files with the most
non-obvious AI/architectural decisions. Ignore boilerplate.

### Step 2 — Flag 2-3 non-obvious decisions
Pick decisions that:
- Could have been done differently (there was a real choice)
- Have a non-obvious reason (not self-evident from the code)
- Will matter when extending or debugging the system later

Present them as: **"We did X. We could have done Y. Here's why X:"**
Keep each explanation to 2-3 sentences. No paragraphs.

### Step 3 — Ask the user to explain it back (before showing answers)
Pick ONE of the decisions from Step 2. Ask the user to explain it in their
own words BEFORE you confirm or correct. Wait for their response.
Example: "Before I confirm — why do you think we put cache_control on the
system prompt specifically, rather than the user message?"

### Step 4 — Respond to their explanation
If correct: confirm and add one detail they may have missed.
If partially correct: acknowledge what they got right, then fill the gap precisely.
If wrong: correct it directly without softening — explain the right mental model.

### Step 5 — Ask one "what would happen if" question
This must require applying understanding, not recalling a fact.
Good form: "What breaks if we [change one specific thing]?"
Bad form: "What is [definition]?"
Wait for their response before answering.

### Step 6 — Suggest one modification to try
Give the user one small, concrete change to make themselves in the code —
something that takes 5-10 minutes. The change should either:
- Reinforce the key concept from Step 2, or
- Break something intentionally so they see the failure mode

Example: "Try removing the cache_control block from quality_agent.py,
run two analyses back-to-back, and compare the token counts in the
API response. Then put it back."

## Tone
Direct. No praise for correct answers. Correct wrong answers without hedging.
The goal is understanding, not encouragement.

## What NOT to do
- Do not summarise everything that was built — only the non-obvious parts
- Do not ask definition questions ("what is RAG?") — ask application questions
- Do not move to the next step until the user has responded to the current one
- Do not skip Step 3 — passive reading of Step 2 is not enough
