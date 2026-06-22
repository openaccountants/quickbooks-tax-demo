"""Review a QuickBooks transaction's tax coding against the loaded OA rules.

The catches a category alone won't flag:
  - a **capital asset expensed** instead of capitalized (over the de-minimis
    safe harbor it should be a Fixed Asset, depreciated / §179) — the classic
  - **business meals** coded at 100% (they're 50%)
  - an **owner's personal** expense sitting in the business books

DELIBERATE SCOPE: a coding-review signal, not a full chart-of-accounts audit.
Production leans on the full OA skill + an agent step; the named-CPA sign-off
makes it relianceable.
"""

from __future__ import annotations

CAPITAL_HINTS = ("equipment", "machine", "machinery", "furniture", "server",
                 "workstation", "vehicle", "laptop", "computer", "camera", "hardware")


def check(t: dict, oa_skill: dict) -> dict:
    rules = oa_skill.get("rules", {})
    base = {"oa_skill": oa_skill.get("slug"), "oa_skill_name": oa_skill.get("name"),
            "tier": oa_skill.get("tier"), "verifier": oa_skill.get("verifier")}
    de_minimis = rules.get("de_minimis_safe_harbor", 2500.0)
    amt = t["amount"]
    text = f"{t['account']} {t['description']} {t['vendor']}".lower()
    acct = t["account"].lower()

    is_personal = "personal" in text or "owner" in text
    is_capital = any(h in text for h in CAPITAL_HINTS)
    is_meal = any(h in text for h in ("meal", "restaurant", "dining", "lunch", "dinner"))
    coded_fixed_asset = "fixed asset" in acct or "asset" in acct

    if is_personal:
        return {**base, "status": "warn",
                "headline": "Personal expense in the business books — not deductible",
                "detail": f"Coded to '{t['account']}'. Reclassify to Owner's Draw / distribution; it's not a deductible business expense."}

    if is_capital and amt > de_minimis and not coded_fixed_asset:
        return {**base, "status": "warn",
                "headline": f"Capital asset expensed — should be capitalized (> ${de_minimis:,.0f} safe harbor)",
                "detail": f"${amt:,.0f} coded to '{t['account']}'. Above the de-minimis safe harbor it should be a Fixed Asset and depreciated (or elect §179/bonus), not expensed."}

    if is_capital and amt <= de_minimis:
        return {**base, "status": "ok",
                "headline": f"Under the ${de_minimis:,.0f} de-minimis safe harbor — OK to expense",
                "detail": f"${amt:,.0f} tangible property; fine to expense rather than capitalize."}

    if is_meal and ("100" in text):
        pct = int(rules.get("meals_deductible_pct", 0.5) * 100)
        return {**base, "status": "warn",
                "headline": f"Business meals are {pct}% deductible — coded at 100%",
                "detail": f"Coded to '{t['account']}'. Move to a {pct}%-meals account so the deduction is limited correctly."}

    if is_meal:
        pct = int(rules.get("meals_deductible_pct", 0.5) * 100)
        return {**base, "status": "info",
                "headline": f"Meal — {pct}% deductible",
                "detail": f"Ensure '{t['account']}' is a {pct}%-meals account, and keep the business-purpose note."}

    return {**base, "status": "ok", "headline": "Coding looks fine",
            "detail": f"${amt:,.0f} to '{t['account']}' — ordinary deductible business expense."}
