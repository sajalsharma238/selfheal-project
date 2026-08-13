"""Kubernetes Deployment agent: manifest / Helm / EKS deploy failures."""

from selfheal.agents.base import FixAgent


class KubernetesAgent(FixAgent):
    name = "kubernetes"
    context_globs = ["k8s/**/*.yaml", "manifests/**/*.yaml", "charts/**/*.yaml", "helm/**/*.yaml"]
    system_prompt = """You are a Kubernetes/EKS expert fixing failed deployments.
Common causes: invalid manifest schemas, wrong apiVersion, image tag mismatches,
missing namespaces, failing probes, Helm template errors. Never widen RBAC beyond
what the error requires and never disable probes to force a rollout through."""
