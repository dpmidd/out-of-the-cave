import random


def roll(attribute: int, difficulty: int, chaos: float) -> bool:
    """Roll a d10 + attribute modifier against a difficulty, influenced by chaos.

    Positive chaos (luck) increases success chance; negative chaos (bad luck) decreases it.

    Returns True if successful, False if failed.
    """
    base_roll = random.randint(1, 10)
    chaos_swing = chaos * random.uniform(0, 3)  # chaos modifier, scales with magnitude and sign
    final = base_roll + attribute + chaos_swing
    target = difficulty + 5  # base target is difficulty + 5
    return final >= target
