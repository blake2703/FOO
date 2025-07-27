import typer
from pathlib import Path
from enum import Enum
from typing import Optional
from rich.progress import Progress
import json
from dotenv import load_dotenv
import sys
import os

# Add the current working directory to the system path for easier imports
sys.path.append(os.getcwd())

# Load environment variables from .env file (e.g., API keys)
load_dotenv()

# Local module imports
from src.agents.agent import AgentConfig
from src.agents.agent_factory import AgentFactory
from src.command_line.utils import chat_loop

# Instantiate Typer CLI app
app = typer.Typer()

# Default config file paths for built-in experiments
PREDEFINED_CONFIG_FILE_PATHS = {
    "single_open_source": Path("test.json"),
    "multi_open_source": Path("config/experiments/multi_open_source.json")
}

# Required keys for agent-specific and global configuration
REQUIRED_AGENT_KEYS = {
    "model_name", "agent_name", "model_description", "temperature",
    "max_completion_tokens", "harmonizer", "agent_directives"
}
REQUIRED_CONFIG_KEYS = {"general_instructions", "general_directives"}


class PredefinedConfig(str, Enum):
    """Enum for selecting predefined configuration modes.
    Options:
        - SINGLE_OPEN_SOURCE: Use a single open-source LLM agent.
        - MULTI_OPEN_SOURCE: Use multiple open-source LLM agents together.
    """
    SINGLE_OPEN_SOURCE = "single_open_source"
    MULTI_OPEN_SOURCE = "multi_open_source"


def load_config(file_path: Path) -> dict:
    """Loads a JSON configuration from the specified file path.
    Args:
        file_path (Path): Path to the config file.
    Returns:
        dict: Parsed configuration dictionary.
    """
    if not file_path.exists():
        raise typer.BadParameter(f"Config file not found: {file_path}")
    with open(file=file_path) as f:
        return json.load(f)


@app.command()
def chat(
    predefined_config: PredefinedConfig = typer.Option(
        PredefinedConfig.SINGLE_OPEN_SOURCE,
        help=(
            "🧠 Choose a predefined config:\n"
            "  • single_open_source →  One open-source agent\n"
            "  • multi_open_source  →  Multiple agents working together"
        ),
        rich_help_panel="🛠 Config Options"
    ),
    user_config: Optional[Path] = typer.Option(
        None,
        help="📁 Optional path to a custom config file (overrides --predefined-config)",
        rich_help_panel="🛠 Config Options"
    )
):
    """Initializes the agents based on the given configuration and launches the chat loop."""
    with Progress(transient=True) as progress_bar:
        # Show status of API keys loaded from .env
        progress_bar.console.rule("🌍 Environment Check")
        progress_bar.console.log(f"OPEN_ROUTER_API_KEY: {'✓ Set' if os.getenv('OPEN_ROUTER_API_KEY') else '✗ Not set'}")
        progress_bar.console.log(f"OPENAI_API_KEY: {'✓ Set' if os.getenv('OPENAI_API_KEY') else '✗ Not set'}")
        progress_bar.console.log(f"ANTHROPIC_API_KEY: {'✓ Set' if os.getenv('ANTHROPIC_API_KEY') else '✗ Not set'}")
        progress_bar.console.rule()

        # Step 1: Load config file
        config_task = progress_bar.add_task("[cyan]Loading configuration...", total=1)
        if user_config:
            path = user_config
            progress_bar.console.log(f"📁 Using custom config from: {path}")
        else:
            path = PREDEFINED_CONFIG_FILE_PATHS[predefined_config.value]
            progress_bar.console.log(f"📄 Using predefined config: {predefined_config.value} ({path})")
        config_data = load_config(file_path=path)
        progress_bar.update(config_task, advance=1)

        # Step 2: Initialize each agent from the config
        agent_task = progress_bar.add_task("[green]Initializing agents...", total=len(config_data["AGENTS"]))
        shared_config = config_data["CONFIG"]
        agents = []

        for agent_config in config_data["AGENTS"]:
            config_dict = {**shared_config, **agent_config}  # Combine global + agent-specific config
            try:
                c = AgentConfig(**config_dict)  # Validate config
                agent = AgentFactory.create_agent(config=c)  # Create agent from config
                agents.append(agent)
                progress_bar.console.log(f"✅ Created and initialized agent: {c.agent_name} using {c.provider}")
            except Exception as e:
                progress_bar.console.log(f"[red]❌ Failed to create agent: {e}")
            progress_bar.update(agent_task, advance=1)
        progress_bar.console.rule("✅ Setup Complete")
        progress_bar.console.log(f"Successfully created {len(agents)} agent(s) ✨")
    # Step 3: Format config for use in the chat loop
    config_dict = {
        "CONFIG": shared_config,
        "AGENTS": config_data["AGENTS"]
    }
    # Launch interactive chat loop
    chat_loop(agents, config_dict)


# Entry point for script usage
if __name__ == "__main__":
    app()