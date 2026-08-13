"""Verification agent: applies patches and runs the REAL test commands.
No AI here — a fix must prove itself against actual commands."""

import subprocess
from pathlib import Path
from selfheal.state import log


class VerificationAgent:
    name = "verification"

    def __init__(self, verify_commands, workspace="."):
        self.verify_commands = verify_commands   # e.g. ["python -m pytest -q"]
        self.workspace = Path(workspace)

    def run(self, state):
        # 1. Write every patch to disk.
        for p in state.get("patches", []):
            target = self.workspace / p["path"]
            if p["action"] == "delete":
                if target.exists():
                    target.unlink()
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(p["content"])

        # 2. Run each verify command; ALL must exit 0.
        attempts = state.get("attempts", 0) + 1
        outputs = []
        passed = True
        for cmd in self.verify_commands:
            proc = subprocess.run(
                cmd, shell=True, cwd=self.workspace,
                capture_output=True, text=True, timeout=900,
            )
            outputs.append(f"$ {cmd}\n(exit {proc.returncode})\n{proc.stdout}{proc.stderr}")
            if proc.returncode != 0:
                passed = False
                break

        output = "\n\n".join(outputs)
        return {
            "verified": passed,
            "verification_output": output,
            "attempts": attempts,
            "feedback": "" if passed else output,   # fed back to the fix agent on retry
            "trace": log(state, f"verification: {'PASSED' if passed else 'FAILED'} (attempt {attempts})"),
        }