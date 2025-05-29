#!/usr/bin/env python3
"""
Main application entry point for the sample Python project.
Demonstrates CLI argument parsing and module integration.
"""

import argparse
import sys
import logging
from typing import Optional

from src.calculator.basic_ops import BasicCalculator
from src.calculator.advanced_ops import AdvancedCalculator
from src.data_processing.data_analyzer import DataAnalyzer
from src.web_scraper.scraper import WebScraper
from src.utils.config_loader import ConfigLoader
from src.utils.logger import setup_logger


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Sample Python Project - Code Development Assistant Test"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Calculator commands
    calc_parser = subparsers.add_parser("calc", help="Calculator operations")
    calc_parser.add_argument("operation", choices=["add", "subtract", "multiply", "divide", "power", "sqrt"])
    calc_parser.add_argument("--a", type=float, required=True, help="First number")
    calc_parser.add_argument("--b", type=float, help="Second number (not required for sqrt)")
    
    # Data processing commands
    data_parser = subparsers.add_parser("data", help="Data processing operations")
    data_parser.add_argument("--file", required=True, help="Input data file")
    data_parser.add_argument("--output", help="Output file (optional)")
    data_parser.add_argument("--operation", choices=["analyze", "transform", "filter"], default="analyze")
    
    # Web scraping commands
    scrape_parser = subparsers.add_parser("scrape", help="Web scraping operations")
    scrape_parser.add_argument("url", help="URL to scrape")
    scrape_parser.add_argument("--selector", help="CSS selector for content")
    scrape_parser.add_argument("--output", help="Output file for scraped data")
    
    # Configuration commands
    config_parser = subparsers.add_parser("config", help="Configuration management")
    config_parser.add_argument("--show", action="store_true", help="Show current configuration")
    config_parser.add_argument("--set", nargs=2, metavar=("KEY", "VALUE"), help="Set configuration value")
    
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    return parser


def handle_calculator_command(args) -> int:
    """Handle calculator operations."""
    basic_calc = BasicCalculator()
    advanced_calc = AdvancedCalculator()
    
    try:
        if args.operation == "add":
            result = basic_calc.add(args.a, args.b)
        elif args.operation == "subtract":
            result = basic_calc.subtract(args.a, args.b)
        elif args.operation == "multiply":
            result = basic_calc.multiply(args.a, args.b)
        elif args.operation == "divide":
            result = basic_calc.divide(args.a, args.b)
        elif args.operation == "power":
            result = advanced_calc.power(args.a, args.b)
        elif args.operation == "sqrt":
            result = advanced_calc.square_root(args.a)
        
        print(f"Result: {result}")
        return 0
        
    except Exception as e:
        logging.error(f"Calculator error: {e}")
        return 1


def handle_data_command(args) -> int:
    """Handle data processing operations."""
    try:
        analyzer = DataAnalyzer()
        
        if args.operation == "analyze":
            results = analyzer.analyze_file(args.file)
            print("Data Analysis Results:")
            for key, value in results.items():
                print(f"  {key}: {value}")
        elif args.operation == "transform":
            analyzer.transform_data(args.file, args.output)
            print(f"Data transformed and saved to {args.output}")
        elif args.operation == "filter":
            analyzer.filter_data(args.file, args.output)
            print(f"Data filtered and saved to {args.output}")
            
        return 0
        
    except Exception as e:
        logging.error(f"Data processing error: {e}")
        return 1


def handle_scrape_command(args) -> int:
    """Handle web scraping operations."""
    try:
        scraper = WebScraper()
        
        if args.selector:
            content = scraper.scrape_with_selector(args.url, args.selector)
        else:
            content = scraper.scrape_text(args.url)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Scraped content saved to {args.output}")
        else:
            print("Scraped Content:")
            print(content[:500] + "..." if len(content) > 500 else content)
            
        return 0
        
    except Exception as e:
        logging.error(f"Web scraping error: {e}")
        return 1


def handle_config_command(args) -> int:
    """Handle configuration management."""
    try:
        config_loader = ConfigLoader()
        
        if args.show:
            config = config_loader.load_yaml_config("config/config.yaml")
            print("Current Configuration:")
            for key, value in config.items():
                print(f"  {key}: {value}")
        elif args.set:
            key, value = args.set
            # In a real application, you would implement config setting logic here
            print(f"Would set {key} = {value}")
            
        return 0
        
    except Exception as e:
        logging.error(f"Configuration error: {e}")
        return 1


def main() -> int:
    """Main application entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logger(level=log_level)
    
    logging.info("Starting sample Python project application")
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Route to appropriate command handler
    if args.command == "calc":
        return handle_calculator_command(args)
    elif args.command == "data":
        return handle_data_command(args)
    elif args.command == "scrape":
        return handle_scrape_command(args)
    elif args.command == "config":
        return handle_config_command(args)
    else:
        logging.error(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
