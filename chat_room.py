#!/usr/bin/env python3
"""Interactive chat room with multiple AI personas."""

import argparse
import subprocess
import requests
import json
import readline  # enables arrow keys, history in input()


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
        # Per-persona message history for continuity
        self.history: list[dict] = []

    def respond(self, user_message: str, conversation_context: list[str]) -> str:
        """Generate a response to a message."""
        print(f"\n\033[1;36m{self.name}\033[0m \033[90m({self.backend}:{self.model})\033[0m")
        print("-" * 40)

        # Build context from conversation
        context_str = "\n".join(conversation_context[-20:]) if conversation_context else ""

        prompt = f"""Conversation so far:
{context_str}

[You] {user_message}

Respond naturally and concisely. You are {self.name}."""

        # Add to this persona's history
        self.history.append({"role": "user", "content": prompt})

        if self.backend == "claude":
            response = send_claude_message(self.model, self.system_prompt, self.history)
        else:
            response = send_ollama_message(self.model, self.system_prompt, self.history)

        # Store response in persona's history
        self.history.append({"role": "assistant", "content": response})

        return response


# Available personas
PERSONAS = {
    "architect": Persona(
        name="Architect",
        model="gemma3:1b",
        system_prompt="You are a senior software architect. Focus on design, structure, and trade-offs. Be concise.",
    ),
    "developer": Persona(
        name="Developer",
        model="gemma3:1b",
        system_prompt="You are a pragmatic developer. Focus on implementation and code. Be concise.",
    ),
    "critic": Persona(
        name="Critic",
        model="qwen2.5:0.5b",
        system_prompt="You are a constructive critic. Find issues and suggest fixes. Be direct and concise.",
    ),
    "creative": Persona(
        name="Creative",
        model="qwen2.5:0.5b",
        system_prompt="You are a creative problem solver. Propose novel ideas. Be concise.",
    ),
    "claude": Persona(
        name="Claude",
        model="haiku",
        system_prompt="You are a helpful AI assistant. Be concise and direct.",
        backend="claude",
    ),
    "sonnet": Persona(
        name="Sonnet",
        model="sonnet",
        system_prompt="You are a helpful AI assistant. Be concise and direct.",
        backend="claude",
    ),
}


def print_help():
    """Print help message."""
    print("""
\033[1mChat Room Commands:\033[0m
  @<persona> <message>  - Send message to a specific persona
  @all <message>        - Send message to all active personas
  /add <persona>        - Add a persona to the room
  /remove <persona>     - Remove a persona from the room
  /list                 - List active personas
  /personas             - List all available personas
  /clear                - Clear conversation history
  /help                 - Show this help
  /quit                 - Exit chat room

\033[1mExamples:\033[0m
  @architect Design a REST API for a todo app
  @claude What do you think of Architect's design?
  @all Let's write a haiku together
""")


def main():
    parser = argparse.ArgumentParser(description="Interactive chat room with AI personas")
    parser.add_argument("--personas", "-p", nargs="+", default=["architect", "developer"],
                        help="Initial personas to include (default: architect developer)")
    args = parser.parse_args()

    # Initialize active personas
    active_personas: dict[str, Persona] = {}
    for name in args.personas:
        if name in PERSONAS:
            active_personas[name] = PERSONAS[name]
        else:
            print(f"Warning: Unknown persona '{name}', skipping")

    # Shared conversation log (what everyone sees)
    conversation_log: list[str] = []

    print("\033[1;32m" + "=" * 50 + "\033[0m")
    print("\033[1;32m  AI Chat Room\033[0m")
    print("\033[1;32m" + "=" * 50 + "\033[0m")
    print(f"\nActive personas: {', '.join(active_personas.keys())}")
    print("Type /help for commands, /quit to exit\n")

    while True:
        try:
            user_input = input("\033[1;33mYou:\033[0m ").strip()

            if not user_input:
                continue

            # Commands
            if user_input.startswith("/"):
                cmd = user_input.lower().split()

                if cmd[0] == "/quit" or cmd[0] == "/exit":
                    print("Goodbye!")
                    break

                elif cmd[0] == "/help":
                    print_help()

                elif cmd[0] == "/list":
                    print(f"Active personas: {', '.join(active_personas.keys())}")

                elif cmd[0] == "/personas":
                    print("Available personas:")
                    for name, p in PERSONAS.items():
                        status = "✓" if name in active_personas else " "
                        print(f"  [{status}] {name} ({p.backend}:{p.model})")

                elif cmd[0] == "/add" and len(cmd) > 1:
                    name = cmd[1]
                    if name in PERSONAS:
                        active_personas[name] = PERSONAS[name]
                        print(f"Added {name} to the room")
                    else:
                        print(f"Unknown persona: {name}")

                elif cmd[0] == "/remove" and len(cmd) > 1:
                    name = cmd[1]
                    if name in active_personas:
                        del active_personas[name]
                        print(f"Removed {name} from the room")
                    else:
                        print(f"{name} is not in the room")

                elif cmd[0] == "/clear":
                    conversation_log.clear()
                    for p in active_personas.values():
                        p.history.clear()
                    print("Conversation cleared")

                else:
                    print(f"Unknown command: {cmd[0]}. Type /help for commands.")

                continue

            # @ mentions
            if user_input.startswith("@"):
                parts = user_input.split(" ", 1)
                target = parts[0][1:].lower()  # Remove @
                message = parts[1] if len(parts) > 1 else ""

                if not message:
                    print("Please include a message after the @mention")
                    continue

                # Add user message to log
                conversation_log.append(f"[You -> @{target}]: {message}")

                if target == "all":
                    # Send to all active personas
                    for name, persona in active_personas.items():
                        response = persona.respond(message, conversation_log)
                        conversation_log.append(f"[{persona.name}]: {response}")

                elif target in active_personas:
                    persona = active_personas[target]
                    response = persona.respond(message, conversation_log)
                    conversation_log.append(f"[{persona.name}]: {response}")

                else:
                    print(f"Unknown persona: @{target}")
                    print(f"Active personas: {', '.join(active_personas.keys())}")

            else:
                print("Use @<persona> to address someone, or /help for commands")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except EOFError:
            print("\nGoodbye!")
            break


if __name__ == "__main__":
    main()
