from __future__ import annotations

from pydantic import BaseModel, Field


class Milestone(BaseModel):
    """A milestone that tracks civilization progress."""

    id: str
    name: str
    description: str
    tier: int  # 1=Survival, 2=Organization, 3=Society, 4=Republic, 5=Legacy
    achieved: bool = False
    stability_reward: float = 0.0
    chaos_reward: float = 0.0  # negative = reduces chaos


def create_milestones() -> list[Milestone]:
    return [
        # --- Tier 1: Survival ---
        Milestone(
            id="fire", name="First Fire",
            description="Build shelter and warmth for your people",
            tier=1, stability_reward=0.03, chaos_reward=-0.03,
        ),
        Milestone(
            id="sustenance", name="Sustenance",
            description="Secure a reliable food source (food >= 8)",
            tier=1, stability_reward=0.03, chaos_reward=-0.03,
        ),
        Milestone(
            id="first_night", name="Survived the Night",
            description="Complete 2 turns without losing anyone",
            tier=1, stability_reward=0.02, chaos_reward=-0.02,
        ),
        # --- Tier 2: Organization ---
        Milestone(
            id="roles_assigned", name="Roles Assigned",
            description="Delegate at least 2 NPCs to roles",
            tier=2, stability_reward=0.03, chaos_reward=-0.04,
        ),
        Milestone(
            id="first_law", name="First Law",
            description="Establish any law",
            tier=2, stability_reward=0.04, chaos_reward=-0.04,
        ),
        Milestone(
            id="explored", name="Explored the Land",
            description="Send a scouting party to discover the surroundings",
            tier=2, stability_reward=0.03, chaos_reward=-0.03,
        ),
        # --- Tier 3: Society ---
        Milestone(
            id="council", name="Council Formed",
            description="3 or more NPCs hold leadership roles",
            tier=3, stability_reward=0.04, chaos_reward=-0.03,
        ),
        Milestone(
            id="conflict_resolved", name="Conflict Resolved",
            description="Survive a major dispute without violence",
            tier=3, stability_reward=0.04, chaos_reward=-0.03,
        ),
        Milestone(
            id="agora", name="The Agora",
            description="Build a gathering place (shelter >= 5)",
            tier=3, stability_reward=0.03, chaos_reward=-0.02,
        ),
        Milestone(
            id="education", name="The First Lesson",
            description="Teach the people something beyond survival (knowledge >= 3)",
            tier=3, stability_reward=0.04, chaos_reward=-0.02,
        ),
        Milestone(
            id="specialization", name="Division of Labor",
            description="Five citizens hold distinct roles in the settlement",
            tier=3, stability_reward=0.03, chaos_reward=-0.02,
        ),
        # --- Tier 4: The Republic ---
        Milestone(
            id="justice", name="Justice Defined",
            description="Establish a system for resolving disputes",
            tier=4, stability_reward=0.05, chaos_reward=-0.03,
        ),
        Milestone(
            id="guardian_class", name="The Guardians",
            description="Establish a warrior-protector class distinct from the rulers",
            tier=4, stability_reward=0.04, chaos_reward=-0.03,
        ),
        Milestone(
            id="allegory_taught", name="The Allegory",
            description="The people understand why they left the cave",
            tier=4, stability_reward=0.05, chaos_reward=-0.03,
        ),
        Milestone(
            id="three_laws", name="Code of Laws",
            description="Three or more laws govern the settlement",
            tier=4, stability_reward=0.04, chaos_reward=-0.02,
        ),
        Milestone(
            id="philosopher_king", name="The Philosopher-King",
            description="Accept or reject permanent authority over the republic",
            tier=4, stability_reward=0.05, chaos_reward=-0.04,
        ),
        # --- Tier 5: Legacy (optional epilogue) ---
        Milestone(
            id="constitution", name="The Constitution",
            description="A written code that outlasts any single leader",
            tier=5, stability_reward=0.05, chaos_reward=-0.03,
        ),
        Milestone(
            id="succession", name="The Successor",
            description="Another is ready to lead when you are gone",
            tier=5, stability_reward=0.04, chaos_reward=-0.03,
        ),
        Milestone(
            id="the_republic", name="The Republic",
            description="A society that can endure",
            tier=5, stability_reward=0.0, chaos_reward=0.0,
        ),
    ]
