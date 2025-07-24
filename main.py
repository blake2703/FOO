# main.py
import json
from src.agents.agent_factory import AgentFactory
from src.agents.agent import AgentConfig
from dotenv import load_dotenv
import os

def main():
    # Load environment variables from .env file
    load_dotenv()
    
    # Debug: Check if environment variables are loaded
    print("Environment variables check:")
    print(f"OPENROUTER_API_KEY: {'✓ Set' if os.getenv('OPEN_ROUTER_API_KEY') else '✗ Not set'}")
    print(f"OPENAI_API_KEY: {'✓ Set' if os.getenv('OPENAI_API_KEY') else '✗ Not set'}")
    print(f"ANTHROPIC_API_KEY: {'✓ Set' if os.getenv('ANTHROPIC_API_KEY') else '✗ Not set'}")
    print("-" * 50)

    # Load JSON configuration
    with open("config/experiments/multi_open_source.json") as f:
        config_data = json.load(f)

    shared_config = config_data["CONFIG"]
    agent_configs = config_data["AGENTS"]

    agents = []

    print("Creating agents...")
    for agent_config in agent_configs:
        # Merge shared config with agent-specific config
        config_dict = {
            **shared_config,
            **agent_config,
        }
        
        try:
            # Create AgentConfig (auto-detects provider and configures API settings)
            c = AgentConfig(**config_dict)
            print(f"✓ Created config for {c.agent_name} using {c.provider} provider")
            
            # Create agent using factory
            agent = AgentFactory.create_agent(config=c)
            agents.append(agent)
            
        except Exception as e:
            print(f"✗ Failed to create agent {agent_config.get('agent_name', 'Unknown')}: {e}")
            continue

    print(f"\nSuccessfully created {len(agents)} agents")
    print("=" * 60)

    # Test each agent
    if agents:
        test_prompt = "How do you respond to hello?"

        for agent in agents:
            try:
                print(f"\n[{agent.config.agent_name}] ({agent.config.provider})")
                print(f"Model: {agent.config.model_name}")
                
                response = agent.generate_response(test_prompt)
                print(f"Response: {response}")
                print("-" * 60)
                
            except Exception as e:
                print(f"[{agent.config.agent_name}] Error: {e}")
                print("-" * 60)
    else:
        print("No agents were successfully created. Please check your configuration and API keys.")

if __name__ == "__main__":
    main()