from src.command_line.base import Command, CommandResult
from src.command_line.console import console

class QuitCommand(Command):
    """ Command to exit the chat application.

    This class implements the `/quit` or `/exit` command, which immediately
    ends the interactive chat session.
    Methods:
        - execute(args, agents, config, current_target): Executes the quit command.
        - get_description(): Returns a short description of the command.
    """

    def execute(self, args, agents, config, current_target):
        """ Executes the `/quit` or `/exit` command.
        Args:
            args (str): Optional arguments passed with the command (unused here).
            agents (list): List of agent objects (unused).
            config (dict): Configuration settings (unused).
            current_target (str): Current active agent (unused).
        Returns:
            CommandResult: Indicates the chat should exit.
        """
        console.print("\n👋 [bold red]Goodbye![/bold red]")
        return CommandResult(should_exit=True)
    
    def get_description(self):
        """
        Returns:
            str: A brief description of the command for the help menu.
        """
        return "Exit the chat"
