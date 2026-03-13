#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Optional


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ARXIV_FILTER = os.path.abspath(os.path.join(ROOT, "..", "arxiv_filter.py"))
DATA_JSON = os.path.join(ROOT, "data", "arxiv_filtered.json")
DATA_CSV = os.path.join(ROOT, "data", "arxiv_filtered.csv")
CONFIG_PATH = os.path.join(ROOT, "data", "config.json")
ENV_PATH = os.path.join(ROOT, ".env")


def load_config() -> Dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_env() -> None:
    if not os.path.exists(ENV_PATH):
        return
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                os.environ[key] = value


def run(cmd: List[str], env: Optional[Dict[str, str]] = None) -> None:
    proc = subprocess.run(cmd, env=env, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")


def main() -> int:
    load_env()
    cfg = load_config()

    if not os.path.exists(ARXIV_FILTER):
        print(f"Missing arxiv_filter.py at: {ARXIV_FILTER}", file=sys.stderr)
        return 1

    provider = cfg.get("provider", "openai")
    if provider == "openai":
        if not os.environ.get("OPENAI_API_KEY"):
            print("OPENAI_API_KEY is not set.", file=sys.stderr)
            return 1
    elif provider == "qwen":
        if not os.environ.get("DASHSCOPE_API_KEY"):
            print("DASHSCOPE_API_KEY is not set.", file=sys.stderr)
            return 1
    elif provider == "minimax":
        if not os.environ.get("MINIMAX_API_KEY"):
            print("MINIMAX_API_KEY is not set.", file=sys.stderr)
            return 1
    elif provider == "gemini":
        if not (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")):
            print("GEMINI_API_KEY (or GOOGLE_API_KEY) is not set.", file=sys.stderr)
            return 1
    elif provider == "hizui":
        if not os.environ.get("HIZUI_API_KEY"):
            print("HIZUI_API_KEY is not set.", file=sys.stderr)
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
        "--provider",
        provider,
        "--openai-model",
        cfg.get("openai_model", "gpt-5"),
        "--qwen-model",
        cfg.get("qwen_model", "qwen-plus"),
        "--qwen-base-url",
        cfg.get("qwen_base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        "--minimax-model",
        cfg.get("minimax_model", "MiniMax-M2.5"),
        "--minimax-base-url",
        cfg.get("minimax_base_url", "https://api.hizui.cn/v1"),
        "--gemini-model",
        cfg.get("gemini_model", "MiniMax-M2.5"),
        "--gemini-base-url",
        cfg.get("gemini_base_url", "https://api.hizui.cn"),
        "--hizui-model",
        cfg.get("hizui_model", "MiniMax-M2.5"),
        "--hizui-base-url",
        cfg.get("hizui_base_url", "https://api.hizui.cn/v1"),
        "--max-output-tokens",
        str(cfg.get("max_output_tokens", 1200)),
    ]
    if cfg.get("force_regen"):
        generate_cmd.append("--force")

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
