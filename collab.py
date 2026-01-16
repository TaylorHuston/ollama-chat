#!/usr/bin/env python3
"""Two AI personas collaborating on a task."""

import argparse
import requests
import json


def send_message(model: str, system_prompt: str, messages: list[dict]) -> str:
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


class Persona:
    def __init__(self, name: str, model: str, system_prompt: str):
        self.name = name
        self.model = model
        self.system_prompt = system_prompt

    def respond(self, messages: list[dict]) -> str:
        print(f"\n{'='*60}")
        print(f"{self.name} ({self.model}):")
        print(f"{'='*60}")
        return send_message(self.model, self.system_prompt, messages)


# Example personas - customize these
PERSONAS = {
    "architect": Persona(
        name="Architect",
        model="gemma3:1b",
        system_prompt="""You are a senior software architect. You focus on:
- High-level design and system structure
- Trade-offs between different approaches
- Scalability and maintainability concerns
- Asking clarifying questions about requirements

When collaborating, build on your partner's ideas and offer concrete suggestions.
Keep responses focused and actionable.""",
    ),
    "developer": Persona(
        name="Developer",
        model="gemma3:1b",
        system_prompt="""You are a pragmatic developer. You focus on:
- Practical implementation details
- Code examples and specific solutions
- Potential edge cases and gotchas
- Getting things working quickly

When collaborating, take architectural suggestions and make them concrete.
Propose specific implementations and ask for feedback.""",
    ),
    "critic": Persona(
        name="Critic",
        model="gemma3:1b",
        system_prompt="""You are a constructive critic and devil's advocate. You focus on:
- Finding flaws and weaknesses in proposals
- Asking hard questions
- Suggesting alternatives
- Ensuring nothing important is overlooked

Be respectful but thorough. Your job is to make the final result better.""",
    ),
    "creative": Persona(
        name="Creative",
        model="gemma3:1b",
        system_prompt="""You are a creative problem solver. You focus on:
- Novel approaches and unconventional ideas
- Making connections between different domains
- "What if" scenarios
- Pushing beyond obvious solutions

Don't self-censor. Propose bold ideas for others to refine.""",
    ),
}


def run_collaboration(persona1: Persona, persona2: Persona, task: str, rounds: int = 3):
    """Run a multi-round collaboration between two personas."""
    print(f"\n{'#'*60}")
    print(f"TASK: {task}")
    print(f"{'#'*60}")
    print(f"\nCollaborators: {persona1.name} + {persona2.name}")
    print(f"Rounds: {rounds}")

    # Shared conversation history (what both personas see)
    # All prior exchanges are "user" messages so the model doesn't confuse itself
    conversation_log = []

    current = persona1
    other = persona2

    for i in range(rounds * 2):  # Each round = both personas speak once
        # Build messages: task context + conversation so far + prompt to respond
        messages = [{"role": "user", "content": f"""Task: {task}

You are collaborating with {other.name}. Here's the conversation so far:

{chr(10).join(conversation_log) if conversation_log else "(No messages yet - you start!)"}

Now it's your turn. Respond as {current.name}."""}]

        response = current.respond(messages)
        conversation_log.append(f"[{current.name}]: {response}")

        # Swap
        current, other = other, current

    print(f"\n{'#'*60}")
    print("COLLABORATION COMPLETE")
    print(f"{'#'*60}")

    return messages


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
            print(f"\n  {name} ({p.model}):")
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
