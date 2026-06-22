#!/usr/bin/env python3
"""QuickBooks -> OpenAccountants bookkeeping-coding review pipeline.

    python pipeline.py                       # bundled sample transactions (mock mode)
    python pipeline.py samples/transactions.json

The flow:
    QBO transactions -> OA MCP (start -> get_skill) -> coding review -> verdict

Live: set OA_MCP_TOKEN (+ QBO_ACCESS_TOKEN / QBO_REALM_ID, free sandbox) to pull
real transactions and verified rules.
"""

from __future__ import annotations

import os
import sys

import qbo_client
import coding_check
from oa_client import OAClient

STATUS = {"ok": "✅", "warn": "⚠️ ", "info": "ℹ️ "}


def run(source: str, oa: OAClient) -> None:
    txns = qbo_client.extract(source)
    plan = oa.start("Review bookkeeping tax coding", "US")
    slug = (plan.get("skills_to_load") or [None])[0]
    skill = oa.get_skill(slug) if slug else {}

    for txn in txns:
        f = qbo_client.normalize(txn)
        print(f"\n📒  {f['vendor']} · ${f['amount']:,.0f} → '{f['account']}'"
              + (f"  ({f['description']})" if f['description'] else ""))
        v = coding_check.check(f, skill)
        trust = f"tier {v.get('tier')}" + (f", signed off by {v['verifier']}" if v.get("verifier") else "")
        print(f"    OpenAccountants → {v.get('oa_skill_name') or 'coding rules'}  ({trust})")
        print(f"    {STATUS.get(v['status'], '')} {v['headline']}")
        print(f"       {v['detail']}")


def main(argv: list[str]) -> int:
    oa = OAClient()
    mode = "LIVE" if oa.live else "MOCK (set OA_MCP_TOKEN + QBO creds to go live)"
    print(f"QuickBooks → OpenAccountants · bookkeeping-coding review  [{mode}]")
    here = os.path.dirname(os.path.abspath(__file__))
    source = argv[1] if len(argv) > 1 else os.path.join(here, "samples", "transactions.json")
    run(source, oa)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
