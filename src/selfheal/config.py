"""Reads configuration from environment variables."""

import os
from dataclasses import dataclass, field
from pathlib import Path
import yaml


@dataclass
class Config:
    github_token: str
    api_key: str
    repo: str
    run_id: int
    provider: str = "anthropic"
    model: str = "claude-sonnet-5"
    dry_run: bool = False
    workspace: Path = field(default_factory=Path.cwd)
    verify_commands: list = field(default_factory=lambda: ["python -m pytest -q"])
    max_attempts: int = 2
    protected_paths: list = field(default_factory=lambda: ["**/secrets*", "**/*.pem"])
    base_branch: str = "main"


def load_config():
    api_key = os.environ.get("SELFHEAL_API_KEY") or os.environ.get("ANTHROPIC_API_KEY", "")
    cfg = Config(
        github_token=os.environ.get("GITHUB_TOKEN", ""),
        api_key=api_key,
        repo=os.environ.get("SELFHEAL_REPO", ""),
        run_id=int(os.environ.get("SELFHEAL_RUN_ID", "0")),
        provider=os.environ.get("SELFHEAL_PROVIDER", "anthropic"),
        model=os.environ.get("SELFHEAL_MODEL", "claude-sonnet-5"),
        dry_run=os.environ.get("SELFHEAL_DRY_RUN", "false").lower() == "true",
    )

    # If the target repo has a .selfheal.yml, let it override the defaults.
    yml = cfg.workspace / ".selfheal.yml"
    if yml.exists():
        data = yaml.safe_load(yml.read_text()) or {}
        cfg.verify_commands = data.get("verify", cfg.verify_commands)
        cfg.max_attempts = int(data.get("max_attempts", cfg.max_attempts))
        cfg.protected_paths = data.get("protected_paths", cfg.protected_paths)
        cfg.base_branch = data.get("base_branch", cfg.base_branch)
    return cfg