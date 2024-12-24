import re
import typing
from typing import Any, Optional, List, Dict

import numpy as np
import rstr
from gymnasium.spaces import Space, Box, Text
from gymnasium.spaces.utils import flatdim, flatten, flatten_space, unflatten
from numpy.typing import NDArray

from collaborative_gym.utils.string import reconstruct_string_from_regex_pattern

MAX_UNICODE_CODEPOINT = 0x10FFFF
MAX_UNICODE_LENGTH = 2**32 - 1


class MultiSpace(Space[Any]):
    """A Space instance that accepts multiple sub-spaces.
    A sample is considered valid if it is valid in at least one of the sub-spaces.
    """

    def __init__(
        self,
        spaces: typing.Iterable[Space[Any]],
        seed: int | typing.Sequence[int] | np.random.Generator | None = None,
    ):
        r"""Constructor of :class:`MultiSpace` space.

        The generated instance will represent the union of :math:`\text{spaces}[0] \times ... \times \text{spaces}[-1]`.

        Args:
            spaces (Iterable[Space]): The spaces that are involved in the cartesian product.
            seed: Optionally, you can use this argument to seed the RNGs of the ``spaces`` to ensure reproducible sampling.
        """
        assert isinstance(spaces, typing.Iterable), f"{spaces} is not an iterable"
        self.spaces = tuple(spaces)
        # assert len(self.spaces) > 0, "Empty `MultiSpace` spaces are not supported."
        for space in self.spaces:
            assert isinstance(
                space, Space
            ), f"{space} does not inherit from `gymnasium.Space`. Actual Type: {type(space)}"
        super().__init__(None, None, seed)

    @property
    def is_np_flattenable(self):
        """Checks whether this space can be flattened to a :class:`spaces.Box`."""
        return all(space.is_np_flattenable for space in self.spaces)

    def seed(self, seed: int | tuple[int, ...] | None = None) -> tuple[int, ...]:
        """Seed the PRNG of this space and all subspaces.

        Depending on the type of seed, the subspaces will be seeded differently

        * ``None`` - All the subspaces will use a random initial seed
        * ``Int`` - The integer is used to seed the :class:`Tuple` space that is used to generate seed values for each of the subspaces. Warning, this does not guarantee unique seeds for all the subspaces.
        * ``Tuple[int, ...]`` - Values used to seed the subspaces, first value seeds the MultiSpace and subsequent seed the subspaces. This allows the seeding of multiple composite subspaces ``[42, 54, ...]``.

        Args:
            seed: An optional int or tuple of ints to seed the MultiSpace space and subspaces. See above for more details.

        Returns:
            A tuple of ints used to seed the MultiSpace space and subspaces
        """
        if seed is None:
            super_seed = super().seed(None)
            return (super_seed,) + tuple(space.seed(None) for space in self.spaces)
        elif isinstance(seed, int):
            super_seed = super().seed(seed)
            subseeds = self.np_random.integers(
                np.iinfo(np.int32).max, size=len(self.spaces)
            )
            # this is necessary such that after int or list/tuple seeding, the OneOf PRNG are equivalent
            super().seed(seed)
            return (super_seed,) + tuple(
                space.seed(int(subseed))
                for space, subseed in zip(self.spaces, subseeds)
            )
        elif isinstance(seed, (tuple, list)):
            if len(seed) != len(self.spaces) + 1:
                raise ValueError(
                    f"Expects that the subspaces of seeds equals the number of subspaces + 1. Actual length of seeds: {len(seed)}, length of subspaces: {len(self.spaces)}"
                )

            return (super().seed(seed[0]),) + tuple(
                space.seed(subseed) for space, subseed in zip(self.spaces, seed[1:])
            )
        else:
            raise TypeError(
                f"Expected None, int, or tuple of ints, actual type: {type(seed)}"
            )

    def sample(self, mask: tuple[Any | None, ...] | None = None) -> tuple[int, Any]:
        """Generates a single random sample inside this space.

        Args:
            mask: An optional tuple of optional masks for each of the subspace's samples,
                expects the same number of masks as spaces

        Returns:
            Tuple of the subspace's samples
        """
        chosen_space = np.random.choice(len(self.spaces))
        subspace = self.spaces[chosen_space]
        if mask is not None:
            assert isinstance(
                mask, tuple
            ), f"Expected type of mask is tuple, actual type: {type(mask)}"
            assert len(mask) == len(
                self.spaces
            ), f"Expected length of mask is {len(self.spaces)}, actual length: {len(mask)}"

            mask = mask[chosen_space]

        return chosen_space, subspace.sample(mask=mask)

    def contains(self, x: Any) -> bool:
        """Return boolean specifying if x is a valid member of this space."""
        return any(space.contains(x) for space in self.spaces)

    def __repr__(self) -> str:
        """Gives a string representation of this space."""
        return "MultiSpace(" + ", ".join([str(s) for s in self.spaces]) + ")"

    def to_jsonable(self, sample_n: typing.Sequence[Any]) -> list[list[Any]]:
        """Convert a batch of samples from this space to a JSONable data type."""
        return [
            [self.spaces[i].to_jsonable([subsample])[0]]
            for (i, subsample) in enumerate(sample_n)
        ]

    def from_jsonable(self, sample_n: list[Any]) -> list[tuple[Any, ...]]:
        """Convert a JSONable data type to a batch of samples from this space."""
        return [
            (self.spaces[space_idx].from_jsonable([jsonable_sample])[0],)
            for space_idx, jsonable_sample in enumerate(sample_n)
        ]

    def __getitem__(self, index: int) -> Space[Any]:
        """Get the subspace at specific `index`."""
        return self.spaces[index]

    def __len__(self) -> int:
        """Get the number of subspaces that are involved in the cartesian product."""
        return len(self.spaces)

    def __eq__(self, other: Any) -> bool:
        """Check whether ``other`` is equivalent to this instance."""
        return isinstance(other, MultiSpace) and self.spaces == other.spaces


class Unicode(Text):
    """A space representing a unicode string.
    Borrowed from https://github.com/Farama-Foundation/miniwob-plusplus/blob/553daee55ea0b2cc32b181a474083ab4cad782a1/miniwob/spaces.py

    Unicode is a replacement for the Text space in Gymnasium, with the
    following differences:

    - Each character can be an arbitrary unicode character.
    - The sample method samples from the specified character set.
    """

    def contains(self, x: Any) -> bool:
        """Return boolean specifying if x is a valid member of this space."""
        # Do not check the character set.
        return isinstance(x, str) and self.min_length <= len(x) <= self.max_length

    def __repr__(self) -> str:
        """Gives a string representation of this space."""
        return f"Unicode({self.min_length}, {self.max_length})"

    def __eq__(self, other: Any) -> bool:
        """Check whether ``other`` is equivalent to this instance."""
        return (
            isinstance(other, Unicode)
            and self.min_length == other.min_length
            and self.max_length == other.max_length
        )


class UnicodeWithRegexPattern(Text):
    """A space representing a unicode string that satisfies a regex pattern.

    This space is used to define action in a string format that can be generated by language models.
    """

    def __init__(
        self,
        max_length: int,
        regex_pattern: re.Pattern,
        params: List[str],
        machine_readable_identifier: Any,
        *,
        min_length: int = 1,
        human_readable_name: Optional[str] = None,
        human_readable_description: Optional[str] = None,
    ):
        """
        Args:
            max_length: The maximum length of the string.
            regex_pattern: The regex pattern that the string should satisfy.
            params: The parameters that the free parts in the pattern represent, need to be in the same order as the
                free parts in the pattern.
            machine_readable_identifier: A machine-readable identifier for the space.
            min_length: The minimum length of the string.
            human_readable_name: A human-readable name for the space.
            human_readable_description: A human-readable description of the space.
        """
        super().__init__(max_length=max_length, min_length=min_length)
        self.pattern = regex_pattern
        self.params = params
        self.machine_readable_identifier = machine_readable_identifier
        self.human_readable_name = human_readable_name
        self.human_readable_description = human_readable_description

    def contains(self, x: Any) -> bool:
        """Return boolean specifying if x is a valid member of this space."""
        if not isinstance(x, str) or not self.min_length <= len(x) <= self.max_length:
            return False
        return self.pattern.fullmatch(x) is not None

    def __repr__(self) -> str:
        """Gives a string representation of this space."""
        return (
            f"UnicodeWithRegexPattern({self.min_length}, {self.max_length}, "
            f"regex_pattern={self.pattern.pattern}, "
            f"human_readable_name={self.human_readable_name}, "
            f"human_readable_description={self.human_readable_description})"
        )

    def __eq__(self, other: Any) -> bool:
        """Check whether ``other`` is equivalent to this instance."""
        return (
            isinstance(other, UnicodeWithRegexPattern)
            and self.min_length == other.min_length
            and self.max_length == other.max_length
            and self.pattern.pattern == other.pattern.pattern
        )

    def sample(
        self,
        mask: None | (tuple[int | None, NDArray[np.int8] | None]) = None,
    ) -> str:
        """Return a random sample from this space."""
        return rstr.xeger(self.pattern)

    def parse(self, x: Any) -> Dict[str, str] | None:
        """Parse the regex pattern to get the parameters."""
        match = self.pattern.fullmatch(x)
        if match:
            return {param: val for param, val in zip(self.params, match.groups())}
        return None

    def construct_action_string_from_params(self, **kwargs):
        """Constructs a valid action string from the given parameters."""
        try:
            param_values = [kwargs[param] for param in self.params]
        except KeyError as e:
            raise ValueError(f"Missing parameter: {e}")
        return reconstruct_string_from_regex_pattern(self.pattern, param_values)

    def execute_from_params(self, **kwargs):
        """Executes the action with the given parameters."""
        action = self.construct_action_string_from_params(**kwargs)
        return self(action)

    def dump_json(self):
        """Dumps the space information to a json object."""
        return {
            "max_length": self.max_length,
            "pattern": self.pattern.pattern,
            "params": self.params,
            "machine_readable_identifier": self.machine_readable_identifier,
            "min_length": self.min_length,
            "human_readable_name": self.human_readable_name,
            "human_readable_description": self.human_readable_description,
        }

    @classmethod
    def from_json(cls, json_obj: dict):
        """Constructs a UnicodeWithRegexPattern from a json object."""
        return cls(
            max_length=json_obj["max_length"],
            regex_pattern=re.compile(json_obj["pattern"]),
            params=json_obj["params"],
            machine_readable_identifier=json_obj["machine_readable_identifier"],
            min_length=json_obj["min_length"],
            human_readable_name=json_obj["human_readable_name"],
            human_readable_description=json_obj["human_readable_description"],
        )

    def __call__(self, x: Any):
        """Parses a valid action and executes it."""
        pass
