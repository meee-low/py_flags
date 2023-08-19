from dataclasses import dataclass
from enum import Enum
from typing import Union, Optional, Literal, Callable, Any, Sequence
import os
from functools import partial
import pprint

DEBUG = False
DEBUG = True

def debug_trace(*args: Any, **kwargs: Any) -> None:
    if DEBUG:
        # pprint.pprint("  DEBUG: ", compact=True)
        # pprint.pprint(*args, **kwargs)
        print("    DEBUG: ", *args, **kwargs)

class FlagType(Enum):
    INT = "int"
    BOOL = "bool"
    STRING = "str"

    @staticmethod
    def assert_that_still_handle_all_types(expected_number_of_types: int) -> None:
        assert len(FlagType) == expected_number_of_types, "Expected a different number of supported flag types (FlagType enum)"

    @staticmethod
    def from_value(s:str) -> 'FlagType':
        for flag_type in FlagType:
            if flag_type.value == s:
                return flag_type
        raise ValueError(f"Invalid value for FlagType enum. `{s}` not found.")

# type aliases
FlagType.assert_that_still_handle_all_types(3)
flag_value = Union[int, bool, str]
literal_flag_types = Literal["int", "bool", "str"]


@dataclass(frozen=True)
class Flag:
    flag: str
    aliases: Optional[list[str]]
    description: str
    default_value: Optional[flag_value]
    optional : bool
    kind: FlagType


class FlagHandler:
    def __init__(self, program_description:Optional[str]=None):
        self.program_description: str = program_description if program_description is not None else ""

        # Instance defaults:
        self.flags: list[Flag] = []
        self.add_default_help_flag()
        self.parsed: bool = False
        self.data: dict[str, flag_value] = {}
        self.output_function: Callable[[str], Any] = partial(print, end="")

    def add_flag(self, flag_name:str, description:str, kind:literal_flag_types,
                 default_value:Optional[str]=None, optional:bool=True, aliases:Optional[list[str]]=None) -> None:
        # Check if flag clashes with a previous flag:
        if self._find(flag_name):
            raise ValueError(f"The flag {flag_name} is already in use. Please choose another name for this flag.")
        if aliases is not None:
            for alias in aliases:
                if self._find(alias):
                    raise ValueError(f"The flag alias {alias} is already in use. Please choose another alias for this flag.")

        flag_type = FlagType.from_value(kind)

        FlagType.assert_that_still_handle_all_types(3)
        if default_value is not None:
            def_value = self._validate_value(flag_type, default_value)
        elif flag_type == FlagType.BOOL: # booleans are always defaulted to False, unless a default is given
            def_value = False
        else:
            def_value = None

        flag = Flag(flag_name, aliases, description, def_value, optional, flag_type)
        self.flags.append(flag)

    @staticmethod
    def _validate_value(flag_type:FlagType, value:str) -> flag_value:
        FlagType.assert_that_still_handle_all_types(3)
        match flag_type:
            case FlagType.BOOL:
                if value in ["false", "False", "FALSE" "0", "f", "F"]:
                    return False
                elif value in ["true", "True", "TRUE" "1", "t", "T"]:
                    return True
                else:
                    raise ValueError(f"{value} is not a valid value for {flag_type}.")
            case FlagType.INT:
                try:
                    return int(value)
                except ValueError as e:
                    raise e
                except Exception as e:
                    raise e
            case FlagType.STRING:
                return str(value)
            case _:
                debug_trace(flag_type)
                assert False, "Unreachable."

    def add_program_description(self, program_description: str) -> None:
        self.program_description = program_description

    def _find(self, flag_name:str) -> Optional[Flag]:
        for flag in self.flags:
            if flag_name == flag.flag or flag.aliases is not None and flag_name in flag.aliases:
                return flag
        return None

    def parse(self, program_name:str, args:Sequence[str]) -> Optional[dict[str, flag_value]]:
        if self.parsed:
            return self.data

        debug_trace("All my flags: ")
        debug_trace(self.flags)
        debug_trace(f"ARGS: {args}")

        # handle all args
        i = 0
        while i < len(args):
            arg = args[i]
            debug_trace(f"ARG: {arg}")
            if (flag := self._find(arg)):
                debug_trace(f"found flag {flag.flag}")
                FlagType.assert_that_still_handle_all_types(3)
                debug_trace(flag.kind)
                debug_trace(FlagType.STRING)
                debug_trace(flag.kind == FlagType.STRING)
                match flag.kind:
                    case FlagType.BOOL:
                        debug_trace(f"it's type bool")
                        self.data[flag.flag] = True
                        #TODO: handle dumb people passing -flag TRUE/FALSE for boolean flags
                    case FlagType.INT | FlagType.STRING:
                        assert i + 1 < len(args), f"Insufficient values passed for flag {arg}!"
                        debug_trace("Either int or str")
                        try:
                            debug_trace("next one: ", args[i+1])
                            value = self._validate_value(flag.kind, args[i+1])
                            debug_trace("value", value)
                            self.data[flag.flag] = value
                            i += 1
                            debug_trace("data: ", self.data)
                        except ValueError as e: #TODO: Better error report
                            raise e
                        except Exception as e:
                            raise e
                    case _:
                        debug_trace("ARG:", arg)
                        debug_trace("flag:", flag)
                        debug_trace(flag.kind)
                        assert False, "Unreachable"
            else: # bad flag, don't know what to do!
                self.output_function(f"Couldn't understand token {arg}. It is not a valid flag in this program.")
                if (candidates := self._find_closest_flags(arg)):
                    self.output_function(" Maybe you meant:\n")
                    for candidate in candidates:
                        self.output_function(f"  - {candidate.flag}")
            i += 1

        # If user asked for help, ignore everything and just show the documentation:
        if self.data.get('-h', False):
            self.output_function(self._generate_help_message(program_name))
            return None

        # check if any non-optional flags have not been passed:
        required_but_not_given_flags = []
        for flag in self.flags:
            if flag.flag in self.data: # given
                continue
            elif flag.optional and flag.default_value is not None: # optional and has default value
                self.data[flag.flag] = flag.default_value
            #TODO: Consider optional with "optional" value (None)
            else: # required
                required_but_not_given_flags.append(flag)
        debug_trace(required_but_not_given_flags)
        missing_flags = ", ".join(flag.flag for flag in required_but_not_given_flags)
        assert len(required_but_not_given_flags) == 0, f"You need to pass the following obligatory flags: {missing_flags}"
        self.parsed = True

        return self.data

    def _generate_usage(self, program_name: str) -> str:
        # TODO: only include the program name, not the folder path
        has_optional_flags = False
        usage_message = f"USAGE: python {program_name}"
        for flag in self.flags:
            if not flag.optional:
                usage_message += f" {flag.flag}"
                FlagType.assert_that_still_handle_all_types(3)
                match flag.kind:
                    case FlagType.BOOL:
                        pass
                    case FlagType.INT:
                        usage_message += " <int>"
                    case FlagType.STRING:
                        usage_message += " <string>"
                    case _:
                        debug_trace(flag.kind)
                        assert False, "Unreachable"
            elif not has_optional_flags:
                has_optional_flags = True
        usage_message += " [OPTIONAL-FLAGS]" if has_optional_flags else ""
        return usage_message

    def add_default_help_flag(self) -> None:
        self.add_flag("-h",  "Prints this help message.", "bool", aliases=["--help"])
        # Make `help` always the first flag:
        help_flag = self.flags.pop()
        self.flags.insert(0, help_flag)

    def _generate_help_message(self, program_name: str) -> str:
        help_message: str = ""
        help_message += self.program_description + "\n" # Welcome message
        help_message += self._generate_usage(program_name) + "\n" # USAGE

        for flag in self.flags:
            help_message += self._describe_flag(flag) + "\n"
        return help_message

    @staticmethod
    def _describe_flag(flag: Flag) -> str:
        # flag_and_aliases = f"{flag.flag}" + ("" if not flag.aliases else f" (or: {', '.join(flag.aliases)})")
        alias_list = f" (alt.: {', '.join(flag.aliases)})" if flag.aliases else ""
        FlagType.assert_that_still_handle_all_types(3)
        argument = f"<{flag.kind.value}>" if flag.kind != FlagType.BOOL else ""
        description = f"{flag.description}"
        flag_and_argument = f"{flag.flag} {argument}"
        # return f"    * {flag_and_aliases:<20}{argument:>7} : {description}"
        return f"        {flag_and_argument:<10} : {description:<30}{alias_list}"

    def _find_closest_flags(self, flag:str, tolerance:int=3) -> list[Flag]:
        """Finds the closest flag to the input string, based on a string distance."""
        assert False, "not implemented"

def string_distance(str1: str, str2: str) -> int:
    """Computes the distance between two strings."""
    assert False, "Not implemented"