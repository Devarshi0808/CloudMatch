"""Explainable catalog matching for the CloudMatch serverless API."""

import json
import os
import re
import urllib.parse
import urllib.request
import zipfile
import xml.etree.ElementTree as ET
from copy import deepcopy
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path


_XLSX_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def normalize(value):
    value = str(value or "").lower().replace("&", " and ")
    value = value.replace("redhat", "red hat")
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def similarity(query, candidate):
    query_tokens = set(normalize(query).split())
    candidate_tokens = set(normalize(candidate).split())
    if not query_tokens or not candidate_tokens:
        return 0.0
    overlap = len(query_tokens & candidate_tokens) / len(query_tokens | candidate_tokens)
    sequence = SequenceMatcher(None, normalize(query), normalize(candidate)).ratio()
    return min(100.0, (overlap * 0.65 + sequence * 0.35) * 100)


def _xlsx_value(cell, shared_strings):
    value = cell.find(f"{_XLSX_NS}v")
    if value is None:
        inline = cell.find(f"{_XLSX_NS}is/{_XLSX_NS}t")
        return inline.text if inline is not None else ""
    raw = value.text or ""
    if cell.get("t") == "s":
        return shared_strings[int(raw)] if int(raw) < len(shared_strings) else ""
    return raw


def load_catalog(path=None):
    path = Path(path or Path(__file__).parent.parent / "data" / "Vendors_and_Products.xlsx")
    with zipfile.ZipFile(path) as workbook:
        shared_strings = []
        if "xl/sharedStrings.xml" in workbook.namelist():
            root = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
            for item in root.findall(f"{_XLSX_NS}si"):
                shared_strings.append("".join(text.text or "" for text in item.iter(f"{_XLSX_NS}t")))

        sheet = ET.fromstring(workbook.read("xl/worksheets/sheet1.xml"))
        rows = []
        for row in sheet.findall(f"{_XLSX_NS}sheetData/{_XLSX_NS}row"):
            values = {}
            for cell in row.findall(f"{_XLSX_NS}c"):
                reference = cell.get("r", "A1")
                column = re.sub(r"[^A-Z]", "", reference)
                values[column] = _xlsx_value(cell, shared_strings)
            rows.append(values)

    if not rows:
        return []
    headers = rows[0]
    return [
        {headers.get(column, column): value for column, value in row.items()}
        for row in rows[1:]
        if any(row.values())
    ]


def marketplace_links(query):
    encoded = urllib.parse.quote_plus(query)
    return {
        "aws": f"https://aws.amazon.com/marketplace/search?searchTerms={encoded}",
        "azure": f"https://azuremarketplace.microsoft.com/en-us/marketplace/apps?search={encoded}",
        "gcp": f"https://console.cloud.google.com/marketplace/browse?q={encoded}",
    }


@lru_cache(maxsize=128)
def _search_catalog_cached(vendor, solution, limit):
    vendor = str(vendor or "").strip()
    solution = str(solution or "").strip()
    query = " ".join(part for part in (vendor, solution) if part)
    if not query:
        return {"query": query, "matches": [], "marketplace_links": {}, "catalog_size": 0}

    matches = []
    for item in load_catalog():
        item_vendor = str(item.get("vendor", "")).strip()
        item_solution = str(item.get("solution_name", "")).strip()
        vendor_score = similarity(vendor, item_vendor) if vendor else 0.0
        solution_score = similarity(solution, item_solution) if solution else 0.0
        score = vendor_score if vendor and not solution else solution_score if solution and not vendor else vendor_score * 0.55 + solution_score * 0.45
        if score < 20:
            continue
        evidence = []
        if vendor:
            evidence.append(f"vendor similarity {vendor_score:.0f}%")
        if solution:
            evidence.append(f"product similarity {solution_score:.0f}%")
        matches.append({
            "vendor": item_vendor,
            "solution": item_solution,
            "score": round(score, 1),
            "evidence": evidence,
            "match_type": "catalog_match",
        })

    matches.sort(key=lambda item: (-item["score"], item["vendor"], item["solution"]))
    return {
        "query": query,
        "matches": matches[:limit],
        "marketplace_links": marketplace_links(query),
        "catalog_size": len(load_catalog()),
        "disclaimer": "Marketplace links open external search pages; catalog matches are ranked from the local vendor catalog.",
    }


def search_catalog(vendor="", solution="", limit=8):
    return deepcopy(_search_catalog_cached(str(vendor or "").strip(), str(solution or "").strip(), limit))


def cache_info():
    return _search_catalog_cached.cache_info()


def llm_suggestions(query):
    """Return optional LLM query suggestions without making the core path dependent on an API key."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"enabled": False, "suggestions": [], "reason": "OPENAI_API_KEY is not configured"}
    payload = json.dumps({
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": "Return JSON only: {\"suggestions\":[string, string, string]}. Suggest marketplace search variants, preserving the user's intent."},
            {"role": "user", "content": query},
        ],
    }).encode()
    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            content = json.loads(response.read().decode())
            parsed = json.loads(content["choices"][0]["message"]["content"])
            return {"enabled": True, "suggestions": parsed.get("suggestions", [])[:3]}
    except Exception:
        return {"enabled": True, "suggestions": [], "reason": "LLM suggestion service unavailable"}
