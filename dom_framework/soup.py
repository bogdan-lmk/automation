"""BeautifulSoup based DOM analyzer."""

from __future__ import annotations

from typing import Any, Iterable

from .base import DOMAnalyzer


class SoupDOMAnalyzer(DOMAnalyzer):
    """Analyzer using BeautifulSoup for static HTML."""

    def __init__(self) -> None:
        self.soup = None

    def load(self, source: str) -> None:
        from bs4 import BeautifulSoup

        self.soup = BeautifulSoup(source, "html.parser")

    def query(self, selector: str) -> Iterable[Any]:
        if not self.soup:
            return []
        return self.soup.select(selector)
