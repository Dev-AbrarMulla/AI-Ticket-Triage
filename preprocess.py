import json
import os
import re

URGENCY_PATTERN = re.compile(
    r"\b(?:urgent|emergency|down|locked out|500 error|refund|asap)\b",
    re.IGNORECASE,
)


def _clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()


def run_preprocessing(
    tickets_path: str = "tickets.json",
    output_path: str = "output/preprocessed_tickets.json",
) -> None:
    with open(tickets_path, encoding="utf-8") as f:
        raw_tickets = json.load(f)

    preprocessed = []
    for ticket in raw_tickets:
        subject = _clean(ticket["subject"])
        body = _clean(ticket["body"])
        combined = f"{subject} {body}"

        preprocessed.append({
            "ticket_id": ticket["ticket_id"],
            "customer_id": ticket["customer_id"],
            "created_at": ticket["created_at"],
            "cleaned_subject": subject,
            "cleaned_body": body,
            "word_count": len(combined.split()),
            "char_count": len(combined),
            "has_urgency_keywords": bool(URGENCY_PATTERN.search(combined)),
            "formatted_prompt_payload": f"Subject: {subject}\nBody: {body}",
        })

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(preprocessed, f, indent=2)

    print(f"Preprocessed {len(preprocessed)} tickets -> {output_path}")
