import streamlit as st
import openai
from dotenv import find_dotenv, load_dotenv
import os
import time
import logging
from datetime import datetime


load_dotenv()

client = openai.OpenAI()

client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
model = "gpt-4o"

# Step 1. upload a file

# step 2. create an assistant
assistant = client.beta.assistants.create(
    name="Study Buddy",
    instructions="""
    You are a helpful study assistant who knows a lot about understanding research papers.
    Your role is to summarize papers, clarify terminology within context, and extract key figures and data.
    Cross-reference information for additional insights and answer related questions comprehensively.
    Analyze the papers, noting strengths and limitations.
    Respond to queries effectively, incorporating feedback to enhance your accuracy.
    Handle data securely and update your knowledge base with the latest research.
    Adhere to ethical standards, respect intellectual property, and provide users with guidance on any limitations.
    Maintain a feedback loop for continuous improvement and user support.
    Your ultimate goal is to facilitate a deeper understanding of complex scientific material, making it more accessible and comprehensible.""",
    tools=[{"type": "file_search"}],
    model=model,
)

vector_store = client.beta.vector_stores.create(name="Cryptocurrency")

# Ready the files for upload to OpenAI
filepath = "./cryptocurrency.pdf"
file_streams = [open(filepath, "rb")]

file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
    vector_store_id=vector_store.id, files=file_streams
)
# file_object = client.files.create(file=open(filepath, "rb"), purpose="assistants")
print(file_batch.status)
print(file_batch.file_counts)

assistant = client.beta.assistants.update(
    assistant_id=assistant.id,
    tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
)

# Get the assistant ID
assistant_id = assistant.id
print(f"Assistant ID:: {assistant_id}")
print(f"Vector Store ID:: {vector_store.id}")

# hardcoded ids once first code run is done and assistant is created
# thread_id =
# assistant_id =

# Step 3. Create a thread

message_file = client.files.create(
    file=open("./cryptocurrency.pdf", "rb"), purpose="assistants"
)

thread = client.beta.threads.create(
    messages=[
        {
            "role": "user",
            "content": "What is crypto mining?",
            # Attach the new file to the message.
            "attachments": [
                {"file_id": message_file.id, "tools": [{"type": "file_search"}]}
            ],
        }
    ]
)

print(thread.tool_resources.file_search)
print(f"Thread ID:: {thread.id}")


# thread = client.beta.threads.create()

# thread_id = thread.id
# print(thread_id)

# run the assistant

run = client.beta.threads.runs.create_and_poll(
    thread_id=thread.id,
    assistant_id=assistant_id,
    instructions="Please address the user as Bruce",
)


def wait_for_run_completion(client, thread_id, run_id, sleep_interval=5):
    """
    Waits for a run to complete and prints the elapsed time.:param client: The OpenAI client object.
    :param thread_id: The ID of the thread.
    :param run_id: The ID of the run.
    :param sleep_interval: Time in seconds to wait between checks.
    """
    while True:
        try:
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
            if run.completed_at:
                elapsed_time = run.completed_at - run.created_at
                formatted_elapsed_time = time.strftime(
                    "%H:%M:%S", time.gmtime(elapsed_time)
                )
                print(f"Run completed in {formatted_elapsed_time}")
                logging.info(f"Run completed in {formatted_elapsed_time}")
                # Get messages here once Run is completed!
                messages = client.beta.threads.messages.list(thread_id=thread_id)
                last_message = messages.data[0]
                response = last_message.content[0].text.value
                print(f"Assistant Response: {response}")
                break
        except Exception as e:
            logging.error(f"An error occurred while retrieving the run: {e}")
            break
        logging.info("Waiting for run to complete...")
        time.sleep(sleep_interval)


# run it

wait_for_run_completion(client=client, thread_id=thread.id, run_id=run.id)

run_steps = client.beta.threads.runs.steps.list(thread_id=thread.id, run_id=run.id)
print(f"Run steps --> {run_steps.data[0]}")
