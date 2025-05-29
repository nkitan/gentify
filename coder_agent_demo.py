#!/usr/bin/env python3
"""
Coder Agent Demo Script

This script demonstrates how to use the AI-driven coder agent with various functionalities
including code generation, analysis, Git operations, and more.
"""
import asyncio
import json
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from code_dev_assistant.coder_agent import CoderAgent, AgentResponse
from code_dev_assistant.llm_client import CodeLLM
from code_dev_assistant.rag_system import CodeRAG
from code_dev_assistant.code_analyzer import CodeAnalyzer
from code_dev_assistant.git_tools import GitTools


async def demo_coder_agent():
    """Demonstrate the capabilities of the coder agent."""
    print("🤖 Initializing Coder Agent Demo...")
    print("=" * 60)
    
    # Initialize the coder agent
    agent = CoderAgent()
    
    # Initialize project context
    print("\n1. Initializing Project Context...")
    response = await agent.initialize_project_context(".")
    print(f"Status: {'✅ Success' if response.success else '❌ Failed'}")
    print(f"Message: {response.message}")
    if response.suggestions:
        print("Suggestions:")
        for suggestion in response.suggestions:
            print(f"  • {suggestion}")
    
    # Demo scenarios
    demo_scenarios = [
        {
            "title": "Code Generation",
            "request": "Generate a Python function that calculates the Fibonacci sequence up to n numbers",
            "context": {"language": "python", "style": "documented"}
        },
        {
            "title": "Code Analysis",
            "request": "Analyze the structure of the current codebase and identify main components",
            "context": {"type": "general"}
        },
        {
            "title": "Git Operations",
            "request": "Show the current Git status of the repository",
            "context": {}
        },
        {
            "title": "Code Review",
            "request": "Review the server.py file for potential improvements",
            "context": {"focus_areas": ["performance", "maintainability"]}
        },
        {
            "title": "Documentation",
            "request": "Generate documentation for the CoderAgent class",
            "context": {"doc_type": "api_docs"}
        },
        {
            "title": "Bug Fixing",
            "request": "Help debug a potential import error in the coder_agent module",
            "context": {"error_message": "ModuleNotFoundError: No module named 'code_dev_assistant'"}
        },
        {
            "title": "Refactoring",
            "request": "Suggest refactoring improvements for better code organization",
            "context": {"goals": ["modularity", "readability"]}
        },
        {
            "title": "Testing",
            "request": "Generate unit tests for the AgentResponse class",
            "context": {"test_framework": "pytest", "coverage_level": "comprehensive"}
        },
        {
            "title": "Chat about Code",
            "request": "Explain the difference between async and sync programming in Python",
            "context": {}
        }
    ]
    
    for i, scenario in enumerate(demo_scenarios, 2):
        print(f"\n{i}. {scenario['title']}")
        print("-" * 40)
        print(f"Request: {scenario['request']}")
        
        try:
            response = await agent.process_natural_language_request(
                scenario['request'], 
                scenario['context']
            )
            
            print(f"Status: {'✅ Success' if response.success else '❌ Failed'}")
            print(f"Message: {response.message}")
            
            if response.data:
                print("Response Data:")
                for key, value in response.data.items():
                    if isinstance(value, str) and len(value) > 200:
                        print(f"  {key}: {value[:200]}...")
                    else:
                        print(f"  {key}: {value}")
            
            if response.suggestions:
                print("Suggestions:")
                for suggestion in response.suggestions[:3]:  # Limit to first 3
                    print(f"  • {suggestion}")
            
            if response.next_actions:
                print("Next Actions:")
                for action in response.next_actions[:3]:  # Limit to first 3
                    print(f"  → {action}")
                    
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print()
    
    print("=" * 60)
    print("🎉 Coder Agent Demo Complete!")
    print("\nThe coder agent provides AI-driven assistance for:")
    print("• Code generation and explanation")
    print("• Code review and refactoring")
    print("• Bug fixing and debugging")
    print("• Documentation generation")
    print("• Test creation")
    print("• Code analysis and metrics")
    print("• Git operations")
    print("• Project setup guidance")
    print("• Interactive code chat")


async def interactive_mode():
    """Run the coder agent in interactive mode."""
    print("🤖 Coder Agent Interactive Mode")
    print("Type 'help' for available commands, 'quit' to exit")
    print("=" * 50)
    
    agent = CoderAgent()
    
    # Initialize project
    print("Initializing project context...")
    await agent.initialize_project_context(".")
    print("✅ Ready! You can now ask me anything about your code.")
    print()
    
    while True:
        try:
            user_input = input("🔍 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            elif user_input.lower() == 'help':
                print_help()
                continue
            elif not user_input:
                continue
            
            print("🤖 Agent: Processing your request...")
            response = await agent.process_natural_language_request(user_input)
            
            print(f"\n{'✅' if response.success else '❌'} {response.message}")
            
            if response.data:
                for key, value in response.data.items():
                    if isinstance(value, str):
                        if len(value) > 500:
                            print(f"\n{key}:\n{value[:500]}...\n[Content truncated for display]")
                        else:
                            print(f"\n{key}:\n{value}")
                    else:
                        print(f"\n{key}: {value}")
            
            if response.suggestions:
                print("\n💡 Suggestions:")
                for suggestion in response.suggestions:
                    print(f"  • {suggestion}")
            
            print("\n" + "-" * 50)
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")


def print_help():
    """Print help information."""
    print("""
🤖 Coder Agent Help

Available Commands:
  help - Show this help message
  quit/exit/q - Exit the interactive mode

Example Requests:
  • "Generate a Python function to sort a list"
  • "Review the main.py file for improvements"
  • "Show Git status"
  • "Explain how the RAG system works"
  • "Create unit tests for the User class"
  • "Fix the import error in module X"
  • "Refactor this code for better performance"
  • "Generate API documentation"
  • "Analyze code complexity in src/ directory"

The agent can handle natural language requests for:
- Code generation and explanation
- Code review and refactoring
- Bug fixing and debugging
- Documentation generation
- Test creation
- Git operations
- Code analysis
- General programming questions
""")


async def quick_test():
    """Quick test of agent functionality."""
    print("🧪 Quick Agent Test")
    agent = CoderAgent()
    
    # Test agent status
    tools = agent.get_agent_tools()
    status_response = await agent.execute_agent_tool("get_agent_status", {})
    print("Agent Status:", status_response[0].text)
    
    # Test simple request
    response = await agent.process_natural_language_request(
        "What is the purpose of this codebase?"
    )
    print(f"\nTest Response: {'✅' if response.success else '❌'}")
    print(f"Message: {response.message}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "demo":
            asyncio.run(demo_coder_agent())
        elif sys.argv[1] == "interactive":
            asyncio.run(interactive_mode())
        elif sys.argv[1] == "test":
            asyncio.run(quick_test())
        else:
            print("Usage: python coder_agent_demo.py [demo|interactive|test]")
    else:
        print("🤖 Coder Agent Demo")
        print("Usage:")
        print("  python coder_agent_demo.py demo        - Run demonstration scenarios")
        print("  python coder_agent_demo.py interactive - Interactive chat mode")
        print("  python coder_agent_demo.py test        - Quick functionality test")
