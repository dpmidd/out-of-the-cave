from pydantic import BaseModel, Field

from src.models.civilization import Civilization
from src.models.milestone import Milestone, create_milestones
from src.models.npc import NPC
from src.models.player import Player


class GameState(BaseModel):
    """The entire game world — fully serializable for save/load."""

    player: Player = Field(default_factory=Player)
    npcs: list[NPC] = Field(default_factory=list)
    civilization: Civilization = Field(default_factory=Civilization)
    milestones: list[Milestone] = Field(default_factory=create_milestones)
    chaos: float = Field(default=0.05, ge=0.0, le=1.0)
    turn: int = 0
    event_history: list[str] = Field(default_factory=list)
    narrative_depth: str = "medium"  # low, medium, high, very_high
    difficulty: str = "normal"  # easy, normal, hard
    delegations: dict[int, str] = Field(default_factory=dict)  # npc_idx -> task_id

    @property
    def current_tier(self) -> int:
        """The highest tier where all milestones are achieved, +1 for the active tier."""
        for tier in range(1, 6):
            tier_milestones = [m for m in self.milestones if m.tier == tier]
            if not all(m.achieved for m in tier_milestones):
                return tier
        return 5

    @property
    def achieved_milestone_ids(self) -> set[str]:
        return {m.id for m in self.milestones if m.achieved}

    @property
    def chaos_label(self) -> str:
        if self.chaos >= 0.8:
            return "Anarchy"
        elif self.chaos >= 0.6:
            return "Volatile"
        elif self.chaos >= 0.3:
            return "Simmering"
        elif self.chaos >= 0.1:
            return "Uneasy"
        else:
            return "Calm"

    @property
    def is_victory(self) -> bool:
        return "philosopher_king" in self.achieved_milestone_ids

    @property
    def is_defeat(self) -> bool:
        return self.civilization.population <= 0 or self.chaos >= 1.0

    def apply_chaos(self, delta: float) -> None:
        self.chaos = round(max(0.0, min(1.0, self.chaos + delta)), 10)

    def decay_chaos(self) -> None:
        """Chaos decays slowly each turn, but has a floor based on tier."""
        decay = 0.005 if self.difficulty == "hard" else 0.01
        floor = 0.02 * (self.current_tier + 1)
        self.chaos = max(floor, self.chaos - decay)

    def decay_stability(self) -> None:
        """Stability erodes each turn — civilization is hard to maintain."""
        civ = self.civilization
        base_erosion = 0.02
        population_pressure = max(0, (civ.population - 10) * 0.003)
        law_bonus = min(len(civ.laws) * 0.005, 0.02)
        chaos_erosion = self.chaos * 0.04
        total = max(0.01, base_erosion + population_pressure + chaos_erosion - law_bonus)
        civ.stability = max(0.0, civ.stability - total)

    def apply_loyalty_all(self, delta: float) -> None:
        for npc in self.npcs:
            if npc.alive:
                npc.loyalty = max(0.0, min(1.0, npc.loyalty + delta))
