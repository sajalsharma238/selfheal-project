"""Code Fix agent: application bugs, failing tests, dependency problems."""

from selfheal.agents.base import FixAgent


class CodeFixAgent(FixAgent):
    name = "code_fix"
    context_globs = ["pyproject.toml", "requirements*.txt"]
    system_prompt = """You are a senior software engineer fixing a broken build or
failing tests in CI. Fix the actual bug — never delete tests, weaken assertions, or
suppress errors just to make CI pass. If the code is wrong, fix the code; if a test
is genuinely stale, fix the test and say so in the rationale."""