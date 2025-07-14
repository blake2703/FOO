"""
Helper.py
Command-line chatbot interface using the OpenAI API and assistant capabilities.
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

# Force UTF-8 encoding for stdout and stderr
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

class OpenAIChatbot:
    def __init__(self, config_file="config.json"):
        # Load the JSON configuration from the provided file
        with open(config_file, 'r') as file:
            raw_config = json.load(file)
            config = raw_config['CONFIG']  # Focus on the CONFIG section only

        # Extract user and assistant name from configuration
        self.user = config['user']
        self.name = config['name']

        # Prepend custom interaction preamble to instruction text
        preamble = f"Please address the user as Beloved {self.user}.\\n\\n Introduce yourself as {self.name}, robot extraordinaire.\\n\\n "
        self.instructions = preamble + config['instructions']

        # Extract the model identifier used for the assistant
        self.model = config['model']

        # Get the OpenAI API key from the environment and validate it
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            print("API key is not set. Please set the OPENAI_API_KEY environment variable.")
            exit(1)

        # Initialize the OpenAI API client
        self.client = openai.OpenAI()

        # Create a new assistant with file search tool enabled
        self.assistant = self.client.beta.assistants.create(
            model=self.model,
            instructions=self.instructions,
            name=self.name,
            tools=[{"type": "file_search"}]
        )

        # Create a new chat thread for maintaining conversation context
        self.thread = self.client.beta.threads.create()

    def upload_file(self, file_path):
        """
        Uploads a local file to the OpenAI API to be used by the assistant.
        Returns the file ID if successful; otherwise, prints an error.
        """
        try:
            with open(file_path, 'rb') as file_data:
                file_object = self.client.files.create(
                    file=file_data,
                    purpose='assistants'
                )
            print(f"File uploaded successfully: ID {file_object.id}")
            return file_object.id
        except Exception as e:
            print(f"Failed to upload file: {e}")
            return None

    def run_chat(self):
        # Display introductory details about the assistant and thread
        print("*****************   N E W   C H A T   *****************")
        print(f"Assistant: {self.assistant.id}")
        print(f"Thread: {self.thread.id}")

        # Main chat loop
        while True:
            print(">>>>>>>>>>>>>>>>>>>>>>>>>>")
            # Prompt user input
            user_input = input(f"{self.user}: ")

            # Exit condition
            if user_input.lower() == 'exit':
                break

            # Handle file upload request
            if user_input.startswith("file:"):
                file_path = user_input[5:].strip()
                file_id = self.upload_file(file_path)
                if file_id:
                    print(f"File ID {file_id} will be used in subsequent requests")
                    try:
                        # Attach uploaded file to the conversation thread
                        message = self.client.beta.threads.messages.create(
                            thread_id=self.thread.id,
                            role="user",
                            content="Query involving an uploaded file.",
                            attachments=[{"file_id": file_id, "tools": [{"type": "file_search"}]}]
                        )
                        continue  # Prompt next input after file handling
                    except Exception as e:
                        print(f"Failed to upload file: {e}")

            try:
                # Send user's input as a new message to the thread
                my_thread_message = self.client.beta.threads.messages.create(
                    thread_id=self.thread.id,
                    role="user",
                    content=user_input,
                )

                # Trigger a run with the assistant to process the message
                my_run = self.client.beta.threads.runs.create(
                    thread_id=self.thread.id,
                    assistant_id=self.assistant.id
                )
            except Exception as e:
                print(f"Error: {e}")

            # Polling loop: wait until assistant finishes processing
            while my_run.status in ["queued", "in_progress"]:
                my_run = self.client.beta.threads.runs.retrieve(
                    thread_id=self.thread.id,
                    run_id=my_run.id
                )

                # Once run is complete, fetch and display the response
                if my_run.status == "completed":
                    all_messages = self.client.beta.threads.messages.list(
                        thread_id=self.thread.id
                    )
                    for message in all_messages.data:
                        if message.role == "assistant":
                            print("\n<<<<<<<<<<<<<<<<<<<<<<<<<<")
                            print("\n" + self.name + f": {message.content[0].text.value}")
                            break
                    break  # Exit polling loop once assistant replies
                else:
                    print(".", end="", flush=True)  # Indicate waiting

# Entry point of the program
if __name__ == "__main__":
    agent = OpenAIChatbot()
    agent.run_chat()
