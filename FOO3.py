import os
import sys
import json
import io
import openai
import anthropic
from PyQt5.QtWidgets import (
    QApplication, QWidget, QTextEdit, QLineEdit, QVBoxLayout,
    QPushButton, QTabWidget, QHBoxLayout, QCheckBox, QLabel, QScrollArea,
    QFileDialog
)
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtCore import QEvent, Qt


# Force UTF-8 encoding for stdout and stderr
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


class BroadcastTextEdit(QTextEdit):
    """Custom QTextEdit that reliably handles Enter key for broadcasting"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        
    def keyPressEvent(self, event):
        """Override keyPressEvent for direct Enter key handling"""
        # Handle all possible Enter key variations
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) or event.text() == '\r':
            # Check if Shift is held (for multiline input)
            if event.modifiers() & Qt.ShiftModifier:
                # Shift+Enter: insert newline normally
                super().keyPressEvent(event)
            else:
                # Plain Enter: broadcast message
                text = self.toPlainText().strip()
                if text:
                    if self.parent_widget and hasattr(self.parent_widget, 'broadcast_message_text'):
                        self.parent_widget.broadcast_message_text(text)
                    self.clear()
                # Don't call super() to prevent newline insertion
                return
        
        # For all other keys, use default behavior
        super().keyPressEvent(event)


class AgentTextEdit(QTextEdit):
    """Custom QTextEdit for individual agent inputs"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.agent_tab = parent  # Store reference to the AgentTab
        
    def keyPressEvent(self, event):
        """Handle Enter key for individual agent inputs"""
        # Handle all possible Enter key variations
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) or event.text() == '\r':
            # Check if Shift is held (for multiline input)
            if event.modifiers() & Qt.ShiftModifier:
                # Shift+Enter: insert newline normally
                super().keyPressEvent(event)
            else:
                # Plain Enter: send message
                text = self.toPlainText().strip()
                if text and self.agent_tab:
                    self.setEnabled(False)
                    self.agent_tab.handle_input(text)
                    self.clear()
                return
        
        super().keyPressEvent(event)


class OpenAIWorker(QThread):
    result_ready = pyqtSignal(str)

    def __init__(self, user_input, client, assistant, thread):
        super().__init__()
        self.user_input = user_input
        self.client = client
        self.assistant = assistant
        self.thread = thread

    def run(self):
        try:
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


class ClaudeWorker(QThread):
    result_ready = pyqtSignal(str)

    def __init__(self, user_input, client, model, history):
        super().__init__()
        self.user_input = user_input
        self.client = client
        self.model = model
        self.history = history

    def run(self):
        try:
            self.history.append({"role": "user", "content": self.user_input})
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.99,
                messages=list(self.history)
            )
            content = response.content[0].text
            self.history.append({"role": "assistant", "content": content})
            self.result_ready.emit(content)
        except Exception as e:
            self.result_ready.emit(f"Error: {e}")


class AgentTab(QWidget):
    def __init__(self, model, name, instructions, user, engine, harmonizer, config):
        super().__init__()
        self.user = user
        self.name = name
        self.model = model
        self.engine = engine
        self.harmonizer = harmonizer
        self.config = config
        self.latest_response = ""
        self.active = True  # Controlled by checkbox

        self.text_area = QTextEdit()
        
        # Use custom text edit for agent input
        self.user_input = AgentTextEdit(self)
        self.user_input.setFixedHeight(60)  
        font = self.user_input.font()
        font.setPointSize(self.config.get("fontsize", 10))
        self.user_input.setFont(font)
        
        self.foo_button = QPushButton("Vulnerability")
        self.foo_button.clicked.connect(self.send_foo_message)

        self.copy_button = QPushButton("Copy Latest Answer")

        preamble = f"Please address the user as Dr. {user}.\n\n Introduce yourself as {name}, AI assistant.\n\n "
        if self.engine == "openai":
            self.instructions = preamble + instructions
            self.client = openai.OpenAI()
            self.assistant = self.client.beta.assistants.create(
                model=model,
                instructions=self.instructions,
                name=name,
                tools=[{"type": "file_search"}]
            )
            self.thread = self.client.beta.threads.create()
        else:
            self.instructions = preamble + instructions
            self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            self.history = []
            self.history.append({"role": "user", "content": self.instructions})

        self.history_file = os.path.join("chats", f"{self.name}.json")
        os.makedirs("chats", exist_ok=True)
        if self.engine == "claude":
            self.history_data = {"history": self.history, "seeded": True, "chat_id": None}
        else:
            self.history_data = {"history": [], "seeded": True, "chat_id": None}

        self.init_ui()
        self.handle_input("Introduce yourself.")

    def init_ui(self):
        layout = QVBoxLayout()
        row = QHBoxLayout()
        self.checkbox = QCheckBox(f"Enable {self.name}")
        self.checkbox.setChecked(True)
        self.checkbox.stateChanged.connect(self.toggle_active)
        row.addWidget(self.checkbox)

        self.harmonizer_checkbox = QCheckBox("Harmonizer")
        self.harmonizer_checkbox.setChecked(self.harmonizer)
        row.addWidget(self.harmonizer_checkbox)

        layout.addLayout(row)

        self.text_area.setReadOnly(True)
        layout.addWidget(self.text_area)

        self.user_input.setPlaceholderText("Type your message and press Enter")
        self.user_input.setFont(self.text_area.font())
        layout.addWidget(self.user_input)

        self.copy_button.clicked.connect(self.copy_latest_answer)
        row2 = QHBoxLayout()
        row2.addWidget(self.copy_button)
        row2.addWidget(self.foo_button)
        self.judgement_button = QPushButton("Judgement")
        self.judgement_button.clicked.connect(self.send_judgement_message)
        self.reflection_button = QPushButton("Reflection")
        self.reflection_button.clicked.connect(self.send_reflection_message)
        row2.addWidget(self.judgement_button)
        row2.addWidget(self.reflection_button)
        layout.addLayout(row2)

        self.setLayout(layout)

    def toggle_active(self, state):
        self.active = bool(state)

    def mark_tab_pending(self):
        parent = self.parent()
        while parent and not isinstance(parent, MultiAgentChat):
            parent = parent.parent()
        if parent:
            index = parent.tabs.indexOf(self)
            if index != -1:
                current_name = parent.tabs.tabText(index)
                if not current_name.startswith("⚙"):
                    parent.tabs.setTabText(index, f"⚙ {self.name}")

    def clear_tab_pending(self):
        parent = self.parent()
        while parent and not isinstance(parent, MultiAgentChat):
            parent = parent.parent()
        if parent:
            index = parent.tabs.indexOf(self)
            if index != -1:
                parent.tabs.setTabText(index, self.name)

    def handle_input(self, text):
        self.mark_tab_pending()
        # Save user entry only for OpenAI; Claude tracks internally
        if self.engine == "openai":
            self.history_data["history"].append({"role": "user", "content": text})
        if not self.active:
            return

        self.text_area.append(f"{self.user}: {text}")
        self.text_area.append(">>>>>>>>>>>>>>>>>>>>>>>>>>")

        if self.engine == "openai":
            self.worker = OpenAIWorker(text, self.client, self.assistant, self.thread)
        else:
            self.worker = ClaudeWorker(text, self.client, self.model, self.history)

        self.worker.result_ready.connect(self.show_response)
        self.worker.start()

    def show_response(self, response):
        # Save chat log entry only for OpenAI; Claude uses updated internal history
        if self.engine == "openai":
            self.history_data["history"].append({"role": "assistant", "content": response})
            # Update OpenAI chat ID with thread ID
            self.history_data["chat_id"] = self.thread.id
        else:
            self.history_data["history"] = self.history
            # For Claude, we could generate a unique chat ID if one doesn't exist
            if not self.history_data.get("chat_id"):
                import uuid
                self.history_data["chat_id"] = str(uuid.uuid4())
        
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to write chat log: {e}")

        self.latest_response = response
        self.text_area.append(f"{self.name}: {response}")
        self.text_area.append("<<<<<<<<<<<<<<<<<<<<<<<<<<")
        self.clear_tab_pending()
        self.user_input.setEnabled(True)
        
        # Notify parent that this agent finished (for broadcast re-enabling)
        self.notify_parent_agent_finished()

    def send_foo_message(self):
        message = f"Agent {self.name} answered the same question as follows, find flaws: {self.latest_response}"
        parent = self.parent()
        while parent and not isinstance(parent, MultiAgentChat):
            parent = parent.parent()
        if parent:
            for tab in parent.agent_tabs:
                if tab != self and tab.active:
                    tab.handle_input(message)

    def send_judgement_message(self):
        parent = self.parent()
        while parent and not isinstance(parent, MultiAgentChat):
            parent = parent.parent()
        if not parent:
            return

        summary_map = {}
        for tab in parent.agent_tabs:
            if not tab.harmonizer and tab.active:
                summary_map[tab.name] = tab.latest_response

        if not summary_map:
            return

        for tab in parent.agent_tabs:
            if tab.harmonizer and tab.active:
                composite = []
                for agent_name, response in summary_map.items():
                    composite.append(f"\n \n Agent {agent_name}: {response}")
                composite_text = "".join(composite)
                message = (
                    f"The following statements are the flaws others found for agent {self.name}'s response."
                    f" Organize their responses by topic in an additive manner (that is, do not eliminate information)."
                    f" Structure your response using the following sections: 'Agreement', 'Disagreement', and 'Unique observations'."
                    f" In 'Agreement', list ideas supported by multiple agents. In 'Disagreement', note contradictory statements."
                    f" In 'Unique observations', highlight observations made by only one agent."
                    f" The agent under review needs detailed responses to be able to improve. Produce the content for these secitons with detailed bulletpoints. \n \n {composite_text}"
                )
                tab.handle_input(message)

    def send_reflection_message(self):
        parent = self.parent()
        while parent and not isinstance(parent, MultiAgentChat):
            parent = parent.parent()
        if not parent:
            return

        reflections = []
        for tab in parent.agent_tabs:
            if tab.harmonizer and tab.active and tab.latest_response.strip():
                reflections.append(tab.latest_response.strip())

        if not reflections:
            return

        composite = "---".join(reflections)
        message = (
            "Judgement of your response has resulted in the observations that follow. "
            "Regenerate your version of thet text under review taking into account the consensus of these observations. If you object to an observation, explain why. \n \n " + composite
        )
        self.handle_input(message)

    def copy_latest_answer(self):
        QApplication.clipboard().setText(self.latest_response)
        self.text_area.append("Latest answer copied to clipboard.")

    def notify_parent_agent_finished(self):
        """Notify the parent MultiAgentChat that this agent finished"""
        parent = self.parent()
        while parent and not isinstance(parent, MultiAgentChat):
            parent = parent.parent()
        if parent and hasattr(parent, 'agent_finished'):
            parent.agent_finished()


class MultiAgentChat(QWidget):
    def __init__(self):
        super().__init__()
        with open("config.json", "r") as f:
            config_data = json.load(f)
        config = config_data["CONFIG"]
        models = config_data["MODELS"]

        self.user = config["user"]
        self.fontsize = int(config.get("fontsize", 10))
        self.active_agents_working = 0  # Track working agents for broadcast disable

        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            print("API key is not set. Please set the OPENAI_API_KEY environment variable.")
            exit(1)

        if not os.getenv("ANTHROPIC_API_KEY"):
            print("Warning: ANTHROPIC_API_KEY not set. Claude agents will not function.")

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"QTabBar::tab {{ font-size: {self.fontsize}pt; min-width: {self.fontsize * 10}px; padding: 6px; }}")
        self.agent_tabs = []

        # Create broadcast text edit first to avoid AttributeError
        self.user_input = BroadcastTextEdit(self)

        for entry in models:
            model_code = entry["model_code"]
            harmonizer = bool(entry.get("harmonizer", False)) if isinstance(entry.get("harmonizer", False), bool) else str(entry.get("harmonizer", "false")).lower() == "true"
            engine = "claude" if model_code.startswith("claude") else "openai"
            tab = AgentTab(
                model=model_code,
                name=entry["agent_name"],
                instructions=config["instructions"],
                user=self.user,
                engine=engine,
                harmonizer=harmonizer,
                config=config)
            self.tabs.addTab(tab, f"⚙ {entry['agent_name']}")
            self.agent_tabs.append(tab)
            font = tab.text_area.font()
            font.setPointSize(self.fontsize)
            tab.text_area.setFont(font)
            tab.user_input.setFont(font)
            tab.copy_button.setFont(font)
            tab.foo_button.setFont(font)
            tab.judgement_button.setFont(font)
            tab.reflection_button.setFont(font)
            tab.checkbox.setFont(font)
            tab.harmonizer_checkbox.setFont(font)

        # Connect the signal after all widgets are created
        self.tabs.currentChanged.connect(self.focus_current_input)
        # Configure the broadcast text edit after creation
        self.user_input.setPlaceholderText("Broadcast message to all active agents (Enter to send, Shift+Enter for newline)")
        self.user_input.setFixedHeight(60)  
        self.user_input.setFocusPolicy(Qt.StrongFocus)
        font = self.user_input.font()
        font.setPointSize(self.fontsize)
        self.user_input.setFont(font)

        # Create Load button
        self.load_button = QPushButton("Load")
        self.load_button.clicked.connect(self.load_agent_files)
        font = self.load_button.font()
        font.setPointSize(self.fontsize)
        self.load_button.setFont(font)

        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        label = QLabel("Message to All Active Agents:")
        font = label.font()
        font.setPointSize(self.fontsize)
        label.setFont(font)
        layout.addWidget(label)
        
        # Create bottom row with Load button and broadcast field
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.load_button)
        bottom_layout.addWidget(self.user_input, 1)  # Give user_input more space
        layout.addLayout(bottom_layout)
        self.setLayout(layout)

        self.setWindowTitle("The Flaws of Others - Multi-agent Consensus")
        self.resize(700, 500)
        
        # Ensure broadcast field gets focus on startup
        self.user_input.setFocus()

    def broadcast_message_text(self, text):
        """Broadcast message to all active agents"""
        print(f"Broadcasting message: '{text}' to active agents")
        
        # Disable the broadcast input while agents are working
        self.user_input.setEnabled(False)
        
        # Track how many agents are working
        self.active_agents_working = 0
        
        for tab in self.agent_tabs:
            if tab.active:
                self.active_agents_working += 1
                tab.handle_input(text)
        
        print(f"Message sent to {self.active_agents_working} active agents")
        
        # If no agents are active, re-enable immediately
        if self.active_agents_working == 0:
            self.user_input.setEnabled(True)

    def focus_current_input(self, index):
        """Modified focus handling to not interfere with broadcast field"""
        # Check if user_input exists and doesn't have focus before changing focus
        if hasattr(self, 'user_input') and not self.user_input.hasFocus():
            if 0 <= index < len(self.agent_tabs):
                self.agent_tabs[index].user_input.setFocus()

    def showEvent(self, event):
        """Ensure broadcast field gets focus when window is shown"""
        super().showEvent(event)
        self.user_input.setFocus()

    def agent_finished(self):
        """Called when an agent finishes processing - used to re-enable broadcast field"""
        self.active_agents_working -= 1
        print(f"Agent finished. {self.active_agents_working} agents still working.")
        
        # Re-enable broadcast field when all agents are done
        if self.active_agents_working <= 0:
            self.active_agents_working = 0  # Ensure it doesn't go negative
            self.user_input.setEnabled(True)
            print("All agents finished. Broadcast field re-enabled.")

    def load_agent_files(self):
        """Load JSON files for each agent from a selected folder and restore chat history"""
        folder_path = QFileDialog.getExistingDirectory(
            self, 
            "Select folder containing agent JSON files",
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if not folder_path:
            print("No folder selected")
            return
            
        print(f"Loading agent JSON files from: {folder_path}")
        
        # Try to load a JSON file for each agent
        for tab in self.agent_tabs:
            agent_name = tab.name
            
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
                        
                        # Check if this is a chat history file with the expected structure
                        if isinstance(json_data, dict) and 'history' in json_data:
                            print(f"Loading chat history from {filename} for agent {agent_name}")
                            success = self.load_chat_history(tab, json_data, filename)
                            if success:
                                file_loaded = True
                                break
                        else:
                            # Try to extract content as before for non-history JSON
                            content = self.extract_content_from_json(json_data)
                            if content and str(content).strip():
                                print(f"Loading JSON content from {filename} for agent {agent_name}")
                                tab.text_area.append(f"=== LOADING JSON CONTENT: {filename} ===")
                                tab.handle_input(str(content).strip())
                                file_loaded = True
                                break
                            
                    except json.JSONDecodeError as e:
                        print(f"Invalid JSON in file {file_path}: {e}")
                        tab.text_area.append(f"Error: Invalid JSON in {filename}: {e}")
                    except Exception as e:
                        print(f"Error reading file {file_path}: {e}")
                        tab.text_area.append(f"Error loading file {filename}: {e}")
            
            if not file_loaded:
                print(f"No JSON file found for agent {agent_name}")
                tab.text_area.append(f"=== NO JSON FILE FOUND ===")
                tab.text_area.append(f"Searched for: {', '.join(possible_files)}")
        
        print("Finished loading agent JSON files")

    def extract_content_from_json(self, json_data):
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

    def load_chat_history(self, tab, json_data, filename):
        """Load chat history for an agent tab"""
        try:
            history = json_data.get('history', [])
            chat_id = json_data.get('chat_id', None)
            seeded = json_data.get('seeded', False)
            
            # Check if this agent uses Claude (has history attribute)
            if hasattr(tab, 'history') and tab.engine == "claude":
                # For Claude agents, restore the conversation history
                tab.history.clear()  # Clear current history
                
                # Load the history from JSON
                for entry in history:
                    if isinstance(entry, dict) and 'role' in entry and 'content' in entry:
                        tab.history.append(entry)
                
                # Update the history data
                tab.history_data = {
                    "history": tab.history,
                    "seeded": seeded,
                    "chat_id": chat_id
                }
                
                # Display the loaded conversation in the text area
                tab.text_area.append(f"=== LOADING CHAT HISTORY: {filename} ===")
                if chat_id:
                    tab.text_area.append(f"Chat ID: {chat_id}")
                
                # Display the conversation history
                for entry in history:
                    role = entry.get('role', 'unknown')
                    content = entry.get('content', '')
                    
                    if role == 'user':
                        tab.text_area.append(f"{tab.user}: {content}")
                        tab.text_area.append(">>>>>>>>>>>>>>>>>>>>>>>>>>")
                    elif role == 'assistant':
                        tab.text_area.append(f"{tab.name}: {content}")
                        tab.text_area.append("<<<<<<<<<<<<<<<<<<<<<<<<<<")
                
                tab.text_area.append(f"=== CHAT HISTORY LOADED ({len(history)} messages) ===")
                
                # Save the updated history
                try:
                    with open(tab.history_file, "w", encoding="utf-8") as f:
                        json.dump(tab.history_data, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    print(f"Failed to save updated chat history: {e}")
                
                print(f"Successfully loaded {len(history)} messages for agent {tab.name}")
                return True
                
            elif tab.engine == "openai":
                # For OpenAI agents, we can't directly restore thread history
                # but we can update our local history tracking
                tab.text_area.append(f"=== CHAT HISTORY REFERENCE: {filename} ===")
                if chat_id:
                    tab.text_area.append(f"OpenAI Thread ID: {chat_id}")
                tab.text_area.append("Note: OpenAI agents use separate thread management.")
                tab.text_area.append("History loaded for reference but new thread created.")
                
                # Update local history data for tracking
                tab.history_data = {
                    "history": history,
                    "seeded": seeded,
                    "chat_id": chat_id,
                    "openai_thread_id": tab.thread.id  # Store current thread ID
                }
                
                # Display conversation for reference
                for entry in history:
                    role = entry.get('role', 'unknown')
                    content = entry.get('content', '')
                    
                    if role == 'user':
                        tab.text_area.append(f"[Ref] {tab.user}: {content}")
                    elif role == 'assistant':
                        tab.text_area.append(f"[Ref] {tab.name}: {content}")
                
                tab.text_area.append(f"=== REFERENCE HISTORY LOADED ({len(history)} messages) ===")
                return True
                
        except Exception as e:
            tab.text_area.append(f"Error loading chat history from {filename}: {e}")
            print(f"Error loading chat history for {tab.name}: {e}")
            return False
        
        return False

    def reset_agents(self):
        for tab in self.agent_tabs:
            tab.text_area.clear()
            tab.user_input.clear()
            tab.latest_response = ""
            if tab.engine == "claude":
                tab.history.clear()
                tab.history_data = {"history": tab.history, "seeded": True, "chat_id": None}
            else:
                tab.history_data = {"history": [], "seeded": True, "chat_id": None}
            try:
                with open(tab.history_file, "w", encoding="utf-8") as f:
                    json.dump(tab.history_data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"Error resetting history for {tab.name}: {e}")


if __name__ == "__main__":
    app = QApplication([])
    window = MultiAgentChat()
    window.show()
    app.exec_()