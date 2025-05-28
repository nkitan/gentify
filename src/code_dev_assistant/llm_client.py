"""
LLM integration for code generation and understanding using Ollama.
"""
import asyncio
import httpx
from typing import List, Dict, Any, Optional
import json
import mcp.types as types


class CodeLLM:
    """LLM integration for code-related tasks using Ollama."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "codellama:7b-instruct"):
        """Initialize LLM client."""
        self.base_url = base_url
        self.model = model
        self.client = httpx.AsyncClient(timeout=60.0)
    
    def get_llm_tools(self) -> List[types.Tool]:
        """Return list of LLM-related MCP tools."""
        return [
            types.Tool(
                name="generate_code",
                description="Generate code based on natural language description",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "description": {
                            "type": "string",
                            "description": "Natural language description of the code to generate"
                        },
                        "language": {
                            "type": "string",
                            "description": "Programming language",
                            "default": "python"
                        },
                        "context": {
                            "type": "string",
                            "description": "Additional context or existing code to consider"
                        },
                        "style": {
                            "type": "string",
                            "description": "Code style preferences",
                            "enum": ["clean", "documented", "performant", "simple"],
                            "default": "clean"
                        }
                    },
                    "required": ["description"],
                }
            ),
            types.Tool(
                name="explain_code",
                description="Explain what a piece of code does",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Code to explain"
                        },
                        "detail_level": {
                            "type": "string",
                            "description": "Level of detail for explanation",
                            "enum": ["brief", "detailed", "line-by-line"],
                            "default": "detailed"
                        }
                    },
                    "required": ["code"],
                }
            ),
            types.Tool(
                name="refactor_code",
                description="Suggest refactoring improvements for code",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Code to refactor"
                        },
                        "goals": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Refactoring goals",
                            "default": ["readability", "performance", "maintainability"]
                        },
                        "language": {
                            "type": "string",
                            "description": "Programming language",
                            "default": "python"
                        }
                    },
                    "required": ["code"],
                }
            ),
            types.Tool(
                name="debug_code",
                description="Help debug code by analyzing potential issues",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Code to debug"
                        },
                        "error_message": {
                            "type": "string",
                            "description": "Error message or description of the problem"
                        },
                        "language": {
                            "type": "string",
                            "description": "Programming language",
                            "default": "python"
                        }
                    },
                    "required": ["code"],
                }
            ),
            types.Tool(
                name="review_code",
                description="Perform a code review and suggest improvements",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Code to review"
                        },
                        "focus_areas": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Areas to focus on during review",
                            "default": ["security", "performance", "style", "best_practices"]
                        },
                        "language": {
                            "type": "string",
                            "description": "Programming language",
                            "default": "python"
                        }
                    },
                    "required": ["code"],
                }
            ),
            types.Tool(
                name="generate_tests",
                description="Generate unit tests for given code",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Code to generate tests for"
                        },
                        "test_framework": {
                            "type": "string",
                            "description": "Testing framework to use",
                            "default": "pytest"
                        },
                        "coverage_level": {
                            "type": "string",
                            "description": "Level of test coverage",
                            "enum": ["basic", "comprehensive", "edge_cases"],
                            "default": "comprehensive"
                        },
                        "language": {
                            "type": "string",
                            "description": "Programming language",
                            "default": "python"
                        }
                    },
                    "required": ["code"],
                }
            ),
            types.Tool(
                name="generate_documentation",
                description="Generate documentation for code",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Code to document"
                        },
                        "doc_type": {
                            "type": "string",
                            "description": "Type of documentation",
                            "enum": ["docstrings", "readme", "api_docs", "inline_comments"],
                            "default": "docstrings"
                        },
                        "language": {
                            "type": "string",
                            "description": "Programming language",
                            "default": "python"
                        }
                    },
                    "required": ["code"],
                }
            ),
            types.Tool(
                name="chat_about_code",
                description="Have a conversation about code with context from the codebase",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "Question or topic to discuss"
                        },
                        "code_context": {
                            "type": "string",
                            "description": "Relevant code context"
                        }
                    },
                    "required": ["question"],
                }
            )
        ]
    
    async def execute_llm_tool(self, name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Execute an LLM tool."""
        try:
            if name == "generate_code":
                return await self._generate_code(
                    arguments["description"],
                    arguments.get("language", "python"),
                    arguments.get("context"),
                    arguments.get("style", "clean")
                )
            elif name == "explain_code":
                return await self._explain_code(
                    arguments["code"],
                    arguments.get("detail_level", "detailed")
                )
            elif name == "refactor_code":
                return await self._refactor_code(
                    arguments["code"],
                    arguments.get("goals", ["readability", "performance", "maintainability"]),
                    arguments.get("language", "python")
                )
            elif name == "debug_code":
                return await self._debug_code(
                    arguments["code"],
                    arguments.get("error_message"),
                    arguments.get("language", "python")
                )
            elif name == "review_code":
                return await self._review_code(
                    arguments["code"],
                    arguments.get("focus_areas", ["security", "performance", "style", "best_practices"]),
                    arguments.get("language", "python")
                )
            elif name == "generate_tests":
                return await self._generate_tests(
                    arguments["code"],
                    arguments.get("test_framework", "pytest"),
                    arguments.get("coverage_level", "comprehensive"),
                    arguments.get("language", "python")
                )
            elif name == "generate_documentation":
                return await self._generate_documentation(
                    arguments["code"],
                    arguments.get("doc_type", "docstrings"),
                    arguments.get("language", "python")
                )
            elif name == "chat_about_code":
                return await self._chat_about_code(
                    arguments["question"],
                    arguments.get("code_context")
                )
            else:
                raise ValueError(f"Unknown LLM tool: {name}")
        except Exception as e:
            return [types.TextContent(type="text", text=f"LLM operation failed: {str(e)}")]
    
    async def _call_ollama(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Call Ollama API."""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            return result["message"]["content"]
            
        except httpx.ConnectError:
            raise RuntimeError(f"Cannot connect to Ollama at {self.base_url}. Make sure Ollama is running.")
        except Exception as e:
            raise RuntimeError(f"Error calling Ollama API: {str(e)}")
    
    async def _generate_code(self, description: str, language: str, context: Optional[str], style: str) -> List[types.TextContent]:
        """Generate code based on description."""
        system_prompt = f"""You are an expert {language} programmer. Generate clean, efficient, and well-structured code.
Style preference: {style}
- clean: Focus on readability and simplicity
- documented: Include comprehensive comments and docstrings  
- performant: Optimize for performance
- simple: Keep it as simple as possible

Always include comments explaining the code logic."""

        prompt = f"Generate {language} code for the following requirement:\n\n{description}"
        
        if context:
            prompt += f"\n\nContext/existing code to consider:\n{context}"
        
        prompt += f"\n\nPlease provide only the code with appropriate comments, formatted properly for {language}."
        
        try:
            response = await self._call_ollama(prompt, system_prompt)
            return [types.TextContent(type="text", text=response)]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Code generation failed: {str(e)}")]
    
    async def _explain_code(self, code: str, detail_level: str) -> List[types.TextContent]:
        """Explain what code does."""
        system_prompt = "You are an expert programmer who explains code clearly and accurately."
        
        if detail_level == "brief":
            prompt = f"Briefly explain what this code does:\n\n{code}"
        elif detail_level == "line-by-line":
            prompt = f"Explain this code line by line:\n\n{code}"
        else:  # detailed
            prompt = f"Provide a detailed explanation of this code, including its purpose, how it works, and any important details:\n\n{code}"
        
        try:
            response = await self._call_ollama(prompt, system_prompt)
            return [types.TextContent(type="text", text=response)]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Code explanation failed: {str(e)}")]
    
    async def _refactor_code(self, code: str, goals: List[str], language: str) -> List[types.TextContent]:
        """Suggest refactoring improvements."""
        system_prompt = f"You are an expert {language} programmer who specializes in code refactoring and optimization."
        
        goals_str = ", ".join(goals)
        prompt = f"""Analyze and refactor the following {language} code to improve: {goals_str}

Original code:
{code}

Please provide:
1. The refactored code
2. Explanation of changes made
3. Why these changes improve the specified goals"""
        
        try:
            response = await self._call_ollama(prompt, system_prompt)
            return [types.TextContent(type="text", text=response)]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Code refactoring failed: {str(e)}")]
    
    async def _debug_code(self, code: str, error_message: Optional[str], language: str) -> List[types.TextContent]:
        """Help debug code."""
        system_prompt = f"You are an expert {language} debugger. Analyze code to find potential issues and suggest fixes."
        
        prompt = f"Analyze this {language} code for potential issues and suggest fixes:\n\n{code}"
        
        if error_message:
            prompt += f"\n\nSpecific error or issue reported:\n{error_message}"
        
        prompt += "\n\nPlease provide:\n1. Identified issues\n2. Suggested fixes\n3. Corrected code if applicable"
        
        try:
            response = await self._call_ollama(prompt, system_prompt)
            return [types.TextContent(type="text", text=response)]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Code debugging failed: {str(e)}")]
    
    async def _review_code(self, code: str, focus_areas: List[str], language: str) -> List[types.TextContent]:
        """Perform code review."""
        system_prompt = f"You are an experienced {language} code reviewer. Provide constructive feedback on code quality."
        
        focus_str = ", ".join(focus_areas)
        prompt = f"""Review this {language} code focusing on: {focus_str}

Code to review:
{code}

Please provide:
1. Overall assessment
2. Specific issues found
3. Recommendations for improvement
4. Best practices that could be applied"""
        
        try:
            response = await self._call_ollama(prompt, system_prompt)
            return [types.TextContent(type="text", text=response)]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Code review failed: {str(e)}")]
    
    async def _generate_tests(self, code: str, test_framework: str, coverage_level: str, language: str) -> List[types.TextContent]:
        """Generate unit tests for code."""
        system_prompt = f"You are an expert in {language} testing with {test_framework}. Generate comprehensive, well-structured unit tests."
        
        prompt = f"""Generate {coverage_level} unit tests for this {language} code using {test_framework}:

{code}

Please provide:
1. Complete test code
2. Test cases covering various scenarios
3. Setup/teardown if needed
4. Comments explaining test logic"""
        
        try:
            response = await self._call_ollama(prompt, system_prompt)
            return [types.TextContent(type="text", text=response)]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Test generation failed: {str(e)}")]
    
    async def _generate_documentation(self, code: str, doc_type: str, language: str) -> List[types.TextContent]:
        """Generate documentation for code."""
        system_prompt = f"You are an expert technical writer who creates clear, comprehensive documentation for {language} code."
        
        if doc_type == "docstrings":
            prompt = f"Add proper docstrings to this {language} code:\n\n{code}"
        elif doc_type == "readme":
            prompt = f"Create a README.md for this {language} code:\n\n{code}"
        elif doc_type == "api_docs":
            prompt = f"Create API documentation for this {language} code:\n\n{code}"
        else:  # inline_comments
            prompt = f"Add detailed inline comments to this {language} code:\n\n{code}"
        
        try:
            response = await self._call_ollama(prompt, system_prompt)
            return [types.TextContent(type="text", text=response)]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Documentation generation failed: {str(e)}")]
    
    async def _chat_about_code(self, question: str, code_context: Optional[str]) -> List[types.TextContent]:
        """Have a conversation about code."""
        system_prompt = "You are a helpful coding assistant with deep knowledge of programming concepts and best practices."
        
        prompt = f"Question: {question}"
        
        if code_context:
            prompt += f"\n\nRelevant code context:\n{code_context}"
        
        prompt += "\n\nPlease provide a helpful, detailed response."
        
        try:
            response = await self._call_ollama(prompt, system_prompt)
            return [types.TextContent(type="text", text=response)]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Chat failed: {str(e)}")]
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
