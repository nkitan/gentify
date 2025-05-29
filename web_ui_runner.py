#!/usr/bin/env python3
"""
Code Development Assistant Web UI Launcher
=========================================

This script launches the Flask web interface for the Code Development Assistant.
It handles environment setup, dependency checking, and graceful error handling.

Usage:
    python web_ui_runner.py [--port PORT] [--host HOST] [--debug]

Examples:
    python web_ui_runner.py                    # Start on localhost:5000
    python web_ui_runner.py --port 8080        # Start on port 8080
    python web_ui_runner.py --debug            # Start with debug mode
"""
import os
import sys
import argparse
import signal
from pathlib import Path

def setup_environment():
    """Setup the Python environment and paths."""
    project_root = Path(__file__).parent
    src_dir = project_root / "src"
    web_ui_dir = project_root / "web_ui"
    
    # Validate directories exist
    if not src_dir.exists():
        print(f"❌ Source directory not found: {src_dir}")
        return False, None, None
    
    if not web_ui_dir.exists():
        print(f"❌ Web UI directory not found: {web_ui_dir}")
        return False, None, None
    
    # Add src directory to Python path
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    
    # Set environment variables
    os.environ['PYTHONPATH'] = str(src_dir)
    
    return True, project_root, web_ui_dir

def check_dependencies():
    """Check if required dependencies are available."""
    print("🔍 Checking dependencies...")
    
    required_packages = ['flask']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Missing required packages: {', '.join(missing_packages)}")
        print("Install them using: uv pip install " + " ".join(missing_packages))
        return False
    
    return True

def validate_web_ui_files(web_ui_dir):
    """Validate that essential web UI files exist."""
    print("🔍 Validating web UI files...")
    
    essential_files = [
        'app.py',
        'templates/base.html',
        'templates/index.html'
    ]
    
    missing_files = []
    for file_path in essential_files:
        full_path = web_ui_dir / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n❌ Missing essential files: {', '.join(missing_files)}")
        return False
    
    return True

def start_flask_app(web_ui_dir, host='127.0.0.1', port=5000, debug=False):
    """Start the Flask application."""
    # Change to web_ui directory
    original_cwd = os.getcwd()
    os.chdir(web_ui_dir)
    
    try:
        # Import and start the Flask app
        from web_ui import app
        
        print(f"\n🚀 Starting Code Development Assistant Web UI...")
        print(f"🌐 Server: http://{host}:{port}")
        print(f"🔧 Debug mode: {'ON' if debug else 'OFF'}")
        print("📝 Press Ctrl+C to stop the server")
        print("-" * 50)
        
        # Set up signal handler for graceful shutdown
        def signal_handler(sig, frame):
            print("\n\n🛑 Shutting down web server...")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        # Start the Flask application
        app.app.run(host=host, port=port, debug=debug, use_reloader=False)
        
    except ImportError as e:
        print(f"❌ Failed to import Flask app: {e}")
        return False
    except Exception as e:
        print(f"❌ Failed to start Flask app: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Restore original working directory
        os.chdir(original_cwd)
    
    return True

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Code Development Assistant Web UI Launcher',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--host', default='127.0.0.1', 
                      help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=5000,
                      help='Port to bind to (default: 5000)')
    parser.add_argument('--debug', action='store_true',
                      help='Enable debug mode')
    
    args = parser.parse_args()
    
    print("Code Development Assistant Web UI Launcher")
    print("=" * 45)
    
    # Setup environment
    success, project_root, web_ui_dir = setup_environment()
    if not success:
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Validate files
    if not validate_web_ui_files(web_ui_dir):
        sys.exit(1)
    
    print("✅ All checks passed!")
    
    # Start the Flask application
    success = start_flask_app(web_ui_dir, args.host, args.port, args.debug)
    
    if not success:
        sys.exit(1)

if __name__ == '__main__':
    main()
