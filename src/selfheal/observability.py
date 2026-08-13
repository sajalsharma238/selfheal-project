"""Observability: a Markdown report on the run page + a metrics JSON file."""

import json
import os
import time
from pathlib import Path

_START = time.time()


def write_summary(state):
    """Write a Markdown report to the GitHub Actions step summary (if available)."""
    lines = [
        "## 🩹 Self-Heal Report",
        "",
        f"- **Category:** `{state.get('category', 'unknown')}`",
        f"- **Confidence:** {state.get('confidence', 0):.0%}",
        f"- **Fix agent:** {state.get('fix_agent', '—')}",
        f"- **Verified:** {'✅' if state.get('verified') else '❌'}",
        f"- **Outcome:** {state.get('outcome', '—')}",
        f"- **PR:** {state.get('pr_url', '—')}",
        "",
        "### Root cause",
        state.get("root_cause", "n/a"),
        "",
        "### Patches",
    ]
    for p in state.get("patches", []):
        lines.append(f"- `{p['action']}` **{p['path']}** — {p['rationale']}")
    if not state.get("patches"):
        lines.append("_none_")

    text = "\n".join(lines)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a") as f:
            f.write(text + "\n")
    else:
        print(text)


def write_metrics(state, path="selfheal-metrics.json"):
    """Emit machine-readable metrics for dashboards (MTTR, categories, outcomes)."""
    metrics = {
        "run_id": state.get("run_id"),
        "category": state.get("category"),
        "confidence": state.get("confidence"),
        "attempts": state.get("attempts", 0),
        "verified": state.get("verified", False),
        "outcome": state.get("outcome"),
        "pr_url": state.get("pr_url"),
        "patched_files": [p["path"] for p in state.get("patches", [])],
        "duration_seconds": round(time.time() - _START, 1),
    }
    Path(path).write_text(json.dumps(metrics, indent=2))
