#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Optional


def load_json(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def safe_filename(name: str) -> str:
    name = re.sub(r"[^\w\-\.]+", "_", name.strip())
    return name


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def build_front_matter(paper: Dict) -> str:
    authors = paper.get("authors") or []
    categories = paper.get("categories") or []
    safe_title = paper.get("title", "").replace('"', "'")
    lines = [
        "---",
        f'title: "{safe_title}"',
        f"arxiv_id: {paper.get('arxiv_id', '')}",
        f"published: {paper.get('published', '')}",
        f"updated: {paper.get('updated', '')}",
        f"doi: {paper.get('doi') or ''}",
        f"journal_ref: {paper.get('journal_ref') or ''}",
        f"primary_category: {paper.get('primary_category') or ''}",
        f"categories: {', '.join(categories)}",
        f"citation_count: {paper.get('citation_count') if paper.get('citation_count') is not None else ''}",
        f"pdf_url: {paper.get('pdf_url', '')}",
        f"arxiv_url: {paper.get('arxiv_url', '')}",
        "authors:",
    ]
    for a in authors:
        lines.append(f"  - {a}")
    lines.append("---")
    return "\n".join(lines)


def build_prompt(template: str, paper: Dict) -> str:
    authors = ", ".join(paper.get("authors") or [])
    categories = ", ".join(paper.get("categories") or [])
    return template.format(
        title=paper.get("title", ""),
        authors=authors,
        published=paper.get("published", ""),
        arxiv_id=paper.get("arxiv_id", ""),
        categories=categories,
        summary=paper.get("summary", ""),
    )


def run_llm(prompt: str, command: str, timeout_s: int = 120) -> Optional[str]:
    try:
        cmd = shlex.split(command)
        proc = subprocess.run(
            cmd,
            input=prompt.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_s,
            check=False,
        )
        if proc.returncode != 0:
            return None
        return proc.stdout.decode("utf-8", errors="ignore").strip()
    except (OSError, subprocess.TimeoutExpired):
        return None


def run_openai(prompt: str, model: str, max_output_tokens: int) -> Optional[str]:
    try:
        from openai import OpenAI
    except ImportError:
        print("OpenAI SDK not installed. Run: pip install openai", file=sys.stderr)
        return None

    client = OpenAI()
    try:
        resp = client.responses.create(
            model=model,
            input=prompt,
            max_output_tokens=max_output_tokens,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"OpenAI request failed: {exc}", file=sys.stderr)
        return None

    output_text = getattr(resp, "output_text", None)
    if output_text:
        return output_text.strip()

    # Fallback: try to extract output text from response items if output_text isn't present.
    try:
        chunks = []
        for item in getattr(resp, "output", []) or []:
            if item.get("type") == "message":
                for c in item.get("content", []) or []:
                    if c.get("type") == "output_text":
                        chunks.append(c.get("text", ""))
        text = "\n".join([c for c in chunks if c])
        return text.strip() if text else None
    except Exception:  # noqa: BLE001
        return None


def run_qwen(prompt: str, model: str, max_output_tokens: int, base_url: str) -> Optional[str]:
    try:
        from openai import OpenAI
    except ImportError:
        print("OpenAI SDK not installed. Run: pip install openai", file=sys.stderr)
        return None

    api_key = os.environ.get("DASHSCOPE_API_KEY", "").strip()
    if not api_key:
        print("DASHSCOPE_API_KEY is not set.", file=sys.stderr)
        return None

    client = OpenAI(api_key=api_key, base_url=base_url)
    try:
        resp = client.responses.create(
            model=model,
            input=prompt,
            max_output_tokens=max_output_tokens,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Qwen request failed: {exc}", file=sys.stderr)
        return None

    output_text = getattr(resp, "output_text", None)
    if output_text:
        return output_text.strip()

    try:
        chunks = []
        for item in getattr(resp, "output", []) or []:
            if item.get("type") == "message":
                for c in item.get("content", []) or []:
                    if c.get("type") == "output_text":
                        chunks.append(c.get("text", ""))
        text = "\n".join([c for c in chunks if c])
        if text:
            return text.strip()
        print("MiniMax returned empty content. Response items had no output_text.", file=sys.stderr)
        return None
    except Exception:  # noqa: BLE001
        return None


def run_minimax(prompt: str, model: str, max_output_tokens: int, base_url: str) -> Optional[str]:
    try:
        from openai import OpenAI
    except ImportError:
        print("OpenAI SDK not installed. Run: pip install openai", file=sys.stderr)
        return None

    api_key = os.environ.get("MINIMAX_API_KEY", "").strip()
    if not api_key:
        print("MINIMAX_API_KEY is not set.", file=sys.stderr)
        return None

    client = OpenAI(api_key=api_key, base_url=base_url)
    try:
        resp = client.responses.create(
            model=model,
            input=prompt,
            max_output_tokens=max_output_tokens,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"MiniMax request failed: {exc}", file=sys.stderr)
        return None

    output_text = getattr(resp, "output_text", None)
    if output_text:
        return output_text.strip()

    try:
        chunks = []
        for item in getattr(resp, "output", []) or []:
            if item.get("type") == "message":
                for c in item.get("content", []) or []:
                    if c.get("type") == "output_text":
                        chunks.append(c.get("text", ""))
        text = "\n".join([c for c in chunks if c])
        return text.strip() if text else None
    except Exception:  # noqa: BLE001
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Chinese draft notes from arXiv JSON.")
    parser.add_argument("--input-json", required=True, help="arXiv filtered JSON path")
    parser.add_argument("--output-dir", required=True, help="draft output directory")
    parser.add_argument("--max-papers", type=int, default=20)
    parser.add_argument("--use-llm", action="store_true", help="use LLM_COMMAND to generate body")
    parser.add_argument("--provider", default="openai", choices=["openai", "qwen", "minimax"])
    parser.add_argument("--openai-model", default="gpt-5", help="OpenAI model ID")
    parser.add_argument("--qwen-model", default="qwen-plus", help="Qwen model ID")
    parser.add_argument(
        "--qwen-base-url",
        default="https://dashscope.aliyuncs.com/compatible-mode/v1",
        help="Qwen OpenAI-compatible base_url",
    )
    parser.add_argument("--minimax-model", default="MiniMax-M2.5", help="MiniMax model ID")
    parser.add_argument(
        "--minimax-base-url",
        default="https://api.hizui.cn",
        help="MiniMax OpenAI-compatible base_url",
    )
    parser.add_argument("--max-output-tokens", type=int, default=1200)
    parser.add_argument("--prompt-template", default=None, help="prompt template path")
    parser.add_argument("--fallback-body", default=None, help="fallback body template path")
    args = parser.parse_args()

    llm_command = os.environ.get("LLM_COMMAND", "").strip()
    prompt_path = args.prompt_template or os.path.join(
        os.path.dirname(__file__), "..", "prompts", "draft_prompt.md"
    )
    fallback_path = args.fallback_body or os.path.join(
        os.path.dirname(__file__), "..", "prompts", "fallback_body.md"
    )

    prompt_template = read_text(prompt_path)
    fallback_body = read_text(fallback_path)

    papers = load_json(args.input_json)
    ensure_dir(args.output_dir)

    count = 0
    for paper in papers:
        if count >= args.max_papers:
            break

        published = paper.get("published", "")
        try:
            dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
        except ValueError:
            dt = datetime.utcnow()

        date_prefix = dt.strftime("%Y-%m-%d")
        arxiv_id = paper.get("arxiv_id", "unknown")
        filename = safe_filename(f"{date_prefix}_{arxiv_id}.md")
        out_path = os.path.join(args.output_dir, filename)

        if os.path.exists(out_path):
            continue

        front_matter = build_front_matter(paper)
        body = fallback_body

        prompt = build_prompt(prompt_template, paper)

        if args.provider == "openai":
            openai_body = run_openai(
                prompt=prompt,
                model=args.openai_model,
                max_output_tokens=args.max_output_tokens,
            )
            if openai_body:
                body = openai_body
        elif args.provider == "qwen":
            qwen_body = run_qwen(
                prompt=prompt,
                model=args.qwen_model,
                max_output_tokens=args.max_output_tokens,
                base_url=args.qwen_base_url,
            )
            if qwen_body:
                body = qwen_body
        elif args.provider == "minimax":
            minimax_body = run_minimax(
                prompt=prompt,
                model=args.minimax_model,
                max_output_tokens=args.max_output_tokens,
                base_url=args.minimax_base_url,
            )
            if minimax_body:
                body = minimax_body
        elif args.use_llm and llm_command:
            llm_body = run_llm(prompt, llm_command)
            if llm_body:
                body = llm_body

        content = f"{front_matter}\n\n{body}\n"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)

        count += 1

    print(f"Generated {count} draft(s) in {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
