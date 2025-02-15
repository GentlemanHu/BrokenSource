"""
<div align="justify">

<div align="center">
  <h1>♻️ BrokenEnum ♻️</h1>

  **Smarter** Python **Enum classes** with builtin **Automation** and **Safety**
</div>

<br>

# 🔥 Description

This package adds lots of utilities to the standard `Enum` class in Python

- **Convenient**: Find members by name or value (or both)
- **Cycling**: You can cycle through the options of an enum
- **Fast**: Functions are cached with `functools.lru_cache`

<br>

# 🚀 Examples
```python
# Import package
from Broken import BrokenEnum

# Define a render quality enum
class Quality(BrokenEnum):
    Low    = 0
    Medium = 1
    High   = 2

# Get values from key or name
assert Quality.get(0)     == Quality.Low
assert Quality.get("Low") == Quality.Low
assert Quality.get("low") == Quality.Low
assert Quality(2)         == Quality.High

# It is safe to .get(member) themselves
assert Quality.get(Quality.Low) == Quality.Low

# If you want to search only by value or name
assert Quality.from_value(0)       == Quality.Low
assert Quality.from_value("low")   == None
assert Quality.from_name("medium") == Quality.Medium
Quality.from_name(2) # Raises ValueError

# Cycling through the options
assert Quality.Low.next()         == Quality.Medium
assert Quality.High.next()        == Quality.Low
assert Quality.Low.next(offset=2) == Quality.High

# Can cycle through the options in reverse and from member
value = Quality.Low
assert value.previous() == Quality.High
assert (value := value.previous(2)) == Quality.Medium

# Getting list of members or names, keys
assert Quality.values  == (0, 1, 2)
assert Quality.names   == ("Low", "Medium", "High")
assert Quality.keys    == ("Low", "Medium", "High")
assert Quality.options == (
    Quality.Low,
    Quality.Medium,
    Quality.High,
)

# Get tuples or key, value
assert Quality.items == (
    ("Low",    0),
    ("Medium", 1),
    ("High",   2),
)

# Get options as a dictionary
assert Quality.dict == dict(Low=0, Medium=1, High=2)
```

</div>
"""
import enum
import functools
from typing import Any, Dict, Optional, Self, Tuple, Union

import attrs


class BrokenEnum(enum.Enum):

    # # Initialization

    @classmethod
    @functools.lru_cache(typed=True)
    def from_name(cls, name: str, *, lowercase: bool=True, must: bool=False) -> Optional[enum.Enum]:
        """
        Get enum members from their name

        Example:
            ```python
            class Fruits(BrokenEnum):
                Apple  = "Maçã"
                Banana = "Banana"
                Orange = "Laranja"

            Fruits.from_name("Apple")  -> Fruits.Apple
            Fruits.from_name("apple")  -> Fruits.Apple
            ```

        Args:
            name: Name of the member to get
            lowercase: Whether to lowercase the name and key before matching
            must: Whether to raise an error if the member is not found

        Returns:
            The enum member with the given name if found, None otherwise
        """
        # Key value must be a string
        if not isinstance(name, str):
            raise TypeError(f"Expected str, got {type(name).__name__} on BrokenEnum.from_name()")

        # Optionally lowercase name for matching
        name = name.lower() if lowercase else name

        # Search for the member by key
        for key, value in cls._member_map_.items():
            if (key.lower() if lowercase else key) == name:
                return value

        # Raise an error if the member was not found
        if must: raise ValueError(f"Member with name '{name}' not found on BrokenEnum.from_name()")

    @classmethod
    @functools.lru_cache(typed=True)
    def from_value(cls, value: Any, *, must: bool=False) -> Optional[enum.Enum]:
        """
        Get enum members from their value (name=value)

        Example:
            ```python
            class Fruits(BrokenEnum):
                Apple  = "Maçã"
                Banana = "Banana"
                Orange = "Laranja"

            Fruits.from_value("Maçã")   -> Fruits.Apple
            Fruits.from_value("Banana") -> Fruits.Banana
            ```

        Args:
            `value`: Value of the member to get
            `must`:  Whether to raise an error if the member is not found

        Returns:
            The enum member with the given value if found, None otherwise
        """
        # Scroll through all members, match by value
        for option in cls:
            if value == option.value:
                return option

        # Raise an error if the member was not found
        if must: raise ValueError(f"Member with value '{value}' not found on BrokenEnum.from_value()")

    # # Utilities properties

    # Values

    @classmethod
    @property
    @functools.lru_cache(typed=True)
    def members(cls) -> Tuple[enum.Enum]:
        """Get all members of the enum"""
        return tuple(cls)

    @classmethod
    @property
    @functools.lru_cache(typed=True)
    def options(cls) -> Tuple[enum.Enum]:
        """Get all members of the enum"""
        return cls.members

    @classmethod
    @property
    @functools.lru_cache(typed=True)
    def values(cls) -> Tuple[Any]:
        """Get all values of the enum (name=value)"""
        return tuple(member.value for member in cls)

    # Key/names properties

    @classmethod
    @property
    @functools.lru_cache(typed=True)
    def keys(cls) -> Tuple[str]:
        """Get all 'keys' of the enum (key=value)"""
        return tuple(member.name for member in cls)

    @classmethod
    @property
    @functools.lru_cache(typed=True)
    def names(cls) -> Tuple[str]:
        """Get all names of the enum (name=value)"""
        return cls.keys

    @classmethod
    @property
    @functools.lru_cache(typed=True)
    def names_lower(cls) -> Tuple[str]:
        """Get all names of the enum (name=value) in lowercase"""
        return tuple(name.lower() for name in cls.keys)

    # Items and dict-like

    @classmethod
    @property
    @functools.lru_cache(typed=True)
    def items(cls) -> Tuple[Tuple[str, Any]]:
        """Get the tuple of (name, value) of all members of the enum"""
        return tuple((member.name, member.value) for member in cls)

    @classmethod
    @property
    @functools.lru_cache(typed=True)
    def as_dict(cls) -> Dict[str, Any]:
        """Get the dictionary of key: value of all members of the enum"""
        return dict(cls.items)

    @classmethod
    @functools.lru_cache(typed=True)
    def to_dict(cls) -> Dict[str, Any]:
        """Alias for .as_dict, but as a method"""
        return cls.as_dict

    # # Smart methods

    @classmethod
    @functools.lru_cache(typed=True)
    def get(cls, value: Union[str, enum.Enum, Any], *, lowercase: bool=True) -> Optional[Self]:
        """
        Get enum members from their value, name or themselves

        Example:
            ```python
            # Inherit from this package
            class Multivalue(BrokenEnum):
                Color  = "blue"
                Hat    = False
                Age    = 9000
                Height = 1.41
                Emoji  = "🔱"

            # Use the .get method
            Multivalue.get("blue")   -> Multivalue.Color
            Multivalue.get(False)    -> Multivalue.Hat
            Multivalue.get("Height") -> Multivalue.Height
            Multivalue.get("height") -> Multivalue.Height

            # Use from a member itself
            Multivalue.get(Multivalue.Color) -> Multivalue.Color
            ```

        Args:
            `value`: Value to get the enum member from, can be the member's name or value

        Returns:
            The enum member with the given value if found, None otherwise
        """

        # Value is already a member of the enum
        if isinstance(value, cls):
            return value

        # Value is a string
        elif isinstance(value, str):
            return cls.from_name(value, lowercase=lowercase) or cls.from_value(value)

        # Search by value
        return cls.from_value(value)

    @functools.lru_cache(typed=True)
    def next(self, value: Union[str, enum.Enum]=None, offset: int=1) -> Self:
        """
        Get the next enum member (in position) from their value, name or themselves

        Example:
            ```python
            # Inherit from this package
            class Platform(BrokenEnum):
                Linux   = "linux"
                Windows = "windows"
                MacOS   = "macos"

            # Cycle through options
            Platform.next("linux")   -> Platform.Windows
            Platform.next("windows") -> Platform.MacOS
            Platform.next("macos")   -> Platform.Linux
            (...)
            ```

        Args:
            `value`: Value to get the next enum member from, can be the Option's name or value

        Returns:
            The next enum member (in position) from the given value
        """
        cls   = type(self)
        value = cls.get(value or self)
        return cls.options[(cls.options.index(value) + offset) % len(cls)]

    def __next__(self) -> Self:
        """Alias for .next, but as a method"""
        return self.next()

    @functools.lru_cache(typed=True)
    def previous(self, value: Union[str, enum.Enum]=None, offset: int=1) -> Self:
        """
        Get the previous enum member (in position) from their value, name or themselves

        Example:
            ```python
            # Inherit from this package
            class Platform(BrokenEnum):
                Linux   = "linux"
                Windows = "windows"
                MacOS   = "macos"

            # Cycle through options
            Platform.previous("linux")   -> Platform.MacOS
            Platform.previous("windows") -> Platform.Linux
            Platform.previous("macos")   -> Platform.Windows
            (...)
            ```

        Args:
            `value`: Value to get the previous enum member from, can be the Option's name or value

        Returns:
            The previous enum member (in position) from the given value
        """
        cls   = type(self)
        value = cls.get(value or self)
        return cls.options[(cls.options.index(value) - offset) % len(cls)]

    # # Advanced functions

    @classmethod
    def extend(cls, name: str, value: Any) -> Self:
        """
        Dynamically extend the enum with a new member (name=value)

        Example:
            ```python
            # Inherit from this package
            class Platform(BrokenEnum):
                ...

            # Extend the enum
            Platform.extend("Android", "android")

            # Use the new member
            platform = Platform.Android
            ```

        Args:
            `name`:  Name of the new member
            `value`: Value of the new member

        Returns:
            Fluent interface, the class that was extended
        """
        raise NotImplementedError("This method is not implemented yet")

    def field(self, **kwargs) -> attrs.Attribute:
        """
        Make a attrs.field() with this member as default and enum class's get method as converter

        Example:
            ```python
            class Platform(BrokenEnum):
                Linux   = "linux"
                Windows = "windows"
                MacOS   = "macos"

            @define
            class Computer:
                os: Platform = Platform.Linux.field()

            # Any setattr will be redirected to the enum's get method
            computer = Computer()
            computer.os = "linux" # Ok
            computer.os = "dne"   # Not ok
            ```

        Args:
            `kwargs`: Keyword arguments to pass to the field, may override default and converter
        """
        return attrs.field(default=self, converter=self.__class__.get, **kwargs)
