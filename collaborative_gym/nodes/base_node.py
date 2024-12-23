"""
Base node implementation for asynchronous communication in Collaborative Gym.

This module extends https://github.com/ProKil/aact/blob/main/src/aact/nodes/base.py
"""

import os
import sys
import time
from asyncio import CancelledError

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self
from typing import Any, AsyncIterator, Generic, Type, TypeVar
from pydantic import BaseModel, ConfigDict

from abc import abstractmethod
from aact.messages import Message
from redis.asyncio import Redis

from aact.messages.base import DataModel

InputType = TypeVar("InputType", covariant=True, bound=DataModel)
OutputType = TypeVar("OutputType", covariant=True, bound=DataModel)

LAST_ACTIVE_TIME_KEY = "pid_to_last_active_time"


class NodeExitSignal(CancelledError):
    """
    Signal for graceful node termination in the event handling system.

    This exception is raised within nodes' event handlers to initiate a clean
    shutdown process. It ensures proper cleanup of Redis connections and
    subscriptions when a node needs to exit.
    """


class BaseNode(BaseModel, Generic[InputType, OutputType]):
    """
    Base class for asynchronous communication nodes in the collaborative environment.

    This class implements Redis pub/sub based message handling, allowing nodes to
    communicate asynchronously through typed channels. Each node can subscribe to
    multiple input channels and publish to multiple output channels.

    Type Parameters:
        InputType: Type of messages this node can receive (must be a DataModel)
        OutputType: Type of messages this node can send (must be a DataModel)

    Attributes:
        input_channel_types: Mapping of channel names to their input message types
        output_channel_types: Mapping of channel names to their output message types
        redis_url: URL for Redis connection (default: "redis://localhost:6379/0")

    The node maintains its active status through Redis, allowing central monitoring
    and management of node processes. Subclasses must implement event_handler to
    define custom behavior for received messages.
    """

    input_channel_types: dict[str, Type[InputType]]
    output_channel_types: dict[str, Type[OutputType]]
    redis_url: str
    model_config = ConfigDict(extra="allow")

    def __init__(
        self,
        input_channel_types: list[tuple[str, Type[InputType]]],
        output_channel_types: list[tuple[str, Type[OutputType]]],
        redis_url: str = "redis://localhost:6379/0",
    ):
        super().__init__(
            input_channel_types=dict(input_channel_types),
            output_channel_types=dict(output_channel_types),
            redis_url=redis_url,
        )

        self.r: Redis = Redis.from_url(redis_url)
        self.pubsub = self.r.pubsub()
        self.pid = os.getpid()

    async def update_last_active_time(self):
        await self.r.hset(LAST_ACTIVE_TIME_KEY, str(self.pid), str(time.time()))

    async def delete_process_record(self):
        await self.r.hdel(LAST_ACTIVE_TIME_KEY, str(self.pid))

    async def __aenter__(self) -> Self:
        try:
            await self.r.ping()
        except ConnectionError:
            raise ValueError(
                f"Could not connect to Redis with the provided url. {self.redis_url}"
            )
        await self.pubsub.subscribe(*self.input_channel_types.keys())
        await self.update_last_active_time()
        return self

    async def __aexit__(self, _: Any, __: Any, ___: Any) -> None:
        await self.delete_process_record()
        await self.pubsub.unsubscribe()
        await self.r.aclose()

    async def _wait_for_input(
        self,
    ) -> AsyncIterator[tuple[str, Message[InputType]]]:
        async for message in self.pubsub.listen():
            channel = message["channel"].decode("utf-8")
            if message["type"] == "message" and channel in self.input_channel_types:
                data = Message[self.input_channel_types[channel]].model_validate_json(  # type: ignore
                    message["data"]
                )
                yield channel, data
        raise Exception("Input channel closed unexpectedly")

    async def event_loop(
        self,
    ) -> None:
        """
        Main event processing loop that handles incoming messages.

        Continuously listens for messages on subscribed channels and processes them
        through the event_handler. For each received message, publishes any resulting
        output messages to their respective channels.

        Raises:
            NodeExitSignal: When graceful shutdown is requested
            Exception: For unexpected errors during message processing
        """
        try:
            async for input_channel, input_message in self._wait_for_input():
                async for output_channel, output_message in self.event_handler(
                    input_channel, input_message
                ):
                    await self.r.publish(
                        output_channel, output_message.model_dump_json()
                    )
        except NodeExitSignal as e:
            self.logger.info(f"Event loop cancelled: {e}. Exiting gracefully.")
        except Exception as e:
            raise e

    @abstractmethod
    async def event_handler(
        self, _: str, __: Message[InputType]
    ) -> AsyncIterator[tuple[str, Message[OutputType]]]:
        """
        Abstract method for processing incoming messages and generating responses.

        Args:
            _: Name of the channel that received the message
            __: The received message with its typed content

        Returns:
            AsyncIterator yielding tuples of (output_channel, output_message)

        This method must be implemented by subclasses to define how the node
        responds to different types of input messages.
        """
        raise NotImplementedError("event_handler must be implemented in a subclass.")
        yield "", self.output_type()  # unreachable: dummy return value
