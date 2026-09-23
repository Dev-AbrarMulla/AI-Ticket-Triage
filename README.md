# AI Support Ticket Triage Pipeline

A replayable pipeline that triages customer support tickets with an LLM (`openai/gpt-oss-20b` via Groq). It cleans each ticket, classifies it by category and urgency, drafts a reply, and routes low-confidence or critical tickets to a human review queue.

## How it works

```
tickets.json ──► preprocess ──► classify ──► route ──► evaluate ──► validate
```

| Stage | File | What it does |
|-------|------|--------------|
| 1. Preprocess | `preprocess.py` | Strips HTML, normalizes whitespace, computes word/char counts, flags urgency keywords, builds the prompt payload |
| 2. Classify | `classify.py` | Calls the LLM in JSON mode for category, urgency, confidence, suggested reply and reasoning; logs every call (latency, model, raw response) |
| 3. Route | `router.py` | Sends a ticket to `HUMAN_REVIEW` if confidence is below the threshold or urgency is `CRITICAL`; otherwise `AUTOMATED` |
| 4. Evaluate | `evaluator.py` | Writes per-ticket prediction comparison and summary metrics |
| 5. Validate | `validator.py` | Checks that all artifacts exist, are non-empty, and that every category and urgency is valid per the schema |

`main.py` runs all five stages in order. `cli.py` is an interactive operator console for working with the pipeline and the review queue.

## Configuration

Categories, urgency levels, the confidence threshold and the auto-flag rule are defined in `label_schema.json`, not in code. Change the taxonomy or thresholds there.

Rou
