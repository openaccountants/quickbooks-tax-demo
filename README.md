# QuickBooks → OpenAccountants: bookkeeping-coding review

**The pitch in one line:** QuickBooks holds the books. OpenAccountants reviews how each transaction is **coded for tax** — catching the classics that cost money at year-end — signed off by a named licensed accountant.

```
QuickBooks transactions
  └─ { vendor, amount, account, description }
        └─ OpenAccountants MCP  →  load the verified bookkeeping/tax-coding skill
              └─ Verdict:  ⚠️ capital asset expensed — should be capitalized   ← the catch
                           ⚠️ meals coded at 100% (they're 50%)
                           ⚠️ owner's personal expense in the business books
                           ✅ under the de-minimis safe harbor / ordinary expense
                 · the rule that decided it (cited)
                 · the named CPA who signed it off
```

![QuickBooks → OpenAccountants demo](demo.svg)

> Regenerate the visual: `python make_svg.py` (static SVG, no deps) · animated GIF: `brew install vhs && vhs demo.tape`

## Why this one

QuickBooks records *where* money went; it doesn't know whether the **tax coding** is right. The errors are quiet and expensive:

- a **$12k server expensed** to Office Supplies should be a Fixed Asset, depreciated (or §179) — not deducted in full;
- **business meals** coded at 100% are only 50% deductible;
- an **owner's personal** purchase in the business books isn't deductible at all.

OpenAccountants is the review layer on top of the ledger — verified rules, a named accountant behind them, and it works on the QuickBooks data your customers already have (free developer sandbox, no approval).

## What it shows

A handful of transactions run through the OpenAccountants MCP:

| Transaction | Verdict |
|---|---|
| **$12,000 server → Office Supplies** | ⚠️ **Capital asset expensed — capitalize & depreciate** |
| $200 client dinner → Meals - 100% | ⚠️ Meals are 50% deductible |
| $800 owner's headphones → Office Expenses | ⚠️ Personal — reclassify to Owner's Draw |
| $1,500 laptop → Office Supplies | ✅ Under the $2,500 safe harbor — OK to expense |
| $300 software subscription | ✅ Ordinary deductible expense |

**The money shot:** the $12,000 hardware expensed in full. Above the **$2,500 de-minimis safe harbor** it must be capitalized as a Fixed Asset and depreciated — expensing it overstates the deduction and misstates the books. A bookkeeper miscodes it; OpenAccountants catches it.

## Run it

```bash
git clone https://github.com/openaccountants/quickbooks-tax-demo
cd quickbooks-tax-demo
python pipeline.py                       # bundled sample (mock mode, no keys)
python pipeline.py samples/transactions.json
```

### Go live

```bash
export OA_MCP_TOKEN=...        # OpenAccountants account token (uses the live verified rules)
export QBO_ACCESS_TOKEN=...    # QuickBooks Online sandbox token (free, no approval)
export QBO_REALM_ID=...
python pipeline.py
```

## Files

| File | Role |
|------|------|
| `pipeline.py` | Orchestrator + CLI: QBO → OA → verdict report |
| `qbo_client.py` | QuickBooks transaction extraction (live API or bundled sample) |
| `oa_client.py` | OpenAccountants MCP JSON-RPC client (live or mock) |
| `coding_check.py` | Reviews each transaction's tax coding → verdict |
| `samples/transactions.json` | QuickBooks-shaped transactions |

## Honest notes

- `coding_check.py` is a **coding-review signal** (de-minimis capitalization, meals 50%, personal expenses) — not a full chart-of-accounts audit or a depreciation schedule. Production leans on the full OA skill + an agent step; the named-CPA sign-off makes the verdict relianceable.
- Rules (the $2,500 de-minimis safe harbor, 50% meals) are US figures; live, every value comes from `get_skill`. The verifier (Amir Pelinkovic) is the real OpenAccountants US lead.
