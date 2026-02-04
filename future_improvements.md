
1. Checking for existing (semantically similar/identical) flashcards before adding to the deck.
2. Creating the agent loop with conversation history (what to add to memory) and modifying /exploring the existing state from the agent object.
3. "I noticed the agent searched 7 times for "Sylvester's Theorem." This often happens if the retrieval_tool returns a result that the LLM thinks is "incomplete."

    Tip: If your PDF chunks are small, the LLM might be trying to piece the theorem together.

    Next Step: You might want to add a "Max Iterations" check or a more descriptive instruction telling the LLM: "If you find a definition and a proof, stop searching and generate the cards."

4. Rewrite MCP server to contain more user-focused tasks that can be completed??

4. Field values of evaluators? 
5. Max depth / iterations or ways for LLMs to stop when stuck.

7. Flashcards already exist (use view existing tool to not add duplicates see if it can find anything else that's not in there from RAG) (for all agents)?


8. forgiving tool calls / return error let agent learn and then saves its learning to an .md file?