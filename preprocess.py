import os
import re
import json
from typing import List, Dict, Any

def run_preprocessing(
    tickets_path: str = "tickets.json",
    output_path: str = "output/preprocessed_tickets.json"
):
    with open(tickets_path, "r", encoding="utf-8") as f:
        raw_tickets = json.load(f)

    os.makedirs("output", exist_ok=True)
    urgency_keywords = {"urgent", "emergency", "down", "locked out", "500 error", "refund", "asap"}
    preprocessed = []

    for t in raw_tickets:
        clean_sub = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", t["subject"])).strip()
        clean_bdy = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", t["body"])).strip()
        combined = f"{clean_sub} {clean_bdy}"

        preprocessed.append({
            "ticket_id": t["ticket_id"],
            "customer_id": t["customer_id"],
            "created_at": t["created_at"],
            "cleaned_subject": clean_sub,
            "cleaned_body": clean_bdy,
            "word_count": len(combined.split()),
            "char_count": len(combined),
            "has_urgency_keywords": any(k in combined.lower() for k in urgency_keywords),
            "formatted_prompt_payload": f"Subject: {clean_sub}\nBody: {clean_bdy}"
        })

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(preprocessed, f, indent=2)

    print(f"🧹 Preprocessed {len(preprocessed)} tickets -> Created '{output_path}'")
