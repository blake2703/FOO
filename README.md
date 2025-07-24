## FOO: The Flaws of Others 

### Overview

FOO is an algorithm that minimizes false information in ensembles of Large Laguage Models (LLMs) agents.  See  the manuscript *A Mathematical Theory of Discursive Networks*    [arXiv: 2507.06565](https://arxiv.org/abs/2507.06565) DOI: [10.48550/arXiv.2507.06565](https://doi.org/10.48550/arXiv.2507.06565)

The step-by-step tutorial to install the tools needed to execute the code in this repository is: [FOO_EnvSetup.pdf](FOO_EnvSetup.pdf)

The easiest entry point is to run the program [foo_gui.py](foo_gui.py)

This repository provides a comprehensive Python framework for multi-agent AI interactions, supporting both OpenAI GPT and Anthropic Claude models. The system features a modular architecture with command-line interfaces, advanced GUI applications, and sophisticated multi-agent orchestration capabilities. All scripts use standard environment variable credentials and support conversational workflows, document processing, vulnerability analysis, and collaborative agent consensus mechanisms.

### Git Protocol

After you make your changes:

```bash
git pull
git add .
git commit -m "[description of the change]"
git push
```

To set up Git credentials:

```bash
git config --global user.email "you@example.com"
git config --global user.name "Your Name"
```

To undo a staged change:

```bash
git reset
```

To discard local changes and sync with the remote:

```bash
git reset --hard HEAD
git push --force
```

### Prerequisites

* Python 3.x
* PyQt5 for GUI applications: `pip install PyQt5`
* An OpenAI API key loaded via environment variable `OPENAI_API_KEY`
* An Anthropic API key loaded via environment variable `ANTHROPIC_API_KEY`
* (Optional) PyPDF2 for PDF processing: `pip install PyPDF2`
* (Optional) NLTK tokenizers: `python -c "import nltk; nltk.download('punkt')"`

### Installation

Clone the repository and run any of the scripts directly.

```bash
git clone https://github.com/biomathematicus/FOO.git
cd FOO
python FOOGUI.py
```

### Core System Architecture

The system is built around a modular architecture with specialized components:

#### Multi-Agent Core Files

* **`cls_openai.py`**: OpenAI agent class with thread management, conversation persistence, file upload support, and busy state tracking to prevent API conflicts.

* **`cls_anthropic.py`**: Anthropic Claude agent class with dual history management (clean for API, timestamped for display), PDF processing, and automatic metadata repair.

* **`cls_foo.py`**: Multi-agent orchestrator that manages message distribution, vulnerability analysis, judgment workflows, and reflection processes across multiple AI agents.

* **`FOOGUI.py`**: Advanced multi-agent GUI interface with asynchronous operations, dynamic configuration loading, project-specific settings, and comprehensive workflow management.

#### Single Agent Applications

* **`agentGPT.py`** (formerly `Helper.py`): Command-line interface for single OpenAI GPT interactions with file upload support and persistent threaded conversations.

* **`agentGPTGUI.py`** (formerly `HelperGUI.py`): PyQt5 GUI for single OpenAI agent interactions with drag-and-drop file support and clipboard integration.

* **`agentClaude.py`** (formerly `ClaudeChat.py`): Basic terminal interface for Anthropic Claude with multi-agent support and conversation history.

* **`ClaudeGUI.py`**: Standalone GUI for Claude interactions with PDF drag-and-drop processing.

#### Legacy and Utility Files

* **`ClaudeChatUL.py`**: Extended Claude terminal interface with PDF upload capabilities.

* **`ClaudeQA.py`**: Minimal single-query Claude testing tool.

* **`agentGroq.py`**: CLI tool using LangChain and Groq's LLaMA API with memory buffers.

* **`generateSummaries.py`**: Batch PDF processing with TextRank summarization.

* **`editJSON.py`**: Interactive JSON tree editor for configuration management.

### Configuration System

* **`config.json`**: Master configuration file defining models, instructions, user settings, font sizes, and Current Working Directory (CWD) for project-specific configurations.

The system supports dynamic configuration loading:
- **Master Config**: Central configuration template
- **Project Configs**: Folder-specific configurations loaded based on CWD setting
- **Dynamic CWD**: Automatically updates based on Load operations

### Advanced Features

#### Multi-Agent Workflows

1. **Vulnerability Analysis**: Agents analyze each other's responses for flaws and weaknesses
2. **Judgment Synthesis**: Harmonizer agents organize findings into structured assessments
3. **Reflection Process**: Original agents refine responses based on peer feedback
4. **Conversation Persistence**: Full conversation history with timestamps and metadata
5. **Asynchronous Operations**: Non-blocking GUI with real-time progress indicators

#### Project Management

- **Dynamic CWD**: Each project can have its own configuration and conversation files
- **Reset with Warning**: Complete reset functionality with file deletion confirmation
- **Load Operations**: Automatically updates working directory and loads project files
- **Missing Metadata Repair**: Automatically fixes incomplete conversation files

#### Interface Features

- **Gear Icon Status**: Visual indicators showing which agents are actively working
- **Broadcast Messaging**: Send messages to all active agents simultaneously
- **Harmonizer Roles**: Specialized agents for conflict resolution and consensus building
- **File Upload Support**: Drag-and-drop for PDFs (Claude) and general files (OpenAI)
- **Thread Safety**: Proper worker thread management prevents GUI freezing

### Usage Examples

#### Multi-Agent Consensus Building

```bash
python FOOGUI.py
```

1. **Configure agents** in `config.json` with different models and roles
2. **Broadcast question** to all agents for initial responses
3. **Use Vulnerability** button to find flaws in responses
4. **Apply Judgment** to synthesize findings via harmonizer agents
5. **Request Reflection** for improved responses based on consensus

#### Single Agent Interactions

```bash
# Command line OpenAI
python agentGPT.py

# GUI OpenAI with file support
python agentGPTGUI.py

# Command line Claude
python agentClaude.py

# GUI Claude with PDF processing
python ClaudeGUI.py
```

#### Configuration Management

```bash
# Edit configurations
python editJSON.py

# Process multiple PDFs
python generateSummaries.py
```

### File Organization

```
FOO/
├── cls_openai.py          # OpenAI agent class
├── cls_anthropic.py       # Claude agent class  
├── cls_foo.py             # Multi-agent orchestrator
├── FOOGUI.py              # Advanced multi-agent GUI
├── agentGPT.py            # Single OpenAI CLI
├── agentGPTGUI.py         # Single OpenAI GUI
├── agentClaude.py         # Single Claude CLI
├── ClaudeGUI.py           # Single Claude GUI
├── config.json            # Master configuration
├── chats/                 # Default conversation storage
└── [project-folders]/     # Project-specific configs and chats
```

### Conversation Management

- **Automatic Persistence**: All conversations saved with timestamps
- **Project Isolation**: Each CWD maintains separate conversation files
- **Metadata Repair**: Missing timestamps and IDs automatically assigned
- **History Display**: Complete conversation restoration on startup
- **Thread Safety**: OpenAI busy state tracking prevents API conflicts

### Advanced Configuration

The `config.json` supports:

```json
{
  "CONFIG": {
    "user": "Your Name",
    "instructions": "Custom agent instructions",
    "fontsize": 12,
    "CWD": "/project-folder"
  },
  "MODELS": [
    {
      "model_code": "gpt-4",
      "agent_name": "Analyst",
      "harmonizer": false
    },
    {
      "model_code": "claude-3-opus-20240229",
      "agent_name": "Synthesizer", 
      "harmonizer": true
    }
  ]
}
```

### License

This project is open-sourced under CC-BY-SA 4.0 International.

### Contact

For queries or suggestions, contact biomathematicus or raise an issue in the repository.
