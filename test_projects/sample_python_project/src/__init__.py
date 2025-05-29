"""
Sample Python Project - A comprehensive test project for code development assistant.

This package contains various modules demonstrating different Python programming patterns
and techniques for testing RAG and code analysis capabilities.
"""

__version__ = "1.0.0"
__author__ = "Code Dev Assistant"
__email__ = "dev@example.com"

# Package-level imports for convenience
from .calculator.basic_ops import BasicCalculator
from .calculator.advanced_ops import AdvancedCalculator
from .data_processing.data_analyzer import DataAnalyzer
from .web_scraper.scraper import WebScraper
from .utils.config_loader import ConfigLoader
from .utils.logger import setup_logger

__all__ = [
    "BasicCalculator",
    "AdvancedCalculator", 
    "DataAnalyzer",
    "WebScraper",
    "ConfigLoader",
    "setup_logger"
]
