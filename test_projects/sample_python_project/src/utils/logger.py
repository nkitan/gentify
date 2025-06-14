"""
Logger Setup Module

This module provides utilities for setting up logging with various handlers,
formatters, and configuration options for the application.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional, Union


def setup_logger(name: str = None, 
                level: Union[int, str] = logging.INFO,
                log_file: Optional[Union[str, Path]] = None,
                console_output: bool = True,
                file_output: bool = True,
                max_file_size: int = 10 * 1024 * 1024,  # 10MB
                backup_count: int = 5,
                format_string: Optional[str] = None) -> logging.Logger:
    """
    Set up a logger with console and/or file handlers.
    
    Args:
        name (str): Logger name (defaults to root logger)
        level (Union[int, str]): Logging level
        log_file (Optional[Union[str, Path]]): Log file path
        console_output (bool): Whether to log to console
        file_output (bool): Whether to log to file
        max_file_size (int): Maximum file size before rotation
        backup_count (int): Number of backup files to keep
        format_string (Optional[str]): Custom format string
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Convert string level to int if needed
    if isinstance(level, str):
        level = getattr(logging, level.upper())
    
    # Get or create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Default format
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    formatter = logging.Formatter(format_string)
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler with rotation
    if file_output and log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger to avoid duplicate messages
    logger.propagate = False
    
    return logger


def setup_application_logging(log_level: str = "INFO", 
                            log_directory: Union[str, Path] = "logs") -> None:
    """
    Set up application-wide logging configuration.
    
    Args:
        log_level (str): Logging level for the application
        log_directory (Union[str, Path]): Directory for log files
    """
    log_dir = Path(log_directory)
    log_dir.mkdir(exist_ok=True)
    
    # Simplified logging - all application components use a single log file
    setup_logger(
        name="sample_app",
        level=log_level,
        log_file=log_dir / "application.log",
        console_output=True,
        file_output=True
    )
    
    # All other components use the same application.log file
    for component in ["calculator", "data_processing", "web_scraper"]:
        setup_logger(
            name=component,
            level=log_level,
            log_file=log_dir / "application.log",
            console_output=False,
            file_output=True
        )
    
    # Suppress noisy third-party loggers
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


class LoggerMixin:
    """
    Mixin class to add logging capabilities to any class.
    
    Provides a logger property that uses the class name as the logger name.
    """
    
    @property
    def logger(self) -> logging.Logger:
        """Get a logger for this class."""
        return logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name (str): Logger name
        
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)


def log_function_call(func):
    """
    Decorator to log function calls with arguments and return values.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        
        # Log function entry
        args_str = ", ".join([repr(arg) for arg in args])
        kwargs_str = ", ".join([f"{k}={repr(v)}" for k, v in kwargs.items()])
        all_args = ", ".join(filter(None, [args_str, kwargs_str]))
        
        logger.debug(f"Calling {func.__name__}({all_args})")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} returned: {repr(result)}")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} raised {type(e).__name__}: {e}")
            raise
    
    return wrapper


def log_execution_time(func):
    """
    Decorator to log function execution time.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    import time
    
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} executed in {execution_time:.4f} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.4f} seconds: {e}")
            raise
    
    return wrapper


class ContextLogger:
    """
    Context manager for logging with additional context information.
    
    Example:
        with ContextLogger("Processing file", file_path="/path/to/file") as logger:
            logger.info("Starting processing")
            # ... do work ...
            logger.info("Processing complete")
    """
    
    def __init__(self, operation: str, logger_name: str = None, **context):
        self.operation = operation
        self.context = context
        self.logger = logging.getLogger(logger_name) if logger_name else logging.getLogger()
        self._start_time = None
    
    def __enter__(self) -> logging.Logger:
        """Enter the context and log the start of operation."""
        self._start_time = __import__('time').time()
        
        context_str = ", ".join([f"{k}={v}" for k, v in self.context.items()])
        self.logger.info(f"Starting {self.operation}" + (f" ({context_str})" if context_str else ""))
        
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context and log the completion or failure."""
        execution_time = __import__('time').time() - self._start_time
        
        if exc_type is None:
            self.logger.info(f"Completed {self.operation} in {execution_time:.4f} seconds")
        else:
            self.logger.error(f"Failed {self.operation} after {execution_time:.4f} seconds: {exc_val}")
        
        return False  # Don't suppress exceptions
