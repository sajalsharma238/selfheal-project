"""YAML / Workflow Fix agent: broken GitHub Actions workflow files."""

from selfheal.agents.base import FixAgent


class YamlFixAgent(FixAgent):
    name = "yaml_fix"
    context_globs = [".github/workflows/*.yml", ".github/workflows/*.yaml"]
    system_prompt = """You are a GitHub Actions expert fixing broken workflow YAML.
Common causes: bad indentation, wrong action versions, invalid expressions, missing
permissions blocks, undefined secrets/env references. Preserve the workflow's intent
exactly and fix only what is broken. Use current stable action versions."""
