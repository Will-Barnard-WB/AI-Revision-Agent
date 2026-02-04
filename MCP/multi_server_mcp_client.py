from langchain_mcp_adapters.client import MultiServerMCPClient

client = MultiServerMCPClient({
    "anki": {
        "transport": "http",  
        "url": "http://127.0.0.1:8000/mcp"
    }
})

