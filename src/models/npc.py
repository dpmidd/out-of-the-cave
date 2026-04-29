from pydantic import BaseModel, Field


class NPC(BaseModel):
    """A cave-dweller following Plato into the light."""

    name: str
    personality: str = "pragmatist"  # loyalist, skeptic, ambitious, fearful, pragmatist
    skills: dict[str, int] = Field(default_factory=dict)  # labor, rhetoric, combat, wisdom, scouting
    loyalty: float = Field(default=0.5, ge=0.0, le=1.0)
    alive: bool = True
    role: str | None = None  # council_member, scout, enforcer, builder, healer

    @property
    def description(self) -> str:
        """What the player sees — impressions, not raw stats."""
        best_skill = max(self.skills, key=self.skills.get) if self.skills else "nothing"
        skill_level = max(self.skills.values()) if self.skills else 0

        if skill_level >= 7:
            skill_desc = f"remarkably skilled in {best_skill}"
        elif skill_level >= 4:
            skill_desc = f"competent at {best_skill}"
        else:
            skill_desc = "unremarkable in ability"

        loyalty_descs = {
            (0.0, 0.3): "eyes you with open suspicion",
            (0.3, 0.5): "seems uncertain about your leadership",
            (0.5, 0.7): "follows along without complaint",
            (0.7, 0.9): "looks to you with trust",
            (0.9, 1.01): "would follow you anywhere",
        }
        loyalty_desc = "is hard to read"
        for (lo, hi), desc in loyalty_descs.items():
            if lo <= self.loyalty < hi:
                loyalty_desc = desc
                break

        personality_descs = {
            "loyalist": "a steady presence",
            "skeptic": "quick to question",
            "ambitious": "restless with ambition",
            "fearful": "anxious and watchful",
            "pragmatist": "practical above all",
        }
        p_desc = personality_descs.get(self.personality, "difficult to read")

        return f"{self.name} — {p_desc}, {skill_desc}. {self.name} {loyalty_desc}."
