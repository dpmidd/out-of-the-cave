from pydantic import BaseModel, Field


class Player(BaseModel):
    """Plato — the player character."""

    rhetoric: int = Field(default=1, ge=1, le=10, description="Persuasion and speechcraft")
    wisdom: int = Field(default=1, ge=1, le=10, description="Philosophical insight and planning")
    courage: int = Field(default=1, ge=1, le=10, description="Boldness in the face of danger")
    authority: int = Field(default=1, ge=1, le=10, description="Command presence and intimidation")
    pragmatism: int = Field(default=1, ge=1, le=10, description="Practical problem-solving")

    @property
    def total_points(self) -> int:
        return self.rhetoric + self.wisdom + self.courage + self.authority + self.pragmatism

    def get_attribute(self, name: str) -> int:
        return getattr(self, name)
