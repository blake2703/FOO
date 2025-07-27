from src.command_line.base import Command, CommandResult
from src.command_line.console import console, AGENT_EMOJIS

class AgentsCommand(Command):
    """Command to display a list of all currently loaded agents in the system.

    This class extends the abstract Command base class and implements the logic 
    for the `/agents` command. When executed, it prints out the names of all agents 
    currently active in the system, each with a unique emoji for clarity.
    Methods:
        - execute: Displays the agent list with emojis.
        - get_description: Returns a short help description.
    """
    def execute(self, args, agents, config, current_target):
        """Executes the `/agents` command. 
        
        Prints the names of all available agents along with a corresponding emoji.
        Args:
            args (str): Not used for this command. No arguments are passed after the command
            agents (list): List of all agent instances.
            config (dict): Loaded configuration dictionary (unused here).
            current_target (str): Currently focused agent name (unused here).
        Returns:
            CommandResult: Indicates no change in chat target or exit status.
        """
        console.print("\n🤖 [bold]Loaded agents:[/bold]")
        for i, agent in enumerate(agents):
            emoji = AGENT_EMOJIS[i % len(AGENT_EMOJIS)]
            console.print(f"  {emoji} [cyan]{agent.config.agent_name}[/cyan]")
        return CommandResult()

    def get_description(self):
        """
        Returns:
            str: A brief description of what this command does.
        """
        return "List of all agent names"
