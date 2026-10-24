#!/usr/bin/env python3
"""
scripts/export_eval_candidates.py - Export downvoted feedback items into eval candidates list.
"""
import argparse
import json
from pathlib import Path
import sys

# Ensure api directory is on sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
API_DIR = REPO_ROOT / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from app.feedback import get_feedback_store


def main():
    parser = argparse.ArgumentParser(description="Export downvoted queries as eval candidates")
    parser.add_argument("--output", "-o", type=str, default=None, help="Output JSON file path")
    parser.add_argument("--data-dir", "-d", type=str, default=None, help="Directory containing feedback.jsonl")
    args = parser.parse_args()

    data_dir = Path(args.data_dir) if args.data_dir else None
    from app.feedback import FeedbackStore
    store = FeedbackStore(data_dir=data_dir)
    candidates = store.get_eval_candidates()

    output_json = json.dumps({"candidates": candidates, "total": len(candidates)}, indent=2)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"Exported {len(candidates)} candidate(s) to {out_path}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()
