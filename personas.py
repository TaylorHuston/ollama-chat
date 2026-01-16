"""Shared persona loading and LangChain-based AI backends."""

import json
from pathlib import Path

from langchain_ollama import ChatOllama
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


def get_llm(backend: str, model: str):
    """Get a LangChain chat model for the given backend."""
    if backend == "ollama":
        return ChatOllama(model=model)
    elif backend == "claude":
        return ChatAnthropic(model_name=model)
    else:
        raise ValueError(f"Unknown backend: {backend}")


def send_message(backend: str, model: str, system_prompt: str, messages: list[dict]) -> str:
    """Send messages using LangChain and get a response with streaming."""
    llm = get_llm(backend, model)

    # Convert to LangChain message format
    lc_messages = [SystemMessage(content=system_prompt)]
    for msg in messages:
        if msg["role"] == "user":
            lc_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            lc_messages.append(AIMessage(content=msg["content"]))

    # Stream the response
    full_response = ""
    for chunk in llm.stream(lc_messages):
        content = chunk.content
        print(content, end="", flush=True)
        full_response += content

    print()  # newline at end
    return full_response


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

        return send_message(self.backend, self.model, self.system_prompt, messages)

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

        response = send_message(self.backend, self.model, self.system_prompt, self.history)

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
