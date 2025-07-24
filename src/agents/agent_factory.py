from src.agents.openRouterAgent import OpenRouterAgent
from src.agents.agent import AgentConfig, Agent, AgentError
from src.agents.provider import Provider


class AgentFactory:
    """Factory class to create agents based on auto-detected provider"""
    
    @staticmethod
    def create_agent(config: AgentConfig) -> Agent:
        """Create an agent based on the auto-detected provider in config"""
        provider = config.provider.lower()
        
        if provider == Provider.OPENAI.value:
            # return OpenAIAgent(config)
            print("hi")
        elif provider == Provider.OPENROUTER.value:
            return OpenRouterAgent(config)
        elif provider == Provider.ANTHROPIC.value:
            print("hi")
        else:
            raise AgentError(f"Unsupported provider: {provider} for model: {config.model_name}")
