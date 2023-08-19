# CLI flags module for python

An interesting API for handling command line arguments/flags in python.

Automatically generates help commands with usage tips and suggests corrections for typos.

Inspired by the Go module [flag](https://pkg.go.dev/flag) and [Tsoding's flag.h for C](https://github.com/tsoding/flag.h). Python already has the built-in library argparse, but I wanted to code my own, and this has a different API that may be simpler or more useful for certain situations.

Work in progress, everything is subject to change.

Feel free to use it without credit (just don't claim it as yours).

## Dependencies

Only built-in libraries, but I used mypy, flake8 and other tools for debugging and linting.

This was tested in python 3.10 and Windows 10, but the current build may work in older versions or different OS's.

## Usage/Example

### test.py
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
### Output
```
>>> python test.py -n Milo -c 5 --praise
Milo 5 True
Hello, Milo!
Hello, Milo!
Hello, Milo!
Hello, Milo!
Hello, Milo!
You're looking good today, Milo!

>>> python test.py -n Milo
Hello, Milo!

>>> python test.py -h
This program tests the flags module made by github.com/meee-low.
USAGE: python test.py -n <string> [OPTIONAL-FLAGS]
      * [-h]            : Prints this help message.                (alt.: --help)      Default Value: `False`
      * -n <string>     : The name to be greeted!                  (alt.: --name)
      * [-c <int>]      : How many times to greet!                 (alt.: --count)     Default Value: `1`
      * [--praise]      : Praises the person with the name.                            Default Value: `False`
...
AssertionError: You need to pass the following obligatory flags: -n
```

## Future features:

- "Greedy" flags, that capture every argument until the next flag.
- Constraints for flags (ranges, length, etc.)
- Float flags
- Maybe an explicit "path" flag?
