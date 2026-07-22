from __future__ import annotations

import argparse
import json

from .experiments import evaluate_manifest
from .repeat_safe import suppress_repeated_ngrams


def main() -> None:
    parser = argparse.ArgumentParser(description="Synthetic Turkish ASR adaptation experiment runner")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("demo")
    evaluate = sub.add_parser("evaluate")
    evaluate.add_argument("--manifest", required=True)
    repeat_safe = sub.add_parser("repeat-safe")
    repeat_safe.add_argument("--text", required=True)
    repeat_safe.add_argument("--ngram", type=int, default=2)
    args = parser.parse_args()
    if args.command == "demo":
        payload = {
            "baseline": evaluate_manifest("experiments/baseline.json"),
            "adapter_candidate": evaluate_manifest("experiments/adapter-routing.json"),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif args.command == "evaluate":
        print(json.dumps(evaluate_manifest(args.manifest), ensure_ascii=False, indent=2))
    else:
        print(suppress_repeated_ngrams(args.text, args.ngram))
