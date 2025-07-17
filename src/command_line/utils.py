def display_chat_intro(agents: list):
    """
    Displays the heading for the command line chatbot

    Args:
        agents (list): all agents involved in the chat
    """
    print("\n" + "="*60)
    print("🤖 Interactive Chat")
    print("="*60)
    print(f"Loaded {len(agents)} agents: {', '.join([name for name, _ in agents])}")
    print("\nCommands:")
    print("  /quit or /exit - Exit the chat")
    print("  /help - Show this help message")
    print("  /agents - List all agents")
    print("  /clear - Clear the screen")
    print("  /config - Show current configuration")
    print("="*60)

def handle_chat_commands(cmd: str, agents: list, config: dict) -> bool:
    """
    Utility function to allow the user to perform operations in the chat

    Args:
        cmd (str): the command from the user
        agents (list): all agents involved in the chat
        config (dict): configuration file for the agents
    Returns:
        bool: whether the loop the chat is still active
    """
    cmd = cmd.lower()
    
    if cmd in ['/quit', '/exit']:
        print("\n👋 Goodbye!")
        return False
    elif cmd == '/help':
        print("\nCommands:")
        print("  /quit or /exit - Exit the chat")
        print("  /help - Show this help message")
        print("  /agents - List all agents")
        print("  /clear - Clear the screen")
        print("  /config - Show current configuration")
    elif cmd == '/agents':
        print(f"\nLoaded agents: {', '.join([name for name, _ in agents])}")
    elif cmd == '/clear':
        print("\033[2J\033[H")
    elif cmd == '/config':
        print(f"\nCurrent configuration:")
        print(f"  General instructions: {config.get('CONFIG', {}).get('general_instructions', 'None')}")
        print(f"  Number of agents: {len(agents)}")
        for name, _ in agents:
            agent_config = next(a for a in config['AGENTS'] if a['agent_name'] == name)
            print(f"    {name}: {agent_config.get('model_description', 'No description')}")
    else:
        print(f"Unknown command: {cmd}")
    return True


def process_user_input(user_input: str, agents: list):
    """
    Utility function to process user input for the agent

    Args:
        user_input (str): query presented by the user
        agents (list): all agents involved in the chat
    """
    print(f"\n🤔 Processing: {user_input}")
    print("-" * 50)
    
    for name, agent in agents:
        print(f"\n🤖 {name}:")
        try:
            response = agent.generate_response(user_input)
            if response.strip():
                print(f"   {response}")
            else:
                print("   [No response generated]")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("-" * 50)

def chat_loop(agents: list, config: dict):
    """
    Utility function to run the chat 

    Args:
        agents (list): all agents involved in the chat
        config (dict): configuration file for the aents
    """
    display_chat_intro(agents)

    while True:
        try:
            user_input = input("\n💬 You: ").strip()
            if not user_input:
                continue
            if user_input.startswith('/'):
                if not handle_chat_commands(user_input, agents, config):
                    break
            else:
                process_user_input(user_input, agents)
        except (KeyboardInterrupt, EOFError):
            print("\n\n👋 Goodbye!")
            break
