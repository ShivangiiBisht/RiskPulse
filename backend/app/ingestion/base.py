from abc import ABC, abstractmethod
from typing import Iterator

from app.schemas import RawDocument


class BaseSource(ABC):
    name: str

    @abstractmethod
    def fetch(self) -> Iterator[RawDocument]:
        """Yield normalized documents."""
