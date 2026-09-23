import argparse
import json
import os
import sys
from typing import List, Dict, Any

from preprocess import run_preprocessing
from classify import run_classification
from router import run_routing_and_reply
from evaluator import run_evaluation
from validator import run_validation_command

HUMAN_QUEUE_PATH = "output/human_review.json"
AUTOMATED_QUEUE_PATH = "output/automated.json"
EVAL_PATH = "output/evaluation_report.json"

def print_banner(title: str):
    print("\n" + "=" * 60)
    print(f" {title.upper()}")
    print("=" * 60)

def cmd_run():
    """Executes the full end-to-end pipeline."""
    print_banner("Running Triage Pipeline")
    run_preprocessing()
    run_classification()
    run_routing_and_reply()
    run_evaluation()
    print_banner("Pipeline Validation")
    run_validation_command()

def cmd_view_queue():
    """Displays tickets pending in the Human Review Queue."""
    print_banner("Human Review Queue")
    if not os.path.exists(HUMAN_QUEUE_PATH):
        print("⚠️ No human review queue found. Run the pipeline first.")
        return

    with open(HUMAN_QUEUE_PATH, "r", encoding="utf-8") as f:
        tickets = json.load(f)

    if not tickets:
        print("🎉 Human review queue is empty!")
        return

    print(f"Found {len(tickets)} ticket(s) requiring human operator attention:\n")
    for idx, t in enumerate(tickets, start=1):
        triage = t.get("triage", {})
        print(f"[{idx}] ID: {t['ticket_id']} | Customer: {t['customer_id']}")
        print(f"    Subject: {t['cleaned_subject']}")
        print(f"    Category: {triage.get('category')} | Urgency: {triage.get('urgency')} | Confidence: {triage.get('confidence'):.2f}")
        print(f"    Reason Flagged: {t.get('routing_reason')}")
        print(f"    Draft Response: {triage.get('suggested_reply')[:90]}...")
        print("-" * 60)

def cmd_resolve(ticket_id: str):
    """Allows operator to approve or modify and resolve a flagged ticket."""
    print_banner(f"Resolving Ticket {ticket_id}")
    if not os.path.exists(HUMAN_QUEUE_PATH):
        print("⚠️ Human review queue file missing.")
        return

    with open(HUMAN_QUEUE_PATH, "r", encoding="utf-8") as f:
        human_tickets: List[Dict[str, Any]] = json.load(f)

    target_idx = None
    target_ticket = None
    for idx, item in enumerate(human_tickets):
        if item["ticket_id"].upper() == ticket_id.upper():
            target_idx = idx
            target_ticket = item
            break

    if target_ticket is None:
        print(f"❌ Ticket ID '{ticket_id}' not found in human review queue.")
        return

    triage = target_ticket.get("triage", {})
    print(f"Ticket ID:      {target_ticket['ticket_id']}")
    print(f"Subject:        {target_ticket['cleaned_subject']}")
    print(f"Body:           {target_ticket['cleaned_body']}")
    print(f"Flagged Reason: {target_ticket.get('routing_reason')}")
    print(f"Draft Reply:    {triage.get('suggested_reply')}\n")

    print("Operator Options:")
    print(" [1] Approve draft reply and resolve")
    print(" [2] Override with custom reply")
    print(" [3] Cancel")

    choice = input("\nSelect choice [1-3]: ").strip()

    if choice == "1":
        final_response = triage.get('suggested_reply')
    elif choice == "2":
        final_response = input("Enter final response to send to customer: ").strip()
        if not final_response:
            print("Operation canceled. Reply cannot be empty.")
            return
    else:
        print("Operation canceled.")
        return

    # Move from human review queue to automated/resolved queue
    resolved_record = {
        **target_ticket,
        "routed_to": "RESOLVED_BY_HUMAN",
        "final_response": final_response
    }

    human_tickets.pop(target_idx)
    with open(HUMAN_QUEUE_PATH, "w", encoding="utf-8") as f:
        json.dump(human_tickets, f, indent=2)

    automated_tickets = []
    if os.path.exists(AUTOMATED_QUEUE_PATH):
        with open(AUTOMATED_QUEUE_PATH, "r", encoding="utf-8") as f:
            automated_tickets = json.load(f)

    automated_tickets.append(resolved_record)
    with open(AUTOMATED_QUEUE_PATH, "w", encoding="utf-8") as f:
        json.dump(automated_tickets, f, indent=2)

    print(f"✅ Ticket {ticket_id} resolved successfully and moved out of the human queue.")

def cmd_report():
    """Displays execution metrics and accuracy summary."""
    print_banner("Triage System Evaluation Report")
    if not os.path.exists(EVAL_PATH):
        print("⚠️ Report file missing. Run the pipeline first.")
        return

    with open(EVAL_PATH, "r", encoding="utf-8") as f:
        report = json.load(f)

    print(f" Report Timestamp:      {report.get('generated_at')}")
    print(f" Total Tickets Processed: {report.get('total_tickets')}")
    print(f" Automation Rate:        {report.get('automation_rate') * 100:.1f}%")
    print(f" Human Review Rate:      {report.get('human_review_rate') * 100:.1f}%")
    print(f" Avg Model Confidence:   {report.get('average_confidence_score'):.3f}")
    print("\n Queue Breakdown:")
    print(f"  └─ Automated Queue:    {report['queue_breakdown']['automated']}")
    print(f"  └─ Human Review Queue: {report['queue_breakdown']['human_review']}")

def interactive_menu():
    """Interactive CLI menu loop when no arguments are passed."""
    while True:
        print_banner("Ticket Triage Operator Console")
        print(" [1] Run Full Triage Pipeline")
        print(" [2] View Human Review Queue")
        print(" [3] Resolve Flagged Ticket")
        print(" [4] View Performance & Evaluation Report")
        print(" [5] Exit")

        choice = input("\nSelect option [1-5]: ").strip()
        if choice == "1":
            cmd_run()
        elif choice == "2":
            cmd_view_queue()
        elif choice == "3":
            tid = input("Enter Ticket ID to resolve (e.g. TCK-102): ").strip()
            if tid:
                cmd_resolve(tid)
        elif choice == "4":
            cmd_report()
        elif choice == "5":
            print("Exiting Operator Console.")
            sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description="CLI Operator Interface for AI Ticket Triage Pipeline")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("run", help="Execute full pipeline end-to-end")
    subparsers.add_parser("queue", help="Display human review queue")
    
    resolve_parser = subparsers.add_parser("resolve", help="Review and resolve a flagged ticket")
    resolve_parser.add_argument("ticket_id", help="Ticket ID to resolve (e.g., TCK-102)")

    subparsers.add_parser("report", help="Display metrics and evaluation report")

    args = parser.parse_args()

    if args.command == "run":
        cmd_run()
    elif args.command == "queue":
        cmd_view_queue()
    elif args.command == "resolve":
        cmd_resolve(args.ticket_id)
    elif args.command == "report":
        cmd_report()
    else:
        interactive_menu()

if __name__ == "__main__":
    main()