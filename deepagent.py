from datetime import datetime
from deepagents import create_deep_agent
from langchain.chat_models import init_chat_model
import asyncio
from deepagents.backends import FilesystemBackend
from langgraph.checkpoint.memory import MemorySaver
from utils import format_messages
from tools import retrieval_tool
from multi_server_mcp_client import client
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.live import Live
from rich.text import Text
from rich.table import Table
from rich.align import Align
from rich.rule import Rule
from rich.syntax import Syntax
import uuid

load_dotenv()

from new_agent.new_prompts import (
    FLASHCARD_GENERATOR_INSTRUCTIONS,
    REVISION_WORKFLOW_INSTRUCTIONS,
    SUBAGENT_DELEGATION_INSTRUCTIONS,
)
from new_agent.new_tools import tavily_search, think_tool

console = Console()

max_concurrent_flashcard_generators = 3
max_generator_iterations = 3

current_date = datetime.now().strftime("%Y-%m-%d")

INSTRUCTIONS = (
    REVISION_WORKFLOW_INSTRUCTIONS
    + "\n\n"
    + "=" * 80
    + "\n\n"
    + SUBAGENT_DELEGATION_INSTRUCTIONS.format(
        max_concurrent_research_units=max_concurrent_flashcard_generators,
        max_researcher_iterations=max_generator_iterations,
    )
)

flashcard_generator_sub_agent = {
    "name": "flashcard-generator",
    "description": (
        "Delegate flashcard generation to this sub-agent. "
        "You MUST provide both a topic name and relevant note excerpts (retrieved via retrieval_tool) as arguments. "
        "If note excerpts are missing, the sub-agent will refuse to generate flashcards. "
        "This ensures all flashcards are grounded in the user's actual notes, not internal knowledge."
    ),
    "system_prompt": FLASHCARD_GENERATOR_INSTRUCTIONS.format(date=current_date) + "\n\nIMPORTANT: Only generate flashcards if you receive both a topic name and relevant note excerpts. If note excerpts are missing, respond: 'ERROR: Note excerpts missing. Cannot generate flashcards.'",
    "tools": [tavily_search, think_tool],
}


async def process_query(agent, messages, config):
    """Process a single query and stream results"""
    
    # Run agent
    result = await agent.ainvoke(
        {"messages": messages},
        config=config
    )
    
    # Handle interrupts if present
    if result.get("__interrupt__"):
        interrupts = result["__interrupt__"][0].value
        action_requests = interrupts["action_requests"]
        review_configs = interrupts["review_configs"]
        config_map = {cfg["action_name"]: cfg for cfg in review_configs}
        decisions = []
        
        for action in action_requests:
            review_config = config_map[action["name"]]
            
            # Create a styled panel for tool review
            tool_info = f"[bold cyan]{action['name']}[/bold cyan]\n"
            tool_info += f"[dim]Arguments:[/dim] {action['args'].get('file_path', action['args'])}\n"
            tool_info += f"[dim]Allowed:[/dim] {', '.join([f'[green]{d}[/green]' for d in review_config['allowed_decisions']])}"
            
            console.print(Panel(
                tool_info,
                title="[bold yellow]⚙️  Tool Review[/bold yellow]",
                border_style="yellow",
                padding=(1, 2)
            ))
            
            user_input = Prompt.ask(
                "[bold cyan]Decision[/bold cyan]",
                choices=review_config['allowed_decisions']
            )
            decisions.append({"type": user_input})
        
        from langgraph.types import Command
        result = await agent.ainvoke(
            Command(resume={"decisions": decisions}),
            config=config
        )
    
    # Display agent response with enhanced styling
    if "messages" in result:
        last_message = result["messages"][-1]
        if hasattr(last_message, "content"):
            console.print()
            response_panel = Panel(
                Markdown(last_message.content),
                title="[bold cyan]✨ Response[/bold cyan]",
                border_style="cyan",
                padding=(2, 3),
                expand=True
            )
            console.print(response_panel)
    
    return result


async def main():
    """Main CLI loop"""
    
    # Display header with branding and intro
    console.print("\n")
    header = Text()
    header.append("📚 ", style="bold magenta")
    header.append("Revision Agent", style="bold magenta")
    
    intro_text = Text()
    intro_text.append("\nAI-Powered Learning Assistant", style="dim")
    intro_text.append("\n\n", style="dim")
    intro_text.append("Synthesize your notes into flashcards, summaries, and practice problems. ", style="cyan")
    intro_text.append("Ask questions to deepen your understanding.", style="cyan")
    
    console.print(
        Panel(
            Align.center(header + intro_text),
            border_style="magenta",
            padding=(2, 4),
            expand=True
        )
    )
    console.print(
        Panel("[bold cyan]Initializing...[/bold cyan]", border_style="blue", padding=(1, 2))
    )
    
    mcp_tools = await client.get_tools()
    new_tools = [retrieval_tool, think_tool] + mcp_tools
    model = init_chat_model(model="openai:gpt-4o-mini", temperature=0.0)
    
    checkpointer = MemorySaver()
    
    interrupt_on = {
        "write_file": {"allowed_decisions": ["approve", "reject"]},
    }
    
    agent = create_deep_agent(
        model=model,
        tools=new_tools,
        system_prompt=INSTRUCTIONS,
        subagents=[flashcard_generator_sub_agent],
        backend=FilesystemBackend(root_dir=".", virtual_mode=False),
        interrupt_on=interrupt_on,
        checkpointer=checkpointer,
    )
    
    # Use single thread ID for conversation continuity
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # Conversation loop
    messages = []
    
    # Display ready state with Claude-style formatting
    ready_text = Text()
    ready_text.append("✓", style="bold green")
    ready_text.append(" Ready\n", style="bold green")
    ready_text.append("\nAsk questions about your revision notes", style="cyan")
    
    console.print(
        Panel(
            ready_text,
            border_style="green",
            padding=(2, 3),
            expand=True
        )
    )
    
    while True:
        try:
            console.print()
            user_input = Prompt.ask("[bold cyan]You[/bold cyan]", console=console).strip()
            
            # Handle exit commands
            if user_input.lower() in ["exit", "quit", "q"]:
                goodbye_text = Text()
                goodbye_text.append("👋", style="bold yellow")
                goodbye_text.append(" Goodbye", style="bold yellow")
                
                console.print()
                console.print(
                    Panel(
                        Align.center(goodbye_text),
                        border_style="yellow",
                        padding=(2, 4),
                        expand=True
                    )
                )
                break
            
            if not user_input:
                continue
            
            # Add user message to history (display happens via agent response)
            messages.append({"role": "user", "content": user_input})
            
            # Show processing with elegant animation
            console.print()
            process_text = Text()
            process_text.append("⏳ ", style="bold blue")
            process_text.append("Processing...", style="blue")
            console.print(process_text)
            
            result = await process_query(agent, messages, config)
            
            # Update messages with full conversation history
            if "messages" in result:
                messages = result["messages"]
        
        except KeyboardInterrupt:
            console.print()
            interrupt_text = Text()
            interrupt_text.append("⊘", style="bold yellow")
            interrupt_text.append(" Interrupted", style="bold yellow")
            
            console.print(
                Panel(
                    Align.center(interrupt_text),
                    border_style="yellow",
                    padding=(1, 3),
                    expand=True
                )
            )
            break
        except Exception as e:
            console.print()
            error_text = Text()
            error_text.append("✗", style="bold red")
            error_text.append(f" Error: {str(e)}", style="red")
            
            console.print(
                Panel(
                    error_text,
                    border_style="red",
                    padding=(1, 2),
                    expand=True
                )
            )


if __name__ == "__main__":
    asyncio.run(main())