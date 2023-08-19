# CLI flags module for python

An interesting API for handling command line arguments/flags in python.

Inspired by the Go module [flag](https://pkg.go.dev/flag) and [Tsoding's flag.h for C](https://github.com/tsoding/flag.h).

Work in progress, everything is subject to change.

Feel free to use it without credit (just don't claim it as yours).

## Dependencies

Only built-in libraries, but I used mypy, flake8 and other tools for debugging and linting.

Requires python 3.10+ (structural pattern matching; typing)

## Usage/Example

```py
import sys
import flags


def main() -> None:
    # Initiate a flag handler
    fh = flags.FlagHandler("This program tests the flags module made by github.com/meee-low.")

    # Add flags
    name        = fh.str_flag("-n", "The name to be greeted!", optional=False, aliases=["--name"])
    count       = fh.int_flag("-c", "How many times to greet!", "1", aliases=["--count"])
    praise_flag = fh.bool_flag("--praise", "Praises the person with the name.")

    # Parse the command line arguments
    fh.parse(sys.argv)

    # Free to use the data stored in each flag now!
    print(name.data, count.data, praise_flag.data)
    for _ in range(count.data):
        print(f"Hello, {name.data}!")
    if praise_flag.data:
        print(f"You're looking good today, {name.data}!")


if __name__ == "__main__":
    main()

```

## Future features:

- "Greedy" flags, that capture every argument until the next flag.
- Constraints for flags (ranges, length, etc.)
- Float flags
- Maybe an explicit "path" flag?
