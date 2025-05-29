#!/usr/bin/env python3
"""
Command Line Interface for the AI-Driven Coder Agent

This CLI provides a comprehensive interface for interacting with the coder agent,
including project initialization, code generation, workflow management, and more.
"""
import asyncio
import argparse
import json
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import rich
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from rich.layout import Layout
from rich.live import Live

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from code_dev_assistant.coder_agent import CoderAgent, AgentResponse
from code_dev_assistant.workflow_orchestrator import WorkflowOrchestrator, WorkflowStatus
from code_dev_assistant.config import get_config, AssistantConfig


console = Console()


class CoderAgentCLI:
    """Command Line Interface for the Coder Agent."""
    
    def __init__(self):
        """Initialize the CLI."""
        self.config = get_config()
        self.agent = None
        self.orchestrator = None
        
    async def initialize_agent(self):
        """Initialize the coder agent and orchestrator."""
        if not self.agent:
            with console.status("[bold blue]Initializing AI Coder Agent..."):
                self.agent = CoderAgent()
                self.orchestrator = WorkflowOrchestrator(self.agent)
                # Initialize project context
                await self.agent.initialize_project_context(
                    self.config.workspace_path or "."
                )
            console.print("✅ [bold green]Coder Agent initialized successfully!")
    
    async def cmd_init(self, args):
        """Initialize a new project with the coder agent."""
        console.print(Panel.fit(
            "[bold blue]🚀 Project Initialization[/bold blue]\n"
            "Setting up your project with AI assistance",
            title="Project Setup"
        ))
        
        await self.initialize_agent()
        
        project_path = args.path or "."
        project_type = args.type or "python"
        
        # Create project setup workflow
        workflow_id = self.orchestrator.create_predefined_workflow(
            "project_setup",
            {
                "project_type": project_type,
                "project_path": project_path,
                "features": args.features or []
            }
        )
        
        console.print(f"📋 Created project setup workflow: {workflow_id}")
        
        if Confirm.ask("Execute the setup workflow now?"):
            await self._execute_workflow_with_progress(workflow_id)
    
    async def cmd_generate(self, args):
        """Generate code based on description."""
        await self.initialize_agent()
        
        description = args.description
        if not description:
            description = Prompt.ask("📝 Describe what you want to generate")
        
        console.print(f"🤖 Generating code: {description}")
        
        with console.status("[bold blue]Generating code..."):
            response = await self.agent.process_natural_language_request(
                f"Generate {args.language or 'Python'} code: {description}",
                {
                    "language": args.language or "python",
                    "style": args.style or "clean",
                    "context": {"file_path": args.file} if args.file else {}
                }
            )
        
        self._display_response(response)
        
        # Optionally save to file
        if response.success and response.data and args.output:
            self._save_generated_code(response.data, args.output)
    
    async def cmd_review(self, args):
        """Review code for improvements."""
        await self.initialize_agent()
        
        files = args.files or ["."]
        focus_areas = args.focus or ["security", "performance", "maintainability"]
        
        console.print(f"🔍 Reviewing files: {', '.join(files)}")
        console.print(f"📊 Focus areas: {', '.join(focus_areas)}")
        
        # Create code review workflow
        workflow_id = self.orchestrator.create_predefined_workflow(
            "code_review_process",
            {
                "files": files,
                "focus_areas": focus_areas
            }
        )
        
        await self._execute_workflow_with_progress(workflow_id)
    
    async def cmd_fix(self, args):
        """Fix bugs or issues in code."""
        await self.initialize_agent()
        
        description = args.description
        if not description:
            description = Prompt.ask("🐛 Describe the bug or issue")
        
        error_message = args.error or ""
        
        console.print(f"🔧 Investigating bug: {description}")
        
        # Create bug investigation workflow
        workflow_id = self.orchestrator.create_predefined_workflow(
            "bug_investigation",
            {
                "bug_description": description,
                "error_message": error_message,
                "affected_files": args.files or []
            }
        )
        
        await self._execute_workflow_with_progress(workflow_id)
    
    async def cmd_refactor(self, args):
        """Refactor code for improvements."""
        await self.initialize_agent()
        
        files = args.files or ["."]
        goals = args.goals or ["readability", "performance", "maintainability"]
        
        console.print(f"🔄 Refactoring files: {', '.join(files)}")
        console.print(f"🎯 Goals: {', '.join(goals)}")
        
        workflow_id = self.orchestrator.create_predefined_workflow(
            "refactoring_task",
            {
                "files": files,
                "goals": goals
            }
        )
        
        await self._execute_workflow_with_progress(workflow_id)
    
    async def cmd_feature(self, args):
        """Develop a complete feature."""
        await self.initialize_agent()
        
        feature_name = args.name
        if not feature_name:
            feature_name = Prompt.ask("✨ Feature name")
        
        description = args.description
        if not description:
            description = Prompt.ask("📋 Feature description")
        
        console.print(f"🏗️ Developing feature: {feature_name}")
        console.print(f"📝 Description: {description}")
        
        # Create feature development workflow
        workflow_id = self.orchestrator.create_predefined_workflow(
            "feature_development",
            {
                "feature_name": feature_name,
                "description": description,
                "requirements": args.requirements or []
            }
        )
        
        await self._execute_workflow_with_progress(workflow_id)
    
    async def cmd_chat(self, args):
        """Start interactive chat with the coder agent."""
        await self.initialize_agent()
        
        console.print(Panel.fit(
            "[bold blue]💬 AI Coder Chat[/bold blue]\n"
            "Ask me anything about your code!\n"
            "Type 'quit' to exit, 'help' for commands",
            title="Interactive Chat"
        ))
        
        while True:
            try:
                question = Prompt.ask("\n[bold blue]You[/bold blue]")
                
                if question.lower() in ['quit', 'exit', 'q']:
                    console.print("👋 [bold]Goodbye![/bold]")
                    break
                elif question.lower() == 'help':
                    self._show_chat_help()
                    continue
                elif not question.strip():
                    continue
                
                with console.status("[bold blue]Thinking..."):
                    response = await self.agent.process_natural_language_request(question)
                
                console.print(f"\n[bold green]🤖 Agent[/bold green]:")
                self._display_response(response, compact=True)
                
            except KeyboardInterrupt:
                console.print("\n👋 [bold]Goodbye![/bold]")
                break
            except Exception as e:
                console.print(f"❌ [bold red]Error:[/bold red] {str(e)}")
    
    async def cmd_workflow(self, args):
        """Manage workflows."""
        await self.initialize_agent()
        
        if args.workflow_action == "list":
            self._list_workflows()
        elif args.workflow_action == "status":
            if not args.workflow_id:
                console.print("❌ [bold red]Error:[/bold red] Workflow ID required")
                return
            self._show_workflow_status(args.workflow_id)
        elif args.workflow_action == "execute":
            if not args.workflow_id:
                console.print("❌ [bold red]Error:[/bold red] Workflow ID required")
                return
            await self._execute_workflow_with_progress(args.workflow_id)
    
    async def cmd_analyze(self, args):
        """Analyze code structure and metrics."""
        await self.initialize_agent()
        
        target = args.target or "."
        analysis_type = args.type or "general"
        
        console.print(f"📊 Analyzing: {target}")
        
        with console.status("[bold blue]Analyzing code..."):
            response = await self.agent.process_natural_language_request(
                f"Analyze the {analysis_type} aspects of {target}",
                {"type": analysis_type, "target": target}
            )
        
        self._display_response(response)
    
    async def cmd_test(self, args):
        """Generate or run tests."""
        await self.initialize_agent()
        
        if args.test_action == "generate":
            target_file = args.file
            if not target_file:
                target_file = Prompt.ask("📁 File to generate tests for")
            
            console.print(f"🧪 Generating tests for: {target_file}")
            
            response = await self.agent.process_natural_language_request(
                f"Generate comprehensive tests for {target_file}",
                {
                    "test_framework": args.framework or "pytest",
                    "coverage_level": args.coverage or "comprehensive"
                }
            )
            
            self._display_response(response)
    
    async def cmd_git(self, args):
        """Git operations with AI assistance."""
        await self.initialize_agent()
        
        operation = args.git_operation
        
        if operation == "status":
            response = await self.agent.process_natural_language_request("Show git status")
        elif operation == "commit":
            message = args.message or Prompt.ask("💬 Commit message")
            response = await self.agent.process_natural_language_request(
                f"Commit changes with message: {message}"
            )
        elif operation == "analyze":
            response = await self.agent.process_natural_language_request(
                "Analyze recent git changes and suggest improvements"
            )
        else:
            console.print(f"❌ [bold red]Error:[/bold red] Unknown git operation: {operation}")
            return
        
        self._display_response(response)
    
    def _display_response(self, response: AgentResponse, compact: bool = False):
        """Display agent response in a formatted way."""
        if response.success:
            console.print(f"✅ [bold green]Success:[/bold green] {response.message}")
            
            if response.data:
                for key, value in response.data.items():
                    if isinstance(value, str) and len(value) > 200 and not compact:
                        # Display code with syntax highlighting
                        if 'code' in key.lower():
                            syntax = Syntax(value, "python", theme="monokai", line_numbers=True)
                            console.print(Panel(syntax, title=f"📝 {key.title()}"))
                        else:
                            console.print(Panel(value, title=f"📄 {key.title()}"))
                    else:
                        display_value = value[:200] + "..." if len(str(value)) > 200 and compact else value
                        console.print(f"[bold]{key}:[/bold] {display_value}")
            
            if response.suggestions and not compact:
                console.print("\n💡 [bold blue]Suggestions:[/bold blue]")
                for suggestion in response.suggestions:
                    console.print(f"  • {suggestion}")
            
            if response.next_actions and not compact:
                console.print("\n🎯 [bold blue]Next Actions:[/bold blue]")
                for action in response.next_actions:
                    console.print(f"  → {action}")
        else:
            console.print(f"❌ [bold red]Error:[/bold red] {response.message}")
    
    def _save_generated_code(self, data: Dict[str, Any], output_file: str):
        """Save generated code to a file."""
        code_content = None
        
        # Extract code from response data
        for key, value in data.items():
            if 'code' in key.lower() and isinstance(value, str):
                code_content = value
                break
        
        if code_content:
            try:
                with open(output_file, 'w') as f:
                    f.write(code_content)
                console.print(f"💾 [bold green]Code saved to:[/bold green] {output_file}")
            except Exception as e:
                console.print(f"❌ [bold red]Error saving file:[/bold red] {str(e)}")
        else:
            console.print("❌ [bold red]No code content found to save[/bold red]")
    
    async def _execute_workflow_with_progress(self, workflow_id: str):
        """Execute workflow with progress display."""
        workflow = self.orchestrator.workflows.get(workflow_id)
        if not workflow:
            console.print(f"❌ [bold red]Workflow not found:[/bold red] {workflow_id}")
            return
        
        console.print(f"🔄 [bold blue]Executing workflow:[/bold blue] {workflow.name}")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            task = progress.add_task("Starting workflow...", total=len(workflow.steps))
            
            def progress_callback(wf, step):
                progress.update(task, description=f"Completed: {step.name}")
                progress.advance(task)
            
            success = await self.orchestrator.execute_workflow(workflow_id, progress_callback)
            
            if success:
                console.print("✅ [bold green]Workflow completed successfully![/bold green]")
                self._show_workflow_results(workflow_id)
            else:
                console.print("❌ [bold red]Workflow failed![/bold red]")
                self._show_workflow_status(workflow_id)
    
    def _list_workflows(self):
        """List all workflows."""
        workflows = self.orchestrator.list_workflows()
        
        if not workflows:
            console.print("📋 No workflows found")
            return
        
        table = Table(title="🔄 Workflows")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Status", style="green")
        table.add_column("Steps", justify="right")
        table.add_column("Created", style="blue")
        
        for workflow in workflows:
            status_color = {
                "completed": "green",
                "running": "yellow",
                "failed": "red",
                "pending": "blue"
            }.get(workflow["status"], "white")
            
            table.add_row(
                workflow["workflow_id"][:8],
                workflow["name"],
                f"[{status_color}]{workflow['status']}[/{status_color}]",
                str(workflow["step_count"]),
                workflow["created_at"].strftime("%Y-%m-%d %H:%M")
            )
        
        console.print(table)
    
    def _show_workflow_status(self, workflow_id: str):
        """Show detailed workflow status."""
        status = self.orchestrator.get_workflow_status(workflow_id)
        
        if not status:
            console.print(f"❌ [bold red]Workflow not found:[/bold red] {workflow_id}")
            return
        
        console.print(Panel.fit(
            f"[bold blue]Workflow:[/bold blue] {status['name']}\n"
            f"[bold blue]Status:[/bold blue] {status['status']}\n"
            f"[bold blue]Started:[/bold blue] {status.get('started_at', 'Not started')}\n"
            f"[bold blue]Completed:[/bold blue] {status.get('completed_at', 'Not completed')}",
            title=f"📊 Workflow Status ({workflow_id[:8]})"
        ))
        
        # Show step details
        table = Table(title="📝 Workflow Steps")
        table.add_column("Step", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Started", style="blue")
        table.add_column("Completed", style="blue")
        table.add_column("Error", style="red")
        
        for step in status["steps"]:
            status_color = {
                "completed": "green",
                "running": "yellow",
                "failed": "red",
                "pending": "blue"
            }.get(step["status"], "white")
            
            table.add_row(
                step["name"],
                f"[{status_color}]{step['status']}[/{status_color}]",
                str(step.get("started_at", "—")),
                str(step.get("completed_at", "—")),
                step.get("error", "—")
            )
        
        console.print(table)
    
    def _show_workflow_results(self, workflow_id: str):
        """Show workflow execution results."""
        workflow = self.orchestrator.workflows.get(workflow_id)
        if not workflow:
            return
        
        console.print(Panel.fit(
            "[bold green]🎉 Workflow Results[/bold green]",
            title="Summary"
        ))
        
        for step in workflow.steps:
            if step.result and step.status.value == "completed":
                console.print(f"\n[bold blue]📋 {step.name}:[/bold blue]")
                if hasattr(step.result, 'message'):
                    console.print(f"  {step.result.message}")
    
    def _show_chat_help(self):
        """Show chat help."""
        help_text = """
[bold blue]💬 Chat Commands:[/bold blue]

• Ask about code: "Explain how the authentication works"
• Generate code: "Create a function to validate email addresses"  
• Review code: "Review this function for security issues"
• Debug issues: "Why is my code throwing this error?"
• Get suggestions: "How can I improve the performance of this code?"
• Git operations: "Show me the git status"
• General questions: "What's the difference between lists and tuples?"

[bold yellow]Special Commands:[/bold yellow]
• quit/exit/q - Exit chat
• help - Show this help
        """
        console.print(Panel(help_text, title="Help"))


def create_parser():
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="AI-Driven Coder Agent CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  agent-cli init --type python                    # Initialize Python project
  agent-cli generate "sort function" --output sort.py  # Generate code
  agent-cli review --files src/ --focus security  # Review code
  agent-cli fix "login not working" --error "..."  # Fix bug
  agent-cli feature --name "user-auth"            # Develop feature
  agent-cli chat                                   # Interactive chat
  agent-cli workflow list                          # List workflows
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize project')
    init_parser.add_argument('--path', '-p', default='.', help='Project path')
    init_parser.add_argument('--type', '-t', choices=['python', 'javascript', 'typescript', 'java'], 
                           default='python', help='Project type')
    init_parser.add_argument('--features', nargs='*', help='Project features')
    
    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate code')
    gen_parser.add_argument('description', nargs='?', help='What to generate')
    gen_parser.add_argument('--language', '-l', help='Programming language')
    gen_parser.add_argument('--style', '-s', choices=['clean', 'documented', 'performant', 'simple'])
    gen_parser.add_argument('--file', '-f', help='Context file')
    gen_parser.add_argument('--output', '-o', help='Output file')
    
    # Review command
    review_parser = subparsers.add_parser('review', help='Review code')
    review_parser.add_argument('--files', nargs='*', help='Files to review')
    review_parser.add_argument('--focus', nargs='*', help='Focus areas')
    
    # Fix command
    fix_parser = subparsers.add_parser('fix', help='Fix bugs')
    fix_parser.add_argument('description', nargs='?', help='Bug description')
    fix_parser.add_argument('--error', '-e', help='Error message')
    fix_parser.add_argument('--files', nargs='*', help='Affected files')
    
    # Refactor command
    refactor_parser = subparsers.add_parser('refactor', help='Refactor code')
    refactor_parser.add_argument('--files', nargs='*', help='Files to refactor')
    refactor_parser.add_argument('--goals', nargs='*', help='Refactoring goals')
    
    # Feature command
    feature_parser = subparsers.add_parser('feature', help='Develop feature')
    feature_parser.add_argument('--name', '-n', help='Feature name')
    feature_parser.add_argument('--description', '-d', help='Feature description')
    feature_parser.add_argument('--requirements', nargs='*', help='Requirements')
    
    # Chat command
    subparsers.add_parser('chat', help='Interactive chat')
    
    # Workflow command
    workflow_parser = subparsers.add_parser('workflow', help='Manage workflows')
    workflow_parser.add_argument('workflow_action', choices=['list', 'status', 'execute'])
    workflow_parser.add_argument('--workflow-id', help='Workflow ID')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze code')
    analyze_parser.add_argument('--target', '-t', help='Target to analyze')
    analyze_parser.add_argument('--type', choices=['general', 'security', 'performance', 'structure'])
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Generate or run tests')
    test_parser.add_argument('test_action', choices=['generate', 'run'])
    test_parser.add_argument('--file', '-f', help='File to test')
    test_parser.add_argument('--framework', choices=['pytest', 'unittest', 'jest'])
    test_parser.add_argument('--coverage', choices=['basic', 'comprehensive', 'edge_cases'])
    
    # Git command
    git_parser = subparsers.add_parser('git', help='Git operations')
    git_parser.add_argument('git_operation', choices=['status', 'commit', 'analyze'])
    git_parser.add_argument('--message', '-m', help='Commit message')
    
    return parser


async def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = CoderAgentCLI()
    
    try:
        # Route to appropriate command
        command_method = getattr(cli, f'cmd_{args.command}', None)
        if command_method:
            await command_method(args)
        else:
            console.print(f"❌ [bold red]Unknown command:[/bold red] {args.command}")
    
    except KeyboardInterrupt:
        console.print("\n👋 [bold]Operation cancelled[/bold]")
    except Exception as e:
        console.print(f"❌ [bold red]Error:[/bold red] {str(e)}")
        if "--debug" in sys.argv:
            raise


if __name__ == "__main__":
    asyncio.run(main())
