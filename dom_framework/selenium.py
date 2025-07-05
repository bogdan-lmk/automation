"""Selenium based DOM analyzer."""

from __future__ import annotations

from typing import Any, Iterable

from .base import DOMAnalyzer


class SeleniumDOMAnalyzer(DOMAnalyzer):
    """Analyzer using Selenium for live pages."""

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
