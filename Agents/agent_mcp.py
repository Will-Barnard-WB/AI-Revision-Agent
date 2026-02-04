import asyncio
from langchain.agents import create_agent
from MCP.multi_server_mcp_client import client
from dotenv import load_dotenv

from Agents.prompts import mcp_prompt
from LLM.model import llm
from Tools.tools import retrieval_tool

load_dotenv()

async def main():
    
    tools = await client.get_tools()

    agent = create_agent(
       model=llm,
       tools=[retrieval_tool] + tools,
       system_prompt=mcp_prompt
    )

    response = await agent.ainvoke({"messages": {"role": "user", "content": f"Generate revision questions on the topic: eigenvalues."}})
    print("Response:", response)
    response = await agent.ainvoke({"messages": {"role": "user", "content": f"Generate revision questions on the topic: symmetric bilinear forms."}})
    print("Response:", response)

asyncio.run(main())
