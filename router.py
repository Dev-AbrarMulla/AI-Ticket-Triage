import json
from typing import List, Dict, Any

def run_routing_and_reply(
    triage_path: str = "output/triage_results.json",
    schema_path: str = "label_schema.json"
):
    with open(triage_path, "r", encoding="utf-8") as f:
        triage_records = json.load(f)
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    threshold = schema["routing_rules"]["require_human_below_confidence"]
    auto_critical = schema["routing_rules"]["auto_flag_critical"]

    routing_decisions = []
    automated_queue = []
    human_queue = []

    for item in triage_records:
        t = item["triage"]
        reasons = []

        if t["confidence"] < threshold:
            reasons.append(f"Low confidence ({t['confidence']:.2f} < {threshold})")
        if auto_critical and t["urgency"] == "CRITICAL":
            reasons.append("Critical urgency auto-flagged")

        needs_human = len(reasons) > 0
        dest = "HUMAN_REVIEW" if needs_human else "AUTOMATED"
        reason_str = " | ".join(reasons) if needs_human else None

        # Reply Generation logic
        if dest == "AUTOMATED":
            final_reply = t["suggested_reply"]
        else:
            final_reply = f"[DRAFT FOR AGENT REVIEW]: {t['suggested_reply']}"

        record = {
            "ticket_id": item["ticket_id"],
            "routed_to": dest,
            "routing_reason": reason_str,
            "final_response": final_reply
        }
        routing_decisions.append(record)

        combined_item = {**item, **record}
        if dest == "AUTOMATED":
            automated_queue.append(combined_item)
        else:
            human_queue.append(combined_item)

    with open("output/routing_decisions.json", "w", encoding="utf-8") as f:
        json.dump(routing_decisions, f, indent=2)
    with open("output/automated.json", "w", encoding="utf-8") as f:
        json.dump(automated_queue, f, indent=2)
    with open("output/human_review.json", "w", encoding="utf-8") as f:
        json.dump(human_queue, f, indent=2)

    print(f"🔀 Routed {len(automated_queue)} tickets to AUTOMATED, {len(human_queue)} to HUMAN_REVIEW")
