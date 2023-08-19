from dataclasses import dataclass
# from enum import Enum
from typing import Union, Optional, Callable, Any, Sequence
from os.path import basename as os_path_basename
from functools import partial
# import pprint

import levenshtein

# DEV SETUP

_DEBUG = False
# _DEBUG = True


def debug_trace(*args: Any, **kwargs: Any) -> None:
    if _DEBUG:
        # pprint.pprint("  DEBUG: ", compact=True)
        # pprint.pprint(*args, **kwargs)
        print("    DEBUG: ", *args, **kwargs)


debug_trace("If you don't want debug logs, change the `_DEBUG` variable in flags.py.")


# FLAG TYPES:

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
            f"Tried to access the data for flag {self.flag} before assigning a value to it.\
                Try using FlagHandler.parse(...)."
        return self._data

    @data.setter
    def data(self, value: str | int) -> None:
        try:
            self._data = int(value)
        except ValueError:
            raise ValueError(f"`{value}` is not a valid value for an `IntFlag`.")
        except Exception as e:
            raise e


@dataclass
class BoolFlag(Flag):
    _data: Optional[bool] = None

    def __post_init__(self) -> None:
        if self.default_value is None:
            self.default_value = False

    @property
    def data(self) -> Optional[bool]:
        assert self._data is not None, \
            f"Tried to access the data for flag {self.flag} before assigning \
                a value to it. Try using FlagHandler.parse(...)."
        return self._data

    @data.setter
    def data(self, value: str | bool) -> None:
        if value in [False, "false", "False", "FALSE" "0", "f", "F"]:
            self._data = False
        elif value in [True, "true", "True", "TRUE" "1", "t", "T"]:
            self._data = True
        else:
            raise ValueError(f"`{value}` is not a valid value for a `BoolFlag`.")


@dataclass
class StringFlag(Flag):
    _data: Optional[str] = None

    @property
    def data(self) -> str:
        assert self._data is not None, \
            f"Tried to access the data for flag {self.flag} before assigning \
                a value to it. Try using FlagHandler.parse(...)."
        return self._data

    @data.setter
    def data(self, value: str) -> None:
        try:
            self._data = str(value)
        except ValueError:
            raise ValueError(f"`{value}` is not a valid value for a `StringFlag`.")
        except Exception as e:
            raise e


def _assert_that_flag_types_havent_changed(expected_number_of_types: int) -> None:
    flag_subclasses = Flag.__subclasses__()
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
        self.help_flag: Optional[BoolFlag] = None  # This is special because we can set it automatically
        self.output_function: Callable[[str], Any] = partial(print, end="")

    def _check_if_flag_already_exists(self, flag_name: str, aliases: Optional[list[str]] = None) -> None:
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
        flag = self._create_typed_flag(IntFlag, flag_name, description, default_value, optional, aliases)
        assert isinstance(flag, IntFlag)
        return flag

    def str_flag(self, flag_name: str, description: str,
                 default_value: Optional[str | int] = None, optional: bool = True,
                 aliases: Optional[list[str]] = None) -> StringFlag:
        flag = self._create_typed_flag(StringFlag, flag_name, description, default_value, optional, aliases)
        assert isinstance(flag, StringFlag)
        return flag

    def bool_flag(self, flag_name: str, description: str,
                  default_value: Optional[str | int] = None, optional: bool = True,
                  aliases: Optional[list[str]] = None) -> BoolFlag:
        flag = self._create_typed_flag(BoolFlag, flag_name, description, default_value, optional, aliases)
        assert isinstance(flag, BoolFlag)
        return flag

    def set_program_description(self, program_description: str) -> None:
        self.program_description = program_description

    def _find(self, flag_name: str) -> Optional[flag_classes]:
        for flag in self.flags:
            if flag_name == flag.flag or flag.aliases is not None and flag_name in flag.aliases:
                return flag
        return None

    def parse(self, args: Sequence[str]) -> Optional[dict[str, flag_value]]:
        debug_trace("All my flags: ")
        debug_trace(self.flags)
        debug_trace(f"ARGS: {args}")

        result: dict[str, flag_value] = {}

        program_path = args[0]

        if not self.help_flag:
            # Generate a help flag if there isn't one already.
            self._add_default_help_flag()

        # handle all args
        i = 1
        while i < len(args):
            arg = args[i]
            debug_trace(f"ARG: {arg}")
            if (flag := self._find(arg)):
                debug_trace(f"found flag {flag.flag}")
                _assert_that_flag_types_havent_changed(3)
                if isinstance(flag, (IntFlag, StringFlag)):
                    assert i+1 < len(args), f"Expected more arguments for flag `{arg}`."
                    flag.data = args[i+1]  # Try to assign the next token to the flag data.
                    result[flag.flag] = flag.data
                    i += 1  # Skip next one, since we already processed it.
                elif isinstance(flag, BoolFlag):
                    flag.data = True
                    result[flag.flag] = flag.data
                else:
                    assert False, "Unreachable"
            else:  # bad flag, don't know what to do!
                if (candidates := self._find_closest_flags(arg)):  # if not empty
                    self.output_function(f"Unexpected flag `{arg}`. Maybe you meant:\n")
                    for candidate in candidates:
                        self.output_function(self._describe_flag(candidate) + "\n")
                raise ValueError(f"Couldn't understand token `{arg}`. It is not a valid flag in this program.")
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

        if len(required_but_not_given_flags) > 0:
            debug_trace(required_but_not_given_flags)
            missing_flags = ", ".join(flag.flag for flag in required_but_not_given_flags)
            # If user asked for help, ignore everything and just show the documentation:
            if i == 1 or result.get('-h', False):
                # If the user didn't pass any arguments (when they should have)
                # or if they explicitly asked for help, show the help.
                self.output_function(self._generate_help_message(program_path))
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
                if isinstance(flag, BoolFlag):
                    pass
                elif isinstance(flag, IntFlag):
                    usage_message += " <int>"
                elif isinstance(flag, StringFlag):
                    usage_message += " <string>"
                else:
                    debug_trace(flag)
                    assert False, "Unreachable"
            elif not has_optional_flags:
                has_optional_flags = True
        usage_message += " [OPTIONAL-FLAGS]" if has_optional_flags else ""
        return usage_message

    def set_help_flag(self, flag_name: str, description: str,
                      aliases: Optional[list[str]] = None) -> None:
        # assert False, "Not implemented"
        flag = self.bool_flag(flag_name, description, default_value=False, optional=True, aliases=aliases)
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
        default = f" Default Value: `{flag.default_value}`" if flag.default_value is not None else ""
        return f"      * {flag_and_argument:<15} : {description:<40}{alias_list:20}{default:<30}"

    def _find_closest_flags(self, attempted_flag: str, tolerance: int = 3, limit: int = 5) -> list[flag_classes]:
        """Finds the closest flag to the input string, based on a string distance."""
        keyed_candidates: list[tuple[flag_classes, int]] = []
        for flag in self.flags:
            shortest_distance = tolerance + 1
            if (distance := string_distance(attempted_flag, flag.flag)) < shortest_distance:
                shortest_distance = distance
            if flag.aliases is not None:
                for alias in flag.aliases:
                    if (distance := string_distance(attempted_flag, alias)) < shortest_distance:
                        shortest_distance = distance
            if shortest_distance <= tolerance:
                keyed_candidates.append((flag, shortest_distance))

        return [c[0] for c in sorted(keyed_candidates, key=lambda t: t[1])][:limit]


def string_distance(str1: str, str2: str) -> int:
    """Computes the distance between two strings."""
    # TODO: Let user customize the edit distance function
    return levenshtein.levenshtein_distance(str1, str2)
