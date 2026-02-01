1. Checking for existing (semantically similar/identical) flashcards before adding to the deck.
2. Creating the agent loop with conversation history (what to add to memory) and modifying /exploring the existing state from the agent object.
3. "I noticed the agent searched 7 times for "Sylvester's Theorem." This often happens if the retrieval_tool returns a result that the LLM thinks is "incomplete."

    Tip: If your PDF chunks are small, the LLM might be trying to piece the theorem together.

    Next Step: You might want to add a "Max Iterations" check or a more descriptive instruction telling the LLM: "If you find a definition and a proof, stop searching and generate the cards."

4. Create custom anki-connect MCP server and connect to agent. Include the necessary tools - e.g. create deck, create flashcards etc
