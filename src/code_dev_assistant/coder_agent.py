"""
Intelligent Coder Agent that orchestrates various AI-driven functionalities
using the MCP server components for comprehensive code development assistance.
"""
import asyncio
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
import mcp.types as types

from .llm_client import CodeLLM
from .rag_system import CodeRAG
from .code_analyzer import CodeAnalyzer
from .git_tools import GitTools


class TaskType(Enum):
    """Types of coding tasks the agent can perform."""
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    BUG_FIXING = "bug_fixing"
    REFACTORING = "refactoring"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    ANALYSIS = "analysis"
    GIT_OPERATIONS = "git_operations"
    PROJECT_SETUP = "project_setup"
    CHAT = "chat"


@dataclass
class AgentTask:
    """Represents a task for the coder agent."""
    task_id: str
    task_type: TaskType
    description: str
    context: Dict[str, Any]
    priority: int = 1
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class AgentResponse:
    """Response from the coder agent."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None
    code_changes: Optional[List[Dict[str, Any]]] = None
    next_actions: Optional[List[str]] = None


class CoderAgent:
    """
    Intelligent coder agent that combines RAG, LLM, code analysis, and Git tools
    to provide comprehensive AI-driven development assistance.
    """
    
    def __init__(self, 
                 llm_client: Optional[CodeLLM] = None,
                 rag_system: Optional[CodeRAG] = None,
                 code_analyzer: Optional[CodeAnalyzer] = None,
                 git_tools: Optional[GitTools] = None):
        """Initialize the coder agent with all necessary components."""
        self.llm_client = llm_client or CodeLLM()
        self.rag_system = rag_system or CodeRAG()
        self.code_analyzer = code_analyzer or CodeAnalyzer()
        self.git_tools = git_tools or GitTools()
        
        # Agent state
        self.session_context = {}
        self.task_history = []
        self.current_project_context = None
        
    async def initialize_project_context(self, project_path: str = ".") -> AgentResponse:
        """Initialize project context by analyzing the codebase."""
        try:
            # Index codebase for RAG
            await self.rag_system.execute_rag_tool("index_codebase", {
                "directory": project_path,
                "force_reindex": False
            })
            
            # Analyze project structure
            project_info = await self.code_analyzer.execute_analysis_tool("extract_code_chunks", {
                "directory": project_path
            })
            
            # Get Git status
            git_status = await self.git_tools.execute_git_tool("git_status", {})
            
            self.current_project_context = {
                "project_path": project_path,
                "indexed_at": asyncio.get_event_loop().time(),
                "git_status": git_status,
                "project_structure": project_info
            }
            
            return AgentResponse(
                success=True,
                message="Project context initialized successfully",
                data=self.current_project_context,
                suggestions=[
                    "Ask me to analyze specific files or functions",
                    "Request code generation for new features",
                    "Get help with Git operations",
                    "Ask for code reviews or refactoring suggestions"
                ]
            )
            
        except Exception as e:
            return AgentResponse(
                success=False,
                message=f"Failed to initialize project context: {str(e)}"
            )
    
    async def process_natural_language_request(self, request: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """
        Process a natural language request and determine the appropriate action.
        This is the main entry point for user interactions.
        """
        try:
            # Analyze the request to determine task type and extract parameters
            task_analysis = await self._analyze_request(request, context)
            
            if not task_analysis["success"]:
                return AgentResponse(
                    success=False,
                    message=task_analysis["error"]
                )
            
            task_type = TaskType(task_analysis["task_type"])
            parameters = task_analysis["parameters"]
            
            # Route to appropriate handler
            if task_type == TaskType.CODE_GENERATION:
                return await self._handle_code_generation(request, parameters)
            elif task_type == TaskType.CODE_REVIEW:
                return await self._handle_code_review(request, parameters)
            elif task_type == TaskType.BUG_FIXING:
                return await self._handle_bug_fixing(request, parameters)
            elif task_type == TaskType.REFACTORING:
                return await self._handle_refactoring(request, parameters)
            elif task_type == TaskType.DOCUMENTATION:
                return await self._handle_documentation(request, parameters)
            elif task_type == TaskType.TESTING:
                return await self._handle_testing(request, parameters)
            elif task_type == TaskType.ANALYSIS:
                return await self._handle_analysis(request, parameters)
            elif task_type == TaskType.GIT_OPERATIONS:
                return await self._handle_git_operations(request, parameters)
            elif task_type == TaskType.PROJECT_SETUP:
                return await self._handle_project_setup(request, parameters)
            elif task_type == TaskType.CHAT:
                return await self._handle_chat(request, parameters)
            else:
                return AgentResponse(
                    success=False,
                    message=f"Unknown task type: {task_type}"
                )
                
        except Exception as e:
            return AgentResponse(
                success=False,
                message=f"Error processing request: {str(e)}"
            )
    
    async def _analyze_request(self, request: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze the user request to determine task type and extract parameters."""
        # Get relevant code context from RAG if available
        rag_context = ""
        try:
            if self.current_project_context:
                rag_results = await self.rag_system.execute_rag_tool("search_code", {
                    "query": request,
                    "limit": 3,
                    "similarity_threshold": 0.6
                })
                if rag_results:
                    rag_context = "\n".join([result.text for result in rag_results])
        except:
            pass
        
        # Use LLM to analyze the request
        analysis_prompt = f"""
Analyze this user request and determine the appropriate task type and parameters:

User Request: "{request}"

Available Task Types:
- code_generation: Generate new code based on requirements
- code_review: Review existing code for improvements
- bug_fixing: Debug and fix code issues
- refactoring: Improve code structure and quality
- documentation: Generate or improve documentation
- testing: Create or improve tests
- analysis: Technical analysis of code structure, dependencies, patterns, metrics, or extracting code chunks
- git_operations: Perform Git version control operations
- project_setup: Help with project initialization or configuration
- chat: General conversation, explanations about how code works, project overviews, or high-level questions

IMPORTANT GUIDELINES:
- Use "chat" for general questions like "explain how this works", "what does this do", "how does this project work"
- Use "analysis" only for technical deep-dive requests like "analyze code structure", "extract patterns", "code metrics"
- If the user asks for a general explanation or overview, use "chat" not "analysis"

Relevant Code Context:
{rag_context}

Additional Context:
{json.dumps(context or {}, indent=2)}

Please respond with a JSON object containing:
{{
    "task_type": "one of the task types above",
    "confidence": "float between 0-1",
    "parameters": {{
        "extracted parameters from the request"
    }},
    "reasoning": "explanation of your analysis"
}}
"""
        
        try:
            response = await self.llm_client._call_ollama(analysis_prompt, 
                "You are an expert at analyzing software development requests and determining appropriate actions.")
            
            # Try to parse JSON response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
                return {
                    "success": True,
                    "task_type": analysis.get("task_type", "chat"),
                    "parameters": analysis.get("parameters", {}),
                    "confidence": analysis.get("confidence", 0.5),
                    "reasoning": analysis.get("reasoning", "")
                }
            else:
                # Fallback to simple keyword matching
                return self._fallback_request_analysis(request)
                
        except Exception as e:
            return self._fallback_request_analysis(request)
    
    def _fallback_request_analysis(self, request: str) -> Dict[str, Any]:
        """Fallback request analysis using simple keyword matching."""
        request_lower = request.lower()
        
        # Check for specific technical analysis patterns first
        if any(pattern in request_lower for pattern in ["analyze code structure", "code metrics", "dependency analysis", "extract patterns", "code chunks"]):
            return {"success": True, "task_type": "analysis", "parameters": {"type": "general"}}
        
        # Check for code generation
        elif any(word in request_lower for word in ["generate", "create", "write", "implement"]):
            return {"success": True, "task_type": "code_generation", "parameters": {"description": request}}
        
        # Check for code review
        elif any(word in request_lower for word in ["review", "check", "improve", "optimize"]):
            return {"success": True, "task_type": "code_review", "parameters": {"request": request}}
        
        # Check for bug fixing
        elif any(word in request_lower for word in ["bug", "error", "fix", "debug", "issue"]):
            return {"success": True, "task_type": "bug_fixing", "parameters": {"description": request}}
        
        # Check for refactoring
        elif any(word in request_lower for word in ["refactor", "restructure", "reorganize"]):
            return {"success": True, "task_type": "refactoring", "parameters": {"goals": ["readability", "maintainability"]}}
        
        # Check for documentation (but exclude general explanation requests)
        elif any(word in request_lower for word in ["document", "docs", "comment"]) and not any(phrase in request_lower for phrase in ["explain how", "what does", "how does", "what is"]):
            return {"success": True, "task_type": "documentation", "parameters": {"type": "explanation"}}
        
        # Check for testing
        elif any(word in request_lower for word in ["test", "testing", "unittest", "pytest"]):
            return {"success": True, "task_type": "testing", "parameters": {"framework": "pytest"}}
        
        # Check for git operations
        elif any(word in request_lower for word in ["git", "commit", "branch", "push", "pull", "merge"]):
            return {"success": True, "task_type": "git_operations", "parameters": {"operation": request}}
        
        # General explanation and chat requests (including "explain how", "what does", etc.)
        else:
            return {"success": True, "task_type": "chat", "parameters": {"question": request}}
    
    async def _handle_code_generation(self, request: str, parameters: Dict[str, Any]) -> AgentResponse:
        """Handle code generation requests."""
        try:
            # Get relevant context from RAG
            context = await self._get_relevant_context(request)
            
            # Generate code using LLM
            result = await self.llm_client.execute_llm_tool("generate_code", {
                "description": parameters.get("description", request),
                "language": parameters.get("language", "python"),
                "context": context,
                "style": parameters.get("style", "clean")
            })
            
            code_content = result[0].text if result else "No code generated"
            
            return AgentResponse(
                success=True,
                message="Code generated successfully",
                data={"generated_code": code_content},
                suggestions=[
                    "Review the generated code for accuracy",
                    "Test the code before integrating",
                    "Consider adding documentation",
                    "Add unit tests for the new code"
                ],
                next_actions=[
                    "Save the code to a file",
                    "Run tests",
                    "Commit changes to Git"
                ]
            )
            
        except Exception as e:
            return AgentResponse(
                success=False,
                message=f"Code generation failed: {str(e)}"
            )
    
    async def _handle_code_review(self, request: str, parameters: Dict[str, Any]) -> AgentResponse:
        """Handle code review requests."""
        try:
            # Find code to review
            code_to_review = await self._extract_code_from_request(request, parameters)
            
            if not code_to_review:
                return AgentResponse(
                    success=False,
                    message="No code found to review. Please specify a file or provide code directly."
                )
            
            # Perform code review
            result = await self.llm_client.execute_llm_tool("review_code", {
                "code": code_to_review,
                "focus_areas": parameters.get("focus_areas", ["security", "performance", "style", "best_practices"]),
                "language": parameters.get("language", "python")
            })
            
            review_content = result[0].text if result else "No review generated"
            
            return AgentResponse(
                success=True,
                message="Code review completed",
                data={"review": review_content},
                suggestions=[
                    "Address critical security issues first",
                    "Consider performance optimizations",
                    "Update documentation if needed"
                ]
            )
            
        except Exception as e:
            return AgentResponse(
                success=False,
                message=f"Code review failed: {str(e)}"
            )
    
    async def _handle_bug_fixing(self, request: str, parameters: Dict[str, Any]) -> AgentResponse:
        """Handle bug fixing requests."""
        try:
            # Get code context and error information
            code_context = await self._extract_code_from_request(request, parameters)
            error_message = parameters.get("error_message", "")
            
            # Use LLM for debugging
            result = await self.llm_client.execute_llm_tool("debug_code", {
                "code": code_context,
                "error_message": error_message,
                "language": parameters.get("language", "python")
            })
            
            debug_content = result[0].text if result else "No debugging information generated"
            
            return AgentResponse(
                success=True,
                message="Bug analysis completed",
                data={"debug_analysis": debug_content},
                suggestions=[
                    "Test the suggested fixes",
                    "Add error handling",
                    "Consider edge cases",
                    "Add unit tests to prevent regression"
                ]
            )
            
        except Exception as e:
            return AgentResponse(
                success=False,
                message=f"Bug fixing failed: {str(e)}"
            )
    
    async def _handle_refactoring(self, request: str, parameters: Dict[str, Any]) -> AgentResponse:
        """Handle code refactoring requests."""
        try:
            code_to_refactor = await self._extract_code_from_request(request, parameters)
            
            if not code_to_refactor:
                return AgentResponse(
                    success=False,
                    message="No code found to refactor. Please specify a file or provide code directly."
                )
            
            result = await self.llm_client.execute_llm_tool("refactor_code", {
                "code": code_to_refactor,
                "goals": parameters.get("goals", ["readability", "performance", "maintainability"]),
                "language": parameters.get("language", "python")
            })
            
            refactor_content = result[0].text if result else "No refactoring suggestions generated"
            
            return AgentResponse(
                success=True,
                message="Refactoring suggestions generated",
                data={"refactored_code": refactor_content},
                suggestions=[
                    "Backup current code before applying changes",
                    "Test thoroughly after refactoring",
                    "Update documentation",
                    "Check for breaking changes"
                ]
            )
            
        except Exception as e:
            return AgentResponse(
                success=False,
                message=f"Refactoring failed: {str(e)}"
            )
    
    async def _handle_documentation(self, request: str, parameters: Dict[str, Any]) -> AgentResponse:
        """Handle documentation requests."""
        try:
            code_to_document = await self._extract_code_from_request(request, parameters)
            
            result = await self.llm_client.execute_llm_tool("generate_documentation", {
                "code": code_to_document,
                "doc_type": parameters.get("doc_type", "docstrings"),
                "language": parameters.get("language", "python")
            })
            
            doc_content = result[0].text if result else "No documentation generated"
            
            return AgentResponse(
                success=True,
                message="Documentation generated",
                data={"documentation": doc_content},
                suggestions=[
                    "Review generated documentation for accuracy",
                    "Add examples where appropriate",
                    "Update README if needed"
                ]
            )
            
        except Exception as e:
            return AgentResponse(
                success=False,
                message=f"Documentation generation failed: {str(e)}"
            )
    
    async def _handle_testing(self, request: str, parameters: Dict[str, Any]) -> AgentResponse:
        """Handle test generation requests."""
        try:
            code_to_test = await self._extract_code_from_request(request, parameters)
            
            result = await self.llm_client.execute_llm_tool("generate_tests", {
                "code": code_to_test,
                "test_framework": parameters.get("test_framework", "pytest"),
                "coverage_level": parameters.get("coverage_level", "comprehensive"),
                "language": parameters.get("language", "python")
            })
            
            test_content = result[0].text if result else "No tests generated"
            
            return AgentResponse(
                success=True,
                message="Tests generated",
                data={"tests": test_content},
                suggestions=[
                    "Run tests to ensure they pass",
                    "Add edge case tests",
                    "Consider integration tests",
                    "Set up CI/CD for automated testing"
                ]
            )
            
        except Exception as e:
            return AgentResponse(
                success=False,
                message=f"Test generation failed: {str(e)}"
            )
    
    async def _handle_analysis(self, request: str, parameters: Dict[str, Any]) -> AgentResponse:
        """Handle code analysis requests."""
        try:
            analysis_type = parameters.get("type", "general")
            
            if "file" in request.lower():
                # Analyze specific file
                file_path = self._extract_file_path_from_request(request)
                if file_path:
                    result = await self.code_analyzer.execute_analysis_tool("analyze_file", {
                        "file_path": file_path
                    })
                else:
                    return AgentResponse(
                        success=False,
                        message="Could not determine file path from request"
                    )
            else:
                # General codebase analysis
                result = await self.code_analyzer.execute_analysis_tool("extract_code_chunks", {
                    "directory": "."
                })
            
            analysis_content = result[0].text if result else "No analysis available"
            
            return AgentResponse(
                success=True,
                message="Code analysis completed",
                data={"analysis": analysis_content},
                suggestions=[
                    "Review identified patterns",
                    "Consider refactoring complex functions",
                    "Address any architectural concerns"
                ]
            )
            
        except Exception as e:
            return AgentResponse(
                success=False,
                message=f"Code analysis failed: {str(e)}"
            )
    
    async def _handle_git_operations(self, request: str, parameters: Dict[str, Any]) -> AgentResponse:
        """Handle Git operations."""
        try:
            # Determine Git operation from request
            operation = self._determine_git_operation(request)
            
            if operation == "status":
                result = await self.git_tools.execute_git_tool("git_status", {})
            elif operation == "add":
                files = parameters.get("files", ["."])
                result = await self.git_tools.execute_git_tool("git_add", {"files": files})
            elif operation == "commit":
                message = parameters.get("message", "Auto-commit by coder agent")
                result = await self.git_tools.execute_git_tool("git_commit", {"message": message})
            elif operation == "branch":
                branch_name = parameters.get("branch_name", "feature/new-branch")
                result = await self.git_tools.execute_git_tool("git_create_branch", {"branch_name": branch_name})
            else:
                return AgentResponse(
                    success=False,
                    message=f"Unsupported Git operation: {operation}"
                )
            
            git_output = result[0].text if result else "Git operation completed"
            
            return AgentResponse(
                success=True,
                message=f"Git {operation} completed",
                data={"git_output": git_output}
            )
            
        except Exception as e:
            return AgentResponse(
                success=False,
                message=f"Git operation failed: {str(e)}"
            )
    
    async def _handle_project_setup(self, request: str, parameters: Dict[str, Any]) -> AgentResponse:
        """Handle project setup requests."""
        try:
            # This could involve creating project structure, setting up dependencies, etc.
            setup_type = parameters.get("type", "python")
            
            suggestions = [
                "Initialize Git repository",
                "Create virtual environment",
                "Set up project structure",
                "Add requirements.txt or pyproject.toml",
                "Create initial documentation"
            ]
            
            return AgentResponse(
                success=True,
                message="Project setup guidance provided",
                data={"setup_type": setup_type},
                suggestions=suggestions,
                next_actions=[
                    "git init",
                    "python -m venv venv",
                    "touch README.md",
                    "mkdir src tests docs"
                ]
            )
            
        except Exception as e:
            return AgentResponse(
                success=False,
                message=f"Project setup failed: {str(e)}"
            )
    
    async def _handle_chat(self, request: str, parameters: Dict[str, Any]) -> AgentResponse:
        """Handle general chat about code."""
        try:
            # Get relevant context
            context = await self._get_relevant_context(request)
            
            # For project overview questions, try to get broader context
            overview_keywords = ["how this works", "what does this do", "explain this code", "how does this project", "what is this"]
            if any(keyword in request.lower() for keyword in overview_keywords):
                # Try to get more comprehensive context for project overview questions
                try:
                    if self.current_project_context:
                        # Get broader context with lower similarity threshold for overview questions
                        rag_results = await self.rag_system.execute_rag_tool("search_code", {
                            "query": "main function class interface API",
                            "limit": 8,
                            "similarity_threshold": 0.4
                        })
                        if rag_results:
                            overview_context = "\n".join([result.text for result in rag_results])
                            if len(overview_context) > len(context):
                                context = overview_context
                except:
                    pass
            
            result = await self.llm_client.execute_llm_tool("chat_about_code", {
                "question": parameters.get("question", request),
                "code_context": context
            })
            
            chat_response = result[0].text if result else "I'm here to help with your coding questions!"
            
            return AgentResponse(
                success=True,
                message="Chat response generated",
                data={"response": chat_response}
            )
            
        except Exception as e:
            return AgentResponse(
                success=False,
                message=f"Chat failed: {str(e)}"
            )
    
    async def _get_relevant_context(self, query: str) -> str:
        """Get relevant code context from RAG system."""
        try:
            if self.current_project_context:
                rag_results = await self.rag_system.execute_rag_tool("search_code", {
                    "query": query,
                    "limit": 5,
                    "similarity_threshold": 0.6
                })
                if rag_results:
                    return "\n".join([result.text for result in rag_results])
        except:
            pass
        return ""
    
    async def _extract_code_from_request(self, request: str, parameters: Dict[str, Any]) -> str:
        """Extract code from the request or find relevant code files."""
        # Check if code is provided directly in parameters
        if "code" in parameters:
            return parameters["code"]
        
        # Try to extract file path from request
        file_path = self._extract_file_path_from_request(request)
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    return f.read()
            except:
                pass
        
        # Search for relevant code using RAG
        return await self._get_relevant_context(request)
    
    def _extract_file_path_from_request(self, request: str) -> Optional[str]:
        """Extract file path from request text."""
        import re
        
        # Look for common file path patterns
        patterns = [
            r'(?:file|path|in)\s+([^\s]+\.(?:py|js|ts|java|cpp|c|h|go|rs))',
            r'([^\s]+\.(?:py|js|ts|java|cpp|c|h|go|rs))',
            r'`([^`]+\.(?:py|js|ts|java|cpp|c|h|go|rs))`',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, request, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _determine_git_operation(self, request: str) -> str:
        """Determine Git operation from request."""
        request_lower = request.lower()
        
        if "status" in request_lower:
            return "status"
        elif "add" in request_lower:
            return "add"
        elif "commit" in request_lower:
            return "commit"
        elif "branch" in request_lower:
            return "branch"
        elif "push" in request_lower:
            return "push"
        elif "pull" in request_lower:
            return "pull"
        else:
            return "status"  # Default
    
    def get_agent_tools(self) -> List[types.Tool]:
        """Get MCP tools for the coder agent."""
        return [
            types.Tool(
                name="process_request",
                description="Process natural language requests for code development assistance",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "request": {
                            "type": "string",
                            "description": "Natural language request for coding assistance"
                        },
                        "context": {
                            "type": "object",
                            "description": "Additional context for the request",
                            "properties": {
                                "file_path": {"type": "string"},
                                "language": {"type": "string"},
                                "project_type": {"type": "string"}
                            }
                        }
                    },
                    "required": ["request"]
                }
            ),
            types.Tool(
                name="initialize_project",
                description="Initialize project context for comprehensive code assistance",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_path": {
                            "type": "string",
                            "description": "Path to the project directory",
                            "default": "."
                        }
                    },
                    "required": []
                }
            ),
            types.Tool(
                name="get_agent_status",
                description="Get current status and capabilities of the coder agent",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            )
        ]
    
    async def execute_agent_tool(self, name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Execute agent tool and return results."""
        try:
            if name == "process_request":
                response = await self.process_natural_language_request(
                    arguments["request"],
                    arguments.get("context")
                )
                return [types.TextContent(type="text", text=json.dumps(asdict(response), indent=2))]
            
            elif name == "initialize_project":
                response = await self.initialize_project_context(
                    arguments.get("project_path", ".")
                )
                return [types.TextContent(type="text", text=json.dumps(asdict(response), indent=2))]
            
            elif name == "get_agent_status":
                status = {
                    "agent_active": True,
                    "project_context": self.current_project_context is not None,
                    "available_capabilities": [
                        "Code Generation",
                        "Code Review",
                        "Bug Fixing",
                        "Refactoring",
                        "Documentation",
                        "Testing",
                        "Code Analysis",
                        "Git Operations",
                        "Project Setup",
                        "Code Chat"
                    ],
                    "session_context": bool(self.session_context),
                    "task_history_count": len(self.task_history)
                }
                return [types.TextContent(type="text", text=json.dumps(status, indent=2))]
            
            else:
                raise ValueError(f"Unknown agent tool: {name}")
                
        except Exception as e:
            error_response = AgentResponse(
                success=False,
                message=f"Agent tool execution failed: {str(e)}"
            )
            return [types.TextContent(type="text", text=json.dumps(asdict(error_response), indent=2))]
