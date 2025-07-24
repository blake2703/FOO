from openai import OpenAI
from src.agents.agent import Agent, AgentError
import requests
import json

class OpenRouterAgent(Agent):
    """Agent for OpenRouter models"""
    
    def _init_client(self) -> OpenAI:
        """
        Initialize OpenRouter client using OpenAI SDK
        Returns:
            OpenAI: OpenAI client
        """
        return OpenAI(
            base_url=self.config.base_url,
            api_key=self.config.api_key,
        )
    
    def _validate_config(self):
        """Validate OpenRouter-specific configuration"""
        if not self.config.api_key:
            raise AgentError("OpenRouter API key is required")
        print(f"Validating OpenRouter agent: {self.config.agent_name}")
    
    def generate_response(self, prompt: str) -> str:
        """
        Generate response using OpenRouter API

        Args:
            prompt (str): prompt asked by the user upon runtime
        Returns:
            str: response from the agent
        """
        try:
            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.temperature,
                max_tokens=self.config.max_completion_tokens
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise AgentError(f"OpenRouter agent failed: {e}")
                    