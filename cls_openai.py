"""
clsOpenAI.py
OpenAI Agent class for multi-agent chat system.
Compatible with Helper.py command-line interface architecture.

By Juan B. Gutiérrez, Professor of Mathematics 
University of Texas at San Antonio.

License: Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
"""

import os
import openai
import json
import sys
from datetime import datetime
from PyQt5.QtCore import QThread, pyqtSignal
from cls_blockchain import IntegrityManager


class OpenAIWorker(QThread):
    """Worker thread for OpenAI API calls to prevent GUI blocking"""
    result_ready = pyqtSignal(str)

    def __init__(self, user_input, client, assistant, thread, agent):
        super().__init__()
        self.user_input = user_input
        self.client = client
        self.assistant = assistant
        self.thread = thread
        self.agent = agent  # Reference to the agent for busy state

    def run(self):
        # Check if agent is busy
        if self.agent.is_busy:
            self.result_ready.emit(f"Agent {self.agent.name} is busy processing a previous request. Please wait.")
            return
        
        try:
            self.agent.is_busy = True  # Mark as busy
            
            self.client.beta.threads.messages.create(
                thread_id=self.thread.id,
                role="user",
                content=self.user_input
            )
            run = self.client.beta.threads.runs.create(
                thread_id=self.thread.id,
                assistant_id=self.assistant.id
            )
            while run.status in ["queued", "in_progress"]:
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=self.thread.id,
                    run_id=run.id
                )
            if run.status == "completed":
                messages = self.client.beta.threads.messages.list(thread_id=self.thread.id)
                for message in messages.data:
                    if message.role == "assistant":
                        self.result_ready.emit(message.content[0].text.value)
                        return
            self.result_ready.emit("Error: No response from assistant.")
        except Exception as e:
            self.result_ready.emit(f"Error: {e}")
        finally:
            self.agent.is_busy = False  # Always clear busy flag


class OpenAIAgent:
    """OpenAI Agent class compatible with Helper.py architecture"""
    
    def __init__(self, model, name, instructions, user, config):
        self.model = model
        self.name = name
        self.user = user
        self.config = config
        self.latest_response = ""
        self.active = True
        self.is_busy = False  # Track if agent is currently processing
        self.integrity_issues = []
        self.integrity_valid = True        

        # Build instructions with preamble (compatible with Helper.py style)
        preamble = f"Please address the user as Dr. {user}.\n\n Introduce yourself as {name}, AI assistant.\n\n "
        self.instructions = preamble + instructions
        
        # Initialize OpenAI client and create assistant/thread
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            raise ValueError("API key is not set. Please set the OPENAI_API_KEY environment variable.")
        
        self.client = openai.OpenAI()
        self.assistant = self.client.beta.assistants.create(
            model=model,
            instructions=self.instructions,
            name=name,
            tools=[{"type": "file_search"}]
        )
        self.thread = self.client.beta.threads.create()
        
        # Set up history file path using CWD from config
        cwd = config.get("CWD", "/chats")
        if cwd.startswith("/"):
            cwd_path = cwd[1:]  # Remove leading slash for relative path
        else:
            cwd_path = cwd
            
        self.history_file = os.path.join(cwd_path, f"{self.name}.json")
        print(f"OpenAI Agent {self.name} will use history file: {self.history_file}")
        
        # Ensure the directory exists
        os.makedirs(cwd_path, exist_ok=True)
        
        # History tracking
        self.history_data = {"history": [], "seeded": True, "chat_id": None}
        
        # Load latest conversation
        self.load_latest_conversation()

    def upload_file(self, file_path):
        """
        Upload a file to OpenAI (compatible with Helper.py file upload)
        Returns the file ID if successful; otherwise returns None.
        """
        try:
            with open(file_path, 'rb') as file_data:
                file_object = self.client.files.create(
                    file=file_data,
                    purpose='assistants'
                )
            print(f"File uploaded successfully: ID {file_object.id}")
            
            # Attach file to conversation thread
            self.client.beta.threads.messages.create(
                thread_id=self.thread.id,
                role="user",
                content="File uploaded for analysis.",
                attachments=[{"file_id": file_object.id, "tools": [{"type": "file_search"}]}]
            )
            return file_object.id
        except Exception as e:
            print(f"Failed to upload file: {e}")
            return None

    def send_message(self, message):
        """
        Send a message to the OpenAI assistant.
        Returns the response or error message.
        Note: The orchestrator handles ALL blockchain integrity.
        This method should NOT add anything to history.
        """
        # Check if agent is busy
        if self.is_busy:
            return f"Agent {self.name} is busy processing a previous request. Please wait."
        
        try:
            self.is_busy = True  # Mark as busy
            
            # Send message to OpenAI (don't add to history_data)
            self.client.beta.threads.messages.create(
                thread_id=self.thread.id,
                role="user",
                content=message
            )
            
            # Create and wait for run completion
            run = self.client.beta.threads.runs.create(
                thread_id=self.thread.id,
                assistant_id=self.assistant.id
            )
            
            while run.status in ["queued", "in_progress"]:
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=self.thread.id,
                    run_id=run.id
                )
            
            if run.status == "completed":
                messages = self.client.beta.threads.messages.list(thread_id=self.thread.id)
                for msg in messages.data:
                    if msg.role == "assistant":
                        response = msg.content[0].text.value
                        
                        # DO NOT add to history_data here - orchestrator handles this
                        # Just update latest_response for copy functionality
                        self.latest_response = response
                        return response
            
            return "Error: No response from assistant."
            
        except Exception as e:
            return f"Error: {e}"
        finally:
            self.is_busy = False  # Always clear busy flag
        
    def create_worker(self, user_input):
        """Create a worker thread for GUI use"""
        return OpenAIWorker(user_input, self.client, self.assistant, self.thread, self)

    def load_latest_conversation(self):
        """Load the latest conversation if it exists"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    saved_data = json.load(f)
                
                if isinstance(saved_data, dict) and 'history' in saved_data:
                    history = saved_data.get('history', [])
                    if len(history) > 0:
                        print(f"Loading latest conversation for {self.name}")
                        self.restore_conversation_from_history(saved_data)
                        return True
            except Exception as e:
                print(f"Error loading latest conversation for {self.name}: {e}")
        return False

    def restore_conversation_from_history(self, saved_data):
        """Restore conversation from saved history data"""
        history = saved_data.get('history', [])
        chat_id = saved_data.get('chat_id', None)
        seeded = saved_data.get('seeded', False)
        
        # Update history data
        self.history_data = {
            "history": history,
            "seeded": seeded,
            "chat_id": chat_id,
            "openai_thread_id": self.thread.id
        }
        
        # Process history entries to add missing timestamps and fix thread ID
        current_time = datetime.now().isoformat()
        updated_history = []
        
        for entry in history:
            if isinstance(entry, dict) and 'role' in entry and 'content' in entry:
                # Add timestamp if missing
                if 'timestamp' not in entry or not entry['timestamp']:
                    entry['timestamp'] = current_time
                    print(f"Added missing timestamp to {entry['role']} message for {self.name}")
                
                updated_history.append(entry)
        
        # Update the history with fixed entries
        self.history_data["history"] = updated_history
        
        # Assign current thread ID if missing or different
        if not chat_id or chat_id != self.thread.id:
            self.history_data["chat_id"] = self.thread.id
            print(f"Updated thread ID for {self.name}: {self.thread.id}")
        
        # Send conversation context to OpenAI if there's previous history
        if len(updated_history) > 0:
            context_message = "We will continue the following conversation we started earlier:\n\n"
            for entry in updated_history:
                role = entry.get('role', 'unknown')
                content = entry.get('content', '')
                timestamp = entry.get('timestamp', '')
                
                if role == 'user':
                    context_message += f"User ({timestamp}): {content}\n"
                elif role == 'assistant':
                    context_message += f"Assistant ({timestamp}): {content}\n"
            
            context_message += "\nPlease continue from where we left off."
            
            # Send context as first message in new thread
            try:
                self.client.beta.threads.messages.create(
                    thread_id=self.thread.id,
                    role="user",
                    content=context_message
                )
                run = self.client.beta.threads.runs.create(
                    thread_id=self.thread.id,
                    assistant_id=self.assistant.id
                )
                # Note: We don't wait for this response as it's just context setting
            except Exception as e:
                print(f"Error sending context to OpenAI for {self.name}: {e}")
        
        # Save the updated history with timestamps and thread ID
        self.save_conversation()

    def save_conversation(self):
        """Save the current conversation to file"""
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to write chat log for {self.name}: {e}")

    def reset_conversation(self):
        """Reset the conversation and create a new thread"""
        try:
            self.is_busy = True  # Mark as busy during reset
            self.thread = self.client.beta.threads.create()
            self.history_data = {"history": [], "seeded": True, "chat_id": None}
            self.latest_response = ""
            self.save_conversation()
            print(f"Conversation reset for {self.name}")
        except Exception as e:
            print(f"Error resetting conversation for {self.name}: {e}")
        finally:
            self.is_busy = False  # Clear busy flag

    def get_info(self):
        """Get agent information (compatible with Helper.py info display)"""
        return {
            "name": self.name,
            "model": self.model,
            "assistant_id": self.assistant.id,
            "thread_id": self.thread.id,
            "active": self.active
        }

    def get_integrity_display_text(self):
        """Get text to display integrity issues in GUI"""
        if not hasattr(self, 'integrity_valid') or self.integrity_valid:
            return ""
        
        if hasattr(self, 'integrity_issues') and self.integrity_issues:
            warning_text = "⚠️ LOG TAMPERED. TRUST HAS BEEN BREACHED. BLOCKCHAIN FAILS\n"
            warning_text += "Integrity Issues:\n"
            for issue in self.integrity_issues:
                warning_text += f"- {issue}\n"
            return warning_text
        
        return "⚠️ INTEGRITY STATUS UNKNOWN"
