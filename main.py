import json
from src.agents.agents import Agent, LlamaAgent

# test opening up the open source data
with open("config/experiments/all_open_source.json") as open_source_config:
    config = json.load(open_source_config)

# # read in the agents defined in the config
# for agent_config in config['AGENTS']:
#     general_instructions = config['CONFIG']['general_instructions']
    
#     general_directives = config['CONFIG']['general_directives']
#     general_directives = " ".join(general_directives)
    
#     agent_directives = agent_config.get('agent_directives', [])
#     agent_directives = " ".join(agent_directives)
    
#     combined_instructions = f"{general_instructions}\n{general_directives}\n{agent_directives}"
#     print(f"\n=== Agent: {agent_config['agent_name']} ===\n")
#     print(combined_instructions)

def create_agent(config: dict) -> Agent:
    model_name = config.get("model_name", "").lower()

    if "llama" in model_name:
        return LlamaAgent(config=config)
    # elif "gpt" in model_name:
    #     return GPTAgent(config=config)
    # elif "claude" in model_name:
    #     return ClaudeAgent(config=config)
    # elif "gemini" in model_name:
    #     return GeminiAgent(config=config)
    else:
        raise ValueError(f"Could not determine agent type from model_name: {model_name}")

agents = []
for agent_config in config["AGENTS"]:
    agent = create_agent(agent_config)
    agents.append((agent_config["agent_name"], agent))

for name, agent in agents:
    response = agent.generate_response("Plants create energy through a process known as")
    print(f"{name}: {response}")

    




