# ollama-chat

Python CLI tools for chatting with Ollama models and experimenting with multi-AI collaboration.

## Features

- **Simple Chat** - Basic single-model conversations
- **Multi-Persona Collaboration** - Two AI personas working together on tasks
- **Interactive Chat Room** - @ mention multiple personas in real-time
- **Batch Processing** - Process markdown files and generate code
- **Tool-Calling Agent** - AI agent that can read/write files and run commands

## Setup

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.ai/) running locally (default port 11434)
- For Claude personas: `ANTHROPIC_API_KEY` environment variable set

### Installation

```bash
# Clone the repo
git clone https://github.com/TaylorHuston/ollama-chat.git
cd ollama-chat

# Install dependencies
pip install -r requirements.txt

# Pull recommended models
ollama pull llama3.2:3b    # Required for tool-calling agent
ollama pull gemma3:1b      # Good for fast chat/collaboration
ollama pull qwen2.5:0.5b   # Ultra-lightweight option
```

### Dependencies

- `langchain-core` - Base LangChain abstractions
- `langchain-ollama` - Ollama integration
- `langchain-anthropic` - Claude integration
- `requests` - HTTP client

## Tools

### 1. Simple Chat (`chat.py`)

Basic single-model chat interface.

```bash
# List available models
python3 chat.py -l

# One-shot message
python3 chat.py "What is the capital of France?"

# Use a specific model
python3 chat.py -m gemma3:1b "Explain quantum computing"

# Interactive chat mode (default)
python3 chat.py
```

### 2. Multi-Persona Collaboration (`collab.py`)

Two AI personas collaborate on a task, passing context back and forth.

```bash
# Default: Architect + Developer
python3 collab.py "Design a key-value store"

# Different personas
python3 collab.py -p1 creative -p2 critic "Ideas for a mobile game"

# Mix Ollama and Claude
python3 collab.py -p1 claude -p2 developer "Write a sorting function"

# More collaboration rounds
python3 collab.py -r 5 "Build a caching strategy"

# List available personas
python3 collab.py -l
```

### 3. Interactive Chat Room (`chat_room.py`)

Chat with multiple AI personas using @ mentions.

```bash
# Start with default personas (architect, developer)
python3 chat_room.py

# Start with specific personas
python3 chat_room.py -p architect claude critic
```

**Chat room commands:**
```
@architect Design a REST API for a todo app
@claude What do you think of Architect's design?
@all Let's write a haiku together

/add critic       # Add a persona to the room
/remove developer # Remove a persona
/list             # Show active personas
/personas         # Show all available personas
/clear            # Clear conversation history
/quit             # Exit the chat room
```

### 4. Batch Processing (`batch.py`)

Process markdown files with AI and extract code to runnable files.

```bash
# Process INPUT.md -> output files
python3 batch.py

# Custom input/output
python3 batch.py -i prompt.md -o result.py

# Use a specific persona
python3 batch.py -p developer

# Use Claude
python3 batch.py -p claude
```

**How it works:**
1. Reads the input markdown file
2. Sends it to the AI persona for processing
3. Extracts Python code blocks from the response
4. Writes them to the output file

**Example INPUT.md:**
```markdown
Write a Python function that reverses a string.
Include an example usage that prints the result.
```

### 5. Tool-Calling Agent (`agent.py`)

An AI agent with filesystem and shell access. Can autonomously complete tasks by calling tools.

```bash
# Single task
python3 agent.py "List all Python files in this directory"

# File operations
python3 agent.py "Read requirements.txt and summarize the dependencies"

# Code generation
python3 agent.py "Create a hello.py file that prints Hello World"

# Shell commands
python3 agent.py "What's the current git branch?"

# Interactive mode
python3 agent.py

# Use a different model (must support tool calling)
python3 agent.py -m llama3.1 "Your task here"
```

**Available tools:**
| Tool | Description |
|------|-------------|
| `read_file(path)` | Read file contents |
| `write_file(path, content)` | Create or overwrite a file |
| `list_files(path)` | List directory contents |
| `run_command(command)` | Execute shell commands |
| `search_files(pattern, path)` | Find files by glob pattern |

**Model requirements:** The agent requires a model that supports tool/function calling:
- `llama3.2:3b` (default, recommended)
- `llama3.1`
- `mistral`

Models like `gemma3:1b` and `qwen2.5:0.5b` do NOT support tool calling.

## Configuration

### Personas (`personas.json`)

All personas are defined in `personas.json`. You can add, modify, or remove personas by editing this file.

```json
{
  "architect": {
    "name": "Architect",
    "model": "gemma3:1b",
    "backend": "ollama",
    "system_prompt": "You are a senior software architect..."
  },
  "claude": {
    "name": "Claude",
    "model": "claude-sonnet-4-20250514",
    "backend": "claude",
    "system_prompt": "You are Claude, an AI assistant by Anthropic..."
  }
}
```

**Fields:**
- `name` - Display name for the persona
- `model` - Model identifier (Ollama model name or Claude model ID)
- `backend` - Either `ollama` or `claude`
- `system_prompt` - Instructions that define the persona's behavior

### Available Personas

| Persona | Backend | Model | Role |
|---------|---------|-------|------|
| `architect` | Ollama | gemma3:1b | High-level system design |
| `developer` | Ollama | gemma3:1b | Implementation focus |
| `critic` | Ollama | gemma3:1b | Find flaws, suggest improvements |
| `creative` | Ollama | gemma3:1b | Novel and creative approaches |
| `claude` | Claude | claude-sonnet-4-20250514 | General-purpose assistant |

## Architecture

```
ollama-chat/
├── chat.py          # Simple single-model chat
├── collab.py        # Two-persona collaboration
├── chat_room.py     # Interactive multi-persona chat room
├── batch.py         # Markdown to code batch processing
├── agent.py         # Tool-calling autonomous agent
├── personas.py      # Shared persona/LLM utilities (LangChain)
├── tools.py         # LangChain tool definitions
├── personas.json    # Persona configuration
└── requirements.txt # Python dependencies
```

### LangChain Integration

The project uses LangChain for:
- **Unified API** - Same code works with Ollama and Claude
- **Streaming** - Real-time response output
- **Tool Calling** - Structured function calls for the agent
- **Message Management** - Proper conversation history handling

## Troubleshooting

### "Connection refused" errors
Make sure Ollama is running:
```bash
ollama serve
```

### "Model not found"
Pull the required model:
```bash
ollama pull gemma3:1b
```

### "does not support tools" error
The agent requires a tool-capable model. Use `llama3.2:3b` or `llama3.1`:
```bash
ollama pull llama3.2:3b
python3 agent.py -m llama3.2:3b "your task"
```

### Claude authentication errors
Set your Anthropic API key:
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

### Out of VRAM
Use smaller models:
- `qwen2.5:0.5b` (397 MB)
- `gemma3:1b` (815 MB)
- `llama3.2:3b` (2.0 GB)

## License

MIT
