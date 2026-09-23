import json
from datetime import datetime, timezone
from typing import List, Dict, Any

def run_evaluation(
    triage_path: str = "output/triage_results.json",
    routing_path: str = "output/routing_decisions.json",
    schema_path: str = "label_schema.json"
):
    with open(triage_path, "r", encoding="utf-8") as f:
        triage_records = json.load(f)
    with open(routing_path, "r", encoding="utf-8") as f:
        routing_records = json.load(f)
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    # 1. Generate prediction_comparison.json
    comparison = []
    threshold = schema["routing_rules"]["require_human_below_confidence"]

    for tr, rr in zip(triage_records, routing_records):
        t = tr["triage"]
        comparison.append({
            "ticket_id": tr["ticket_id"],
            "predicted_category": t["category"],
            "predicted_urgency": t["urgency"],
            "model_confidence": t["confidence"],
            "threshold_applied": threshold,
            "passed_threshold": t["confidence"] >= threshold,
            "routed_destination": rr["routed_to"],
            "has_routing_flag": rr["routed_to"] == "HUMAN_REVIEW"
        })

    with open("output/prediction_comparison.json", "w", encoding="utf-8") as f:
        json.dump(comparison, f, indent=2)

    # 2. Generate evaluation_report.json
    total = len(triage_records)
    auto_cnt = sum(1 for c in comparison if c["routed_destination"] == "AUTOMATED")
    human_cnt = sum(1 for c in comparison if c["routed_destination"] == "HUMAN_REVIEW")
    avg_conf = sum(c["model_confidence"] for c in comparison) / total if total else 0.0

    eval_report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_tickets": total,
        "automation_rate": round(auto_cnt / total, 2) if total else 0.0,
        "human_review_rate": round(human_cnt / total, 2) if total else 0.0,
        "average_confidence_score": round(avg_conf, 3),
        "queue_breakdown": {
            "automated": auto_cnt,
            "human_review": human_cnt
        }
    }

    with open("output/evaluation_report.json", "w", encoding="utf-8") as f:
        json.dump(eval_report, f, indent=2)

    print("📊 Generated 'prediction_comparison.json' and 'evaluation_report.json'")