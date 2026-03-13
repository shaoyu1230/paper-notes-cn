#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import csv
import json
import sys
from datetime import datetime
from typing import Dict, List, Optional

import requests


JOURNAL_WHITELIST = {
    "Nature",
    "Cell",
    "Science",
    "Nature Cancer",
    "Cancer Cell",
    "Nature Genetics",
}


def crossref_query(author: str, from_date: str, until_date: str, rows: int) -> List[Dict]:
    url = "https://api.crossref.org/works"
    params = {
        "filter": f"from-pub-date:{from_date},until-pub-date:{until_date}",
        "query.author": author,
        "rows": rows,
        "select": "DOI,title,author,container-title,issued,URL,type",
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json().get("message", {}).get("items", [])


def pick_container_title(item: Dict) -> str:
    titles = item.get("container-title") or []
    return titles[0] if titles else ""


def authors_to_str(item: Dict) -> str:
    authors = item.get("author") or []
    names = []
    for a in authors:
        given = a.get("given", "") or ""
        family = a.get("family", "") or ""
        name = " ".join([given, family]).strip()
        if name:
            names.append(name)
    return "; ".join(names)


def issued_to_date(item: Dict) -> str:
    issued = item.get("issued", {}).get("date-parts", [])
    if issued and issued[0]:
        parts = issued[0]
        year = parts[0]
        month = parts[1] if len(parts) > 1 else 1
        day = parts[2] if len(parts) > 2 else 1
        return f"{year:04d}-{month:02d}-{day:02d}"
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect candidate papers for series (Crossref).")
    parser.add_argument("--authors", nargs="+", required=True)
    parser.add_argument("--from-date", required=True)
    parser.add_argument("--until-date", required=True)
    parser.add_argument("--rows", type=int, default=200)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-csv", required=True)
    args = parser.parse_args()

    candidates: List[Dict] = []
    seen = set()

    for author in args.authors:
        items = crossref_query(author, args.from_date, args.until_date, args.rows)
        for item in items:
            container = pick_container_title(item)
            if container not in JOURNAL_WHITELIST:
                continue
            doi = item.get("DOI", "")
            if not doi or doi in seen:
                continue
            seen.add(doi)
            candidates.append(
                {
                    "doi": doi,
                    "title": (item.get("title") or [""])[0],
                    "authors": authors_to_str(item),
                    "journal": container,
                    "issued": issued_to_date(item),
                    "url": item.get("URL", ""),
                    "type": item.get("type", ""),
                }
            )

    candidates.sort(key=lambda x: (x["issued"], x["journal"], x["title"]))

    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(candidates, f, ensure_ascii=False, indent=2)

    with open(args.output_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["doi", "title", "authors", "journal", "issued", "url", "type"]
        )
        writer.writeheader()
        writer.writerows(candidates)

    print(f"Collected {len(candidates)} candidate papers.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
