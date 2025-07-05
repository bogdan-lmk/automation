"""DOM analysis framework."""

from __future__ import annotations

from typing import Dict, Type

from .base import DOMAnalyzer
from .soup import SoupDOMAnalyzer
from .selenium import SeleniumDOMAnalyzer

_ANALYZERS: Dict[str, Type[DOMAnalyzer]] = {
    "soup": SoupDOMAnalyzer,
    "selenium": SeleniumDOMAnalyzer,
}


def register_analyzer(name: str, analyzer_cls: Type[DOMAnalyzer]) -> None:
    """Register a custom analyzer class."""
    _ANALYZERS[name] = analyzer_cls


def create_analyzer(name: str) -> DOMAnalyzer:
    """Factory for analyzer instances."""
    if name not in _ANALYZERS:
        raise ValueError(f"Analyzer '{name}' is not registered")
    return _ANALYZERS[name]()

__all__ = [
    "DOMAnalyzer",
    "SoupDOMAnalyzer",
    "SeleniumDOMAnalyzer",
    "register_analyzer",
    "create_analyzer",
]
