"""
Run a LangSmith experiment to evaluate the revision question generation agent.
"""
from langsmith import Client, evaluate
from langsmith.schemas import Run, Example
from dotenv import load_dotenv
import sys
import os
import asyncio
import uuid
import re
import json
import anthropic

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agent_factory import create_agent

load_dotenv()

client = Client()
dataset_name = "revision-questions-dataset"


def run_agent(inputs: dict) -> dict:
    """
    Wrapper function to invoke the agent.
    LangSmith's evaluate() calls this and expects a plain dict back.
    """
    user_input = inputs["input"]

    async def _invoke():
        agent = await create_agent()
        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": user_input}]},
            config=config
        )
        messages = result.get("messages", [])
        if messages:
            output = messages[-1].content if hasattr(messages[-1], 'content') else str(messages[-1])
        else:
            output = str(result)
        return {"output": output}

    return asyncio.run(_invoke())


def count_flashcards(run: Run, example: Example) -> dict:
    """
    Evaluator: counts flashcards in both numbered list and markdown table formats.
    """
    output = (run.outputs or {}).get("output", "")

    numbered = re.findall(r'^\s*\d+[\.\)]\s', output, re.MULTILINE)
    table_rows = re.findall(r'^\|\s*\d+\s*\|', output, re.MULTILINE)
    card_count = len(numbered) + len(table_rows)

    score = 1.0 if card_count > 0 else 0.0
    return {
        "key": "flashcard_count",
        "score": score,
        "comment": f"Found {card_count} flashcards."
    }


def references_topic(run: Run, example: Example) -> dict:
    """
    Evaluator: checks that the output references content from the input topic.
    """
    output = (run.outputs or {}).get("output", "").lower()
    topic = (example.inputs or {}).get("input", "").lower()

    keywords = [w for w in topic.split() if len(w) > 4]
    matched = any(kw in output for kw in keywords)

    return {
        "key": "references_topic",
        "score": 1.0 if matched else 0.0,
        "comment": f"Output {'references' if matched else 'does not reference'} topic keywords."
    }


def llm_judge(run: Run, example: Example) -> dict:
    """
    LLM-as-judge evaluator: asks Claude to score the agent's output
    on relevance, completeness, and clarity.
    """
    output = (run.outputs or {}).get("output", "")
    topic = (example.inputs or {}).get("input", "")

    prompt = f"""You are evaluating the output of a revision flashcard retrieval agent.

The user asked: {topic}
The agent responded: {output}

Please score the response on the following criteria (each out of 10):
1. **Relevance** — Does the output directly address the topic requested?
2. **Completeness** — Are the flashcards thorough and well-covering the topic?
3. **Clarity** — Are the flashcards clearly written and easy to understand?

Respond ONLY with a JSON object like this, no preamble or markdown:
{{"relevance": 8, "completeness": 7, "clarity": 9, "overall": 8, "reasoning": "one sentence explanation"}}"""

    anthropic_client = anthropic.Anthropic()
    message = anthropic_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()
    scores = json.loads(raw)
    overall = scores.get("overall", 0)

    return {
        "key": "llm_judge",
        "score": overall / 10.0,
        "comment": f"Relevance: {scores['relevance']}/10, Completeness: {scores['completeness']}/10, Clarity: {scores['clarity']}/10 — {scores['reasoning']}"
    }


if __name__ == "__main__":
    results = evaluate(
        run_agent,
        data=dataset_name,
        evaluators=[count_flashcards, references_topic, llm_judge],
        experiment_prefix="revision-agent-eval",
        metadata={"version": "1.0"},
    )

    for result in results:
        print("Input:  ", result.get("example", {}).inputs)
        print("Output: ", result.get("run", {}).outputs)
        for eval_result in result.get("evaluation_results", {}).get("results", []):
            print(f"  [{eval_result.key}] score={eval_result.score} — {eval_result.comment}")
        print()