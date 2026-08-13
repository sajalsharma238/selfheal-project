"""Docker Troubleshooting agent: image build failures."""

from selfheal.agents.base import FixAgent


class DockerAgent(FixAgent):
    name = "docker"
    context_globs = ["Dockerfile*", "**/Dockerfile*", "docker-compose*.yml"]
    system_prompt = """You are a Docker expert fixing failed image builds in CI.
Common causes: missing base image tags, apt/apk failures, wrong build-context paths,
COPY of nonexistent files, missing build args. Prefer pinned, slim base images and
fix only what the build error requires."""
