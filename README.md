# AI Support Ticket Triage Pipeline

An end-to-end, replayable customer support ticket triage engine powered by openai/gpt-oss-20b. The system ingests local customer support tickets, cleans and preprocesses text, classifies tickets into categories and urgency levels, drafts customer responses, and routes low-confidence or high-risk cases to a human review queue.

---

## Features

* **Modular 10-Stage Architecture**: Clear separation of responsibilities across preprocessing, LLM call logging, confidence routing, reply generation, evaluation reporting, and schema validation.
* **Structured Output via Groq**: Enforces strict JSON output schemas for category assignment, urgency scoring, confidence metrics, and reasoning.
* **Configurable Taxonomy**: All categories, urgency levels, confidence thresholds, and auto-flagging rules are defined externally in `label_schema.json`.
* **Confidence & Safety Routing**: Automatically flags low-confidence predictions or `CRITICAL` urgency tickets for human review.
* **Complete Call Auditing**: Logs raw prompt payloads, model responses, latency, and timestamps into structured JSON files for observability.
* **Interactive Operator CLI**: Command-line interface (`cli.py`) for operators to run pipelines, inspect pending queues, manually resolve flagged tickets, and view execution analytics.

---

## Pipeline Architecture & Output Artifacts

The pipeline generates 8 machine-readable artifacts during execution:

| Artifact File | Description |
| :--- | :--- |
| `tickets.json` | Input batch of raw customer support tickets. |
| `label_schema.json` | Input taxonomy, confidence thresholds, and routing rules. |
| `output/preprocessed_tickets.json` | Normalized, cleaned ticket payloads with word and character metrics. |
| `output/triage_results.json` | Parsed LLM classification results, confidence scores, and reasoning. |
| `output/llm_calls.json` | Operational audit logs including latency, model ID, and raw responses. |
| `output/routing_decisions.json` | Final routing determinations (`AUTOMATED` vs. `HUMAN_REVIEW`). |
| `output/prediction_comparison.json` | Per-ticket breakdown comparing confidence scores against defined thresholds. |
| `output/evaluation_report.json` | System metrics including automation rate, average confidence, and queue splits. |

---

## Directory Structure

```text
ticket_pipeline/
│
├── .env                          # API credentials (GROQ_API_KEY)
├── .gitignore                    # Git exclusion patterns
├── label_schema.json             # Taxonomy configuration
├── tickets.json                  # Batch input tickets
│
├── preprocess.py                 # Stage 1: Preprocessing & normalization
├── classify.py                   # Stage 2: Groq LLM classification & call logging
├── router.py                     # Stage 3: Confidence routing & reply formatting
├── evaluator.py                  # Stage 4: Evaluation & prediction metrics
├── validator.py                  # Stage 5: Output artifact schema validator
├── main.py                       # Orchestrator script
├── cli.py                        # Interactive Operator Console CLI
│
└── output/                       # Output artifacts directory
    ├── preprocessed_tickets.json
    ├── triage_results.json
    ├── llm_calls.json
    ├── routing_decisions.json
    ├── prediction_comparison.json
    ├── evaluation_report.json
    ├── automated.json
    └── human_review.json
