from os import environ, listdir
import os
import shutil

from crewai import Crew
from dotenv import find_dotenv, load_dotenv, set_key
import panel as pn

from aiagents.cml_agents.manager_agents import ManagerAgents
from aiagents.cml_agents.swagger_splitter import SwaggerSplitterAgents
from aiagents.cml_agents.agents import Agents
from aiagents.cml_agents.parse_for_manager import swagger_parser
from aiagents.cml_agents.callback_utils import custom_callback, custom_initialization_callback
from aiagents.cml_agents.tasks import Tasks, TasksInitialize

from aiagents.config import Initialize, configuration
from bokeh.server.contexts import BokehSessionContext

from aiagents.custom_threading import threads


# we can't directly import the agents and tasks because we want to ensure that the configuration is first
# initialize the configuration with panel hooks, and then pass it as an argument
def StartCrewInitialization(configuration: Initialize):
    #manager_agents = ManagerAgents(configuration=configuration)
    swagger_splitter_agents = SwaggerSplitterAgents(configuration=configuration)
    #agents = Agents(configuration=configuration)
    ##please call swagger splitter here

    ## if generated folder has any entries delete the same.

    # """Delete all files and subdirectories inside the specified directory."""
    # if os.path.exists(configuration.generated_folder_path):
    #     # Remove the directory and all its contents
    #     shutil.rmtree(configuration.generated_folder_path)
    #     # Recreate the empty directory
    #     os.makedirs(configuration.generated_folder_path)

    configuration.chat_interface.send(
        pn.pane.Markdown(
            """Your API Specification file is currently being processed. This may take a few moments. ⏳
            We are analyzing the content to ensure all details are captured correctly. 
            Please hold on as we prepare everything for you. 
            You’ll be notified as soon as the processing is complete. 🚀""",
            styles=configuration.chat_styles,
        ),
        user="System",
        respond=False,
    )

    for filename in listdir(configuration.swagger_files_directory):
            if filename == configuration.new_file_name:
                swagger_parser(
                    filename,
                    configuration.swagger_files_directory,
                    configuration.generated_folder_path,
                )
    agent_dict = {
        # "swagger_splitter_agent": swagger_splitter_agents.swagger_splitter_agent,
        "metadata_summarizer_agent": swagger_splitter_agents.metadata_summarizer_agent,
    }
    tasks = TasksInitialize(configuration=configuration, agents=agent_dict)
    embedding = {
        "provider": "azure_openai",
        "config": {
            "model": environ.get(
                "OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002"
            ),
            "deployment_name": environ.get(
                "AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "ada-embedding"
            ),
        },
    } if configuration.openai_provider=="AZURE_OPENAI" else {
        "provider": "openai",
        "config": {
            "model": environ.get(
                "OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002"
            )
        },
    }

    splitterCrew = Crew(
        agents=[
            # agent_dict["swagger_splitter_agent"],
            agent_dict["metadata_summarizer_agent"],
            # agent_dict["task_matching_agent"],
            # agent_dict["manager_agent"],
            # agent_dict["human_input_agent"],
            # # agent_dict["api_caller_agent"],
            # agent_dict["validator_agent"],
        ],
        tasks=[
            tasks.metadata_summarizer_task,
            # tasks.initial_human_input_task,
            # tasks.task_matching_task,
            # tasks.manager_task,
            # tasks.api_calling_task,
        ],
        verbose=1,
        memory=False,
        embedder=embedding,
        task_callback=custom_initialization_callback
    )
    try:
        splitterCrew.kickoff()
        # configuration.metadata_summarization_status.value = "Processed the API Spec File"
        configuration.chat_interface.send(
        pn.pane.Markdown(
            """Processed the API Spec File""",
            styles=configuration.chat_styles,
        ),
        user="System",
        respond=False,)
        env_file = find_dotenv()
        load_dotenv(env_file)
        file_count = os.getenv("fileCount")
        if file_count == '0':
            session_created()
    except Exception as err:
        configuration.chat_interface.send(
        pn.pane.Markdown(
            f"""Failed with {err}\nPlease upload the details again.""",
            styles=configuration.chat_styles,
        ),
        user="System",
        respond=False,
    )
        configuration.spinner.visible=False
        configuration.spinner.value=False
        configuration.reload_button.disabled=False
        configuration.upload_button.disabled=False




def StartCrewInteraction(configuration: Initialize):
    manager_agents = ManagerAgents(configuration=configuration)
    agents = Agents(configuration=configuration)



    agent_dict = {
        # "swagger_splitter_agent": swagger_splitter_agents.swagger_splitter_agent,
        #"metadata_summarizer_agent": swagger_splitter_agents.metadata_summarizer_agent,
        "task_matching_agent": manager_agents.task_matching_agent,
        "manager_agent": manager_agents.manager_agent,
        "human_input_agent": agents.human_input_agent,
        # "api_caller_agent": agents.api_caller_agent,
        "validator_agent": agents.validator_agent,
    }

    tasks = Tasks(configuration=configuration, agents=agent_dict)

    embedding = {
        "provider": "azure_openai",
        "config": {
            "model": environ.get(
                "OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002"
            ),
            "deployment_name": environ.get(
                "AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "ada-embedding"
            ),
        },
    } if configuration.openai_provider=="AZURE_OPENAI" else {
        "provider": "openai",
        "config": {
            "model": environ.get(
                "OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002"
            )
        },
    }

    splitterCrew = Crew(
        agents=[
            # agent_dict["swagger_splitter_agent"],
            #agent_dict["metadata_summarizer_agent"],
            agent_dict["task_matching_agent"],
            agent_dict["manager_agent"],
            agent_dict["human_input_agent"],
            # agent_dict["api_caller_agent"],
            agent_dict["validator_agent"],
        ],
        tasks=[
            #tasks.metadata_summarizer_task,
            tasks.initial_human_input_task,
            tasks.task_matching_task,
            tasks.manager_task,
            # tasks.api_calling_task,
        ],
        verbose=1,
        memory=False,
        embedder=embedding,
        task_callback=custom_callback
    )

    try:
        splitterCrew.kickoff()
        env_file = find_dotenv()
        load_dotenv(env_file)
        file_count = os.getenv("fileCount")
        file_count = int(file_count) + 1 if file_count is not None else 1
        set_key(env_file, 'fileCount',file_count)

        configuration.chat_interface.send(
            "If you have any other queries or need further assistance, please Reload the Crew.", 
            user="System", 
            respond=False)
        configuration.spinner.value = False
        configuration.spinner.visible = False
    
    except Exception as err:
        configuration.chat_interface.send(
            pn.pane.Markdown(
                object=f"Starting Interaction Crew Failed with {err}\n Please Reload the Crew.",
                styles=configuration.chat_styles
            ),
            user="System",
            respond=False
        )

        configuration.spinner.visible=False
        configuration.spinner.value=False
        configuration.reload_button.disabled=False

# Handle session creation, which includes starting the CrewAI process
def session_created():
    # Disable the start button and clear chat interface to start a session
    # start_crew_button.disabled = True
    # configuration.chat_interface.clear()
    configuration.chat_interface.send(
        pn.pane.Markdown(
            "Starting the Crew!",
            styles=configuration.chat_styles
        ), user="System", respond=False
    )
    # Show the loading spinner as the Crew loads
    configuration.spinner.value = True
    configuration.spinner.visible = True
    configuration.crew_thread = threads.thread_with_trace(
        target=StartCrewInteraction, args=(configuration,)
    )
    configuration.crew_thread.daemon = True  # Ensure the thread dies when the main thread (the one that created it) dies
    configuration.crew_thread.start()