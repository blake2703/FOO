from src.command_line.base import Command, CommandResult
from src.command_line.console import console

class ConfigCommand(Command):
    """ Command to display the current system configuration.

    This class implements the `/config` command, which prints out the general
    instructions and configuration details of each agent loaded into the system.
    It's useful for debugging or confirming settings during runtime.
    Methods:
        - execute: Displays general instructions and agent-specific configuration.
        - get_description: Provides a short description for the help menu.
    """
    def execute(self, args: str, agents: list, config: dict, current_target: str) -> CommandResult:
        """ Executes the `/config` command by printing the current configuration.
        Args:
            args (str): Optional arguments for the command (unused here).
            agents (list): List of agent objects currently active.
            config (dict): The overall configuration loaded from the JSON file.
            current_target (str): The agent currently being focused (unused here).
        Returns:
            CommandResult: Indicates the system should continue running with no changes.
        """
        console.rule("[bold yellow]Current Configuration")
        console.print(f"[bold]General Instructions:[/bold] {config.get('CONFIG', {}).get('general_instructions', 'None')}")
        console.print(f"[bold]Number of agents:[/bold] {len(agents)}\n")

        for agent in agents:
            agent_name = agent.config.agent_name
            agent_config = next((a for a in config['AGENTS'] if a['agent_name'] == agent_name), {})
            console.print(f"[bold cyan]{agent_name} Configuration:[/bold cyan]")
            for key, value in agent_config.items():
                console.print(f"  [green]{key}[/green]: {value}")
            console.print("") 
        console.rule()
        return CommandResult()
    
    def get_description(self) -> str:
        """
        Returns:
            str: A short description of the command for the help display.
        """
        return "Show current configuration"
