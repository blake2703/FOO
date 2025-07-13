import json

# test opening up the open source data
with open("config/experiments/all_open_source.json") as open_source_config:
    config = json.load(open_source_config)

# read in the agents defined in the config
for agent_config in config['AGENTS']:
    general_instructions = config['CONFIG']['general_instructions']
    
    general_directives = config['CONFIG']['general_directives']
    general_directives = " ".join(general_directives)
    
    agent_directives = agent_config.get('agent_directives', [])
    agent_directives = " ".join(agent_directives)
    
    combined_instructions = f"{general_instructions}\n{general_directives}\n{agent_directives}"
    print(f"\n=== Agent: {agent_config['agent_name']} ===\n")
    print(combined_instructions)
