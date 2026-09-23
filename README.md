# AI Support Ticket Triage Pipeline

A replayable pipeline that triages customer support tickets with an LLM (`openai/gpt-oss-20b` via Groq). It cleans each ticket, classifies it by category and urgency, drafts a reply, and routes low-confidence or critical tickets to a human review queue.

## How it works

```
tickets.json ──► preprocess ──► classify ──► route ──► evaluate ──► validate
```

| Stage | File | What it does |
|-------|------|--------------|
| 1.Preprocess | `preprocess.py` | Strips HTML, normalizes whitespace, computes word/char counts, flags urgency keywords, builds the prompt payload |
| 2. Classify | `classify.py` | Calls the LLM in JSON mode for category, urgency, confidence, suggested reply and reasoning; logs every call (latency, model, raw response) |
| 3. Route | `router.py` | Sends a ticket to `HUMAN_REVIEW` if confidence is below the threshold or urgency is `CRITICAL`; otherwise `AUTOMATED` |
| 4. Evaluate | `evaluator.py` | Writes per-ticket prediction comparison and summary metrics |
| 5. Validate | `validator.py` | Checks that all artifacts exist, are non-empty, and that every category and urgency is valid per the schema |

`main.py` runs all five stages in order. `cli.py` is an interactive operator console for working with the pipeline and the review queue.

## Configuration

Categories, urgency levels, the confidence threshold and the auto-flag rule are defined in `label_schema.json`, not in code. Change the taxonomy or thresholds there.

Routing rules:
- confidence below `routing_rules.require_human_below_confidence` → human review
- urgency `CRITICAL` (when `routing_rules.auto_flag_critical` is true) → human review
- human-review replies are prefixed with `[DRAFT FOR AGENT REVIEW]`

## Setup

Requires Python 3.9+ and a [Groq API key](https://console.groq.com).

```bash
git clone https://github.com/Dev-AbrarMulla/AI-Ticket-Triage.git
cd AI-Ticket-Triage

python -m venv .venv
# Windows:   .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate

pip install -r requirements.txt
```

Create a `.env` file (see `.env.example`):

```
GROQ_API_KEY=your_key_here
```

## Usage

Run the full pipeline:

```bash
python main.py
```

Run the operator console:

```bash
python cli.py
```

Each stage can also be run on its own by importing its function (`run_preprocessing`, `run_classification`, `run_routing_and_reply`, `run_evaluation`, `run_validation_command`), or by running `python validator.py` to re-check existing outputs.

## Output artifacts

Generated in `output/` (git-ignored):

| File | Description |
|------|-------------|
| `preprocessed_tickets.json` | Cleaned tickets with word/char counts and urgency keyword flag |
| `triage_results.json` | Parsed LLM results: category, urgency, confidence, reply, reasoning |
| `llm_calls.json` | Audit log: timestamp, model, latency, prompt and raw response |
| `routing_decisions.json` | Per-ticket routing decision, reason and final response |
| `automated.json` | Tickets routed to automation |
| `human_review.json` | Tickets routed to the human review queue |
| `prediction_comparison.json` | Per-ticket confidence compared against thresholds |
| `evaluation_report.json` | Summary metrics: automation rate, average confidence, queue split |

Inputs are `tickets.json` (raw tickets) and `label_schema.json` (taxonomy and routing rules).

## Project structure

```
AI-Ticket-Triage/
├── main.py             # Runs the full pipeline
├── cli.py              # Interactive operator console
├── preprocess.py       # Stage 1
├── classify.py         # Stage 2
├── router.py           # Stage 3
├── evaluator.py        # Stage 4
├── validator.py        # Stage 5
├── label_schema.json   # Taxonomy, thresholds, routing rules
├── tickets.json        # Input tickets
├── requirements.txt
├── .env.example
└── output/             # Generated artifacts
```

## Known limitations

- A malformed or failed LLM response for one ticket aborts the whole batch; there is no per-ticket retry or fallback.
- The model's category and urgency are only checked after the run (by `validator.py`), not at classification time.
- Confidence is self-reported by the model and is not calibrated against labeled data.
- `has_urgency_keywords` is computed during preprocessing but not used in routing.
- Keyword matching is substring-based (for example "down" also matches "download").
