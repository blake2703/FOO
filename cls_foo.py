"""
cls_foo.py
Multi-Agent Orchestration class for distributing messages and managing agent interactions.
Handles vulnerability analysis, judgment, and reflection workflows.

By Juan B. Gutiérrez, Professor of Mathematics 
University of Texas at San Antonio.

License: Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
"""

import os
import json
import sys
from datetime import datetime
from cls_openai import OpenAIAgent
from cls_anthropic import AnthropicAgent


class MultiAgentOrchestrator:
    """
    Orchestrates multiple AI agents (OpenAI and Anthropic) for collaborative analysis.
    Manages message distribution, vulnerability analysis, judgment, and reflection workflows.
    """
    
    def __init__(self, config_file="config.json"):
        """Initialize the multi-agent system from configuration file"""
        self.agents = []
        self.active_agents_working = 0
        self.config_file = config_file
        
        # Load configuration
        try:
            with open(config_file, "r") as f:
                config_data = json.load(f)
        except FileNotFoundError:
            print(f"Config file {config_file} not found, trying default config.json")
            with open("config.json", "r") as f:
                config_data = json.load(f)
        
        self.config = config_data["CONFIG"]
        self.models = config_data["MODELS"]
        self.user = self.config["user"]
        
        # Initialize agents based on configuration
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize all agents from configuration"""
        for entry in self.models:
            model_code = entry["model_code"]
            agent_name = entry["agent_name"]
            harmonizer = bool(entry.get("harmonizer", False)) if isinstance(entry.get("harmonizer", False), bool) else str(entry.get("harmonizer", "false")).lower() == "true"
            
            try:
                if model_code.startswith("claude"):
                    # Create Anthropic agent
                    agent = AnthropicAgent(
                        model=model_code,
                        name=agent_name,
                        instructions=self.config["instructions"],
                        user=self.user,
                        config=self.config
                    )
                else:
                    # Create OpenAI agent
                    agent = OpenAIAgent(
                        model=model_code,
                        name=agent_name,
                        instructions=self.config["instructions"],
                        user=self.user,
                        config=self.config
                    )
                
                # Add harmonizer flag
                agent.harmonizer = harmonizer
                self.agents.append(agent)
                print(f"Initialized agent: {agent_name} ({model_code})")
                
            except Exception as e:
                print(f"Failed to initialize agent {agent_name}: {e}")
    
    def get_active_agents(self):
        """Get list of active agents"""
        return [agent for agent in self.agents if agent.active]
    
    def get_harmonizer_agents(self):
        """Get list of active harmonizer agents"""
        return [agent for agent in self.agents if agent.active and getattr(agent, 'harmonizer', False)]
    
    def get_non_harmonizer_agents(self):
        """Get list of active non-harmonizer agents"""
        return [agent for agent in self.agents if agent.active and not getattr(agent, 'harmonizer', False)]
    
    def broadcast_message(self, message):
        """
        Broadcast a message to all active agents.
        Returns a dictionary with agent names as keys and responses as values.
        """
        responses = {}
        active_agents = self.get_active_agents()
        
        print(f"Broadcasting message to {len(active_agents)} active agents: '{message}'")
        
        for agent in active_agents:
            try:
                response = agent.send_message(message)
                responses[agent.name] = response
                print(f"Response from {agent.name}: {response[:100]}..." if len(response) > 100 else f"Response from {agent.name}: {response}")
            except Exception as e:
                error_msg = f"Error: {e}"
                responses[agent.name] = error_msg
                print(f"Error from {agent.name}: {error_msg}")
        
        return responses
    
    def send_vulnerability_analysis(self, source_agent_name):
        """
        Send vulnerability analysis request to other agents about source agent's latest response.
        Compatible with the "Vulnerability" button functionality.
        """
        source_agent = None
        for agent in self.agents:
            if agent.name == source_agent_name:
                source_agent = agent
                break
        
        if not source_agent or not source_agent.latest_response:
            print(f"No response found for agent {source_agent_name}")
            return {}
        
        message = f"Agent {source_agent_name} answered the same question as follows, find flaws: {source_agent.latest_response}"
        
        # Send to all other active agents
        responses = {}
        for agent in self.get_active_agents():
            if agent.name != source_agent_name:
                try:
                    response = agent.send_message(message)
                    responses[agent.name] = response
                except Exception as e:
                    responses[agent.name] = f"Error: {e}"
        
        return responses
    
    def send_judgment_analysis(self, source_agent_name):
        """
        Send judgment analysis to harmonizer agents.
        Collects responses from non-harmonizer agents and sends organized analysis to harmonizers.
        """
        # Collect responses from non-harmonizer agents
        summary_map = {}
        for agent in self.get_non_harmonizer_agents():
            if agent.latest_response:
                summary_map[agent.name] = agent.latest_response
        
        if not summary_map:
            print("No responses found from non-harmonizer agents")
            return {}
        
        # Send to harmonizer agents
        responses = {}
        for agent in self.get_harmonizer_agents():
            composite = []
            for agent_name, response in summary_map.items():
                composite.append(f"\n \n Agent {agent_name}: {response}")
            composite_text = "".join(composite)
            
            message = (
                f"The following statements are the flaws others found for agent {source_agent_name}'s response."
                f" Organize their responses by topic in an additive manner (that is, do not eliminate information)."
                f" Structure your response using the following sections: 'Agreement', 'Disagreement', and 'Unique observations'."
                f" In 'Agreement', list ideas supported by multiple agents. In 'Disagreement', note contradictory statements."
                f" In 'Unique observations', highlight observations made by only one agent."
                f" The agent under review needs detailed responses to be able to improve. Produce the content for these sections with detailed bulletpoints. \n \n {composite_text}"
            )
            
            try:
                response = agent.send_message(message)
                responses[agent.name] = response
            except Exception as e:
                responses[agent.name] = f"Error: {e}"
        
        return responses
    
    def send_reflection_analysis(self, target_agent_name):
        """
        Send reflection analysis to target agent based on harmonizer feedback.
        """
        target_agent = None
        for agent in self.agents:
            if agent.name == target_agent_name:
                target_agent = agent
                break
        
        if not target_agent:
            print(f"Target agent {target_agent_name} not found")
            return None
        
        # Collect reflections from harmonizer agents
        reflections = []
        for agent in self.get_harmonizer_agents():
            if agent.latest_response and agent.latest_response.strip():
                reflections.append(agent.latest_response.strip())
        
        if not reflections:
            print("No reflections found from harmonizer agents")
            return None
        
        composite = "---".join(reflections)
        message = (
            "Judgment of your response has resulted in the observations that follow. "
            "Regenerate your version of the text under review taking into account the consensus of these observations. If you object to an observation, explain why. \n \n " + composite
        )
        
        try:
            response = target_agent.send_message(message)
            return response
        except Exception as e:
            return f"Error: {e}"
    
    def reset_all_agents(self):
        """Reset all agents and ask them to introduce themselves"""
        print("Resetting all agents...")
        responses = {}
        
        for agent in self.agents:
            try:
                agent.reset_conversation()
                response = agent.send_message("Introduce yourself.")
                responses[agent.name] = response
            except Exception as e:
                responses[agent.name] = f"Error resetting: {e}"
        
        print("All agents reset and asked to introduce themselves")
        return responses
    
    def load_agent_files(self, folder_path):
        """
        Load JSON files for each agent from a folder.
        Compatible with the Load button functionality.
        """
        if not os.path.exists(folder_path):
            print(f"Folder not found: {folder_path}")
            return {}
        
        print(f"Loading agent JSON files from: {folder_path}")
        
        results = {}
        for agent in self.agents:
            agent_name = agent.name
            
            # Try different JSON file naming patterns
            possible_files = [
                f"{agent_name}.json",
                f"{agent_name.lower()}.json",
                f"{agent_name.replace(' ', '_')}.json",
                f"{agent_name.replace(' ', '-')}.json"
            ]
            
            file_loaded = False
            for filename in possible_files:
                file_path = os.path.join(folder_path, filename)
                
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            json_data = json.load(f)
                        
                        # Check if this is a chat history file
                        if isinstance(json_data, dict) and 'history' in json_data:
                            print(f"Loading chat history from {filename} for agent {agent_name}")
                            
                            # Fix missing timestamps and IDs before restoring
                            json_data = self._fix_missing_metadata(json_data, agent)
                            
                            agent.restore_conversation_from_history(json_data)
                            results[agent_name] = f"Chat history loaded from {filename}"
                            file_loaded = True
                            break
                        else:
                            # Try to extract content for non-history JSON
                            content = self._extract_content_from_json(json_data)
                            if content and str(content).strip():
                                print(f"Loading JSON content from {filename} for agent {agent_name}")
                                response = agent.send_message(str(content).strip())
                                results[agent_name] = f"Content loaded and processed from {filename}"
                                file_loaded = True
                                break
                                
                    except json.JSONDecodeError as e:
                        results[agent_name] = f"Invalid JSON in {filename}: {e}"
                        print(f"Invalid JSON in file {file_path}: {e}")
                    except Exception as e:
                        results[agent_name] = f"Error loading {filename}: {e}"
                        print(f"Error reading file {file_path}: {e}")
            
            if not file_loaded:
                results[agent_name] = f"No JSON file found. Searched: {', '.join(possible_files)}"
                print(f"No JSON file found for agent {agent_name}")
        
        print("Finished loading agent JSON files")
        return results
    
    def _fix_missing_metadata(self, json_data, agent):
        """Fix missing timestamps and chat IDs in loaded JSON data"""
        current_time = datetime.now().isoformat()
        
        # Fix missing timestamps in history
        history = json_data.get('history', [])
        updated_history = []
        
        for entry in history:
            if isinstance(entry, dict) and 'role' in entry and 'content' in entry:
                # Add timestamp if missing
                if 'timestamp' not in entry or not entry['timestamp']:
                    entry['timestamp'] = current_time
                    print(f"Added missing timestamp to {entry['role']} message in loaded file for {agent.name}")
                
                updated_history.append(entry)
        
        json_data['history'] = updated_history
        
        # Fix missing chat ID
        if 'chat_id' not in json_data or not json_data['chat_id']:
            if hasattr(agent, 'thread'):
                # OpenAI agent - use thread ID
                json_data['chat_id'] = agent.thread.id
                print(f"Added missing thread ID to loaded file for {agent.name}: {agent.thread.id}")
            else:
                # Claude agent - generate UUID
                import uuid
                json_data['chat_id'] = str(uuid.uuid4())
                print(f"Generated missing chat ID for loaded file for {agent.name}: {json_data['chat_id']}")
        
        return json_data
    
    def _extract_content_from_json(self, json_data):
        """Extract content from JSON - helper method"""
        content = None
        possible_keys = ['content', 'message', 'text', 'prompt', 'query', 'input']
        
        for key in possible_keys:
            if key in json_data:
                content = json_data[key]
                break
        
        # If no specific key found, try to use the entire JSON as string
        if content is None:
            if isinstance(json_data, str):
                content = json_data
            elif isinstance(json_data, dict):
                # Convert dict to readable format
                content = json.dumps(json_data, indent=2)
            else:
                content = str(json_data)
        
        return content
    
    def get_agent_by_name(self, name):
        """Get agent by name"""
        for agent in self.agents:
            if agent.name == name:
                return agent
        return None
    
    def get_system_status(self):
        """Get status of all agents"""
        status = {
            "total_agents": len(self.agents),
            "active_agents": len(self.get_active_agents()),
            "harmonizer_agents": len(self.get_harmonizer_agents()),
            "non_harmonizer_agents": len(self.get_non_harmonizer_agents()),
            "agents": []
        }
        
        for agent in self.agents:
            agent_info = agent.get_info()
            agent_info["harmonizer"] = getattr(agent, 'harmonizer', False)
            status["agents"].append(agent_info)
        
        return status
    
    def run_command_line_interface(self):
        """
        Run a command-line interface for the multi-agent system.
        Compatible with Helper.py style interaction.
        """
        print("*****************   M U L T I - A G E N T   C H A T   *****************")
        status = self.get_system_status()
        print(f"Initialized {status['total_agents']} agents ({status['active_agents']} active)")
        
        for agent_info in status["agents"]:
            print(f"  - {agent_info['name']}: {agent_info['model']} ({'Harmonizer' if agent_info.get('harmonizer') else 'Standard'})")
        
        print("\nCommands:")
        print("  'exit' - Exit the program")
        print("  'reset' - Reset all agents")
        print("  'status' - Show system status")
        print("  'load <folder>' - Load conversations from folder")
        print("  'file:<path>' - Upload file (OpenAI agents only)")
        print("  'vuln <agent_name>' - Run vulnerability analysis")
        print("  'judge <agent_name>' - Run judgment analysis")
        print("  'reflect <agent_name>' - Run reflection analysis")
        print("  Any other text will be broadcast to all active agents")
        
        while True:
            print("\n>>>>>>>>>>>>>>>>>>>>>>>>>>")
            user_input = input(f"{self.user}: ")
            
            if user_input.lower() == 'exit':
                break
            elif user_input.lower() == 'reset':
                responses = self.reset_all_agents()
                for name, response in responses.items():
                    print(f"\n{name}: {response}")
            elif user_input.lower() == 'status':
                status = self.get_system_status()
                print(f"\nSystem Status:")
                print(f"  Total agents: {status['total_agents']}")
                print(f"  Active agents: {status['active_agents']}")
                print(f"  Harmonizer agents: {status['harmonizer_agents']}")
                for agent_info in status["agents"]:
                    active_status = "Active" if agent_info["active"] else "Inactive"
                    harmonizer_status = " (Harmonizer)" if agent_info.get("harmonizer") else ""
                    print(f"    {agent_info['name']}: {active_status}{harmonizer_status}")
            elif user_input.startswith('load '):
                folder_path = user_input[5:].strip()
                results = self.load_agent_files(folder_path)
                for name, result in results.items():
                    print(f"{name}: {result}")
            elif user_input.startswith('file:'):
                file_path = user_input[5:].strip()
                # Upload to OpenAI agents only
                for agent in self.get_active_agents():
                    if hasattr(agent, 'upload_file'):
                        try:
                            file_id = agent.upload_file(file_path)
                            if file_id:
                                print(f"File uploaded to {agent.name}: {file_id}")
                        except Exception as e:
                            print(f"Error uploading to {agent.name}: {e}")
                    else:
                        print(f"File upload not supported for {agent.name} (Claude agent)")
            elif user_input.startswith('vuln '):
                agent_name = user_input[5:].strip()
                responses = self.send_vulnerability_analysis(agent_name)
                for name, response in responses.items():
                    print(f"\n{name}: {response}")
            elif user_input.startswith('judge '):
                agent_name = user_input[6:].strip()
                responses = self.send_judgment_analysis(agent_name)
                for name, response in responses.items():
                    print(f"\n{name}: {response}")
            elif user_input.startswith('reflect '):
                agent_name = user_input[8:].strip()
                response = self.send_reflection_analysis(agent_name)
                if response:
                    print(f"\n{agent_name}: {response}")
            else:
                # Broadcast message to all active agents
                responses = self.broadcast_message(user_input)
                print("\n<<<<<<<<<<<<<<<<<<<<<<<<<<")
                for name, response in responses.items():
                    print(f"\n{name}: {response}")


# Example usage and testing
if __name__ == "__main__":
    try:
        orchestrator = MultiAgentOrchestrator()
        orchestrator.run_command_line_interface()
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")