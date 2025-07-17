import json
from src.agents.agents import Agent, KimiK2

# test opening up the open source data
with open("config/experiments/single_llama.json") as open_source_config:
    config = json.load(open_source_config)


def create_agent(config: dict) -> Agent:
    model_name = config.get("model_name", "").lower()

    if "llama" in model_name:
        return
        # return LlamaAgent(config=config)
    elif "kimi" in model_name:
        return KimiK2(config=config)
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
    merged_config = {
        **agent_config,
        "CONFIG": config["CONFIG"]
    }
    agent = create_agent(merged_config)
    agents.append((agent_config["agent_name"], agent))


for name, agent in agents:
    response = agent.generate_response("what are the names of the planets in our solar system?")
    print(f"{name}: {response}")

    




