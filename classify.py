import json
import os
import time
from datetime import datetime, timezone

from dotenv import load_dotenv
from groq import Groq

MODEL_NAME = "openai/gpt-oss-20b"

SYSTEM_PROMPT = """You are a support ticket classifier.
Classify the ticket into exactly one category and one urgency level.

Categories:
{categories}

Allowed urgency levels: {urgency_levels}

Respond with a JSON object only:
{{"category": "<CATEGORY_NAME>", "urgency": "<URGENCY_LEVEL>", "confidence": <float 0.0-1.0>, "suggested_reply": "<short reply to the customer>", "reasoning": "<one or two sentences>"}}"""

FALLBACK_TRIAGE = {
    "category": "UNCLASSIFIED",
    "urgency": "UNKNOWN",
    "confidence": 0.0,
    "suggested_reply": "",
    "reasoning": "",
}


def _build_system_prompt(schema: dict) -> str:
    categories = "\n".join(f"- {c['name']}: {c['description']}" for c in schema["categories"])
    return SYSTEM_PROMPT.format(
        categories=categories,
        urgency_levels=", ".join(schema["urgency_levels"]),
    )


def _validate(triage: dict, schema: dict) -> None:
    valid_categories = {c["name"] for c in schema["categories"]}
    if triage.get("category") not in valid_categories:
        raise ValueError(f"invalid category: {triage.get('category')!r}")
    if triage.get("urgency") not in schema["urgency_levels"]:
        raise ValueError(f"invalid urgency: {triage.get('urgency')!r}")
    triage["confidence"] = min(max(float(triage["confidence"]), 0.0), 1.0)


def run_classification(
    preprocessed_path: str = "output/preprocessed_tickets.json",
    schema_path: str = "label_schema.json",
    output_dir: str = "output",
) -> None:
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set. Add it to your .env file.")
    client = Groq(api_key=api_key)

    with open(preprocessed_path, encoding="utf-8") as f:
        tickets = json.load(f)
    with open(schema_path, encoding="utf-8") as f:
        schema = json.load(f)

    system_prompt = _build_system_prompt(schema)
    triage_results, call_logs = [], []

    for ticket in tickets:
        payload = ticket["formatted_prompt_payload"]
        raw_output, error = None, None
        started = time.perf_counter()

        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": payload},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            raw_output = response.choices[0].message.content
            triage = json.loads(raw_output)
            _validate(triage, schema)
        except Exception as exc:  # failed tickets go to human review instead of aborting the batch
            error = str(exc)
            triage = {**FALLBACK_TRIAGE, "reasoning": f"Classification failed: {error}"}

        latency_ms = round((time.perf_counter() - started) * 1000, 2)

        triage_results.append({
            "ticket_id": ticket["ticket_id"],
            "customer_id": ticket["customer_id"],
            "cleaned_subject": ticket["cleaned_subject"],
            "cleaned_body": ticket["cleaned_body"],
            "triage": triage,
        })
        call_logs.append({
            "call_id": f"CALL-{ticket['ticket_id']}",
            "ticket_id": ticket["ticket_id"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model": MODEL_NAME,
            "latency_ms": latency_ms,
            "prompt_payload": payload,
            "raw_response": raw_output,
            "status": "FAILED" if error else "SUCCESS",
            "error": error,
        })

    os.makedirs(output_dir, exist_ok=True)
    for name, data in (("triage_results.json", triage_results), ("llm_calls.json", call_logs)):
        with open(os.path.join(output_dir, name), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    failed = sum(1 for log in call_logs if log["status"] == "FAILED")
    print(f"Classified {len(tickets)} tickets with {MODEL_NAME} ({failed} failed)")
