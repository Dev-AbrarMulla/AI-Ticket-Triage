import os
import json
import time
from datetime import datetime, timezone
from typing import List, Dict, Any
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is missing in .env file.")

client = Groq(api_key=GROQ_API_KEY)

# Use an active, widely accessible Groq model ID
# Change this variable to any of the supported model IDs above:
MODEL_NAME = "openai/gpt-oss-20b"# Alternative: "llama3-70b-8192"

def run_classification(
    preprocessed_path: str = "output/preprocessed_tickets.json",
    schema_path: str = "label_schema.json"
):
    with open(preprocessed_path, "r", encoding="utf-8") as f:
        tickets = json.load(f)
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    categories_str = "\n".join([f"- {c['name']}: {c['description']}" for c in schema["categories"]])
    system_prompt = f"""You are an automated support ticket classifier.
Classify the ticket into exactly one category and urgency level.

Categories:
{categories_str}

Allowed Urgency Levels: {schema['urgency_levels']}

Return strictly a valid JSON object matching:
{{
  "category": "<CATEGORY_NAME>",
  "urgency": "<URGENCY_LEVEL>",
  "confidence": <float 0.0-1.0>,
  "suggested_reply": "<Short reply>",
  "reasoning": "<Reasoning>"
}}"""

    triage_results = []
    llm_call_logs = []

    for ticket in tickets:
        start_time = time.time()
        
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": ticket["formatted_prompt_payload"]}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        latency_ms = round((time.time() - start_time) * 1000, 2)
        raw_output = response.choices[0].message.content
        parsed = json.loads(raw_output)

        triage_results.append({
            "ticket_id": ticket["ticket_id"],
            "customer_id": ticket["customer_id"],
            "cleaned_subject": ticket["cleaned_subject"],
            "cleaned_body": ticket["cleaned_body"],
            "triage": parsed
        })

        llm_call_logs.append({
            "call_id": f"CALL-{ticket['ticket_id']}",
            "ticket_id": ticket["ticket_id"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model": MODEL_NAME,
            "latency_ms": latency_ms,
            "prompt_payload": ticket["formatted_prompt_payload"],
            "raw_response": raw_output,
            "status": "SUCCESS"
        })

    with open("output/triage_results.json", "w", encoding="utf-8") as f:
        json.dump(triage_results, f, indent=2)
    with open("output/llm_calls.json", "w", encoding="utf-8") as f:
        json.dump(llm_call_logs, f, indent=2)

    print(f"🤖 Classified {len(tickets)} tickets using '{MODEL_NAME}' -> Created 'triage_results.json' & 'llm_calls.json'")
