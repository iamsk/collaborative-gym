import logging
from typing import Callable, List

from collaborative_gym.core import CoEnv

logger = logging.getLogger(__name__)


class EnvFactory:
    """
    Factory class for registering and creating CoEnv.

    It maintains a mapping between environment names and their corresponding classes.

    Attributes:
        registry: Dictionary mapping environment names to their CoEnv subclasses
    """

    registry: dict[str, type[CoEnv]] = {}

    @classmethod
    def register(cls, name: str) -> Callable[[type[CoEnv]], type[CoEnv]]:
        """
        Class decorator for registering new environment types.

        Args:
            name: Unique identifier for the environment class

        Returns:
            A decorator function that registers the environment class

        Example:
            @EnvFactory.register("my_env")
            class MyEnv(CoEnv):
                pass
        """

        def inner_wrapper(
            wrapped_class: type[CoEnv],
        ) -> type[CoEnv]:
            if name in cls.registry:
                logger.warning("Environment %s already exists. Will replace it", name)
            cls.registry[name] = wrapped_class
            return wrapped_class

        return inner_wrapper

    @classmethod
    def make(cls, name: str, team_members: List[str], env_id: str, **kwargs) -> CoEnv:
        """
        Create an instance of a registered environment.

        Args:
            name: Name of the registered environment to create
            team_members: List of team member identifiers
            env_id: Unique identifier for this environment instance
            **kwargs: Additional arguments passed to the environment constructor

        Returns:
            An instance of the specified environment

        Raises:
            ValueError: If the environment name is not found in the registry
        """
        if name not in cls.registry:
            raise ValueError(f"Environment {name} not found in registry")
        return cls.registry[name](team_members=team_members, env_id=env_id, **kwargs)
