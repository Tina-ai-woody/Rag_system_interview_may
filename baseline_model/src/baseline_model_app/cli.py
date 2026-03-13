import sys
from .rag_pipeline import main as pipeline_main


def build() -> None:
    sys.argv = ["run_baseline.py", "build"]
    pipeline_main()


def eval() -> None:
    sys.argv = ["run_baseline.py", "eval"]
    pipeline_main()
