import argparse
from pathlib import Path

from .experiment import run


def main():
    parser = argparse.ArgumentParser(description="Run an offline, frozen FL decipherment experiment")
    parser.add_argument("command", choices=["run"])
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--config", default="experiments/kamri_excerpt_v1.json")
    parser.add_argument("--benchmark", default="benchmarks/kamri_excerpt_v1.json")
    parser.add_argument("--run-id")
    args = parser.parse_args()
    root = args.root.resolve()
    out = run(root, root / args.config, root / args.benchmark, args.run_id)
    print(out / "report.md")
