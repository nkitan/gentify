#!/usr/bin/env python3
"""
Test script to verify the simplified logging configuration.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from code_dev_assistant.logger import setup_application_logging, get_logger

def test_simplified_logging():
    """Test the simplified logging configuration."""
    print("Testing simplified logging configuration...")
    
    # Set up logging
    loggers = setup_application_logging(
        log_level="DEBUG",
        log_directory="logs",
        enable_structured_logging=False
    )
    
    print(f"Created {len(loggers)} loggers: {list(loggers.keys())}")
    
    # Test each logger
    for component, logger in loggers.items():
        logger.info(f"Testing {component} logger - this should appear in the appropriate log file")
        logger.debug(f"Debug message from {component}")
        logger.warning(f"Warning message from {component}")
    
    # Test context management
    main_logger = loggers["main"]
    with main_logger.context_manager("test_operation"):
        main_logger.info("This is inside a context manager")
    
    print("Logging test completed. Check the log files:")
    print("- application.log should contain logs from: main, server, git, rag, llm, code_analyzer, coder_agent, workflow, health_check")
    print("- web_ui.log should contain logs from: web_ui")

if __name__ == "__main__":
    test_simplified_logging()
