"""Root Cause agent: classifies the failure into one category and explains it."""

from selfheal.state import log

# The categories the pipeline knows how to route to.
CATEGORIES = [
    "code", "tests", "dependencies", "workflow_yaml", "docker",
    "kubernetes", "terraform", "database", "security", "flaky", "unknown",
]

SYSTEM = f"""You are a root-cause analysis expert for CI/CD failures.
Classify the failure into exactly ONE category from: {", ".join(CATEGORIES)}.
Use 'flaky' ONLY for transient issues (network timeouts, registry 5xx, runner
hiccups) where simply re-running would likely succeed. When unsure between a real
bug and flaky, pick the real bug."""


class RootCauseAgent:
    name = "root_cause"

    def __init__(self, llm):
        self.llm = llm

    def run(self, state):
        result = self.llm.complete_json(
            SYSTEM,
            f"Failure summary:\n{state.get('failure_summary', '')}\n\n"
            f"Key errors:\n" + "\n".join(state.get("key_errors", [])) + "\n\n"
            'Return JSON: {"category": "<one category>", '
            '"root_cause": "detailed explanation", '
            '"confidence": 0.0-1.0, '
            '"files_implicated": ["likely files to change"]}',
        )

        category = result.get("category", "unknown")
        if category not in CATEGORIES:
            category = "unknown"

        return {
            "category": category,
            "root_cause": result.get("root_cause", ""),
            "confidence": float(result.get("confidence", 0.0)),
            "files_implicated": result.get("files_implicated", []),
            "trace": log(state, f"root_cause: {category}"),
        }