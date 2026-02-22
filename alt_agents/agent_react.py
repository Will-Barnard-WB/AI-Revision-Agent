from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from tools import retrieval_tool, add_anki_notes
from alt_agents.alt_prompts import standard_prompt

load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

tools = [retrieval_tool, add_anki_notes]

system_prompt = standard_prompt

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=system_prompt
)

agent.invoke({"messages": {"role": "user", "content": f"Generate revision questions on the topic: eigenvalues."}})



