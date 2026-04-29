from pydantic import BaseModel, Field


class Civilization(BaseModel):
    """The state of the fledgling society outside the cave."""

    population: int = Field(default=12, ge=0)
    stability: float = Field(default=0.1, ge=0.0, le=1.0)
    food: int = Field(default=0, ge=0)
    shelter: int = Field(default=0, ge=0)
    knowledge: int = Field(default=0, ge=0)
    laws: list[str] = Field(default_factory=list)
    starvation_turns: int = Field(default=0, ge=0)

    @property
    def stability_label(self) -> str:
        if self.stability >= 0.8:
            return "Flourishing"
        elif self.stability >= 0.6:
            return "Organized"
        elif self.stability >= 0.4:
            return "Fragile"
        elif self.stability >= 0.2:
            return "Unstable"
        else:
            return "Chaos"

    def apply_effects(self, effects: dict) -> list[str]:
        """Apply a dict of effects and return descriptions of what changed."""
        log = []
        if "population" in effects:
            delta = effects["population"]
            self.population = max(0, self.population + delta)
            if delta > 0:
                log.append(f"+{delta} population")
            else:
                log.append(f"{delta} population")

        if "stability" in effects:
            delta = effects["stability"]
            self.stability = max(0.0, min(1.0, self.stability + delta))
            if delta > 0:
                log.append(f"+{delta:.0%} stability")
            else:
                log.append(f"{delta:.0%} stability")

        if "food" in effects:
            delta = effects["food"]
            self.food = max(0, self.food + delta)
            if delta > 0:
                log.append(f"+{delta} food")
            else:
                log.append(f"{delta} food")

        if "shelter" in effects:
            delta = effects["shelter"]
            self.shelter = max(0, self.shelter + delta)
            if delta > 0:
                log.append(f"+{delta} shelter")
            else:
                log.append(f"{delta} shelter")

        if "knowledge" in effects:
            delta = effects["knowledge"]
            self.knowledge = max(0, self.knowledge + delta)
            if delta > 0:
                log.append(f"+{delta} knowledge")
            else:
                log.append(f"{delta} knowledge")

        if "law" in effects:
            self.laws.append(effects["law"])
            log.append(f"New law: {effects['law']}")

        return log
