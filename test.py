import sys
import flags

def main() -> None:
    fh = flags.FlagHandler("This program tests the flags module made by Matheus Ferreira Drumond (github.com/meee-low).")
    fh.add_flag("-n", "The name to be greeted!", "str", optional=False, aliases=["--name"])
    fh.add_flag("-c", "How many times to greet!", "int", "1", aliases=["--count"])
    fh.add_flag("--insult", "Insults the person with the name.", "bool")

    fh.parse(sys.argv[0], sys.argv[1:])

    name = fh.data['-n']
    count = fh.data['-c']
    insult_flag = fh.data['--insult']
    for _ in range(int(count)):
        insult = ", you buffoon" if insult_flag else ""
        print(f"Hello, {name}{insult}!")

if __name__ == "__main__":
    main()