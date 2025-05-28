# Import server only when needed to avoid dependency issues in web UI
import asyncio

def main():
    """Main entry point for the package."""
    from . import server  # Import here to avoid circular dependencies
    asyncio.run(server.main())

# Optionally expose other important items at package level
__all__ = ['main']