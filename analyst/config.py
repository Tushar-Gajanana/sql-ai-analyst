import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str
    api_key: str
    model: str = "llama-3.3-70b-versatile"

    @classmethod
    def from_env(cls):
        values = [os.getenv("DATABASE_URL", ""), os.getenv("GROQ_API_KEY", "")]
        if not all(values):
            raise ValueError("Set DATABASE_URL and GROQ_API_KEY in your secrets or .env.")
        return cls(*values, model=os.getenv("GROQ_MODEL", cls.model))
