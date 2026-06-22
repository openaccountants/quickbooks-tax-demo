"""QuickBooks Online transaction extraction.

In live mode (QBO_ACCESS_TOKEN + QBO_REALM_ID) this would query the QuickBooks
Online API (Purchase/Expense objects) — a free developer sandbox is available
with no approval. For the demo it loads bundled samples in a similar shape and
normalizes each to the facts the coding check needs.
"""

from __future__ import annotations

import json
import os

QBO_ACCESS_TOKEN = os.environ.get("QBO_ACCESS_TOKEN")
QBO_REALM_ID = os.environ.get("QBO_REALM_ID")


def extract(source: str) -> list[dict]:
    if QBO_ACCESS_TOKEN and QBO_REALM_ID:
        return _extract_live()
    with open(source) as fh:
        data = json.load(fh)
    return data if isinstance(data, list) else [data]


def _extract_live() -> list[dict]:  # pragma: no cover - needs sandbox creds
    """Live QBO pull. Wired but inert until sandbox creds are present.

    GET /v3/company/{realm}/query?query=SELECT * FROM Purchase
    """
    import urllib.parse
    import urllib.request

    q = urllib.parse.quote("SELECT * FROM Purchase MAXRESULTS 25")
    url = f"https://quickbooks.api.intuit.com/v3/company/{QBO_REALM_ID}/query?query={q}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {QBO_ACCESS_TOKEN}", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.load(r)
    return body.get("QueryResponse", {}).get("Purchase", [])


def normalize(txn: dict) -> dict:
    return {
        "vendor": txn.get("vendor", ""),
        "amount": float(txn.get("amount", 0)),
        "account": txn.get("account", ""),       # the GL account it was coded to
        "description": txn.get("description", ""),
    }
