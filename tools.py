from langchain_core.tools import tool

@tool
def retrieval_tool(query: str) -> str:
    '''
    This tool searches and returns the information from the Stock Market Performance 2024 document.

    '''

    docs = retriever.invoke(query)

    if not docs:
        return "I found no relevant information in the Stock Market Performance 2024 document."
    
    results = []
    for i, doc in enumerate(docs):
        results.append(f"Document {i+1}:\n{doc.page_content}")

    return "\n\n".join(results)