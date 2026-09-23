import json
import os


def _routing_reasons(triage: dict, threshold: float, flag_critical: bool) -> list[str]:
    reasons = []
    if triage["confidence"] < threshold:
        reasons.append(f"Low confidence ({triage['confidence']:.2f} < {threshold})")
    if flag_critical and triage["urgency"] == "CRITICAL":
        reasons.append("Critical urgency auto-flagged")
    return reasons


def _write_json(path: str, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def run_routing_and_reply(
    triage_path: str = "output/triage_results.json",
    schema_path: str = "label_schema.json",
    output_dir: str = "output",
) -> None:
    with open(triage_path, encoding="utf-8") as f:
        records = json.load(f)
    with open(schema_path, encoding="utf-8") as f:
        rules = json.load(f)["routing_rules"]

    threshold = rules["require_human_below_confidence"]
    flag_critical = rules["auto_flag_critical"]

    decisions, automated, human_review = [], [], []

    for item in records:
        triage = item["triage"]
        reasons = _routing_reasons(triage, threshold, flag_critical)
        needs_human = bool(reasons)

        decision = {
            "ticket_id": item["ticket_id"],
            "routed_to": "HUMAN_REVIEW" if needs_human else "AUTOMATED",
            "routing_reason": " | ".join(reasons) if needs_human else None,
            "final_response": (
                f"[DRAFT FOR AGENT REVIEW]: {triage['suggested_reply']}"
                if needs_human
                else triage["suggested_reply"]
            ),
        }
        decisions.append(decision)
        (human_review if needs_human else automated).append({**item, **decision})

    _write_json(os.path.join(output_dir, "routing_decisions.json"), decisions)
    _write_json(os.path.join(output_dir, "automated.json"), automated)
    _write_json(os.path.join(output_dir, "human_review.json"), human_review)

    print(f"Routed {len(automated)} tickets to AUTOMATED, {len(human_review)} to HUMAN_REVIEW")
