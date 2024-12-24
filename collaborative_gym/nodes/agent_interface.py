import asyncio
from typing import AsyncIterator, Self, Any

from aact import NodeFactory, Message

from collaborative_gym.core import logger
from collaborative_gym.nodes.base_node import BaseNode
from collaborative_gym.nodes.commons import JsonObj

AGENT_TO_PID_KEY = "agent_to_pid"


@NodeFactory.register("agent")
class AgentNode(BaseNode[JsonObj, JsonObj]):
    """
    Agent node in asynchronous interaction among humans, agents, and environments.

    This node handles the lifecycle of an LM agent, including initialization,
    observation processing, action generation, and cleanup. It uses Redis pub/sub
    for message passing and implements concurrent task management for handling
    multiple observations.

    This node expects the agent to have the following methods:
    - `start(self, name: str, team_members: List[str], task_description: str, action_space: List[str], example_question: str, example_trajectory: str) -> None`
        - This method will be called when the node receives a start message.
    - `get_action(self, observation: dict, chat_history: List[dict]) -> str`
        - This method will be called when the node receives a new observation message.
    - `end(self, result_dir: str) -> None`
        - This method will be called when the node receives an end message.

    Type Parameters:
        JsonObj: Both input and output message types use JSON-serializable objects

    Attributes:
        env_uuid: Unique identifier for the environment instance
        node_name: Name of this agent node
        wait_time: Delay in seconds between receiving observation and sending action
        agent: The AI agent instance that generates actions
        tasks: List of concurrent observation processing tasks
        is_processing_observation: Flag to prevent concurrent observation processing
        is_processing_observation_lock: AsyncIO lock for observation processing
    """

    def __init__(
        self,
        env_uuid: str,
        node_name: str,
        agent,
        wait_time: int = 20,
        redis_url: str = "redis://localhost:6379/0",
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
        self.wait_time = wait_time
        self.agent = agent

        self.tasks = []
        self.is_processing_observation = False
        self.is_processing_observation_lock = asyncio.Lock()

    async def __aenter__(self) -> Self:
        await super().__aenter__()
        await self.r.hset(
            AGENT_TO_PID_KEY, f"{self.env_uuid}_{self.node_name}", self.pid
        )
        return self

    async def delete_process_record(self):
        await super().delete_process_record()
        await self.r.hdel(AGENT_TO_PID_KEY, f"{self.env_uuid}_{self.node_name}")

    async def event_loop(self) -> None:
        """
        Main event loop that processes incoming messages with concurrent observation handling.

        Manages concurrent processing of observations while handling other messages
        sequentially. Uses asyncio tasks and locks to prevent observation processing
        overlap. Control messages (start/end) are processed immediately while
        observations are processed concurrently.

        Returns:
            None
        """
        self.tasks = []
        async for input_channel, input_message in self._wait_for_input():
            if input_channel == f"{self.env_uuid}/{self.node_name}/observation":
                async with self.is_processing_observation_lock:
                    if self.is_processing_observation:
                        continue
                    self.is_processing_observation = True
                # Run the event handler in a separate task
                task = asyncio.create_task(
                    self.handle_event(input_channel, input_message)
                )
                self.tasks.append(task)
            else:
                await self.handle_event(input_channel, input_message)

        await asyncio.gather(*self.tasks)

    async def handle_event(self, input_channel: str, input_message: Message[JsonObj]):
        """
        Process a single event and publish any resulting messages.

        Args:
            input_channel: The channel that received the message
            input_message: The received message with its JSON content

        Returns:
            None
        """
        async for output_channel, output_message in self.event_handler(
            input_channel, input_message
        ):
            await self.r.publish(output_channel, output_message.model_dump_json())

    async def event_handler(
        self, input_channel: str, input_message: Message[JsonObj]
    ) -> AsyncIterator[tuple[str, Message[JsonObj]]]:
        """
        Handle different types of input messages and generate appropriate responses.

        Processes three types of messages:
        1. Start: Initializes the agent with task information
        2. Observation: Gets agent's action based on current state
        3. End: Cleans up agent resources and stops processing

        Args:
            input_channel: The channel that received the message
            input_message: The received message with its JSON content

        Returns:
            AsyncIterator yielding (channel, message) pairs for responses

        Raises:
            asyncio.CancelledError: When receiving an end message
        """
        if input_channel == f"{self.env_uuid}/start":
            logger.info(f"AgentNode ({self.node_name}): received start message")
            self.agent.start(
                name=self.node_name,
                team_members=input_message.data.object["team_members"],
                task_description=input_message.data.object["task_description"],
                action_space=input_message.data.object["action_space"],
                example_question=input_message.data.object["example_question"],
                example_trajectory=input_message.data.object["example_trajectory"],
            )
        elif input_channel == f"{self.env_uuid}/{self.node_name}/observation":
            logger.info(f"AgentNode ({self.node_name}): received observation message")
            observation = input_message.data.object["observation"]
            chat_history = input_message.data.object["chat_history"]
            action = self.agent.get_action(
                observation=observation, chat_history=chat_history
            )
            payload = {"action": action, "role": self.node_name}
            await asyncio.sleep(
                self.wait_time
            )  # Leave time for other team members to respond
            await self.update_last_active_time()
            yield f"{self.env_uuid}/step", Message[JsonObj](
                data=JsonObj(object=payload)
            )
            async with self.is_processing_observation_lock:
                self.is_processing_observation = False
        elif input_channel == f"{self.env_uuid}/end":
            logger.info(f"AgentNode ({self.node_name}): received end message")
            self.agent.end(result_dir=input_message.data.object["result_dir"])
            for task in self.tasks:
                task.cancel()
            await self.delete_process_record()
            raise asyncio.CancelledError
