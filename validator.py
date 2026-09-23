import os
import json
from typing import List, Dict, Any

REQUIRED_ARTIFACTS = [
    "tickets.json",
    "label_schema.json",
    "output/preprocessed_tickets.json",
    "output/triage_results.json",
    "output/llm_calls.json",
    "output/routing_decisions.json",
    "output/prediction_comparison.json",
    "output/evaluation_report.json"
]

def run_validation_command() -> bool:
    print("🔍 [CHECK] Running Validation Command on Pipeline Artifacts...")
    errors: List[str] = []

    # 1. File existence check
    for path in REQUIRED_ARTIFACTS:
        if not os.path.exists(path):
            errors.append(f"Missing required artifact: {path}")
        elif os.path.getsize(path) == 0:
            errors.append(f"Artifact is empty: {path}")

    if errors:
        print("❌ Validation Failed:")
        for err in errors:
            print(f"  - {err}")
        return False

    # 2. Schema compliance check
    with open("label_schema.json", "r", encoding="utf-8") as f:
        schema = json.load(f)
    
    valid_categories = {c["name"] for c in schema["categories"]}
    valid_urgencies = set(schema["urgency_levels"])

    with open("output/triage_results.json", "r", encoding="utf-8") as f:
        triage_data = json.load(f)

    for item in triage_data:
        t = item.get("triage", {})
        if t.get("category") not in valid_categories:
            errors.append(f"Invalid category '{t.get('category')}' in ticket {item.get('ticket_id')}")
        if t.get("urgency") not in valid_urgencies:
            errors.append(f"Invalid urgency '{t.get('urgency')}' in ticket {item.get('ticket_id')}")

    if errors:
        print("❌ Data Integrity Validation Failed:")
        for err in errors:
            print(f"  - {err}")
        return False

    print("✅ All 8 Artifacts Validated Successfully!")
    return True

if __name__ == "__main__":
    run_validation_command()