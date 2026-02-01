from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from tools import retrieval_tool, add_anki_notes
from prompts import standard_prompt

load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

tools = [retrieval_tool, add_anki_notes]

system_prompt = standard_prompt

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=system_prompt
)

conversation_history = []

agent.invoke({"messages": {"role": "user", "content": f"Generate revision questions on the topic: eigenvalues."}})
agent.invoke({"messages": {"role": "user", "content": f"Generate revision questions on the topic: the first isomorphism theorem."}})
agent.invoke({"messages": {"role": "user", "content": f"Generate revision questions on the topic: quotient spaces."}})
agent.invoke({"messages": {"role": "user", "content": f"Generate revision questions on the topic: symmetric bilinear forms."}})
agent.invoke({"messages": {"role": "user", "content": f"Generate revision questions on the topic: maximum likelihood estimators."}})


