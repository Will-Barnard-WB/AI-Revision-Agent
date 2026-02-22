"""
RevisionAgent — CLI entry point.

Uses the shared agent_factory for agent creation.
Run ``python server.py`` for the web UI instead.
"""

import asyncio
import sys
import uuid

from langgraph.types import Command

from agent_factory import create_agent
from utils import format_messages


async def main(message: str | None = None):
    """Run the agent interactively from the command line.

    Parameters
    ----------
    message : str, optional
        If provided, run this single message.  Otherwise enter a REPL.
    """
    agent = await create_agent()
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    single_shot = message is not None

    if not single_shot:
        print("📚 RevisionAgent CLI — type your request (or 'quit' to exit)")

    while True:
        # Get next message
        if single_shot:
            user_msg = message
        else:
            try:
                user_msg = input("\n🧑 You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nBye!")
                break
            if user_msg.lower() in ("quit", "exit", "q"):
                print("Bye!")
                break
            if not user_msg:
                continue

        # Run the agent
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": user_msg}]},
            config=config,
        )

        # Handle interrupt (human-in-the-loop approval)
        while result.get("__interrupt__"):
            interrupts = result["__interrupt__"][0].value
            action_requests = interrupts["action_requests"]
            review_configs = interrupts["review_configs"]
            config_map = {cfg["action_name"]: cfg for cfg in review_configs}

            decisions = []
            for action in action_requests:
                review_config = config_map[action["name"]]
                print(f"\n⚠️  Tool: {action['name']}")
                print(f"   Args: {action['args'].get('file_path', action['args'])}")
                print(f"   Allowed: {review_config['allowed_decisions']}")

                user_input = input("   Decision (approve/reject): ").strip().lower()
                if user_input not in review_config["allowed_decisions"]:
                    user_input = "reject"
                decisions.append({"type": user_input})

            result = await agent.ainvoke(
                Command(resume={"decisions": decisions}),
                config=config,
            )

        format_messages(result["messages"])

        # In single-message mode, exit after one round
        if single_shot:
            break


if __name__ == "__main__":
    # Accept an optional message as CLI argument
    msg = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else None
    asyncio.run(main(msg))




