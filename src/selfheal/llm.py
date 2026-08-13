"""Talks to the AI model and pulls JSON out of its replies."""

import json
import re
import anthropic


class LLM:
    """A thin wrapper around the Claude API."""

    def __init__(self, api_key, model="claude-sonnet-5", max_tokens=8192):
        self._client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens

    def complete(self, system, user):
        """Send a system + user prompt, get back plain text."""
        msg = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(block.text for block in msg.content if block.type == "text")

    def complete_json(self, system, user):
        """Same, but force the reply to be JSON and parse it."""
        text = self.complete(
            system + "\nReply with valid JSON only. No prose, no code fences.",
            user,
        )
        return extract_json(text)

def extract_json(text):
    """Find and parse the JSON in a model's reply, even if it's wrapped in
```code fences``` or surrounded by chatty prose."""
    text = text.strip()

    # If the model wrapped the JSON in ```json ... ``` fences, grab the inside.
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()

    # Try parsing the whole thing as JSON.
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Otherwise, find the first {...} block and parse just that.
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        return json.loads(text[start:end + 1])

    raise ValueError("No JSON found in the model's reply")