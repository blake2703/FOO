from rich.panel import Panel
from rich.table import Table
from rich import box
from src.command_line.base import Command, CommandResult
from src.command_line.console import console, AGENT_EMOJIS


class HelpCommand(Command):
    """ Command to display the help menu.

    This class implements the `/help` command, which provides a list of all available
    commands along with their descriptions. It also displays a header panel with
    the active agents.
    Attributes:
        command_registry: An instance of CommandRegistry that stores all available commands.
    Methods:
        - _display_help(agents): Renders the help menu with the commands and agent list.
        - execute(args, agents, config, current_target): Executes the `/help` command.
        - get_description(): Returns a short description of the command.
    """
    def __init__(self, command_registry):
        """ Initialize the HelpCommand with a command registry.
        Args:
            command_registry: The CommandRegistry instance containing all available commands.
        """
        self.command_registry = command_registry
    
    def _display_help(self, agents: list):
        """ Render the help panel with a list of active agents and available commands.
        Args:
            agents (list): List of active agent objects to display in the header.
        """
        console.print("\n", Panel.fit("🤖 [bold cyan]Interactive Multi-Agent Chat[/bold cyan]", style="bold green"))

        for i, agent in enumerate(agents):
            emoji = AGENT_EMOJIS[i % len(AGENT_EMOJIS)]
            console.print(f"  {emoji} [bold cyan]{agent.config.agent_name}[/bold cyan]")

        table = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE)
        table.add_column("Command", style="cyan")
        table.add_column("Description")

        for cmd_name, command in self.command_registry.commands.items():
            table.add_row(f"/{cmd_name}", command.get_description())
        console.print(table)
            
    def execute(self, args, agents, config, current_target):
        """ Executes the `/help` command to display the help menu.
        Args:
            args: Additional arguments for the command (unused here).
            agents (list): List of agent objects.
            config (dict): The current configuration (unused here).
            current_target (str): Current active agent (unused here).
        Returns:
            CommandResult: Indicates the chat loop should continue with no state changes.
        """
        self._display_help(agents=agents)
        return CommandResult()
    
    def get_description(self):
        """
        Returns:
            str: A short description of this command for the help menu.
        """
        return "Show help message"
