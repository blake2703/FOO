## FOO: The Flaws of Others 

### Overview
FOO is an algorithm that minimizes false information in ensembles of Large Laguage Models (LLMs) agents.  See  the manuscript *A Mathematical Theory of Discursive Networks*    [arXiv: 2507.06565](https://arxiv.org/abs/2507.06565) DOI: [10.48550/arXiv.2507.06565](https://doi.org/10.48550/arXiv.2507.06565)

This repository provides a comprehensive Python framework for multi-agent AI interactions, supporting different types of LLMs. The system features a modular architecture with command-line interfaces, advanced GUI applications, and sophisticated multi-agent orchestration capabilities. All scripts use standard environment variable credentials and support conversational workflows, document processing, vulnerability analysis, and collaborative agent consensus mechanisms.

### Core System Architecutre
The FOO system is structured as a modular architecture centered around agent creation, configuration, and behavior orchestration. Below is a breakdown of the main components as depicted in the flow diagram.

1. AgentFactory
    - Responsibility: instantiating new agents

2. Agent
   - Responsibility: abstract class that each agent will inherit from

3. AgentConfig
    - Responsibility: extracts the configuration of each agent

4. AgentError
   - Responsibility: exception class used for handling errors during agent initialization or response generation
  
5. ProviderManager
   - Responsibility: manages different LLM provider settings and selects the appropriate one based on the model

6. ProviderSettings:
   - Responsibility: holds the configuration data needed to interact with a specific LLM provider

7. Provider:
   - Responsibility: defines enumerations for the names of supported LLM providers

8. ProviderError
    - Responsibility: exception raised for invalid or unsupported provider configurations

9. OpenRouterAgent
   - Responsibility: a concrete implementation of an Agent that specifically knows how to talk to OpenRouter’s API

<img width="1372" height="1306" alt="FOO drawio" src="https://github.com/user-attachments/assets/f9470819-3869-4448-9e40-5a5999f6558c" />
