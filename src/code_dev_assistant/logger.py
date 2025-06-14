"""
Comprehensive Logging Utility for Code Development Assistant

This module provides centralized logging configuration with debug capabilities,
structured logging, performance tracking, and context-aware log formatting.
"""
import logging
import logging.handlers
import sys
import os
import json
import traceback
import time
import functools
from pathlib import Path
from typing import Any, Dict, Optional, Union, Callable
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum


class LogLevel(Enum):
    """Log levels with descriptions."""
    DEBUG = ("DEBUG", "Detailed diagnostic information")
    INFO = ("INFO", "General information about application flow")
    WARNING = ("WARNING", "Something unexpected happened but application continues")
    ERROR = ("ERROR", "A serious problem occurred")
    CRITICAL = ("CRITICAL", "The application may not be able to continue")


@dataclass
class LogContext:
    """Context information for structured logging."""
    module: str
    function: str = ""
    operation: str = ""
    user_id: str = ""
    session_id: str = ""
    request_id: str = ""
    additional_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.additional_data is None:
            self.additional_data = {}


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging with JSON output."""
    
    def __init__(self, include_context: bool = True):
        self.include_context = include_context
        super().__init__()
    
    def format(self, record):
        """Format log record as structured JSON."""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add context if available
        if hasattr(record, 'context') and self.include_context:
            log_entry["context"] = asdict(record.context)
        
        # Add custom attributes
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'getMessage', 'exc_info', 
                          'exc_text', 'stack_info', 'context']:
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str)


class PerformanceTracker:
    """Tracks performance metrics for logging."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self._timers: Dict[str, float] = {}
    
    def start_timer(self, operation: str) -> None:
        """Start timing an operation."""
        self._timers[operation] = time.time()
        self.logger.debug(f"Started timer for operation: {operation}")
    
    def end_timer(self, operation: str) -> float:
        """End timing an operation and log the duration."""
        if operation not in self._timers:
            self.logger.warning(f"Timer for operation '{operation}' was not started")
            return 0.0
        
        duration = time.time() - self._timers[operation]
        del self._timers[operation]
        
        self.logger.debug(f"Operation '{operation}' completed in {duration:.4f} seconds", 
                         extra={"operation": operation, "duration": duration})
        return duration
    
    def time_context(self, operation: str):
        """Context manager for timing operations."""
        return TimerContext(self, operation)


class TimerContext:
    """Context manager for timing operations."""
    
    def __init__(self, tracker: PerformanceTracker, operation: str):
        self.tracker = tracker
        self.operation = operation
    
    def __enter__(self):
        self.tracker.start_timer(self.operation)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.tracker.end_timer(self.operation)


class DebugLogger:
    """Enhanced logger with debug capabilities and structured logging."""
    
    def __init__(self, name: str = None, 
                 level: Union[str, int] = logging.DEBUG,
                 log_file: Optional[str] = None,
                 enable_console: bool = True,
                 enable_file: bool = True,
                 enable_structured: bool = False,
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5):
        """
        Initialize debug logger with comprehensive configuration.
        
        Args:
            name: Logger name
            level: Logging level
            log_file: Path to log file
            enable_console: Enable console output
            enable_file: Enable file output
            enable_structured: Enable structured JSON logging
            max_file_size: Maximum file size before rotation
            backup_count: Number of backup files to keep
        """
        self.logger = logging.getLogger(name or __name__)
        self.performance_tracker = PerformanceTracker(self.logger)
        self.context_stack = []
        
        # Convert string level to int if needed
        if isinstance(level, str):
            level = getattr(logging, level.upper())
        
        self.logger.setLevel(level)
        self.logger.handlers.clear()
        
        # Console handler
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            
            if enable_structured:
                console_formatter = StructuredFormatter()
            else:
                console_formatter = logging.Formatter(
                    "%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S"
                )
            
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
        
        # File handler
        if enable_file and log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_path,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(level)
            
            if enable_structured:
                file_formatter = StructuredFormatter()
            else:
                file_formatter = logging.Formatter(
                    "%(asctime)s | %(name)s | %(levelname)s | %(module)s.%(funcName)s:%(lineno)d | %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S"
                )
            
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
        
        self.logger.propagate = False
    
    def push_context(self, context: LogContext):
        """Push a new context onto the stack."""
        self.context_stack.append(context)
        self.debug(f"Pushed context: {context.operation or context.function}")
    
    def pop_context(self):
        """Pop the current context from the stack."""
        if self.context_stack:
            context = self.context_stack.pop()
            self.debug(f"Popped context: {context.operation or context.function}")
            return context
        return None
    
    def get_current_context(self) -> Optional[LogContext]:
        """Get the current context without removing it."""
        return self.context_stack[-1] if self.context_stack else None
    
    def _log_with_context(self, level: int, msg: str, *args, **kwargs):
        """Log message with current context."""
        extra = kwargs.get('extra', {})
        
        # Add current context if available
        if self.context_stack:
            extra['context'] = self.context_stack[-1]
        
        kwargs['extra'] = extra
        self.logger.log(level, msg, *args, **kwargs)
    
    def debug(self, msg: str, *args, **kwargs):
        """Log debug message."""
        self._log_with_context(logging.DEBUG, msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs):
        """Log info message."""
        self._log_with_context(logging.INFO, msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        """Log warning message."""
        self._log_with_context(logging.WARNING, msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        """Log error message."""
        self._log_with_context(logging.ERROR, msg, *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs):
        """Log critical message."""
        self._log_with_context(logging.CRITICAL, msg, *args, **kwargs)
    
    def exception(self, msg: str, *args, **kwargs):
        """Log exception with traceback."""
        kwargs['exc_info'] = True
        self.error(msg, *args, **kwargs)
    
    def log_function_entry(self, func_name: str, args: tuple = (), kwargs: dict = None):
        """Log function entry with parameters."""
        kwargs = kwargs or {}
        self.debug(f"Entering function: {func_name}", 
                  extra={"function_args": args, "function_kwargs": kwargs})
    
    def log_function_exit(self, func_name: str, result: Any = None, duration: float = None):
        """Log function exit with result."""
        extra = {"function_result_type": type(result).__name__}
        if duration is not None:
            extra["duration"] = duration
        self.debug(f"Exiting function: {func_name}", extra=extra)
    
    def log_variable(self, name: str, value: Any, context: str = ""):
        """Log variable value for debugging."""
        context_str = f" in {context}" if context else ""
        self.debug(f"Variable {name}{context_str}: {value}", 
                  extra={"variable_name": name, "variable_value": value, 
                        "variable_type": type(value).__name__})
    
    def log_api_call(self, endpoint: str, method: str = "GET", params: dict = None, 
                     response_code: int = None, duration: float = None):
        """Log API call details."""
        extra = {
            "api_endpoint": endpoint,
            "api_method": method,
            "api_params": params,
            "api_response_code": response_code,
            "api_duration": duration
        }
        self.info(f"API call: {method} {endpoint}", extra=extra)
    
    def log_database_operation(self, operation: str, table: str = None, 
                              query: str = None, duration: float = None):
        """Log database operation."""
        extra = {
            "db_operation": operation,
            "db_table": table,
            "db_query": query,
            "db_duration": duration
        }
        self.debug(f"Database operation: {operation}", extra=extra)
    
    def context_manager(self, operation: str, **context_data):
        """Context manager for automatic context handling."""
        return LogContextManager(self, operation, **context_data)


class LogContextManager:
    """Context manager for automatic logging context management."""
    
    def __init__(self, logger: DebugLogger, operation: str, **context_data):
        self.logger = logger
        self.operation = operation
        self.context_data = context_data
        self.start_time = None
    
    def __enter__(self):
        context = LogContext(
            module=self.logger.logger.name,
            operation=self.operation,
            additional_data=self.context_data
        )
        self.logger.push_context(context)
        self.start_time = time.time()
        self.logger.info(f"Starting operation: {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time if self.start_time else 0
        
        if exc_type is not None:
            self.logger.exception(f"Operation failed: {self.operation}", 
                                extra={"duration": duration, "error_type": exc_type.__name__})
        else:
            self.logger.info(f"Operation completed: {self.operation}", 
                           extra={"duration": duration})
        
        self.logger.pop_context()


def log_function_calls(logger: DebugLogger = None):
    """Decorator to automatically log function calls."""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            func_logger = logger or get_logger(func.__module__)
            
            # Log function entry
            func_logger.log_function_entry(func.__name__, args, kwargs)
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                func_logger.log_function_exit(func.__name__, result, duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                func_logger.exception(f"Function {func.__name__} raised exception", 
                                    extra={"duration": duration})
                raise
        
        return wrapper
    return decorator


def setup_application_logging(log_level: str = "DEBUG",
                            log_directory: str = "logs",
                            enable_structured_logging: bool = False,
                            enable_performance_tracking: bool = True) -> Dict[str, DebugLogger]:
    """
    Set up application-wide logging configuration.
    
    Args:
        log_level: Default logging level for all loggers
        log_directory: Directory for log files
        enable_structured_logging: Enable JSON structured logging
        enable_performance_tracking: Enable performance tracking
    
    Returns:
        Dictionary of configured loggers by component name
    """
    log_dir = Path(log_directory)
    log_dir.mkdir(exist_ok=True)
    
    loggers = {}
    
    # Simplified component configurations - only 2 log files
    components = {
        # Application components (MCP server, RAG, code analyzer, etc.) - all use application.log
        "main": {"file": "application.log", "console": True},
        "server": {"file": "application.log", "console": False},
        "git": {"file": "application.log", "console": False},
        "rag": {"file": "application.log", "console": False},
        "llm": {"file": "application.log", "console": False},
        "code_analyzer": {"file": "application.log", "console": False},
        "coder_agent": {"file": "application.log", "console": False},
        "workflow": {"file": "application.log", "console": False},
        "health_check": {"file": "application.log", "console": False},
        # Web UI components - use separate web_ui.log
        "web_ui": {"file": "web_ui.log", "console": False},
    }
    
    for component, config in components.items():
        logger = DebugLogger(
            name=component,
            level=log_level,
            log_file=log_dir / config["file"],
            enable_console=config["console"],
            enable_file=True,
            enable_structured=enable_structured_logging
        )
        loggers[component] = logger
    
    # Suppress noisy third-party loggers
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("git").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    
    # Log successful setup
    main_logger = loggers["main"]
    main_logger.info("Application logging initialized", 
                    extra={"log_level": log_level, "log_directory": str(log_dir),
                          "structured_logging": enable_structured_logging})
    
    return loggers


# Global logger registry
_loggers: Dict[str, DebugLogger] = {}


def get_logger(name: str = None, **kwargs) -> DebugLogger:
    """
    Get or create a logger instance.
    
    Args:
        name: Logger name (defaults to calling module)
        **kwargs: Additional arguments for logger creation
    
    Returns:
        DebugLogger instance
    """
    if name is None:
        # Get calling module name
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'unknown')
    
    if name not in _loggers:
        _loggers[name] = DebugLogger(name=name, **kwargs)
    
    return _loggers[name]


def setup_debug_environment():
    """Set up enhanced debug environment."""
    os.environ['PYTHONDEVMODE'] = '1'  # Enable Python development mode
    os.environ['PYTHONASYNCIODEBUG'] = '1'  # Enable asyncio debugging
    
    # Set up comprehensive logging
    loggers = setup_application_logging(
        log_level="DEBUG",
        enable_structured_logging=True,
        enable_performance_tracking=True
    )
    
    main_logger = loggers["main"]
    main_logger.info("Debug environment configured")
    
    return loggers


if __name__ == "__main__":
    # Test the logging system
    loggers = setup_debug_environment()
    
    # Test basic logging
    logger = get_logger("test")
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    # Test context management
    with logger.context_manager("test_operation", user_id="test_user"):
        logger.info("Inside context")
        logger.log_variable("test_var", {"key": "value"})
    
    # Test performance tracking
    with logger.performance_tracker.time_context("test_timer"):
        time.sleep(0.1)
    
    logger.info("Logging test completed")
