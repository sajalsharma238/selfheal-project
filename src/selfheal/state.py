"""The shared 'clipboard' that flows through the whole pipeline.

Every agent reads some fields and writes others. total=False means every field
is optional — the pipeline fills them in as it goes."""

from typing import TypedDict


class Patch(TypedDict):
    """One file change proposed by a fix agent."""
    path: str          # which file, e.g. "src/app.py"
    action: str        # "replace", "create", or "delete"
    content: str       # the full new contents of the file
    rationale: str     # one line: why this change


class FailedJob(TypedDict):
    """One failed CI job we pulled from GitHub."""
    name: str          # job name, e.g. "unit-tests"
    logs: str          # the raw log text
    failed_steps: list[str]


class PipelineState(TypedDict, total=False):
    # --- filled in before the pipeline starts ---
    repo: str                    # "owner/name"
    run_id: int                  # the failed workflow run
    workflow_name: str
    head_branch: str
    failed_jobs: list[FailedJob]

    # --- written by the Log Analysis agent ---
    failure_summary: str
    key_errors: list[str]

    # --- written by the Root Cause agent ---
    category: str                # code | tests | docker | ... | flaky
    root_cause: str
    confidence: float
    files_implicated: list[str]

    # --- written by the Fix agents ---
    fix_agent: str
    patches: list[Patch]
    attempts: int
    feedback: str                # verification output, fed back on a retry

    # --- written by the Verification agent ---
    verified: bool
    verification_output: str

    # --- the final outcome ---
    outcome: str                 # pr_created | draft_pr_created | retriggered | no_action | error
    pr_url: str
    trace: list[str]             # human-readable log of what happened


def log(state, message):
    """Append a line to the state's trace and print it, so you can watch the
    pipeline think in real time. Returns the updated trace list."""
    trace = list(state.get("trace", []))
    trace.append(message)
    print("[selfheal]", message)
    return trace