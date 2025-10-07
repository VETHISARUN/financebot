#!/usr/bin/env python3
"""
FLAMES game
F - Friends
L - Love
A - Affection
M - Marriage
E - Enemy
S - Siblings
"""

def normalize(name: str) -> str:
    """Lowercase, remove spaces and non-letter characters."""
    return ''.join(ch for ch in name.lower() if ch.isalpha())

def remaining_count(name1: str, name2: str) -> int:
    """
    Remove common letters between the two names (like cancelling matched characters)
    and return the count of letters left.
    """
    n1 = list(normalize(name1))
    n2 = list(normalize(name2))

    # Cancel common letters (one-to-one)
    i = 0
    while i < len(n1):
        ch = n1[i]
        if ch in n2:
            n1.pop(i)
            n2.remove(ch)
            # do not increment i, because list shifted left
        else:
            i += 1

    # total remaining letters
    return len(n1) + len(n2)

def flames_result(count: int) -> str:
    """
    Use the elimination process on the string 'FLAMES' using the count.
    If count is 0 (identical names after normalization), treat specially.
    """
    mapping = {
        'F': 'Friends',
        'L': 'Love',
        'A': 'Affection',
        'M': 'Marriage',
        'E': 'Enemy',
        'S': 'Siblings'
    }

    if count == 0:
        # If both names have exactly same letters (after removal) — friendly message
        return "Perfect match! (All letters cancelled) — usually treated as 'Siblings' or 'Friends'."

    letters = list("FLAMES")
    idx = 0  # starting index

    # Eliminate until one letter remains
    while len(letters) > 1:
        # (count - 1) because elimination counts inclusively from current position
        idx = (idx + count - 1) % len(letters)
        letters.pop(idx)
        # next round starts from current idx (no +1)

    return mapping[letters[0]]

def play_flames():
    print("FLAMES game\nEnter two names to find the relationship.\n")
    name1 = input("Name 1: ").strip()
    name2 = input("Name 2: ").strip()

    if not name1 or not name2:
        print("Both names are required.")
        return

    count = remaining_count(name1, name2)
    result = flames_result(count)

    print(f"\nRemaining letter count after cancelling common letters: {count}")
    print(f"Result: {result}")

if __name__ == "__main__":
    while True:
        play_flames()
        again = input("\nPlay again? (y/n): ").strip().lower()
        if again not in ('y', 'yes'):
            print("Bye!")
            break
