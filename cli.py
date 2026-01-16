#!/usr/bin/env python3
"""
Unified REPL for ollama-chat tools.

Launch with: python3 cli.py
Then use slash commands:
    /session                  # List all sessions
    /session my-project       # Start/resume session
    /workflow "Build X"       # Run workflow
    /agent "List files"       # Tool-calling agent
    /chat                     # Simple chat mode
    /collab "Design Y"        # Two-persona collaboration
    /room                     # Multi-persona chat room
    /models                   # List available models
    /help                     # Show commands
    /quit                     # Exit
"""

from __future__ import annotations

import shlex
import sys
from typing import Optional

from config import DEFAULT_MODEL, DEFAULT_BACKEND

# Rich for nice output (comes with typer[all])
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import print as rprint
    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    console = None

# =============================================================================
# STATE
# =============================================================================

class State:
    """Global REPL state."""
    def __init__(self):
        self.current_session: Optional[str] = None
        self.model: str = DEFAULT_MODEL
        self.backend: str = DEFAULT_BACKEND
        self.running: bool = True

state = State()


# =============================================================================
# HELPERS
# =============================================================================

def echo(msg: str = "", style: str = None):
    """Print with optional rich styling."""
    if HAS_RICH and style:
        rprint(f"[{style}]{msg}[/{style}]")
    else:
        print(msg)


def error(msg: str):
    """Print error message."""
    echo(f"Error: {msg}", "red")


def success(msg: str):
    """Print success message."""
    echo(msg, "green")


def info(msg: str):
    """Print info message."""
    echo(msg, "dim")


def parse_args(text: str) -> list[str]:
    """Parse command arguments, handling quotes."""
    try:
        return shlex.split(text)
    except ValueError:
        return text.split()


# =============================================================================
# COMMANDS
# =============================================================================

def cmd_help(args: list[str]):
    """Show available commands."""
    if HAS_RICH:
        table = Table(title="Available Commands", show_header=True)
        table.add_column("Command", style="cyan")
        table.add_column("Description")

        commands = [
            ("/session", "List all sessions (with IDs)"),
            ("/session <#|name>", "Start/resume a session"),
            ("/session <#|name> --new", "Force create new session"),
            ("/session <#|name> --history", "Show conversation history"),
            ("/session <#|name> --spec", "Show extracted spec"),
            ("/session <#|name> --delete", "Delete a session"),
            ("", ""),
            ("/workflow <task>", "Run spec-implement-review workflow"),
            ("/agent [task]", "Tool-calling agent (interactive if no task)"),
            ("/chat [message]", "Simple chat (interactive if no message)"),
            ("/collab <task>", "Two-persona collaboration"),
            ("/room", "Multi-persona chat room"),
            ("/batch", "Process markdown files"),
            ("", ""),
            ("/models", "List available Ollama models"),
            ("/model <name>", "Set default model"),
            ("/backend <name>", "Set backend (ollama/claude)"),
            ("/status", "Show current settings"),
            ("", ""),
            ("/help", "Show this help"),
            ("/quit, /exit, /q", "Exit the REPL"),
        ]

        for cmd, desc in commands:
            table.add_row(cmd, desc)

        console.print(table)
    else:
        print("""
Available Commands:
  /session                  - List all sessions (with IDs)
  /session <#|name>         - Start/resume a session
  /session <#|name> --new   - Force create new session
  /session <#|name> --history - Show conversation history
  /session <#|name> --spec  - Show extracted spec
  /session <#|name> --delete - Delete a session

  /workflow <task>  - Run spec-implement-review workflow
  /agent [task]     - Tool-calling agent
  /chat [message]   - Simple chat
  /collab <task>    - Two-persona collaboration
  /room             - Multi-persona chat room
  /batch            - Process markdown files

  /models           - List available models
  /model <name>     - Set default model
  /backend <name>   - Set backend (ollama/claude)
  /status           - Show current settings

  /help             - Show this help
  /quit             - Exit
""")


def cmd_status(args: list[str]):
    """Show current state."""
    echo(f"Model:   {state.model}")
    echo(f"Backend: {state.backend}")
    if state.current_session:
        echo(f"Session: {state.current_session}")


def cmd_models(args: list[str]):
    """List available Ollama models."""
    from chat import list_models
    models = list_models()
    echo("Available models:")
    for m in models:
        marker = " *" if m == state.model else ""
        echo(f"  - {m}{marker}")


def cmd_model(args: list[str]):
    """Set the default model."""
    if not args:
        echo(f"Current model: {state.model}")
        return
    state.model = args[0]
    success(f"Model set to: {state.model}")


def cmd_backend(args: list[str]):
    """Set the backend."""
    if not args:
        echo(f"Current backend: {state.backend}")
        return
    if args[0] not in ("ollama", "claude"):
        error("Backend must be 'ollama' or 'claude'")
        return
    state.backend = args[0]
    success(f"Backend set to: {state.backend}")


def _get_sessions_list():
    """Get sessions as a list with stable ordering for numeric IDs."""
    from sessions import list_sessions
    sessions = list_sessions()
    # Sort by updated_at descending (most recent first)
    return sorted(sessions, key=lambda s: s.updated_at or "", reverse=True)


def _resolve_session_name(identifier: str) -> str | None:
    """Resolve a session identifier (name or number) to session name."""
    # Check if it's a number
    try:
        idx = int(identifier)
        sessions = _get_sessions_list()
        if 1 <= idx <= len(sessions):
            return sessions[idx - 1].name
        return None
    except ValueError:
        # It's a name, return as-is
        return identifier


def cmd_session(args: list[str]):
    """Manage and interact with conversation sessions."""
    from sessions import Session, delete_session
    from conversation import chat_loop

    # No args = list all sessions
    if not args:
        sessions = _get_sessions_list()
        if not sessions:
            echo("No sessions found. Start one with: /session <name>")
            return

        echo(f"\n{'#':<4} {'Name':<25} {'Messages':<10} {'Spec':<6} {'Updated':<16}")
        echo("-" * 65)
        for i, s in enumerate(sessions, 1):
            spec_indicator = "✓" if s.has_spec else ""
            updated = s.updated_at[5:16] if s.updated_at else ""  # MM-DD HH:MM
            echo(f"{i:<4} {s.name:<25} {s.message_count:<10} {spec_indicator:<6} {updated:<16}")
        return

    # Resolve session identifier (number or name)
    session_id = args[0]
    session_name = _resolve_session_name(session_id)

    if session_name is None:
        error(f"Session '{session_id}' not found")
        return

    # Handle management flags (don't start chat)
    if "--delete" in args:
        if delete_session(session_name):
            success(f"Deleted session '{session_name}'")
        else:
            error(f"Session '{session_name}' not found")
        return

    if "--history" in args or "--spec" in args:
        try:
            sess = Session(session_name)
            sess.load()
        except FileNotFoundError:
            error(f"Session '{session_name}' not found")
            return

        if "--history" in args:
            echo(sess.get_history_text())
        elif "--spec" in args:
            spec = sess.get_spec()
            if spec:
                echo(spec)
            else:
                echo("No spec saved for this session")
        return

    # Start/resume session for chatting
    new_session = "--new" in args

    # Create workflow args for compatibility
    class Args:
        pass
    wf_args = Args()
    wf_args.spec_model = state.model
    wf_args.spec_backend = state.backend
    wf_args.impl_model = DEFAULT_MODEL
    wf_args.review_model = state.model
    wf_args.threshold = 85
    wf_args.max_iter = 5

    sess = Session(session_name, model=state.model, backend=state.backend)

    if new_session:
        try:
            sess.create("")
            success(f"Created new session: {session_name}")
        except FileExistsError:
            error(f"Session '{session_name}' already exists. Use without --new to resume.")
            return
    else:
        created = sess.load_or_create("")
        if created:
            success(f"Created new session: {session_name}")
        else:
            info(f"Resuming session: {session_name}")

    state.current_session = session_name
    chat_loop(sess, wf_args)


def cmd_workflow(args: list[str]):
    """Run a workflow."""
    from workflow import create_spec_implement_review_workflow
    from handoffs import list_runs, get_run, print_run_summary

    # Handle --list-runs
    if "--list-runs" in args:
        runs = list_runs("workflow_runs")
        if not runs:
            echo("No runs found")
            return
        echo(f"\n{'Run ID':<45} {'Status':<12} {'Steps':<6}")
        echo("-" * 65)
        for run in runs:
            echo(f"{run['id']:<45} {run['status']:<12} {run['steps']:<6}")
        return

    # Handle --inspect
    if "--inspect" in args:
        idx = args.index("--inspect")
        if idx + 1 >= len(args):
            error("--inspect requires a run ID")
            return
        run = get_run(args[idx + 1], "workflow_runs")
        if not run:
            error(f"Run not found")
            return
        print_run_summary(run)
        return

    # Handle --visualize
    if "--visualize" in args:
        echo("""
Workflow: spec_implement_review

  ┌──────────┐
  │  START   │
  └────┬─────┘
       │
       ▼
  ┌──────────┐
  │   spec   │  Write detailed specification
  └────┬─────┘
       │
       ▼
┌────────────┐
│ implement  │  Generate code from spec
└─────┬──────┘
      │
      ▼
  ┌──────────┐
  │  review  │  Score 0-100 + feedback
  └────┬─────┘
       │
       ▼
  ┌──────────────┐     yes    ┌──────────┐
  │ score >= 85? │──────────▶│   DONE   │
  └──────┬───────┘            └──────────┘
         │ no
         └──────────────┐
                        ▼
               (back to implement)
""")
        return

    if not args:
        echo("Usage: /workflow <task>")
        echo("       /workflow --list-runs")
        echo("       /workflow --inspect <run-id>")
        echo("       /workflow --visualize")
        return

    task = " ".join(args)
    persist = "--persist" in args
    if persist:
        task = task.replace("--persist", "").strip()

    wf = create_spec_implement_review_workflow(
        spec_model=state.model,
        spec_backend=state.backend,
        impl_model=DEFAULT_MODEL,
        review_model=state.model,
        pass_threshold=85,
    )

    result = wf.run(
        initial_state={"task": task, "max_iterations": 5},
        persist=persist,
        runs_dir="workflow_runs",
    )

    if result:
        echo(f"\n{'='*60}")
        success("WORKFLOW COMPLETE")
        echo(f"{'='*60}")
        echo(f"Iterations: {result.get('iteration', 0)}")
        echo(f"Final Score: {result.get('score', 'N/A')}")
        if result.get("code"):
            echo(f"\nGenerated Code:\n")
            echo(result["code"])


def cmd_agent(args: list[str]):
    """Run the tool-calling agent."""
    from agent import run_agent

    if args:
        task = " ".join(args)
        run_agent(task, backend=state.backend, model=state.model, max_iterations=10)
    else:
        # Interactive agent mode
        echo(f"🤖 Agent: {state.backend}:{state.model}")
        echo("Type a task or 'quit' to exit.\n")

        while True:
            try:
                task_input = input("Task> ").strip()
            except (KeyboardInterrupt, EOFError):
                echo("\n")
                break

            if task_input.lower() in ("quit", "exit", "q", ""):
                break

            run_agent(task_input, backend=state.backend, model=state.model, max_iterations=10)
            echo()


def cmd_chat(args: list[str]):
    """Simple chat."""
    from chat import chat as send_chat, interactive_chat

    if args:
        message = " ".join(args)
        send_chat(state.model, message, stream=True)
    else:
        interactive_chat(state.model)


def cmd_collab(args: list[str]):
    """Two-persona collaboration."""
    from personas import load_personas
    from collab import run_collaboration

    personas = load_personas()

    if "--list" in args or "-l" in args:
        echo("Available personas:")
        for name, p in personas.items():
            echo(f"  - {name}: {p.name} ({p.backend}:{p.model})")
        return

    if not args:
        echo("Usage: /collab <task>")
        echo("       /collab --list")
        return

    task = " ".join(args)
    p1 = personas.get("architect")
    p2 = personas.get("developer")

    if not p1 or not p2:
        error("Default personas not found")
        return

    run_collaboration(p1, p2, task, rounds=3)


def cmd_room(args: list[str]):
    """Multi-persona chat room."""
    from chat_room import ChatRoom
    from personas import load_personas

    all_personas = load_personas()
    default_personas = ["architect", "developer"]

    # Validate
    for p in default_personas:
        if p not in all_personas:
            error(f"Unknown persona: {p}")
            return

    chat_room = ChatRoom({p: all_personas[p] for p in default_personas}, all_personas)
    chat_room.run()


def cmd_batch(args: list[str]):
    """Batch processing."""
    from batch import run_batch

    input_file = "INPUT.md"
    output_file = "output.py"
    persona = "developer"

    # Parse args
    i = 0
    while i < len(args):
        if args[i] in ("-i", "--input") and i + 1 < len(args):
            input_file = args[i + 1]
            i += 2
        elif args[i] in ("-o", "--output") and i + 1 < len(args):
            output_file = args[i + 1]
            i += 2
        elif args[i] in ("-p", "--persona") and i + 1 < len(args):
            persona = args[i + 1]
            i += 2
        else:
            i += 1

    run_batch(input_file, output_file, persona)


def cmd_quit(args: list[str]):
    """Exit the REPL."""
    state.running = False
    echo("Goodbye!")


# =============================================================================
# COMMAND DISPATCH
# =============================================================================

COMMANDS = {
    "help": cmd_help,
    "?": cmd_help,
    "status": cmd_status,
    "models": cmd_models,
    "model": cmd_model,
    "backend": cmd_backend,
    "session": cmd_session,
    "s": cmd_session,
    "workflow": cmd_workflow,
    "wf": cmd_workflow,
    "agent": cmd_agent,
    "chat": cmd_chat,
    "collab": cmd_collab,
    "room": cmd_room,
    "batch": cmd_batch,
    "quit": cmd_quit,
    "exit": cmd_quit,
    "q": cmd_quit,
}


def dispatch(line: str):
    """Parse and dispatch a command."""
    line = line.strip()

    if not line:
        return

    # Must start with /
    if not line.startswith("/"):
        echo("Commands start with /. Try /help")
        return

    # Parse command and args
    parts = parse_args(line[1:])  # Remove leading /
    if not parts:
        return

    cmd = parts[0].lower()
    args = parts[1:]

    if cmd in COMMANDS:
        try:
            COMMANDS[cmd](args)
        except Exception as e:
            error(str(e))
    else:
        error(f"Unknown command: /{cmd}")
        echo("Try /help for available commands")


# =============================================================================
# MAIN REPL
# =============================================================================

def print_banner():
    """Print welcome banner."""
    if HAS_RICH:
        console.print(Panel.fit(
            "[bold cyan]ollama-chat[/bold cyan]\n"
            "[dim]Multi-agent AI workflows[/dim]\n\n"
            "Type [bold]/help[/bold] for commands, [bold]/quit[/bold] to exit",
            border_style="cyan"
        ))
    else:
        print("""
╔═══════════════════════════════════════╗
║           ollama-chat                 ║
║     Multi-agent AI workflows          ║
║                                       ║
║  Type /help for commands, /quit to exit
╚═══════════════════════════════════════╝
""")


def repl():
    """Main REPL loop."""
    print_banner()
    echo()

    while state.running:
        try:
            prompt = f"[{state.model}]> " if state.current_session is None else f"[{state.current_session}]> "
            line = input(prompt)
            dispatch(line)
        except KeyboardInterrupt:
            echo("\n(Use /quit to exit)")
        except EOFError:
            cmd_quit([])


def main():
    """Entry point."""
    # If arguments provided, treat as direct command
    if len(sys.argv) > 1:
        cmd_line = " ".join(sys.argv[1:])
        if not cmd_line.startswith("/"):
            cmd_line = "/" + cmd_line
        dispatch(cmd_line)
    else:
        repl()


if __name__ == "__main__":
    main()
