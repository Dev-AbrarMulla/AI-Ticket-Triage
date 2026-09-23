from preprocess import run_preprocessing
from classify import run_classification
from router import run_routing_and_reply
from evaluator import run_evaluation
from validator import run_validation_command

def main():
    print("=" * 60)
    print("STARTING MODULAR TRIAGE PIPELINE EXECUTION")
    print("=" * 60 + "\n")

    # 1. Preprocessing
    run_preprocessing()

    # 2. Classification & Call Logging
    run_classification()

    # 3. Routing & Reply Generation
    run_routing_and_reply()

    # 4. Evaluation & Prediction Comparison
    run_evaluation()

    print("\n" + "=" * 60)
    # 5. Bottom Check / Validation
    success = run_validation_command()
    print("=" * 60)

    if success:
        print("\n🎉 Pipeline Execution Completed Successfully!")
    else:
        print("\n❌ Pipeline Execution Ended With Validation Errors.")

if __name__ == "__main__":
    main()
