# Automation Utilities

This repository contains various scripts for UI automation. The new `dom_framework` package provides a simple and extensible framework for DOM analysis. The package is split into multiple modules for easier maintenance.

## DOM Framework

The package organizes analyzers in separate modules (`base`, `soup`, `selenium`) following modern Python package practices.

`dom_framework` provides a base `DOMAnalyzer` class and implementations for BeautifulSoup (`SoupDOMAnalyzer`) and Selenium (`SeleniumDOMAnalyzer`).

Use `create_analyzer("soup")` for static HTML or `create_analyzer("selenium")` for live pages. You can register custom analyzers with `register_analyzer`.

Example:
```python
from dom_framework import create_analyzer

analyzer = create_analyzer("soup")
analyzer.load(html_string)
links = analyzer.query("a")
for link in links:
    print(link.get_text())
```

The framework aims to make DOM analysis flexible and scalable for future extensions.
