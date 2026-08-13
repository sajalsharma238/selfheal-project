"""The LangGraph orchestrator — connects every agent into one flowing machine."""

from langgraph.graph import StateGraph, END

from selfheal.state import PipelineState, log
from selfheal.agents.log_analysis import LogAnalysisAgent
from selfheal.agents.root_cause import RootCauseAgent
from selfheal.agents.code_fix import CodeFixAgent
from selfheal.agents.yaml_fix import YamlFixAgent
from selfheal.agents.docker_agent import DockerAgent
from selfheal.agents.kubernetes_agent import KubernetesAgent
from selfheal.agents.terraform_agent import TerraformAgent
from selfheal.agents.db_migration_agent import DBMigrationAgent
from selfheal.agents.security_agent import SecurityAgent
from selfheal.agents.verification import VerificationAgent

# Which fix agent handles each failure category.
FIX_AGENTS = {
    "code": CodeFixAgent,
    "tests": CodeFixAgent,
    "dependencies": CodeFixAgent,
    "workflow_yaml": YamlFixAgent,
    "docker": DockerAgent,
    "kubernetes": KubernetesAgent,
    "terraform": TerraformAgent,
    "database": DBMigrationAgent,
    "security": SecurityAgent,
    "unknown": CodeFixAgent,
}


def build_graph(llm, gh, workspace, verify_commands,
                protected_paths=None, max_attempts=2, dry_run=True, base_branch="main"):

    log_agent = LogAnalysisAgent(llm)
    rc_agent = RootCauseAgent(llm)
    verifier = VerificationAgent(verify_commands, workspace)

    # ---------- NODES (each is a step in the pipeline) ----------

    def fix(state):
        agent_cls = FIX_AGENTS.get(state.get("category"), CodeFixAgent)
        agent = agent_cls(llm, workspace, protected_paths)
        return agent.run(state)

    def retrigger(state):
        if not dry_run:
            gh.rerun_failed_jobs(state["run_id"])
        return {"outcome": "retriggered", "trace": log(state, "retrigger: re-ran the pipeline")}

    def finalize(state):
        if not state.get("patches"):
            return {"outcome": "no_action", "trace": log(state, "finalize: no safe fix found")}
        if dry_run:
            return {"outcome": "no_action", "trace": log(state, "finalize: dry run, no PR opened")}
        verified = state.get("verified", False)
        url = gh.create_pr(f"selfheal/fix-{state['run_id']}", base_branch,
                           f"fix(ci): auto-fix run {state['run_id']}",
                           state.get("root_cause", ""), draft=not verified)
        return {"pr_url": url, "outcome": "pr_created" if verified else "draft_pr_created",
                "trace": log(state, f"finalize: opened {url}")}

    # ---------- ROUTING (the decision arrows) ----------

    def after_root_cause(state):
        return "retrigger" if state.get("category") == "flaky" else "fix"

    def after_fix(state):
        return "verify" if state.get("patches") else "finalize"

    def after_verify(state):
        if state.get("verified"):
            return "finalize"
        return "fix" if state.get("attempts", 0) < max_attempts else "finalize"

    # ---------- ASSEMBLY (register nodes + connect the arrows) ----------

    g = StateGraph(PipelineState)
    g.add_node("log_analysis", log_agent.run)
    g.add_node("root_cause", rc_agent.run)
    g.add_node("fix", fix)
    g.add_node("verify", verifier.run)
    g.add_node("retrigger", retrigger)
    g.add_node("finalize", finalize)

    g.set_entry_point("log_analysis")
    g.add_edge("log_analysis", "root_cause")
    g.add_conditional_edges("root_cause", after_root_cause, ["retrigger", "fix"])
    g.add_conditional_edges("fix", after_fix, ["verify", "finalize"])
    g.add_conditional_edges("verify", after_verify, ["fix", "finalize"])
    g.add_edge("retrigger", END)
    g.add_edge("finalize", END)
    return g.compile()