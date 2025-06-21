import os
import sys
import json
import io
import openai
import anthropic
from PyQt5.QtWidgets import (
    QApplication, QWidget, QTextEdit, QLineEdit, QVBoxLayout,
    QPushButton, QTabWidget, QHBoxLayout, QCheckBox, QLabel, QScrollArea
)
from PyQt5.QtCore import QThread, pyqtSignal

# Force UTF-8 encoding for stdout and stderr
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

class OpenAIWorker(QThread):
    result_ready = pyqtSignal(str)

    def __init__(self, user_input, client, assistant, thread):
        super().__init__()
        self.user_input = user_input
        self.client = client
        self.assistant = assistant
        self.thread = thread

    def run(self):
        # Always use fresh copy of current history to maintain Claude context
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

import os

class AgentTab(QWidget):
    def __init__(self, model, name, instructions, user, engine, harmonizer):
        super().__init__()
        self.user = user
        self.name = name
        self.model = model
        self.engine = engine
        self.harmonizer = harmonizer
        self.latest_response = ""
        self.active = True  # Controlled by checkbox

        self.text_area = QTextEdit()
        self.user_input = QLineEdit()
        self.foo_button = QPushButton("Vulnerability")
        self.foo_button.clicked.connect(self.send_foo_message)

        self.copy_button = QPushButton("Copy Latest Answer")

        if self.engine == "openai":
            preamble = f"Please address the user as Beloved {user}.\\n\\n Introduce yourself as {name}, robot extraordinaire.\\n\\n "
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
            preamble = f"Please address the user as Beloved {user}. Introduce yourself as {name}, robot extraordinaire."
            self.instructions = preamble + instructions
            self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            self.history = []
            self.history.append({"role": "user", "content": self.instructions})

        self.history_file = os.path.join("chats", f"{self.name}.json")
        os.makedirs("chats", exist_ok=True)
        if self.engine == "claude":
            self.history_data = {"history": self.history, "seeded": True}
        else:
            self.history_data = {"history": [], "seeded": True}

        self.init_ui()

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
        layout.addWidget(self.user_input)

        self.user_input.returnPressed.connect(self.send_input)
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

    def send_input(self):
        text = self.user_input.text().strip()
        if text:
            self.user_input.setEnabled(False)
            self.handle_input(text)
        self.user_input.clear()

    def mark_tab_pending(self):
        parent = self.parent()
        while parent and not isinstance(parent, MultiAgentChat):
            parent = parent.parent()
        if parent:
            index = parent.tabs.indexOf(self)
            if index != -1:
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
        else:
            self.history_data["history"] = self.history
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
                    composite.append(f"Agent {agent_name}: {response}")
                composite_text = "".join(composite)
                message = (
                    f"The following statements are the flaws others found for agent {self.name}'s response."
                    f" Organize their responses by topic in an additive manner (that is, do not eliminate information)."
                    f" Structure your response using the following sections: 'Agreement', 'Disagreement', and 'Unique observations'."
                    f" In 'Agreement', list ideas supported by multiple agents. In 'Disagreement', note contradictory statements."
                    f" In 'Unique observations', highlight observations made by only one agent.{composite_text}"
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
            "Improve your response accordingly. \\n \\n " + composite
        )
        self.handle_input(message)

    def copy_latest_answer(self):
        QApplication.clipboard().setText(self.latest_response)
        self.text_area.append("Latest answer copied to clipboard.")

class MultiAgentChat(QWidget):
    def __init__(self):
        super().__init__()
        with open("config.json", "r") as f:
            config_data = json.load(f)
        config = config_data["CONFIG"]
        models = config_data["MODELS"]

        self.user = config["user"]
        self.fontsize = int(config.get("fontsize", 10))

        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            print("API key is not set. Please set the OPENAI_API_KEY environment variable.")
            exit(1)

        if not os.getenv("ANTHROPIC_API_KEY"):
            print("Warning: ANTHROPIC_API_KEY not set. Claude agents will not function.")

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"QTabBar::tab {{ font-size: {self.fontsize}pt; min-width: {self.fontsize * 10}px; padding: 6px; }}")
        self.tabs.currentChanged.connect(self.focus_current_input)
        self.agent_tabs = []

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
                harmonizer=harmonizer)
            self.tabs.addTab(tab, entry["agent_name"])
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

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Broadcast message to all active agents")
        self.user_input.returnPressed.connect(self.broadcast_message)

        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        label = QLabel("Message to All Active Agents:")
        font = label.font()
        font.setPointSize(self.fontsize)
        label.setFont(font)
        layout.addWidget(label)
        layout.addWidget(self.user_input)
        self.setLayout(layout)

        self.setWindowTitle("The Flaws of Others - Multi-agent Consensus")
        self.resize(700, 500)

    def broadcast_message(self):
        text = self.user_input.text().strip()
        if not text:
            return
        for tab in self.agent_tabs:
            tab.handle_input(text)
        self.user_input.clear()

    def focus_current_input(self, index):
        if 0 <= index < len(self.agent_tabs):
            self.agent_tabs[index].user_input.setFocus()

    def reset_agents(self):
        for tab in self.agent_tabs:
            tab.text_area.clear()
            tab.user_input.clear()
            tab.latest_response = ""
            if tab.engine == "claude":
                tab.history.clear()
                tab.history_data = {"history": tab.history, "seeded": True}
            else:
                tab.history_data = {"history": [], "seeded": True}
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
