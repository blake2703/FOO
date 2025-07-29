from src.command_line.console import console, AGENT_EMOJIS
from src.command_line.registry import CommandRegistry
from src.logging.logger import *


def process_user_input(user_input: str, agents: list, target_agent: str, logger: CommandLineLogger):
    """Processes the user's input and routes it to the appropriate agent(s) for response.
    Args:
        user_input (str): The text input provided by the user.
        agents (list): List of initialized agent objects.
        target_agent (str): Name of the currently focused agent, or None to broadcast to all.
    """
    # Visual feedback for incoming input
    console.print(f"\n[bold]🤔 Processing:[/bold] [italic green]{user_input}[/italic green]")
    console.print("-" * 50)

    # Filter agents based on current target (all agents if no specific one is targeted)
    response_agents = [
        (i, agent) for i, agent in enumerate(agents)
        if target_agent is None or agent.config.agent_name.lower() == target_agent
    ]

    if not response_agents:
        console.print("[red]❌ No matching agent found.[/red]")
        return

    # Loop through selected agents and get their responses
    for i, agent in response_agents:
        emoji = AGENT_EMOJIS[i % len(AGENT_EMOJIS)]  # Rotate emojis for flair
        with console.status(f"[bold green]{emoji} {agent.config.agent_name} is thinking...[/bold green]", spinner="dots"):
            start_time = time.time()
            try:
                response = agent.generate_response(user_input).strip()
                response_time = time.time() - start_time
                interaction = AgentInteraction(
                    agent_name=agent.config.agent_name,
                    user_input=user_input,
                    agent_response=response,
                    response_time=response_time,
                    tokens_used=getattr(agent, 'last_token_count', None),
                    error=None
                )
                logger.log_agent_response(interaction=interaction)
                
                
                console.print(
                    f"\n{emoji} [bold cyan]{agent.config.agent_name}[/bold cyan]: "
                    f"{response if response else '[dim]No response generated[/dim]'}"
                )
            except Exception as e:
                console.print(f"\n{emoji} [bold cyan]{agent.config.agent_name}[/bold cyan]: [red]❌ Error: {e}[/red]")

    console.print("-" * 50)


def chat_loop(agents: list, config: dict):
    """Launches the main chat interface that handles both agent interaction and command execution.
    Args:
        agents (list): List of initialized agent instances.
        config (dict): Configuration dictionary with global and agent-specific settings.
    """
    command_registry = CommandRegistry()   # Set up command system (e.g., /help, /talkto)
    current_target = None  # Initially talking to all agents
    
    # Begin log
    logger = CommandLineLogger()

    # Show help info on start
    help_command = command_registry.commands["help"]
    help_command.execute("", agents, config, current_target)
    logger.log_session_start(agents=agents, config=config)

    while True:
        try:
            user_input = input("\n💬 You: ").strip()
            if not user_input:
                continue

            if user_input.startswith('/'):
                # Handle command (like /quit or /talkto AgentA)
                result = command_registry.execute_command(user_input, agents, config, current_target)
                if result.should_exit:
                    break
                if result.new_target is not None:
                    current_target = result.new_target
            else:
                # Send message to targeted agent(s)
                logger.log_user_input(user_input=user_input, current_target=current_target)
                process_user_input(user_input, agents, current_target, logger=logger)

        except (KeyboardInterrupt, EOFError):
            # Graceful exit on Ctrl+C or Ctrl+D
            console.print("\n\n👋 [bold red]Goodbye![/bold red]")
            break
    logger.log_session_end()
