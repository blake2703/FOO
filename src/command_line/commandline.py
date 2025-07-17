# Add path to find files in other modules
import sys
import os
sys.path.append(os.getcwd())

import typer
from typing import Optional
from pathlib import Path
import json
from enum import Enum
from rich.progress import Progress
from src.agents.agents import Agent, KimiK2
from utils import chat_loop

# Instantiate typer because we have multiple functions
app = typer.Typer()

# Configurations for the CLI arguments
class PredefinedConfig(str, Enum):
    SINGLE = "single_open_source"
    MULTI = "multi_open_source"
    
DEFAULT_CONFIGS = {
    "single_open_source": Path("test.json"),
    "multi_open_source": Path("config/experiments/multi_open_source.json")
}

def load_config(file_path: Path) -> dict:
    """
    Loads a json configuration for a user-defined file or a built in experiment from FOO

    Args:
        file_path (Path): a file path
    Returns:
        dict: a config dictionary
    """
    if not file_path.exists():
        raise typer.BadParameter(f"Config file not found: {file_path}")
    with open(file=file_path) as f:
        return json.load(f)

def create_agent(config: dict) -> Agent:
    """
    Creates an agent with the factory design pattern

    Args:
        config (dict): a json configuration
    Returns:
        Agent: the specified llm agent
    """
    model_name = config.get("model_name", "").lower()
    if "kimi" in model_name:
        return KimiK2(config=config)
    else:
        raise ValueError(f"Could not determine agent type from model_name: {model_name}. Agent may not be available at time of writing.")


@app.command()
def chat(
    predefined_config: PredefinedConfig = typer.Option(
        PredefinedConfig.SINGLE,
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
    """
    Enables a user to have a conversation with a single agent or multiple agents.
    """
    with Progress() as progress:
        # Load configuration file
        config_task = progress.add_task("[cyan]Loading configuration...", total=1)
        if predefined_config:
            path = Path(DEFAULT_CONFIGS[predefined_config])
            config = load_config(file_path=path)
        else:
            config = load_config(file_path=user_config)
        progress.update(config_task, advance=1)
        # Load agents
        agent_task = progress.add_task("[green]Initializing agents...", total=len(config["AGENTS"]))
        agents = []
        for agent_config in config["AGENTS"]:
            merged_config = {
                **agent_config,
                "CONFIG": config["CONFIG"]
            }
            agent = create_agent(merged_config)
            agents.append((agent_config["agent_name"], agent))
            progress.update(agent_task, advance=1)
    chat_loop(agents, config)

if __name__ == "__main__":
    app()