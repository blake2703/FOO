from src.command_line.base import Command, CommandResult
from src.command_line.console import console

class ClearCommand(Command):
    """ Command to clear the terminal screen.

    This class implements the `/clear` command functionality, which wipes the terminal 
    display using Rich's `console.clear()` method. It can be useful for improving 
    readability during long chat sessions.
    Methods:
        - execute: Clears the terminal screen.
        - get_description: Provides a short description for the help menu.
    """
    def execute(self, args: str, agents: list, config: dict, current_target: str) -> CommandResult:
        """ Executes the `/clear` command by clearing the terminal output.
        Args:
            args (str): Any arguments passed to the command (not used).
            agents (list): List of agent instances (not used).
            config (dict): Configuration dictionary (not used).
            current_target (str): Currently targeted agent (not used).
        Returns:
            CommandResult: Indicates no change in target or exit state.
        """
        console.clear()
        return CommandResult()
    
    def get_description(self) -> str:
        """
        Returns:
            str: A short description of the command for the help display.
        """
        return "Clear the screen"
