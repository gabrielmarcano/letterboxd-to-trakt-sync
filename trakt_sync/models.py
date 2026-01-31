from dataclasses import dataclass
from typing import Optional

@dataclass
class Movie:
    title: str
    year: int
    uri: str
    rating: Optional[float] = None
    watched_at: Optional[str] = None
