"""
Create a LangSmith dataset for evaluating the revision question generation agent.
This script creates a dataset with sample topic requests.
"""
from langsmith import Client
from dotenv import load_dotenv

load_dotenv()

# Initialize LangSmith client
client = Client()

# Dataset name
dataset_name = "revision-questions-dataset"

# Create the dataset
dataset = client.create_dataset(
    dataset_name=dataset_name,
    description="Sample topics for testing the revision question generation agent"
)

print(f"Created dataset: {dataset_name}")

# Define example inputs - these are topics the agent should generate questions for
examples = [
    {
        "input": "Generate revision questions on the topic: generalised eigenspaces",
        "expected_output": "Should generate 3-7 Q/A pairs about generalised eigenspaces and add them to Anki"
    },
    {
        "input": "Generate revision questions on the topic: symmetric bilinear forms",
        "expected_output": "Should generate 3-7 Q/A pairs about symmetric bilinear forms and add them to Anki"
    },
    {
        "input": "Generate revision questions on the topic: cosets",
        "expected_output": "Should generate 3-7 Q/A pairs about cosets and add them to Anki"
    },
    {
        "input": "Generate revision questions on the topic: ",
        "expected_output": "Should generate 3-7 Q/A pairs about basis and dimension and add them to Anki"
    },
]

# Add examples to the dataset
for example in examples:
    client.create_example(
        inputs={"input": example["input"]},
        outputs={"expected": example["expected_output"]},
        dataset_id=dataset.id
    )

print(f"Added {len(examples)} examples to dataset")
print(f"Dataset ID: {dataset.id}")
print("\nYou can view the dataset in LangSmith UI:")
print(f"https://smith.langchain.com/datasets/{dataset.id}")
