from abc import ABC, abstractmethod
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


class Agent(ABC):
    
    @abstractmethod
    def generate_response(self, prompt: str) -> str:
        pass
        
    
    


class LlamaAgent(Agent):
    def __init__(self, config: dict):
       self.device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
       self.model_name = config['model_name']
       self.temperature = config.get('temperature', 0.0)
       self.max_tokens = config.get('max_completion_tokens', 0.0)
       
       self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
       self.model = AutoModelForCausalLM.from_pretrained(
           self.model_name,
           torch_dtype=torch.float32
       ).to(self.device)
    
    def generate_response(self, prompt):
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        with torch.no_grad():
            output = self.model.generate(
                **inputs,
                max_new_tokens=self.max_tokens,
                temperature=self.temperature,
            )
        return self.tokenizer.decode(output[0], skip_special_tokens=True)
    