def levenshtein_distance(str1: str, str2: str) -> int:
    """Naive recursive implementation of Levenshtein distance

    Args:
        str1 (str): The origin string.
        str2 (str): The target string.

    Returns:
        int: The levenshtein distance.
    """
    if len(str2) == 0:  # Goal is empty string
        return len(str1)  # Remove all characters
    elif len(str1) == 0:  # Start is empty string
        return len(str2)  # Add all the characters
    elif str1[0] == str2[0]:
        return levenshtein_distance(str1[1:], str2[1:])  # Recurse on the non-matching section
    else:
        return 1 + min(levenshtein_distance(str1[1:], str2),
                       levenshtein_distance(str1, str2[1:]),
                       levenshtein_distance(str1[1:], str2[1:]))


def main():
    def test_lev(str1: str, str2: str, expected: int) -> bool:
        actual_result = levenshtein_distance(str1, str2)
        print(f"Testing: {str1:>10} -> {str2:<10}: ", end="")
        if expected == actual_result:
            print(f"Got: {actual_result}!")
            return True
        else:
            print(f"Got: {actual_result}, expected: {expected}")
            return False

    test_lev("", "apple", 5)
    test_lev("apple", "", 5)
    test_lev("apple", "apples", 1)


if __name__ == "__main__":
    main()
