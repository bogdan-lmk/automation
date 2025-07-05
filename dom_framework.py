from __future__ import annotations

"""Simple, extensible DOM analysis framework."""

from abc import ABC, abstractmethod
from typing import Any, Iterable, Dict, Type


class DOMAnalyzer(ABC):
    """Base class for DOM analyzers."""

    @abstractmethod
    def load(self, source: str) -> None:
        """Load HTML/URL content into the analyzer."""

    @abstractmethod
    def query(self, selector: str) -> Iterable[Any]:
        """Return elements matching CSS selector."""

    def close(self) -> None:
        """Clean up resources."""
        return None


class SoupDOMAnalyzer(DOMAnalyzer):
    """BeautifulSoup based analyzer for static HTML."""

    def __init__(self) -> None:
        self.soup = None

    def load(self, source: str) -> None:
        from bs4 import BeautifulSoup

        self.soup = BeautifulSoup(source, "html.parser")

    def query(self, selector: str) -> Iterable[Any]:
        if not self.soup:
            return []
        return self.soup.select(selector)


class SeleniumDOMAnalyzer(DOMAnalyzer):
    """Selenium based analyzer for live pages."""

    def __init__(self, driver: Any | None = None) -> None:
        self.driver = driver

    def load(self, source: str) -> None:
        if self.driver is None:
            from selenium import webdriver

            self.driver = webdriver.Chrome()
        self.driver.get(source)

    def query(self, selector: str) -> Iterable[Any]:
        if not self.driver:
            return []
        return self.driver.find_elements("css selector", selector)

    def close(self) -> None:
        if self.driver:
            self.driver.quit()
            self.driver = None


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
