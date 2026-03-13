#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import subprocess
import sys
from datetime import datetime
from typing import Dict, List


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ARXIV_FILTER = os.path.abspath(os.path.join(ROOT, "..", "arxiv_filter.py"))
DATA_JSON = os.path.join(ROOT, "data", "arxiv_filtered.json")
DATA_CSV = os.path.join(ROOT, "data", "arxiv_filtered.csv")
CONFIG_PATH = os.path.join(ROOT, "data", "config.json")


def load_config() -> Dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def run(cmd: List[str], env: Dict[str, str] | None = None) -> None:
    proc = subprocess.run(cmd, env=env, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")


def main() -> int:
    cfg = load_config()

    if not os.path.exists(ARXIV_FILTER):
        print(f"Missing arxiv_filter.py at: {ARXIV_FILTER}", file=sys.stderr)
        return 1

    if not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is not set.", file=sys.stderr)
        return 1

    arxiv_cmd = [
        "python3",
        ARXIV_FILTER,
        "--output-json",
        DATA_JSON,
        "--output-csv",
        DATA_CSV,
        "--max-results",
        str(cfg.get("max_results", 200)),
    ]

    categories = cfg.get("categories") or []
    if categories:
        arxiv_cmd += ["--categories", *categories]

    keywords = cfg.get("keywords") or []
    if keywords:
        arxiv_cmd += ["--keywords", *keywords]

    authors = cfg.get("authors") or []
    if authors:
        arxiv_cmd += ["--authors", *authors]

    journal_keywords = cfg.get("journal_keywords") or []
    if journal_keywords:
        arxiv_cmd += ["--journal-keywords", *journal_keywords]

    citation_min = cfg.get("citation_min")
    if citation_min is not None:
        arxiv_cmd += ["--citation-min", str(citation_min)]

    run(arxiv_cmd)

    generate_cmd = [
        "python3",
        os.path.join(ROOT, "scripts", "generate_drafts.py"),
        "--input-json",
        DATA_JSON,
        "--output-dir",
        os.path.join(ROOT, "drafts"),
        "--max-papers",
        str(cfg.get("max_papers_per_day", 5)),
        "--use-openai",
        "--openai-model",
        cfg.get("openai_model", "gpt-5"),
        "--openai-max-output-tokens",
        str(cfg.get("openai_max_output_tokens", 1200)),
    ]

    run(generate_cmd, env=os.environ.copy())

    # Commit drafts if there are changes
    status_cmd = ["git", "-C", ROOT, "status", "--porcelain", "drafts"]
    status = subprocess.check_output(status_cmd).decode("utf-8").strip()
    if not status:
        print("No new drafts to commit.")
        return 0

    run(["git", "-C", ROOT, "add", "drafts"])

    today = datetime.now().strftime("%Y-%m-%d")
    run(["git", "-C", ROOT, "commit", "-m", f"Add drafts {today}"])
    run(["git", "-C", ROOT, "push", "origin", "main"])

    print("Daily pipeline finished.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
