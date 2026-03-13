#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional

import requests


def pubmed_id_from_doi(doi: str) -> Optional[str]:
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {"db": "pubmed", "term": f"{doi}[DOI]"}
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    root = ET.fromstring(resp.text)
    ids = root.findall(".//IdList/Id")
    return ids[0].text if ids else None


def pubmed_abstract(pmid: str) -> str:
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {"db": "pubmed", "id": pmid, "retmode": "xml"}
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    root = ET.fromstring(resp.text)
    parts = []
    for ab in root.findall(".//Abstract/AbstractText"):
        label = ab.attrib.get("Label")
        text = (ab.text or "").strip()
        if label:
            parts.append(f"{label}: {text}")
        else:
            parts.append(text)
    return "\n".join([p for p in parts if p]).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Build series input JSON from candidates + PubMed.")
    parser.add_argument("--input-json", required=True)
    parser.add_argument("--output-json", required=True)
    args = parser.parse_args()

    with open(args.input_json, "r", encoding="utf-8") as f:
        candidates = json.load(f)

    out: List[Dict] = []
    for item in candidates:
        doi = item.get("doi", "")
        pmid = None
        summary = ""
        if doi:
            try:
                pmid = pubmed_id_from_doi(doi)
                if pmid:
                    summary = pubmed_abstract(pmid)
            except Exception as exc:  # noqa: BLE001
                print(f"PubMed lookup failed for {doi}: {exc}", file=sys.stderr)

        authors = item.get("authors", "")
        author_list = [a.strip() for a in authors.split(";") if a.strip()]

        out.append(
            {
                "arxiv_id": doi or item.get("url", ""),
                "title": item.get("title", ""),
                "authors": author_list,
                "published": item.get("issued", ""),
                "updated": item.get("issued", ""),
                "summary": summary,
                "doi": doi,
                "journal_ref": item.get("journal", ""),
                "primary_category": item.get("journal", ""),
                "categories": [item.get("journal", "")] if item.get("journal") else [],
                "pdf_url": "",
                "arxiv_url": item.get("url", ""),
            }
        )

    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"Built {len(out)} series input records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
