#!/usr/bin/env python3
"""Batch mode: Read task from INPUT.md, write results to OUTPUT.md"""

import argparse
from pathlib import Path
from personas import load_personas


def run_batch(
    input_file: str = "INPUT.md",
    output_file: str = "OUTPUT.md",
    persona1: str = "architect",
    persona2: str = "developer",
    rounds: int = 3,
):
    """Read task from input, run collaboration, write to output."""
    personas = load_personas()

    # Read input
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"Error: {input_file} not found")
        print(f"Create {input_file} with your task/prompt and run again.")
        return

    task = input_path.read_text().strip()
    print(f"📖 Read task from {input_file}")
    print(f"   ({len(task)} chars)")

    # Get personas
    p1 = personas[persona1]
    p2 = personas[persona2]

    print(f"🤖 Running: {p1.name} + {p2.name} ({rounds} rounds)")
    print("-" * 50)

    # Run collaboration
    conversation_log = []
    current, other = p1, p2

    for i in range(rounds * 2):
        messages = [{"role": "user", "content": f"""Task:
{task}

You are collaborating with {other.name}. Conversation so far:

{chr(10).join(conversation_log) if conversation_log else "(You start!)"}

Your turn. Produce concrete output."""}]

        print(f"\n{'='*50}")
        print(f"{current.name}:")
        print("=" * 50)

        response = current.respond(messages, show_header=False)
        conversation_log.append(f"## {current.name}\n\n{response}")

        current, other = other, current

    # Write output
    output_content = f"""# Output

**Task:** {input_file}
**Personas:** {p1.name} + {p2.name}
**Rounds:** {rounds}

---

{"---".join(conversation_log)}
"""

    Path(output_file).write_text(output_content)
    print(f"\n{'='*50}")
    print(f"✅ Wrote results to {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Batch collaboration: INPUT.md → OUTPUT.md")
    parser.add_argument("-i", "--input", default="INPUT.md", help="Input file (default: INPUT.md)")
    parser.add_argument("-o", "--output", default="OUTPUT.md", help="Output file (default: OUTPUT.md)")
    parser.add_argument("-p1", "--persona1", default="architect", help="First persona")
    parser.add_argument("-p2", "--persona2", default="developer", help="Second persona")
    parser.add_argument("-r", "--rounds", type=int, default=3, help="Rounds of collaboration")

    args = parser.parse_args()
    run_batch(args.input, args.output, args.persona1, args.persona2, args.rounds)


if __name__ == "__main__":
    main()
