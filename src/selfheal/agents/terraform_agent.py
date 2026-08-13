"""IaC / Terraform agent: plan and apply failures."""

from selfheal.agents.base import FixAgent


class TerraformAgent(FixAgent):
    name = "terraform"
    context_globs = ["**/*.tf", "**/*.tfvars"]
    system_prompt = """You are a Terraform/IaC expert fixing failed plans and applies.
Common causes: syntax errors, provider version constraints, missing required
arguments, deprecated attributes, bad references. NEVER propose changes that destroy
or replace stateful resources (databases, volumes, buckets) — if the fix needs that,
return [] and note a human must review."""
