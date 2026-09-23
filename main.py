import sys

from classify import run_classification
from evaluator import run_evaluation
from preprocess import run_preprocessing
from router import run_routing_and_reply
from validator import run_validation_command


def main() -> int:
    run_preprocessing()
    run_classification()
    run_routing_and_reply()
    run_evaluation()

    if run_validation_command():
        print("Pipeline completed successfully.")
        return 0
    print("Pipeline finished with validation errors.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
