"""Base classes for DOM analysis."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterable


class DOMAnalyzer(ABC):
    """Abstract base class for DOM analyzers."""

    @abstractmethod
    def load(self, source: str) -> None:
        """Load HTML or URL content into the analyzer."""

    @abstractmethod
    def query(self, selector: str) -> Iterable[Any]:
        """Return elements matching the CSS selector."""

    def close(self) -> None:
        """Clean up resources, if any."""
        return None
