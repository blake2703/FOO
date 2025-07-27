from src.command_line.base import Command, CommandResult
from src.command_line.console import console

class TalkToCommand(Command):
    """Command to focus interaction on a single agent or reset to broadcasting to all agents.
    
    Allows the user to temporarily direct their messages to one specific agent in the chat.
    """

    def execute(self, args: str, agents: list, config: dict, current_target: str) -> CommandResult:
        """Executes the /talkto command.

        If no arguments are provided, the command resets the target to all agents.
        If an agent name is provided, it checks for a match and switches the focus to that agent.
        Args:
            args (str): User input after the command (e.g., the agent name)
            agents (list): List of loaded agent objects
            config (dict): Full configuration dictionary
            current_target (str): The current target agent name (if any)
        Returns:
            CommandResult: Object containing updated target info or an error message
        """
        if not args.strip():
            # Reset to all agents if no specific target is provided
            console.print(f"[green]🔄 Switched back to all agents[/green]")
            return CommandResult(new_target=None)
        
        target = args.strip().lower()
        # Look for a matching agent by name (case-insensitive)
        matching_agent = next(
            (agent for agent in agents if agent.config.agent_name.lower() == target), 
            None
        )
        
        if matching_agent:
            if current_target == target:
                # If already focused on the agent, toggle back to all agents
                console.print(f"[green]🔄 Switched back to all agents[/green]")
                return CommandResult(new_target=None)
            else:
                # Switch to the matched agent
                console.print(f"[bold green]🗣️ Now talking to:[/bold green] [cyan]{matching_agent.config.agent_name}[/cyan]")
                return CommandResult(new_target=target)
        else:
            # No matching agent found
            console.print(f"[red]❌ No agent named '{target}' found[/red]")
            return CommandResult(new_target=current_target)

    def get_description(self) -> str:
        """Returns a description of the /talkto command for use in help output."""
        return "Focus chat to a single agent (type /talkto to reset to all agents)"
