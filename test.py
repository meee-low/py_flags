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
