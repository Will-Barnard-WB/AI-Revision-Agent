"""
Run a LangSmith experiment to evaluate the revision question generation agent.
This script runs the agent on a dataset and evaluates the outputs.
"""
from langsmith import Client, evaluate
from langsmith.schemas import Run, Example
from dotenv import load_dotenv
from Agents.agent_react import agent
import re

load_dotenv()

# Initialize LangSmith client
client = Client()

# Dataset name (must match the one created in create_dataset.py)
dataset_name = "revision-questions-dataset"


def run_agent(inputs: dict) -> dict:
    """
    Wrapper function to invoke the agent.
    This function takes the input and returns the agent's response.
    """
    user_input = inputs["input"]

    # Invoke the agent with the input
    result = agent.invoke({"messages": [{"role": "user", "content": user_input}]})

    # Extract the final output message
    messages = result.get("messages", [])
    if messages:
        # Get the last AI message
        output = messages[-1].content if hasattr(messages[-1], 'content') else str(messages[-1])
    else:
        output = str(result)

    return {"output": output}


# Evaluator: Count Q/A pairs in the output
def count_qa_pairs(run: Run, _example: Example) -> dict:
    """
    Count the number of Q/A pairs in the output by looking for the "**Q:**" pattern.
    The agent's output contains formatted Q/A pairs like:
    1. **Q:** What is...
       **A:** It is...
    """
    output = run.outputs.get("output", "") if run.outputs else ""

    # Count occurrences of Q/A patterns
    q_count = output.count("**Q:**")

    # Check if we got a reasonable number (3-7)
    if q_count >= 3 and q_count <= 7:
        score = 1.0
        comment = f"Generated {q_count} Q/A pairs (good)"
    elif q_count > 0:
        score = 0.7
        comment = f"Generated {q_count} Q/A pairs (outside expected range 3-7)"
    else:
        score = 0.0
        comment = "No Q/A pairs found in output"

    return {
        "key": "qa_pair_count",
        "score": score,
        "comment": comment
    }


# Run the experiment
if __name__ == "__main__":
    print(f"Running experiment on dataset: {dataset_name}")

    results = evaluate(
        run_agent,
        data=dataset_name,
        evaluators=[
            count_qa_pairs
        ],
        experiment_prefix="revision-agent-eval",
        metadata={
            "version": "2.0",
            "description": "Simplified evaluation - counts Q/A pairs in output"
        }
    )

    print("\nExperiment completed!")
    print(f"View results in LangSmith UI")
