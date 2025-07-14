"""
HelperGUI.py
GUI chatbot interface using the OpenAI API and assistant capabilities.
Configuration is dynamically loaded from a JSON file with user and assistant properties.
Includes support for file uploads and persistent threaded interactions.

By Juan B. Gutiérrez, Professor of Mathematics 
University of Texas at San Antonio.

License: Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
"""
import os
import openai
import json
import sys
import io
from PyQt5.QtWidgets import QApplication, QWidget, QTextEdit, QLineEdit, QVBoxLayout, QPushButton
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QClipboard

# Force UTF-8 encoding for stdout and stderr
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

class LLMWorker(QThread):
    # Define a signal to emit when the assistant's response is ready
    result_ready = pyqtSignal(str)

    def __init__(self, user_input, openai_client, assistant_openai, thread_openai):
        super().__init__()
        self.user_input = user_input
        self.openai_client = openai_client
        self.assistant_openai = assistant_openai
        self.thread_openai = thread_openai

    def run(self):
        # Run the assistant interaction in a separate thread
        try:
            # Send user's message to the thread
            thread_message = self.openai_client.beta.threads.messages.create(
                thread_id=self.thread_openai.id,
                role="user",
                content=self.user_input,
            )
            # Trigger assistant response
            run_openai = self.openai_client.beta.threads.runs.create(
                thread_id=self.thread_openai.id,
                assistant_id=self.assistant_openai.id
            )
            # Wait for completion
            while run_openai.status in ["queued", "in_progress"]:
                run_openai = self.openai_client.beta.threads.runs.retrieve(
                    thread_id=self.thread_openai.id,
                    run_id=run_openai.id
                )
                # Emit the assistant's message once completed
                if run_openai.status == "completed":
                    all_messages = self.openai_client.beta.threads.messages.list(
                        thread_id=self.thread_openai.id
                    )
                    for message in all_messages.data:
                        if message.role == "assistant":
                            self.result_ready.emit(message.content[0].text.value)
                            return
            self.result_ready.emit("Error: No response from the assistant.")
        except Exception as e:
            self.result_ready.emit(f"Error: {e}")

class OpenAIChatbot(QWidget):
    def __init__(self):
        super().__init__()

        # Load configuration from CONFIG section
        config_file = "config.json"
        with open(config_file, 'r') as file:
            raw_config = json.load(file)
            config = raw_config['CONFIG']

        # Extract configuration values
        self.user = config['user']
        self.name = config['name']

        # Build instructions with dynamic user and assistant introduction
        preamble = f"Please address the user as Beloved {self.user}.\\n\\n Introduce yourself as {self.name}, robot extraordinaire.\\n\\n "
        self.instructions = preamble + config['instructions']
        self.model = config['model']
        self.latest_response = ""

        # Load API key from environment
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            print("API key is not set. Please set the OPENAI_API_KEY environment variable.")
            exit(1)

        # Create OpenAI API client
        self.client = openai.OpenAI()

        # Create assistant and thread instances
        self.assistant = self.client.beta.assistants.create(
            model=self.model,
            instructions=self.instructions,
            name=self.name,
            tools=[{"type": "file_search"}]
        )
        self.thread = self.client.beta.threads.create()

        # Set up the GUI interface
        self.init_gui()

    def init_gui(self):
        # Set up main window parameters
        self.setWindowTitle("JuanGPT")
        self.setGeometry(100, 100, 600, 400)
        self.setAcceptDrops(True)  # Enable drag and drop

        layout = QVBoxLayout()

        # Text display area for messages
        self.text_area = QTextEdit(self)
        self.text_area.setReadOnly(True)
        layout.addWidget(self.text_area)

        # Display assistant and thread information
        self.text_area.append(f"Assistant ID: {self.assistant.id}")
        self.text_area.append(f"Thread ID: {self.thread.id}")
        self.text_area.append("<<<<<<<<<<<<<<<<<<<<<<<<<<")

        # User input field
        self.user_input = QLineEdit(self)
        self.user_input.setPlaceholderText("Type your message and press Enter")
        layout.addWidget(self.user_input)

        # Button to copy latest assistant response
        self.copy_button = QPushButton("Copy Latest Answer")
        self.copy_button.clicked.connect(self.copy_latest_answer)
        layout.addWidget(self.copy_button)

        # Bind Enter key to user input processing
        self.user_input.returnPressed.connect(self.on_enter_pressed)

        # Apply layout to the window
        self.setLayout(layout)

    def dragEnterEvent(self, event: QDragEnterEvent):
        # Accept drag event if a file is present
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        # Handle file drop by extracting path
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self.upload_file(file_path)

    def upload_file(self, file_path):
        # Upload a file to the assistant
        try:
            with open(file_path, 'rb') as file_data:
                file_object = self.client.files.create(
                    file=file_data,
                    purpose='assistants'
                )
            self.text_area.append(f"File uploaded successfully: ID {file_object.id}")
            # Attach file to the conversation thread
            try:
                self.client.beta.threads.messages.create(
                    thread_id=self.thread.id,
                    role="user",
                    content="File uploaded.",
                    attachments=[{"file_id": file_object.id, "tools": [{"type": "file_search"}]}]
                )
            except Exception as e:
                self.text_area.append(f"Failed to attach file to thread: {e}")
            self.text_area.append(">>>>>>>>>>>>>>>>>>>>>>>>>>")
        except Exception as e:
            self.text_area.append(f"Failed to upload file: {e}")

    def on_enter_pressed(self):
        # Process input when Enter is pressed
        user_input = self.user_input.text().strip()
        if user_input:
            self.process_user_input(user_input)
        self.user_input.clear()

    def process_user_input(self, user_input):
        # Display user input
        self.text_area.append(f"{self.user}: {user_input}")
        self.text_area.append(">>>>>>>>>>>>>>>>>>>>>>>>>>")
        self.user_input.setEnabled(False)

        # Launch worker thread to handle assistant response
        self.worker_thread = LLMWorker(
            user_input, self.client, self.assistant, self.thread
        )
        self.worker_thread.result_ready.connect(self.display_results)
        self.worker_thread.start()

    def display_results(self, response):
        # Show assistant response
        self.latest_response = response
        self.text_area.append(f"{self.name}: {response}")
        self.text_area.append("<<<<<<<<<<<<<<<<<<<<<<<<<<")
        self.user_input.setEnabled(True)

    def copy_latest_answer(self):
        # Copy latest assistant message to clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText(self.latest_response)
        self.text_area.append("Latest answer copied to clipboard.")

# Start the GUI application
if __name__ == "__main__":
    app = QApplication([])
    chatbot = OpenAIChatbot()
    chatbot.show()
    app.exec_()
