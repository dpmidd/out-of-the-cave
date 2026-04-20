import random


def roll(attribute: int, difficulty: int, chaos: float) -> tuple[bool, int, int]:
    """Roll a d10 + attribute modifier against a difficulty, influenced by chaos.

    Chaos makes outcomes less predictable by adding a random swing.

    Returns (success, roll_value, target).
    """
    base_roll = random.randint(1, 10)
    chaos_swing = random.uniform(-chaos * 4, chaos * 2)  # chaos hurts more than it helps
    final = base_roll + attribute + chaos_swing
    target = difficulty + 5  # base target is difficulty + 5
    return final >= target, round(final), target
