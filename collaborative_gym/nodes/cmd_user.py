import asyncio
from typing import AsyncIterator

from aact import NodeFactory, Message
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.patch_stdout import patch_stdout

from collaborative_gym.core import logger
from collaborative_gym.nodes.base_node import BaseNode
from collaborative_gym.nodes.commons import JsonObj
from collaborative_gym.spaces import UnicodeWithRegexPattern
from collaborative_gym.utils.dict import trim_dict
from collaborative_gym.utils.string import (
    make_string_bold,
    print_highlighted_text,
    make_string_green,
)


class CommandLineUserProxy:
    """
    Enhanced command-line interface for human user interaction.

    Provides an interactive command-line interface using prompt_toolkit for human users
    to interact with the collaborative environment. Supports rich text formatting,
    multi-line input with proper indentation, and formatted display of task status.

    Attributes:
        task_description: Description of the collaborative task
        action_space: List of available actions with their descriptions
        prompt_session: PromptSession instance for enhanced CLI interaction
    """

    def __init__(self, task_description: str, action_space: list):
        self.task_description = task_description
        self.action_space = action_space
        self.prompt_session = (
            PromptSession()
        )  # Prompt user for input in the command line

    async def prompt_user_for_multiple_line_input(self, message: str) -> str:
        """
        Prompt user for multi-line input with enhanced formatting.

        Creates an interactive prompt supporting multi-line input with features like
        line numbering, tab completion for indentation, and proper continuation lines.

        Args:
            message: The prompt message to display to the user

        Returns:
            str: The complete multi-line input from the user
        """
        bindings = KeyBindings()

        @bindings.add("tab")
        def insert_tab(event):
            event.app.current_buffer.insert_text("    ")

        def prompt_continuation(width, line_number, wrap_count):
            if wrap_count > 0:
                return " " * (width - 3) + "-> "
            else:
                text = ("- %02i - " % (line_number + 1)).rjust(width)
                return HTML("<strong>%s</strong>") % text

        with patch_stdout():
            answer = await self.prompt_session.prompt_async(
                f"{message}\n(Press [Esc] followed by [Enter] to accept input.)\n- 01 - ",
                multiline=True,
                prompt_continuation=prompt_continuation,
                key_bindings=bindings,
            )

        return answer

    async def prompt_user_for_single_line_input(self, message: str) -> str:
        """
        Prompt user for single-line input.

        Creates an interactive prompt for single-line input with proper stdout handling
        to prevent interference with asynchronous operations.

        Args:
            message: The prompt message to display to the user

        Returns:
            str: The single-line input from the user
        """
        with patch_stdout():
            answer = await self.prompt_session.prompt_async(message, multiline=False)

        return answer

    async def get_action(self, obs: dict) -> str:
        """
        Get user action through command-line interaction.

        Displays the current task state, observation, and event log in a formatted manner,
        then prompts the user to select and configure an action from the available options.

        Args:
            obs: Dictionary containing current observation and event log

        Returns:
            str: The constructed action string based on user input
        """
        # Display current information
        event_log = obs["event_log"]
        obs.pop("event_log")
        trimmed_obs = trim_dict(obs, n=15)
        print(make_string_bold("**Task Description**"))
        print(self.task_description)
        print(make_string_bold("**Current Observation**"))
        for k, v in trimmed_obs.items():
            print(make_string_green(f"*{k}*"))
            print(v)
            print()
        print(make_string_bold("**Event Log**"))
        print_highlighted_text(
            event_log,
            keywords={
                "[user]": "ansiblue",
                "[agent]": "ansiblue",
                "[environment]": "ansigreen",
                "succeeded": "ansigreen",
                "failed": "ansired",
            },
        )

        # Prompt the user to give an action
        print("\nHere are the available actions:")
        for i, act in enumerate(self.action_space):
            print(
                f'{i + 1}. {act["human_readable_name"]}: '
                f'{act["human_readable_description"]}'
            )

        get_valid_action_idx = False
        while not get_valid_action_idx:
            try:
                # action_idx_str = await aioconsole.ainput('Please provide the index of the action you want to take:\n')
                action_idx_str = await self.prompt_user_for_single_line_input(
                    "Please provide the index of the action you want to take:"
                )
                print(f"You selected action index: {action_idx_str}")
                action_idx = int(action_idx_str) - 1
            except ValueError:
                print("Invalid input. Please provide a valid integer.")
                continue
            if 0 <= action_idx < len(self.action_space):
                get_valid_action_idx = True
            action = UnicodeWithRegexPattern.from_json(self.action_space[action_idx])

            params = {}
            for p in action.params:
                val = await self.prompt_user_for_multiple_line_input(
                    f"Please provide the value for parameter [{p}] of the action:"
                )
                params[p] = val
            action_str = action.construct_action_string_from_params(**params)

        return action_str


@NodeFactory.register("cmd_user")
class CmdUserNode(BaseNode[JsonObj, JsonObj]):
    """
    Asynchronous node for managing command-line user interactions.

    Handles the communication between the human user (via command line) and the
    environment through Redis channels. Manages message processing and user input
    with support for concurrent operations and proper synchronization.

    Type Parameters:
        JsonObj: Both input and output message types use JSON-serializable objects

    Attributes:
        env_uuid: Unique identifier for the environment instance
        node_name: Name/role of this command-line user interface
        user_proxy: Instance of CommandLineUserProxy handling CLI interaction
        is_processing_observation: Flag to prevent concurrent observation processing
        is_processing_observation_lock: AsyncIO lock for observation handling
    """

    def __init__(
        self, env_uuid: str, node_name: str, redis_url: str = "redis://localhost:6379/0"
    ):
        super().__init__(
            input_channel_types=[
                (f"{env_uuid}/{node_name}/observation", JsonObj),
                (f"{env_uuid}/start", JsonObj),
                (f"{env_uuid}/end", JsonObj),
            ],
            output_channel_types=[(f"{env_uuid}/step", JsonObj)],
            redis_url=redis_url,
        )
        self.env_uuid = env_uuid
        self.node_name = node_name
        self.user_proxy = None
        self.is_processing_observation = False
        self.is_processing_observation_lock = asyncio.Lock()

    async def event_loop(self) -> None:
        """
        Main event processing loop for handling user interactions.

        Manages concurrent task processing and ensures proper handling of
        observations with locking mechanisms to prevent race conditions.
        Maintains a list of active tasks for proper cleanup.

        Returns:
            None
        """
        tasks = []
        async for input_channel, input_message in self._wait_for_input():
            if input_channel == f"{self.env_uuid}/observation":
                async with self.is_processing_observation_lock:
                    if self.is_processing_observation:
                        continue
                    self.is_processing_observation = True
                # Run the event handler in a separate task
                task = asyncio.create_task(
                    self.handle_event(input_channel, input_message)
                )
                tasks.append(task)
            else:
                await self.handle_event(input_channel, input_message)

        await asyncio.gather(*tasks)

    async def handle_event(self, input_channel, input_message):
        async for output_channel, output_message in self.event_handler(
            input_channel, input_message
        ):
            await self.r.publish(output_channel, output_message.model_dump_json())

    async def event_handler(
        self, input_channel: str, input_message: Message[JsonObj]
    ) -> AsyncIterator[tuple[str, Message[JsonObj]]]:
        """
        Process incoming messages and manage user interactions.

        Handles three types of messages:
        1. Start: Initialize the command-line interface with task parameters
        2. End: Clean up resources and terminate gracefully
        3. Observation: Display current state and get user action

        Args:
            input_channel: The Redis channel receiving the message
            input_message: The received message containing task data

        Returns:
            AsyncIterator yielding (channel, message) pairs for responses

        Raises:
            asyncio.CancelledError: When task completes or cleanup is needed
        """
        if input_channel == f"{self.env_uuid}/start":
            action_space = input_message.data.object["action_space"]
            self.user_proxy = CommandLineUserProxy(
                task_description=input_message.data.object["task_description"],
                action_space=action_space,
            )
        elif input_channel == f"{self.env_uuid}/observation":
            # await asyncio.sleep(5)
            observation = input_message.data.object["observation"]
            action = await self.user_proxy.get_action(obs=observation)
            payload = {
                "action": action,  # 'UPDATE_EDITOR(text=1st message)', # action,
                "role": self.node_name,
            }
            await self.update_last_active_time()
            yield f"{self.env_uuid}/step", Message[JsonObj](
                data=JsonObj(object=payload)
            )
            async with self.is_processing_observation_lock:
                self.is_processing_observation = False
        elif input_channel == f"{self.env_uuid}/end":
            await self.delete_process_record()
            raise asyncio.CancelledError
