# ollama-chat

Simple Python CLI wrapper for chatting with Ollama models.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
# List available models
python chat.py -l

# One-shot message
python chat.py "What is the capital of France?"

# Use a specific model
python chat.py -m mistral "Explain quantum computing"

# Interactive chat mode (omit message)
python chat.py
python chat.py -m codellama
```

## Requirements

- Ollama running locally on port 11434
- Python 3.10+
