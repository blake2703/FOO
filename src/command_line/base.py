from abc import ABC, abstractmethod

class CommandResult:
    """Represents the result of executing a user command in the chat interface.
    
    This class is used to indicate what the system should do after a command is processed and
    whether the chat loop should exit or if the target agent should change.
    Attributes:
        should_exit (bool): if True, the chat loop should terminate.
        new_target (str or None): the new agent to focus responses on. If None, no change.
    """
    def __init__(self, should_exit: bool = False, new_target: str = None):
        self.should_exit = should_exit
        self.new_target = new_target


class Command(ABC):
    """Abstract base class for all user commands in the multi-agent chat interface.

    Subclasses must implement:
        - execute(): the logic for executing the command
        - get_description(): a short description for displaying in the help menu
    Methods:
        execute(args, agents, config, current_target): Executes the command with given parameters.
        get_description(): Returns a short description of the command.
    """
    @abstractmethod
    def execute(self, args: str, agents: list, config: dict, current_target: str) -> CommandResult:
        """Execute the logic associated with the command.
        Args:
            args (str): Any argument or additional text provided after the command.
            agents (list): List of agent objects available in the system.
            config (dict): Configuration settings loaded from JSON or defaults.
            current_target (str): The agent currently being focused, or None if chatting with all.
        Returns:
            CommandResult: Object indicating whether to exit or switch target agent.
        """
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Return a short description of what the command does. Used for the /help menu.
        Returns:
            str: Description of the command.
        """
        pass