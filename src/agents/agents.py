from abc import ABC, abstractmethod
from openai import OpenAI
from dotenv import load_dotenv
import os

# Load in environment variables
load_dotenv()

class Agent(ABC):
    """
    An abstract class for all agents
    """
    @abstractmethod
    def generate_response(self, prompt: str) -> str:
        pass

class KimiK2(Agent):
    """
    Derived class from the base of agents. Instantiates the Kimi-k2 agent
    """
    def __init__(self, config: dict):
        self.model = config["model_name"]
        self.temperature = config.get('temperature', 0.6)
        self.max_tokens = config.get('max_completion_tokens', 256)
        self.general_instructions = config["CONFIG"].get("general_instructions", "")
        self.general_directives = config["CONFIG"].get("general_directives", [])
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv('OPEN_ROUTER_API_KEY')
        )

    def generate_response(self, prompt: str) -> str:
        messages = [
            {"role": "system", "content": f"{self.general_instructions} {self.general_directives}"},
            {"role": "user", "content": prompt}
        ]
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        return completion.choices[0].message.content.strip()    