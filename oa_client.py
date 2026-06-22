"""OpenAccountants MCP client.

JSON-RPC 2.0 to https://www.openaccountants.com/api/mcp. The MCP requires auth on
tool calls (OA_MCP_TOKEN) for live mode; without one it returns bundled sample
responses that mirror the live shape so the demo runs end to end.

  - start(intent, jurisdiction)  -> which verified skill governs the question
  - get_skill(slug)              -> the bookkeeping/tax rules + tier + named verifier
"""

from __future__ import annotations

import json
import os
import urllib.request
import urllib.error

MCP_URL = os.environ.get("OA_MCP_URL", "https://www.openaccountants.com/api/mcp")
MCP_TOKEN = os.environ.get("OA_MCP_TOKEN")


class OAClient:
    def __init__(self, token: str | None = MCP_TOKEN, url: str = MCP_URL):
        self.token, self.url, self._id = token, url, 0

    @property
    def live(self) -> bool:
        return bool(self.token)

    def start(self, intent: str, jurisdiction: str) -> dict:
        if not self.live:
            return _MOCK_START.get(jurisdiction.upper(), _MOCK_START["_DEFAULT"])
        return self._call("start", {"intent": intent, "jurisdiction": jurisdiction})

    def get_skill(self, slug: str) -> dict:
        if not self.live:
            return _MOCK_SKILL.get(slug, _MOCK_SKILL["_DEFAULT"])
        return self._call("get_skill", {"slug": slug})

    def _call(self, tool: str, arguments: dict) -> dict:
        self._id += 1
        body = json.dumps({"jsonrpc": "2.0", "id": self._id, "method": "tools/call",
                           "params": {"name": tool, "arguments": arguments}}).encode()
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"  # scheme TBD; swap if OA uses apikey
        req = urllib.request.Request(self.url, data=body, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = json.load(resp)
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"OA MCP HTTP {e.code}: {e.read().decode()[:300]}") from e
        if "error" in payload and payload["error"]:
            raise RuntimeError(f"OA MCP error: {payload['error']}")
        result = payload.get("result", {})
        if isinstance(result.get("structuredContent"), (dict, list)):
            return result["structuredContent"]
        return json.loads((result.get("content") or [{}])[0].get("text", "{}"))


# --- Bundled sample responses (mirror live MCP shape) ----------------------
# Verifier is the real OpenAccountants US lead. Live, every value comes from get_skill.

_MOCK_START = {
    "US": {"jurisdiction": "US", "skills_to_load": ["us-bookkeeping-coding"],
           "next_action": "Load the skill, then review each transaction's tax coding."},
    "_DEFAULT": {"jurisdiction": "US", "skills_to_load": ["us-bookkeeping-coding"],
                 "next_action": "Load the skill, then review each transaction's tax coding."},
}

_MOCK_SKILL = {
    "us-bookkeeping-coding": {
        "slug": "us-bookkeeping-coding",
        "name": "US bookkeeping / tax coding review",
        "jurisdiction": "US", "tier": 1, "verifier": "Amir Pelinkovic (US lead)",
        "rules": {
            # Illustrative — production reads these from the skill.
            "de_minimis_safe_harbor": 2500.0,   # capitalize tangible property above this
            "meals_deductible_pct": 0.5,        # business meals 50%
            "personal_not_deductible": True,    # owner personal -> Owner's Draw
        },
        "source": "https://www.openaccountants.com/skills/us-bookkeeping-coding",
    },
    "_DEFAULT": {"slug": "us-bookkeeping-coding", "name": "Bookkeeping coding",
                 "jurisdiction": "US", "tier": 2, "verifier": None, "rules": {},
                 "source": "https://www.openaccountants.com/skills"},
}
