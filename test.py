import sys
import flags


def main() -> None:
    # Initiate a flag handler
    fh = flags.FlagHandler("""This program tests the flags module made by \
Matheus Ferreira Drumond (github.com/meee-low).""")

    # Add flags
    name        = fh.str_flag("-n", "The name to be greeted!", optional=False, aliases=["--name"])
    count       = fh.int_flag("-c", "How many times to greet!", "1", aliases=["--count"])
    insult_flag = fh.bool_flag("--insult", "Insults the person with the name.")

    # Parse the command line arguments
    fh.parse(sys.argv)

    # Free to use the data stored in each flag now!
    for _ in range(count.data):
        insult = ", you buffoon" if insult_flag.data else ""
        print(f"Hello, {name.data}{insult}!")


if __name__ == "__main__":
    main()
