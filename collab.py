#!/usr/bin/env python3
"""Two AI personas collaborating on a task."""

import argparse
import subprocess
import requests
import json


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
    prompt = messages[0]["content"] if messages else ""

    cmd = [
        "claude",
        "-p",  # Print mode (non-interactive)
        "--model", model,
        "--system-prompt", system_prompt,
        prompt
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error: {result.stderr}", flush=True)
        return f"[Error: {result.stderr}]"

    # Print streaming-style for consistency
    response = result.stdout.strip()
    print(response, flush=True)
    return response


class Persona:
    """Base persona class."""
    def __init__(self, name: str, model: str, system_prompt: str, backend: str = "ollama"):
        self.name = name
        self.model = model
        self.system_prompt = system_prompt
        self.backend = backend  # "ollama" or "claude"

    def respond(self, messages: list[dict]) -> str:
        print(f"\n{'='*60}")
        print(f"{self.name} ({self.backend}:{self.model}):")
        print(f"{'='*60}")

        if self.backend == "claude":
            return send_claude_message(self.model, self.system_prompt, messages)
        else:
            return send_ollama_message(self.model, self.system_prompt, messages)


# Example personas - customize these
PERSONAS = {
    "architect": Persona(
        name="Architect",
        model="gemma3:1b",
        system_prompt="""You are a senior software architect. You MUST:
- Propose concrete designs, not just ask questions
- Include diagrams, structures, or pseudocode in every response
- Build on your collaborator's ideas with specific improvements

Keep responses focused. Produce artifacts, not discussion.""",
    ),
    "developer": Persona(
        name="Developer",
        model="gemma3:1b",
        system_prompt="""You are a pragmatic developer. You MUST:
- Write actual code or pseudocode in every response
- Take ideas and make them concrete implementations
- Point out specific issues and fix them immediately

Keep responses focused. Produce code, not discussion.""",
    ),
    "critic": Persona(
        name="Critic",
        model="gemma3:1b",
        system_prompt="""You are a constructive critic. You MUST:
- Find specific flaws and propose fixes in the same response
- Never just ask questions - always include your suggested answer
- Be direct and specific, not vague

Keep responses focused. Critique AND improve, don't just question.""",
    ),
    "creative": Persona(
        name="Creative",
        model="gemma3:1b",
        system_prompt="""You are a creative problem solver. You MUST:
- Propose bold, specific ideas - not vague suggestions
- Include concrete examples or prototypes
- Build on others' work with unexpected additions

Keep responses focused. Create artifacts, not discussion.""",
    ),
    # Claude personas
    "claude-sonnet": Persona(
        name="Claude-Sonnet",
        model="sonnet",
        system_prompt="""You are collaborating with another AI. You MUST:
- Produce concrete output (code, text, designs) in every response
- Build directly on what your partner created
- Never just ask questions - always include your contribution

Be concise. Create, don't discuss.""",
        backend="claude",
    ),
    "claude-haiku": Persona(
        name="Claude-Haiku",
        model="haiku",
        system_prompt="""You are collaborating with another AI. You MUST:
- Produce concrete output (code, text, designs) in every response
- Build directly on what your partner created
- Never just ask questions - always include your contribution

Be concise. Create, don't discuss.""",
        backend="claude",
    ),
}


def run_collaboration(persona1: Persona, persona2: Persona, task: str, rounds: int = 3):
    """Run a multi-round collaboration between two personas."""
    print(f"\n{'#'*60}")
    print(f"TASK: {task}")
    print(f"{'#'*60}")
    print(f"\nCollaborators: {persona1.name} + {persona2.name}")
    print(f"Rounds: {rounds}")

    # Shared conversation history
    conversation_log = []

    current = persona1
    other = persona2

    for i in range(rounds * 2):  # Each round = both personas speak once
        # Build messages: task context + conversation so far + prompt to respond
        messages = [{"role": "user", "content": f"""Task: {task}

You are collaborating with {other.name}. Here's the conversation so far:

{chr(10).join(conversation_log) if conversation_log else "(No messages yet - you start!)"}

Now it's your turn. Respond as {current.name}. Remember: produce concrete output, not just discussion."""}]

        response = current.respond(messages)
        conversation_log.append(f"[{current.name}]: {response}")

        # Swap
        current, other = other, current

    print(f"\n{'#'*60}")
    print("COLLABORATION COMPLETE")
    print(f"{'#'*60}")

    return conversation_log


def main():
    parser = argparse.ArgumentParser(description="Two AI personas collaborate on a task")
    parser.add_argument("task", nargs="?", help="The task for the personas to work on")
    parser.add_argument("-p1", "--persona1", default="architect", choices=PERSONAS.keys(),
                        help="First persona (default: architect)")
    parser.add_argument("-p2", "--persona2", default="developer", choices=PERSONAS.keys(),
                        help="Second persona (default: developer)")
    parser.add_argument("-r", "--rounds", type=int, default=3,
                        help="Number of back-and-forth rounds (default: 3)")
    parser.add_argument("-m1", "--model1", help="Override model for persona 1")
    parser.add_argument("-m2", "--model2", help="Override model for persona 2")
    parser.add_argument("-l", "--list", action="store_true", help="List available personas")

    args = parser.parse_args()

    if args.list:
        print("Available personas:")
        for name, p in PERSONAS.items():
            print(f"\n  {name} ({p.backend}:{p.model}):")
            print(f"    {p.system_prompt.split(chr(10))[0]}")
        return

    if not args.task:
        parser.error("task is required (unless using -l/--list)")

    p1 = PERSONAS[args.persona1]
    p2 = PERSONAS[args.persona2]

    # Allow model overrides
    if args.model1:
        p1.model = args.model1
    if args.model2:
        p2.model = args.model2

    run_collaboration(p1, p2, args.task, args.rounds)


if __name__ == "__main__":
    main()
