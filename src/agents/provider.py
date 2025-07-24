from enum import Enum
from dataclasses import dataclass
from typing import Optional
import os

class ProviderError(Exception):
    """Custom exception for api provider-related errors"""
    pass


class Provider(Enum):
    """Supported API providers"""
    OPENAI = "openai"
    OPENROUTER = "openrouter"
    ANTHROPIC = "anthropic"


@dataclass
class ProviderSettings:
    """Provider-specific configuration settings"""
    api_key_env: str
    default_base_url: str


class ProviderManager:
    """Handles provider detection and API configuration
        _PROVIDER_SETTINGS: 
            - a dictionary containing the enum value of the provider (openai, openrouter, anthropic)
            - contains the api key for the provider
            - contains a base url needed to ineract with the provider
        _MODEL_PATTERNS:
            - a dictionary of lists for each provider containing the models they offer
    """
    _PROVIDER_SETTINGS = {
        Provider.OPENAI.value: ProviderSettings(
            api_key_env="OPENAI_API_KEY",
            default_base_url="https://api.openai.com/v1" 
        ),
        Provider.OPENROUTER.value: ProviderSettings(
            api_key_env="OPEN_ROUTER_API_KEY",
            default_base_url="https://openrouter.ai/api/v1"
        ),
        Provider.ANTHROPIC.value: ProviderSettings(
            api_key_env="ANTHROPIC_API_KEY",
            default_base_url="https://api.anthropic.com"
        )
    }
    _MODEL_PATTERNS = {
        Provider.OPENAI.value: ["gpt-3.5", "gpt-4"],
        Provider.ANTHROPIC.value: ["claude-3", "claude-4"],
        Provider.OPENROUTER.value: ["kimi"]
    }
    
    @classmethod
    def detect_provider(cls, model_name: str) -> str:
        """
        Detect provider based on model name patterns
        Args:
            model_name (str): name of the LLM model being used
        Returns:
            str: the api provider that enables api calls to the specific LLM model
        """
        model_lower = model_name.lower()
        for provider, patterns in cls._MODEL_PATTERNS.items():
            if any(pattern in model_lower for pattern in patterns):
                return provider
        raise ProviderError(f"Could not determine provider from model name: {model_name}")
    
    @classmethod
    def get_provider_settings(cls, provider: str) -> ProviderSettings:
        """
        Get provider-specific settings
        Args:
            provider (str): the name of the api provider 
        Returns:
            ProviderSettings: the LLMs associated with the api provider
        """
        if provider not in cls._PROVIDER_SETTINGS:
            raise ValueError(f"Unsupported provider: {provider}")
        return cls._PROVIDER_SETTINGS[provider]
    
    @classmethod
    def get_api_key(cls, provider: str) -> str:
        """
        Get API key from environment variable
        Args:
            provider (str): the name of the api provider 
        Returns:
            str: api key for the associated provider
        """          
        settings = cls.get_provider_settings(provider)
        api_key = os.getenv(settings.api_key_env)
        
        if not api_key:
            raise ValueError(
                f"API key not found for provider '{provider}'. "
                f"Please set environment variable '{settings.api_key_env}'"
            )
        return api_key
    
    @classmethod
    def get_base_url(cls, provider: str) -> str:
        """
        Get the base url
        Args:
            provider (str): the name of the api provider 
        Returns:
            str: the base url for the associated provider
        """   
        return cls.get_provider_settings(provider).default_base_url