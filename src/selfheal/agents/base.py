"""Base class for all fix agents: gather files -> ask the model -> sanitize."""

import glob
from pathlib import Path
from selfheal.state import log

# Instructions appended to every fix agent's prompt, describing the patch format.
PATCH_FORMAT = """Return a JSON array of patches. Each patch looks like:
{"path": "relative/path.py", "action": "replace"|"create"|"delete",
 "content": "FULL new file content (empty for delete)", "rationale": "one line why"}
Rules: return the COMPLETE file for replace/create (never a diff). Make the
minimal change that fixes the failure. If you can't find a safe fix, return []."""


class FixAgent:
    name = "base"
    context_globs = []          # extra files this specialist usually needs
    system_prompt = "You are a senior engineer fixing a CI/CD failure."

    def __init__(self, llm, workspace=".", protected_paths=None):
        self.llm = llm
        self.workspace = Path(workspace)
        self.protected_paths = protected_paths or []

    def gather_files(self, state):
        """Read the files the Root Cause agent flagged, plus this agent's globs."""
        paths = list(state.get("files_implicated", []))
        for pattern in self.context_globs:
            for hit in glob.glob(str(self.workspace / pattern), recursive=True):
                rel = str(Path(hit).relative_to(self.workspace))
                if rel not in paths:
                    paths.append(rel)

        files = {}
        for rel in paths[:12]:                        # cap how much we send
            f = self.workspace / rel
            if f.is_file():
                files[rel] = f.read_text(errors="replace")[:30000]
        return files

    def run(self, state):
        files = self.gather_files(state)
        file_block = "\n\n".join(f"===== {p} =====\n{c}" for p, c in files.items()) \
            or "(no files retrieved)"

        user = (
            f"Root cause: {state.get('root_cause', '')}\n\n"
            f"Key errors:\n" + "\n".join(state.get("key_errors", [])) + "\n\n"
            f"Files:\n{file_block}\n\n{PATCH_FORMAT}"
        )
        raw = self.llm.complete_json(self.system_prompt, user)
        patches = self._sanitize(raw, state)
        return {
            "patches": patches,
            "fix_agent": self.name,
            "trace": log(state, f"{self.name}: proposed {len(patches)} patch(es)"),
        }

    def _sanitize(self, raw, state):
        """NEVER trust the model's output. Validate every patch."""
        patches = []
        if not isinstance(raw, list):
            return patches
        for item in raw:
            if not isinstance(item, dict) or not item.get("path"):
                continue
            path = str(item["path"]).lstrip("/")
            if ".." in path.split("/"):                       # block path traversal
                continue
            if any(Path(path).match(p) for p in self.protected_paths):  # block secrets
                log(state, f"{self.name}: skipped protected path {path}")
                continue
            if item.get("action") not in ("replace", "create", "delete"):
                continue
            patches.append({
                "path": path,
                "action": item["action"],
                "content": str(item.get("content", "")),
                "rationale": str(item.get("rationale", ""))[:300],
            })
        return patches