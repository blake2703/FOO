from abc import ABC, abstractmethod
from typing import List, Optional, Any
from dataclasses import dataclass
from src.agents.provider import ProviderManager


class AgentError(Exception):
    """Custom exception for agent-related errors."""
    pass


@dataclass
class AgentConfig:
    """
    Configuration for an agent with automatic provider detection based on model name
    Args:
        model_name: LLM model to use
        agent_name: Name of the agent
        agent_description: Description of the model configuration
        general_instructions: Global instructions for all agents
        general_directives: Global directives for all agents
        temperature: Model randomness (0.0-2.0)
        max_completion_tokens: Maximum response tokens
        harmonizer: Whether this agent is the harmonizer
        agent_directives: Agent-specific directives
        base_url: Custom API base URL (auto-detected if None)
        api_key: API key (auto-detected from env if None)
        provider: Provider type (auto-detected if None)
    """
    model_name: str
    agent_name: str
    agent_description: str
    general_instructions: Optional[str] = None
    general_directives: Optional[List[str]] = None
    temperature: float = 0.0
    max_completion_tokens: int = 1000
    harmonizer: bool = False
    agent_directives: Optional[List[str]] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    provider: Optional[str] = None

    def __post_init__(self):
        """Validate configuration and auto-configure provider settings"""
        self._validate_config()
        self._configure_provider()

    def _validate_config(self) -> None:
        """Validate basic configuration parameters"""
        validations = [
            (not (0.0 <= self.temperature <= 2.0), "Temperature must be between 0.0 and 2.0"),
            (self.max_completion_tokens <= 0, "max_completion_tokens must be positive"),
            (not self.model_name.strip(), "model_name cannot be empty"),
            (not self.agent_name.strip(), "agent_name cannot be empty"),
            (not self.agent_description.strip(), "agent_description cannot be empty")
        ]
        
        for condition, message in validations:
            if condition:
                raise ValueError(message)

    def _configure_provider(self) -> None:
        """Auto-detect provider and configure API settings"""
        if not self.provider:
            self.provider = ProviderManager.detect_provider(self.model_name)
        self.api_key = ProviderManager.get_api_key(self.provider)
        self.base_url = ProviderManager.get_base_url(self.provider)


class Agent(ABC):
    """Abstract base class for all agents"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self._validate_config()
        self.client = self._init_client()

    @abstractmethod
    def _init_client(self) -> Any:
        """Initialize the provider-specific client"""
        pass

    @abstractmethod
    def generate_response(self, prompt: str) -> str:
        """Generate a response to the given prompt"""
        pass

    @abstractmethod
    def _validate_config(self) -> None:
        """Validate agent-specific configuration"""
        pass