from dataclasses import dataclass
from typing import Union, Optional, Callable, Any, Sequence, cast
from typing_extensions import assert_never
from os.path import basename as os_path_basename
from functools import partial
import warnings

# DEV SETUP

_FLAGS_DEBUG = False
# __FLAGS_DEBUG = True


def _flags_debug_trace(*args: Any, **kwargs: Any) -> None:
    if _FLAGS_DEBUG:
        print("    DEBUG: ", *args, **kwargs)


_flags_debug_trace("If you don't want debug logs, change the `_DEBUG` variable in flags.py.")


# FLAG TYPES:

# TODO: Change Flags to have a "take" method that tries to parse the next argument(s), \
# i.e. change the responsibility to parse the argument to the flags instead of the \
# FlagHandler. This will probably make implementing "greedy" flags trivial.


# TODO: Refactor code duplication in errors for the diffent kinds of typed flags.

@dataclass
class Flag:
    flag: str
    aliases: Optional[list[str]]
    description: str
    default_value: Optional['flag_value']
    optional: bool


@dataclass
class IntFlag(Flag):
    _data: Optional[int] = None

    @property
    def data(self) -> int:
        assert self._data is not None, \
            f"""Tried to access the data for flag `{self.flag}` before assigning a value to it. \
Try using FlagHandler.parse(...)."""
        return self._data

    @data.setter
    def data(self, value: str | int) -> None:
        assert value is not None, "You can't set the flag's data to a None value."
        try:
            self._data = int(value)
            # TODO: There's nothing actually enforcing value is an integer. This would just truncate floats, for example.
        except ValueError:
            raise ValueError(
                f"`{value}` is not a valid value for an `IntFlag`.")
        except Exception as e:
            raise e


@dataclass
class BoolFlag(Flag):
    _data: Optional[bool] = None

    def __post_init__(self) -> None:
        if self.default_value is None:
            self.default_value = False

    @property
    def data(self) -> bool:
        assert self._data is not None, \
            f"""Tried to access the data for flag `{self.flag}` before assigning a value to it. \
Try using FlagHandler.parse(...)."""
        return self._data

    @data.setter
    def data(self, value: str | bool) -> None:
        assert value is not None, "You can't set the flag's data to a None value."
        if value in [False, "false", "False", "FALSE" "0", "f", "F"]:
            self._data = False
        elif value in [True, "true", "True", "TRUE" "1", "t", "T"]:
            self._data = True
        else:
            raise ValueError(
                f"`{value}` is not a valid value for a `BoolFlag`.")


@dataclass
class StringFlag(Flag):
    _data: Optional[str] = None

    @property
    def data(self) -> str:
        assert self._data is not None, \
            f"""Tried to access the data for flag `{self.flag}` before assigning a value to it. \
Try using FlagHandler.parse(...)."""
        return self._data

    @data.setter
    def data(self, value: str) -> None:
        assert value is not None, "You can't set the flag's data to a None value."
        try:
            self._data = str(value)
        except ValueError:
            raise ValueError(
                f"`{value}` is not a valid value for a `StringFlag`.")
        except Exception as e:
            raise e


def _assert_that_flag_types_havent_changed(expected_number_of_types: int) -> None:
    # Used in places that hard-coded some expectation for how many and which flags there are.
    # If more flag types are added, this will hopefully flag the places that need to be changed.

    flag_subclasses = Flag.__subclasses__()
    # This method of counting subclasses is naive and doesn't handle
    # runtime/user changes or sub-subclasses.
    assert len(flag_subclasses) == expected_number_of_types, \
        "Expected a different number of supported flag types (FlagType enum)"


# type aliases
_assert_that_flag_types_havent_changed(3)
flag_classes = IntFlag | BoolFlag | StringFlag
flag_classes_type = type[flag_classes]
flag_value = Union[int, bool, str]

# Used to show "usage" for each flag
flag_type_arguments: dict[flag_classes_type, str] = {
    IntFlag: "<int>",
    BoolFlag: "",
    StringFlag: "<string>",
}


class FlagHandler:
    def __init__(self, program_description: Optional[str] = None):
        self.program_description: str = program_description \
                                    if program_description is not None\
                                    else ""

        # Instance defaults:
        self.flags: list[flag_classes] = []
        self.help_flag: Optional[BoolFlag] = None
        # The help flag is special because we can set it automatically
        self.output_function: Callable[[str], Any] = partial(print, end="")
        self.string_distance_function: Callable[[str, str], int] = naive_levenshtein_distance

    def _check_if_flag_already_exists(self, flag_name: str,
                                      aliases: Optional[list[str]] = None) -> None:
        if self._find(flag_name):
            raise ValueError(f"The flag {flag_name} is already in use. \
                Please choose another name for this flag.")
        if aliases is not None:
            for alias in aliases:
                if self._find(alias):
                    raise ValueError(f"The flag alias {alias} is already in use. \
                        Please choose another alias for this flag.")

    def _create_typed_flag(self, flag_cls: flag_classes_type, flag_name: str, description: str,
                           default_value: Optional[str | int] = None, optional: bool = True,
                           aliases: Optional[list[str]] = None) -> flag_classes:
        self._check_if_flag_already_exists(flag_name, aliases)
        flag = flag_cls(flag_name, aliases, description, default_value, optional)
        self.flags.append(flag)
        return self.flags[-1]

    def int_flag(self, flag_name: str, description: str,
                 default_value: Optional[str | int] = None, optional: bool = True,
                 aliases: Optional[list[str]] = None) -> IntFlag:
        """Create a flag that can accept int data.

        Args:
            flag_name (str): The main name for the flag.
            description (str): A short description of what the flag is used for.
            default_value (Optional[str  |  int], optional): The default value for the flag. \
                Defaults to None.
            optional (bool, optional): Toggles if the flag is optional. Defaults to True.
            aliases (Optional[list[str]], optional): A list of strings of alternative aliases for\
                this flag. Defaults to None.

        Returns:
            IntFlag: An IntFlag. To access the data, FlagHandler.parse, then use access the \
                flag.data attribute.
        """
        flag = self._create_typed_flag(IntFlag, flag_name, description,
                                       default_value, optional, aliases)
        flag = cast(IntFlag, flag)
        return flag

    def str_flag(self, flag_name: str, description: str,
                 default_value: Optional[str | int] = None, optional: bool = True,
                 aliases: Optional[list[str]] = None) -> StringFlag:
        """Create a flag that can accept string data.

        Args:
            flag_name (str): The main name for the flag.
            description (str): A short description of what the flag is used for.
            default_value (Optional[str  |  int], optional): The default value for the flag. \
                Defaults to None.
            optional (bool, optional): Toggles if the flag is optional. Defaults to True.
            aliases (Optional[list[str]], optional): A list of strings of alternative aliases for \
                this flag. Defaults to None.

        Returns:
            StringFlag: A StringFlag. To access the data, FlagHandler.parse, then use access the \
                flag.data attribute.
        """
        flag = self._create_typed_flag(StringFlag, flag_name, description,
                                       default_value, optional, aliases)
        flag = cast(StringFlag, flag)
        return flag

    def bool_flag(self, flag_name: str, description: str,
                  default_value: bool = False, optional: bool = True,
                  aliases: Optional[list[str]] = None) -> BoolFlag:
        """Create a flag that can accept bool data.

        Args:
            flag_name (str): The main name for the flag.
            description (str):  A short description of what the flag is used for.
            default_value (Optional[bool], optional): The default value for the flag. Defaults to \
                False.
            optional (bool, optional): Toggles if the flag is optional. Defaults to True.
            aliases (Optional[list[str]], optional): A list of strings of alternative aliases for \
                this flag. Defaults to None.

        Returns:
            BoolFlag: A BoolFlag. To access the data, FlagHandler.parse, then use access the \
                flag.data attribute.
        """
        flag = self._create_typed_flag(BoolFlag, flag_name, description,
                                       default_value, optional, aliases)
        flag = cast(BoolFlag, flag)
        return flag

    def set_program_description(self, program_description: str) -> None:
        self.program_description = program_description

    def _find(self, flag_name: str) -> Optional[flag_classes]:
        for flag in self.flags:
            if flag_name == flag.flag or flag.aliases is not None and flag_name in flag.aliases:
                return flag
        return None

    def parse(self, args: Sequence[str]) -> dict[str, flag_value]:
        """Parses the sequence of strings. Typical use is .parse(sys.argv), but you can pass \
            anything. Updates the data of the flags in place, but also returns \
            a dictionary with the values.

        Args:
            args (Sequence[str]): The sequence of strs to be parsed. \
                Each flag/word/value/token should be its own element of the array.

        Raises:
            ValueError: When it doesn't understand one of the parsed flags.

        Returns:
            dict[str, flag_value]: A dict mapping flags main names to their values.
        """
        _flags_debug_trace("All my flags: ")
        _flags_debug_trace(self.flags)
        _flags_debug_trace(f"ARGS: {args}")

        result: dict[str, flag_value] = {}

        program_path = args[0]  # Consumes index 0 already.

        if not self.help_flag:
            # Generate a help flag if there isn't one already.
            self._add_default_help_flag()
        help_requested = False

        # handle all args
        i = 1  # Since we consumed index 0 (program name).
        while i < len(args):
            arg = args[i]
            _flags_debug_trace(f"ARG: {arg}")
            if (flag := self._find(arg)):
                if flag.flag in result:
                    # We have parsed this flag before.
                    warnings.warn(f"Already parsed flag `{arg}`. Did you really mean to repeat this flag? The value will be set to the last instance of the argument.")
                    # TODO: only throw one warning per flag.
                    # Comment on above ^ This already happens. Maybe because warnings.warn doesn't throw additional warnings with the same message?
                # TODO: handle cases where overriding flags that already have values. e.g:
                # warnings.warn(f"The flag `{arg}` already has a value, despite having not been parsed this time. Now trying to overwrite the previous value with the new value.")
                _flags_debug_trace(f"found flag {flag.flag}")
                _assert_that_flag_types_havent_changed(3)
                match flag:
                    case IntFlag() | StringFlag():
                        assert i + 1 < len(args), f"Expected more arguments for flag `{arg}`."
                        # Try to assign the next token to the flag data.
                        flag.data = args[i+1]
                        result[flag.flag] = flag.data
                        i += 1  # Skip next one, since we already processed it.
                    case BoolFlag():
                        flag.data = True
                        result[flag.flag] = flag.data
                    case _ as unreachable:
                        assert_never(unreachable)
            else:  # bad flag, don't know what to do!
                if (candidates := self._find_closest_flags(arg)):  # if not empty
                    self.output_function(f"Unexpected flag `{arg}`. Maybe you meant:\n")
                    for candidate in candidates:
                        self.output_function(self._describe_flag(candidate) + "\n")
                    self.output_function("\n")
                raise ValueError(f"Couldn't understand token `{arg}`. It is not a valid flag in \
this program.")
            i += 1

        # check if any non-optional flags were forgotten:
        required_but_not_given_flags = []
        for flag in self.flags:
            if flag.flag in result:  # given
                continue
            elif flag.optional and flag.default_value is not None:  # optional and has default value
                flag.data = flag.default_value
                result[flag.flag] = flag.data
            else:  # required
                required_but_not_given_flags.append(flag)

        self.help_flag = cast(BoolFlag, self.help_flag)
        help_requested = self.help_flag.data  # read the data in the flag
        if len(required_but_not_given_flags) > 0 or help_requested:
            # If user asked for help, ignore everything and just show the documentation:
            if i == 1 or help_requested:
                # If the user didn't pass any arguments (when they should have)
                # or if they explicitly asked for help, show the help.
                self.output_function(self._generate_help_message(program_path))
            _flags_debug_trace(required_but_not_given_flags)
            missing_flags = ", ".join(flag.flag for flag in required_but_not_given_flags)
            assert len(required_but_not_given_flags) == 0, \
                f"You need to pass the following obligatory flags: {missing_flags}"

        return result

    def _generate_usage(self, program_path: str) -> str:
        has_optional_flags = False
        program_name = os_path_basename(program_path)  # Strip the folder path
        usage_message = f"USAGE: python {program_name}"
        for flag in self.flags:
            if not flag.optional:
                usage_message += f" {flag.flag}"
                _assert_that_flag_types_havent_changed(3)
                match flag:
                    case BoolFlag():
                        pass
                    case IntFlag():
                        usage_message += " <int>"
                    case StringFlag():
                        usage_message += " <string>"
                    case _ as unreachable:
                        assert_never(unreachable)
            elif not has_optional_flags:
                has_optional_flags = True
        usage_message += " [OPTIONAL-FLAGS]" if has_optional_flags else ""
        return usage_message

    def set_help_flag(self, flag_name: str, description: str,
                      aliases: Optional[list[str]] = None) -> None:
        flag = self.bool_flag(flag_name, description,
                              default_value=False, optional=True, aliases=aliases)
        self.help_flag = flag  # Ok to override, since setting manually

        # Make sure `help` is the first flag (for order of printing):
        help_flag = self.flags.pop()
        self.flags.insert(0, help_flag)

    def _add_default_help_flag(self) -> None:
        if self.help_flag is None:
            # Don't override a manually set or previously automatically generated help flag.
            self.help_flag = self.bool_flag("-h", "Prints this help message.", aliases=["--help"])

            # Make sure `help` is the first flag (for order of printing):
            help_flag = self.flags.pop()
            self.flags.insert(0, help_flag)
        else:
            pass

    def _generate_help_message(self, program_path: str) -> str:
        help_message: str = ""
        help_message += self.program_description + "\n"  # Welcome message
        help_message += self._generate_usage(program_path) + "\n"  # USAGE

        for flag in self.flags:
            help_message += self._describe_flag(flag) + "\n"
        help_message += "\n"
        return help_message

    @staticmethod
    def _describe_flag(flag: flag_classes) -> str:
        alias_list = f" (alt.: {', '.join(flag.aliases)})" if flag.aliases else ""
        _assert_that_flag_types_havent_changed(3)
        argument = flag_type_arguments[type(flag)]
        description = f"{flag.description}"
        flag_and_argument = f"{flag.flag} {argument}"
        if flag.optional:
            flag_and_argument = "[" + flag_and_argument.strip() + "]"
        default = f" Default Value: `{flag.default_value}`" \
            if flag.default_value is not None \
            else ""

        return f"      * {flag_and_argument:<15} : {description:<40}{alias_list:20}{default:<30}"

    def _find_closest_flags(self, attempted_flag: str,
                            tolerance: int = 3, limit: int = 5) -> list[flag_classes]:
        """Finds the closest flags to the input string, based on a string distance."""
        assert tolerance >= 0
        assert limit >= 0

        # pairs of flag and the corresponding distances
        keyed_candidates: list[tuple[flag_classes, int]] = []

        for flag in self.flags:
            shortest_distance = tolerance + 1  # Initiate outside the tolerance
            # Update the shortest distance if new shortest distance was found
            shortest_distance = min(shortest_distance,
                                    self.string_distance_function(attempted_flag, flag.flag))
            if flag.aliases is not None and len(flag.aliases) > 0:
                # Find the shortest distance to any of the aliases
                min_alias_distance = min(self.string_distance_function(attempted_flag, alias)
                                         for alias in flag.aliases)
                # Update the shortest distance if new shortest distance was found
                # Could be done in one line, but this is easier to see.
                shortest_distance = min(shortest_distance, min_alias_distance)
            if shortest_distance <= tolerance:
                # This candidate is within the tolerance, so it may be returned.
                keyed_candidates.append((flag, shortest_distance))

        # Return the flags (only the flags, first item of tuple)
        # by ascending order of distance, up to the defined limit.
        return [c[0] for c in sorted(keyed_candidates, key=lambda t: t[1])][:limit]


def naive_levenshtein_distance(str1: str, str2: str) -> int:
    """Naive recursive implementation of Levenshtein distance

    Args:
        str1 (str): The origin string.
        str2 (str): The target string.

    Returns:
        int: The levenshtein distance.
    """

    # TODO: write the non-naive dynamic programming version of lev distance
    if len(str2) == 0:  # Goal is empty string
        return len(str1)  # Remove all characters
    elif len(str1) == 0:  # Start is empty string
        return len(str2)  # Add all the characters
    elif str1[0] == str2[0]:
        # Recurse on the non-matching section
        return naive_levenshtein_distance(str1[1:], str2[1:])
    else:
        return 1 + min(naive_levenshtein_distance(str1[1:], str2),
                       naive_levenshtein_distance(str1, str2[1:]),
                       naive_levenshtein_distance(str1[1:], str2[1:]))
