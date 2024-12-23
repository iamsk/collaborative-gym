from pydantic import BaseModel, ConfigDict, Field


class EnvArgs(BaseModel):
    """
    Flexible container for environment-specific arguments.

    This model allows arbitrary additional fields through its 'extra="allow"'
    configuration, making it suitable for storing diverse environment parameters
    that vary between different environment types.
    """

    model_config = ConfigDict(extra="allow")


class EnvConfig(BaseModel):
    """
    Configuration model for environment creation and initialization.

    This model specifies which environment class to instantiate and its
    initialization arguments. It works in conjunction with EnvFactory
    to create environment instances.

    Attributes:
        env_class: String identifier for the environment class in EnvFactory
        env_args: Environment-specific arguments used for initialization
    """

    env_class: str
    env_args: EnvArgs = Field(default_factory=EnvArgs)
