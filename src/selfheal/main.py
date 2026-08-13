"""The `selfheal run` command — the real entry point used inside GitHub Actions."""

import argparse
import sys

from selfheal.config import load_config
from selfheal.github_client import GitHubClient
from selfheal.llm import LLM
from selfheal.graph import build_graph
from selfheal.observability import write_summary, write_metrics


def run():
    cfg = load_config()

    # Fail loudly if something required is missing.
    missing = [n for n, v in [
        ("GITHUB_TOKEN", cfg.github_token),
        ("SELFHEAL_REPO", cfg.repo),
        ("SELFHEAL_RUN_ID", cfg.run_id),
        ("API key", cfg.api_key),
    ] if not v]
    if missing:
        print(f"::error::selfheal: missing config: {', '.join(missing)}")
        return 1

    gh = GitHubClient(cfg.github_token, cfg.repo)
    llm = LLM(cfg.api_key, cfg.model)

    run_info = gh.get_run(cfg.run_id)
    failed = gh.get_failed_jobs(cfg.run_id)
    if not failed:
        print("selfheal: no failed jobs — nothing to do.")
        return 0

    # Turn each failed job into the shape the pipeline expects.
    jobs = [{
        "name": j["name"],
        "logs": gh.get_job_logs(j["id"]),
        "failed_steps": [s["name"] for s in j.get("steps", []) if s.get("conclusion") == "failure"],
    } for j in failed]

    state = {
        "repo": cfg.repo,
        "run_id": cfg.run_id,
        "workflow_name": run_info.get("name", ""),
        "head_branch": run_info.get("head_branch", "main"),
        "failed_jobs": jobs,
        "attempts": 0,
        "trace": [],
    }

    graph = build_graph(
        llm, gh, cfg.workspace, cfg.verify_commands,
        protected_paths=cfg.protected_paths, max_attempts=cfg.max_attempts,
        dry_run=cfg.dry_run, base_branch=state["head_branch"],
    )
    final = graph.invoke(state)
    write_summary(final)      # Markdown report on the run page
    write_metrics(final)      # metrics JSON for dashboards
    print(f"selfheal: outcome = {final.get('outcome')}  pr = {final.get('pr_url', '-')}")
    return 0


def cli():
    parser = argparse.ArgumentParser(prog="selfheal")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("run", help="Heal the failed run given by SELFHEAL_RUN_ID.")
    args = parser.parse_args()
    if args.command == "run":
        sys.exit(run())


if __name__ == "__main__":
    cli()