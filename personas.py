"""Shared persona loading and AI backend utilities."""

import json
import subprocess
import requests
from pathlib import Path


def send_ollama_message(model: str, system_prompt: str, messages: list[dict]) -> str:
    """Send messages to Ollama and get a response."""
    url = "http://localhost:11434/api/chat"

    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system_prompt}] + messages,
        "stream": True,
    }

    response = requests.post(url, json=payload, stream=True)
    response.raise_for_status()

    full_response = ""
    for line in response.iter_lines():
        if line:
            data = json.loads(line)
            chunk = data.get("message", {}).get("content", "")
            print(chunk, end="", flush=True)
            full_response += chunk
            if data.get("done"):
                print()
                break

    return full_response


def send_claude_message(model: str, system_prompt: str, messages: list[dict]) -> str:
    """Send messages to Claude CLI and get a response."""
    # Build the prompt from messages
    prompt = messages[-1]["content"] if messages else ""

    # Include recent context in the prompt
    context = ""
    if len(messages) > 1:
        context = "Recent conversation:\n"
        for msg in messages[-10:-1]:  # Last 10 messages for context
            context += f"{msg['content']}\n"
        context += "\nNow respond to:\n"

    full_prompt = context + prompt

    cmd = [
        "claude",
        "-p",
        "--model", model,
        "--system-prompt", system_prompt,
        full_prompt
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error: {result.stderr}", flush=True)
        return f"[Error: {result.stderr}]"

    response = result.stdout.strip()
    print(response, flush=True)
    return response


class Persona:
    """AI persona that can participate in chat."""
    def __init__(self, name: str, model: str, system_prompt: str, backend: str = "ollama"):
        self.name = name
        self.model = model
        self.system_prompt = system_prompt
        self.backend = backend
        self.history: list[dict] = []

    def respond(self, messages: list[dict], show_header: bool = True) -> str:
        """Generate a response to messages."""
        if show_header:
            print(f"\n{'='*60}")
            print(f"{self.name} ({self.backend}:{self.model}):")
            print(f"{'='*60}")

        if self.backend == "claude":
            return send_claude_message(self.model, self.system_prompt, messages)
        else:
            return send_ollama_message(self.model, self.system_prompt, messages)

    def respond_with_history(self, user_message: str, conversation_context: list[str]) -> str:
        """Generate a response using persona's own history for continuity."""
        print(f"\n\033[1;36m{self.name}\033[0m \033[90m({self.backend}:{self.model})\033[0m")
        print("-" * 40)

        context_str = "\n".join(conversation_context[-20:]) if conversation_context else ""

        prompt = f"""Conversation so far:
{context_str}

[You] {user_message}

Respond naturally and concisely. You are {self.name}."""

        self.history.append({"role": "user", "content": prompt})

        if self.backend == "claude":
            response = send_claude_message(self.model, self.system_prompt, self.history)
        else:
            response = send_ollama_message(self.model, self.system_prompt, self.history)

        self.history.append({"role": "assistant", "content": response})
        return response

    @classmethod
    def from_dict(cls, data: dict) -> "Persona":
        """Create a Persona from a dictionary."""
        return cls(
            name=data["name"],
            model=data["model"],
            system_prompt=data["system_prompt"],
            backend=data.get("backend", "ollama"),
        )


def load_personas(config_path: str | Path | None = None) -> dict[str, Persona]:
    """Load personas from JSON config file."""
    if config_path is None:
        config_path = Path(__file__).parent / "personas.json"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Personas config not found: {config_path}")

    with open(config_path) as f:
        data = json.load(f)

    return {key: Persona.from_dict(value) for key, value in data.items()}
