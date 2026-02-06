import asyncio
from unittest import result
from langchain.agents import create_agent
from multi_server_mcp_client import client
from dotenv import load_dotenv

from utils import show_prompt, format_messages
from IPython.display import Image, display

from prompts import mcp_prompt
from model import llm
from tools import retrieval_tool, thinking_tool

load_dotenv()

async def main():
    
    tools = await client.get_tools()

    agent = create_agent(
       model=llm,
       tools=[retrieval_tool, thinking_tool] + tools,
       system_prompt=mcp_prompt,
    )

    result = await agent.ainvoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "Generate revision questions on the topic: eigenvalues.",
            }
        ],
    }, 
)
    format_messages(result["messages"])

asyncio.run(main())


