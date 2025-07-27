from src.command_line.base import Command, CommandResult
from src.command_line.quit_command import QuitCommand
from src.command_line.help_command import HelpCommand
from src.command_line.agents_command import AgentsCommand
from src.command_line.clear_command import ClearCommand
from src.command_line.config_command import ConfigCommand
from src.command_line.talkto_command import TalkToCommand
from src.command_line.console import console

class CommandRegistry:
    """ Registry for managing and executing CLI commands.

    This class acts as the central hub that stores all available commands,
    handles user command input, and delegates execution to the correct Command object.
    """

    def __init__(self):
        """Initializes the command registry and registers all default commands."""
        self.commands = {}
        self._register_default_commands()
    
    def register_command(self, name: str, command: Command):
        """Registers a custom command to the registry.
        Args:
            name (str): Command name (without '/')
            command (Command): Command object implementing the Command interface
        """
        self.commands[name.lower()] = command
    
    def _register_default_commands(self):
        """Internal method to register the default set of commands."""
        self.register_command("quit", QuitCommand())
        self.register_command("help", HelpCommand(self))
        self.register_command("agents", AgentsCommand())
        self.register_command("clear", ClearCommand())
        self.register_command("config", ConfigCommand())
        self.register_command("talkto", TalkToCommand())
    
    def execute_command(self, cmd_input: str, agents: list, config: dict, current_target: str) -> CommandResult:
        """Parses and executes a CLI command entered by the user.

        This function checks if the input is a valid command (starting with '/'), extracts the command name
        and any accompanying arguments, looks up the corresponding Command object, and executes it. If the
        command is unknown, it prints an error message.
        Args:
            cmd_input (str): Raw command string from the user (e.g., "/talkto agent1")
            agents (list): List of agent objects
            config (dict): Configuration dictionary from JSON
            current_target (str): Name of the currently targeted agent (or None)
        Returns:
            CommandResult: Result of the command execution, including exit status or target switch
        """
        if not cmd_input.startswith('/'):
            raise ValueError("Commands must start with '/'")
        
        # Remove the '/' and split command from arguments
        cmd_input = cmd_input[1:]
        parts = cmd_input.split(' ', 1)
        cmd_name = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        # Look up and execute the command
        command = self.commands.get(cmd_name)
        if command:
            return command.execute(args, agents, config, current_target)
        else:
            console.print(f"[red]❌ Unknown command: /{cmd_name}[/red]")
            console.print("Type [cyan]/help[/cyan] for available commands")
            return CommandResult()
