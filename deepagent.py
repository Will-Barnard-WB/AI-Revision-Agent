from datetime import datetime
from deepagents import create_deep_agent
from langchain.chat_models import init_chat_model
import asyncio 

from utils import format_messages
from tools import retrieval_tool

from multi_server_mcp_client import client

from dotenv import load_dotenv

load_dotenv()

# Think tool needed??? 


from new_agent.new_prompts import (
    FLASHCARD_GENERATOR_INSTRUCTIONS,
    REVISION_WORKFLOW_INSTRUCTIONS,
    SUBAGENT_DELEGATION_INSTRUCTIONS,
)
from new_agent.new_tools import tavily_search, think_tool

max_concurrent_flashcard_generators = 3
max_generator_iterations = 3

current_date = datetime.now().strftime("%Y-%m-%d")

INSTRUCTIONS = (
    REVISION_WORKFLOW_INSTRUCTIONS
    + "\n\n"
    + "=" * 80
    + "\n\n"
    + SUBAGENT_DELEGATION_INSTRUCTIONS.format(
        max_concurrent_research_units=max_concurrent_flashcard_generators,
        max_researcher_iterations=max_generator_iterations,
    )
)

flashcard_generator_sub_agent = {
    "name": "flashcard-generator",
    "description": (
        "Delegate flashcard generation to this sub-agent. "
        "You MUST provide both a topic name and relevant note excerpts (retrieved via retrieval_tool) as arguments. "
        "If note excerpts are missing, the sub-agent will refuse to generate flashcards. "
        "This ensures all flashcards are grounded in the user's actual notes, not internal knowledge."
    ),
    "system_prompt": FLASHCARD_GENERATOR_INSTRUCTIONS.format(date=current_date) + "\n\nIMPORTANT: Only generate flashcards if you receive both a topic name and relevant note excerpts. If note excerpts are missing, respond: 'ERROR: Note excerpts missing. Cannot generate flashcards.'",
    "tools": [tavily_search, think_tool],
}


async def main():
    
    mcp_tools = await client.get_tools()

    new_tools = [retrieval_tool, think_tool] + mcp_tools

    model = init_chat_model(model="openai:gpt-4o-mini", temperature=0.0)

    agent = create_deep_agent(
        model=model,
        tools=new_tools,
        system_prompt=INSTRUCTIONS,
        subagents=[flashcard_generator_sub_agent],
    )

    result = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "What flashcards from my ankido I have to do with bases?",
                }
            ],
        },
    )

    format_messages(result["messages"])


if __name__ == "__main__":
    asyncio.run(main())

    

