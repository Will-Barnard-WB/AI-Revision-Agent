"""
Create a LangSmith dataset for evaluating the revision question generation agent.
This script creates a dataset with sample topic requests.
"""
 # Minimal LangSmith dataset creation script
from langsmith import Client
from dotenv import load_dotenv

load_dotenv()
 
client = Client()
 
dataset_name = "revision-questions-dataset"
 
dataset = client.create_dataset(
	 dataset_name=dataset_name,
	 description="Sample topics for testing the revision question generation agent"
)
 
examples = [
	{
		"input": "Retrieve all Anki flashcards for the topic: generalised eigenspaces",
		"expected_output": "Should return a list of flashcards related to generalised eigenspaces."
	},
	{
		"input": "Retrieve all Anki flashcards for the topic: symmetric bilinear forms",
		"expected_output": "Should return a list of flashcards related to symmetric bilinear forms."
	},
	{
		"input": "Retrieve all Anki flashcards for the topic: cosets",
		"expected_output": "Should return a list of flashcards related to cosets."
	},
	{
		"input": "Retrieve all Anki flashcards for the topic: basis and dimension",
		"expected_output": "Should return a list of flashcards related to basis and dimension."
	}
]
 
for example in examples:
	 client.create_example(
		 inputs={"input": example["input"]},
		 outputs={"expected": example["expected_output"]},
		 dataset_id=dataset.id
	 )
 
print(f"Created dataset: {dataset_name} with {len(examples)} examples.")

