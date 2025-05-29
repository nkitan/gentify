#!/usr/bin/env python3
"""
Health check script for the Code Development Assistant services.
"""
import sys
import time
import requests
import subprocess
import json
from pathlib import Path


def check_web_ui(host="localhost", port=5000, timeout=5):
    """Check if the web UI is responding."""
    try:
        response = requests.get(f"http://{host}:{port}/", timeout=timeout)
        if response.status_code == 200:
            print("✅ Web UI is healthy")
            return True
        else:
            print(f"❌ Web UI returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Web UI health check failed: {e}")
        return False


def check_mcp_server():
    """Check if the MCP server can be initialized."""
    try:
        # Try to import and initialize basic components
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        from code_dev_assistant.config import get_config
        from code_dev_assistant.server import server
        
        # Basic configuration check
        config = get_config()
        if config:
            print("✅ MCP server configuration is valid")
            return True
        else:
            print("❌ MCP server configuration failed")
            return False
    except Exception as e:
        print(f"❌ MCP server health check failed: {e}")
        return False


def check_database():
    """Check if the RAG database is accessible."""
    try:
        db_path = Path("./code_rag_db")
        if db_path.exists():
            print("✅ RAG database directory exists")
            return True
        else:
            print("❌ RAG database directory not found")
            return False
    except Exception as e:
        print(f"❌ Database health check failed: {e}")
        return False


def check_ollama_connection(host="ollama", port=11434):
    """Check if Ollama service is accessible."""
    try:
        response = requests.get(f"http://{host}:{port}/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama service is accessible")
            return True
        else:
            print(f"❌ Ollama service returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Ollama service health check failed: {e}")
        return False


def main():
    """Main health check function."""
    print("🔍 Running health checks...")
    
    checks = []
    
    # Check based on environment or service type
    service_type = sys.argv[1] if len(sys.argv) > 1 else "web"
    
    if service_type == "web":
        checks.append(("Web UI", check_web_ui))
        checks.append(("Database", check_database))
        checks.append(("Ollama", check_ollama_connection))
    elif service_type == "mcp":
        checks.append(("MCP Server", check_mcp_server))
        checks.append(("Database", check_database))
    else:
        # Run all checks
        checks.extend([
            ("Web UI", check_web_ui),
            ("MCP Server", check_mcp_server),
            ("Database", check_database),
            ("Ollama", check_ollama_connection)
        ])
    
    failed_checks = []
    
    for check_name, check_func in checks:
        print(f"\n🔍 Checking {check_name}...")
        try:
            if not check_func():
                failed_checks.append(check_name)
        except Exception as e:
            print(f"❌ {check_name} check threw exception: {e}")
            failed_checks.append(check_name)
    
    print("\n" + "="*50)
    if failed_checks:
        print(f"❌ Health check failed. Failed checks: {', '.join(failed_checks)}")
        sys.exit(1)
    else:
        print("✅ All health checks passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
