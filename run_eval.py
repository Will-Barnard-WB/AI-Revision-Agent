from agent2 import agent as rag_agent
from langsmith import Client
from openevals.llm import create_llm_as_judge
from openevals.prompts import CORRECTNESS_PROMPT

client = Client()

dataset = client.create_dataset(
    dataset_name="anki-flashcards-linear-algebra-dataset", description="A sample dataset of topics found in the linear algebra lecture notes."
)
#examples = [
#    {
#        "inputs": {"question": "Generate revision questions on the topic: eigenvalues."},
#        "outputs": {"messages": [{"role": "assistant", "content": "I have generated and added revision questions on the topic of eigenvalues to your Anki deck."}]},
#    },
#    {
#        "inputs": {"question": "Generate revision questions on the topic: first isomorphism theorem."},
#        "outputs": {"messages": [{"role": "assistant", "content": "I have generated and added revision questions on the topic of the first isomorphism theorem to your Anki deck."}]},
#    },
#    {
#        "inputs": {"question": "Generate revision questions on the topic: maximum likelihood estimators."},
#        "outputs": {"messages": [{"role": "assistant", "content": "No Q/A pairs could be generated for the topic maximum likelihood estimators. Please provide more specific details or another topic for retrieval."}]},
#    },
#]

#client.create_examples(dataset_id=dataset.id, examples=examples)

# Define the application logic to evaluate.
# Dataset inputs are automatically sent to this target function.
def target(inputs: dict) -> dict:
    """
    inputs: dict from your LangSmith dataset, e.g.
    {
        "messages": {"role": "user", "content": "Generate revision questions on polynomials"}
    }
    """
    # Call your agent with the dataset input
    response = rag_agent.invoke(inputs)  # your agent returns {"messages": [...]}

    # Return the full output dict for evaluators
    return response

CORRECTNESS_PROMPT = CORRECTNESS_PROMPT = """
The assistant should generate revision questions on the specified topic.
Check if the output:
1. Addressed the topic in the user input.
2. Actually produced revision questions.
3. Summarized correctly if it added them to the Anki deck.

Return 'true' if correct, 'false' if not.
"""


# Define an LLM-as-a-judge evaluator to evaluate correctness of the output
def correctness_evaluator(inputs: dict, outputs: dict, reference_outputs: dict):
    evaluator = create_llm_as_judge(
        prompt=CORRECTNESS_PROMPT,
        model="openai:o4-mini",
        feedback_key="correctness",
    )
    eval_result = evaluator(
        inputs=inputs, outputs=outputs, reference_outputs=reference_outputs
    )
    return eval_result


experiment_results = client.evaluate(
    target,
    data="anki-flashcards-linear-algebra-dataset",
    evaluators=[correctness_evaluator],
    experiment_prefix="experiment-anki-flashcards-linear-algebra",
    max_concurrency=2,
)