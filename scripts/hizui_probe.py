#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sys

import requests


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENV_PATH = os.path.join(ROOT, ".env")


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


def main() -> int:
    load_env()
    api_key = os.environ.get("GEMINI_API_KEY", "").strip() or os.environ.get("GOOGLE_API_KEY", "").strip()
    if not api_key:
        print("GEMINI_API_KEY (or GOOGLE_API_KEY) is not set.", file=sys.stderr)
        return 1

    base_url = os.environ.get("GOOGLE_GEMINI_BASE_URL", "").strip() or "https://api.hizui.cn"
    model = os.environ.get("GEMINI_MODEL", "").strip() or "MiniMax-M2.5"

    url = f"{base_url.rstrip('/')}/v1/responses"
    payload = {
        "model": model,
        "input": "请用中文写一句话说明单细胞研究的价值。",
        "max_output_tokens": 200,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
    print("Status:", resp.status_code)
    try:
        print(json.dumps(resp.json(), ensure_ascii=False, indent=2))
    except Exception:
        print(resp.text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
