import random
from pathlib import Path

import yaml

from src.models.npc import NPC


DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


def _load_yaml(filename: str) -> dict:
    with open(DATA_DIR / filename) as f:
        return yaml.safe_load(f)


def generate_npcs(count: int) -> list[NPC]:
    """Generate a pool of random cave-dweller NPCs."""
    names_data = _load_yaml("names.yaml")
    traits_data = _load_yaml("traits.yaml")

    all_names = names_data["male"] + names_data["female"]
    random.shuffle(all_names)
    chosen_names = all_names[:count]

    personalities = traits_data["personalities"]
    personality_names = list(personalities.keys())
    personality_weights = [personalities[p]["weight"] for p in personality_names]

    skill_names = traits_data["skills"]
    skill_lo, skill_hi = traits_data["skill_range"]

    npcs = []
    for name in chosen_names:
        personality = random.choices(personality_names, weights=personality_weights, k=1)[0]
        p_data = personalities[personality]
        loyalty = random.uniform(*p_data["loyalty_range"])

        skills = {}
        for skill in skill_names:
            skills[skill] = random.randint(skill_lo, skill_hi)

        npcs.append(NPC(
            name=name,
            personality=personality,
            skills=skills,
            loyalty=round(loyalty, 2),
        ))

    return npcs
