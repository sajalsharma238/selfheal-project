"""Log Analysis agent: turns raw CI logs into a short summary + key errors."""

from selfheal.state import log

SYSTEM = """You are a CI/CD log analysis expert. You read raw GitHub Actions logs
from failed jobs and extract exactly what failed. Be precise: quote real error
lines and name files and line numbers when you see them."""


class LogAnalysisAgent:
    name = "log_analysis"

    def __init__(self, llm):
        self.llm = llm

    def run(self, state):
        # Stitch all the failed jobs' logs into one block for the model.
        jobs_block = "\n\n".join(
            f"===== JOB: {j['name']} =====\n{j['logs']}"
            for j in state.get("failed_jobs", [])
        )

        result = self.llm.complete_json(
            SYSTEM,
            f"Analyze these failed job logs:\n\n{jobs_block}\n\n"
            'Return JSON: {"failure_summary": "2-4 sentences on what failed", '
            '"key_errors": ["verbatim error line", "..."]}',
        )

        return {
            "failure_summary": result.get("failure_summary", ""),
            "key_errors": result.get("key_errors", []),
            "trace": log(state, "log_analysis: summarized the failure"),
        }