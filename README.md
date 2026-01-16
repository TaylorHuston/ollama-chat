# ollama-chat

Python CLI tools for chatting with Ollama models and experimenting with multi-AI collaboration.

## Setup

```bash
pip install -r requirements.txt
```

## Tools

### 1. Simple Chat (`chat.py`)

Basic single-model chat interface.

```bash
# List available models
python3 chat.py -l

# One-shot message
python3 chat.py "What is the capital of France?"

# Use a specific model
python3 chat.py -m mistral "Explain quantum computing"

# Interactive chat mode
python3 chat.py
```

### 2. Multi-Persona Collaboration (`collab.py`)

Two AI personas collaborate on a task.

```bash
# Default: Architect + Developer
python3 collab.py "Design a key-value store"

# Different personas
python3 collab.py -p1 creative -p2 critic "Ideas for a mobile game"

# Mix Ollama and Claude
python3 collab.py -p1 claude-haiku -p2 developer "Write a sorting function"

# More rounds
python3 collab.py -r 5 "Build a caching strategy"

# List personas
python3 collab.py -l
```

**Available personas:**
- `architect` - High-level design (Ollama)
- `developer` - Implementation focus (Ollama)
- `critic` - Find flaws, suggest fixes (Ollama)
- `creative` - Novel approaches (Ollama)
- `claude-sonnet` - Claude Sonnet via CLI
- `claude-haiku` - Claude Haiku via CLI

### 3. Interactive Chat Room (`chat_room.py`)

Chat with multiple AI personas using @ mentions.

```bash
# Start with default personas (architect, developer)
python3 chat_room.py

# Start with specific personas
python3 chat_room.py -p architect claude critic
```

**In the chat room:**
```
@architect Design a REST API for a todo app
@claude What do you think of Architect's design?
@all Let's write a haiku together

/add critic       # Add a persona
/remove developer # Remove a persona
/list             # Show active personas
/personas         # Show all available
/clear            # Clear history
/quit             # Exit
```

## Requirements

- Ollama running locally on port 11434
- Python 3.10+
- For Claude personas: `claude` CLI installed and configured
