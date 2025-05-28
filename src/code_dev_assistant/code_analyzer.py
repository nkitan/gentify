"""
Code analysis and parsing utilities using tree-sitter for semantic understanding.
"""
import os
import ast
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import tree_sitter
from tree_sitter import Language, Parser, Node
import mcp.types as types


@dataclass
class CodeChunk:
    """Represents a semantic chunk of code."""
    content: str
    file_path: str
    start_line: int
    end_line: int
    chunk_type: str  # function, class, method, import, etc.
    name: Optional[str] = None
    docstring: Optional[str] = None
    language: Optional[str] = None


class CodeAnalyzer:
    """Analyzes code using tree-sitter for semantic parsing."""
    
    def __init__(self):
        """Initialize code analyzer with tree-sitter parsers."""
        self.parsers = {}
        self.languages = {}
        self._setup_parsers()
    
    def _setup_parsers(self):
        """Set up tree-sitter parsers for different languages."""
        try:
            # Try to load pre-built languages (these would need to be built first)
            language_configs = {
                'python': 'python',
                'javascript': 'javascript', 
                'typescript': 'typescript',
                'java': 'java',
                'go': 'go',
                'rust': 'rust',
                'cpp': 'cpp'
            }
            
            for lang_name, lib_name in language_configs.items():
                try:
                    # This would need proper tree-sitter language library setup
                    # For now, we'll focus on Python with AST
                    pass
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"Warning: Could not initialize tree-sitter parsers: {e}")
    
    def get_code_analysis_tools(self) -> List[types.Tool]:
        """Return list of code analysis MCP tools."""
        return [
            types.Tool(
                name="analyze_file",
                description="Analyze a single code file for functions, classes, and structure",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the code file to analyze"
                        },
                        "include_docstrings": {
                            "type": "boolean",
                            "description": "Include docstrings in analysis",
                            "default": True
                        }
                    },
                    "required": ["file_path"],
                }
            ),
            types.Tool(
                name="find_function",
                description="Find a specific function or method in the codebase",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "function_name": {
                            "type": "string",
                            "description": "Name of the function to find"
                        },
                        "search_path": {
                            "type": "string",
                            "description": "Path to search in (defaults to current directory)",
                            "default": "."
                        }
                    },
                    "required": ["function_name"],
                }
            ),
            types.Tool(
                name="find_class",
                description="Find a specific class in the codebase",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "class_name": {
                            "type": "string",
                            "description": "Name of the class to find"
                        },
                        "search_path": {
                            "type": "string",
                            "description": "Path to search in (defaults to current directory)",
                            "default": "."
                        }
                    },
                    "required": ["class_name"],
                }
            ),
            types.Tool(
                name="extract_code_chunks",
                description="Extract semantic code chunks from files for RAG indexing",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "Directory to analyze",
                            "default": "."
                        },
                        "file_extensions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "File extensions to include",
                            "default": [".py", ".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c", ".h"]
                        },
                        "max_chunk_size": {
                            "type": "integer",
                            "description": "Maximum size of code chunks in characters",
                            "default": 2000
                        }
                    },
                    "required": [],
                }
            ),
            types.Tool(
                name="get_file_structure",
                description="Get the overall structure of a code file",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the code file"
                        }
                    },
                    "required": ["file_path"],
                }
            )
        ]
    
    async def execute_analysis_tool(self, name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Execute a code analysis tool."""
        try:
            if name == "analyze_file":
                return await self._analyze_file(
                    arguments["file_path"],
                    arguments.get("include_docstrings", True)
                )
            elif name == "find_function":
                return await self._find_function(
                    arguments["function_name"],
                    arguments.get("search_path", ".")
                )
            elif name == "find_class":
                return await self._find_class(
                    arguments["class_name"],
                    arguments.get("search_path", ".")
                )
            elif name == "extract_code_chunks":
                return await self._extract_code_chunks(
                    arguments.get("directory", "."),
                    arguments.get("file_extensions", [".py", ".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c", ".h"]),
                    arguments.get("max_chunk_size", 2000)
                )
            elif name == "get_file_structure":
                return await self._get_file_structure(arguments["file_path"])
            else:
                raise ValueError(f"Unknown analysis tool: {name}")
        except Exception as e:
            return [types.TextContent(type="text", text=f"Code analysis failed: {str(e)}")]
    
    async def _analyze_file(self, file_path: str, include_docstrings: bool = True) -> List[types.TextContent]:
        """Analyze a single code file."""
        try:
            if not os.path.exists(file_path):
                return [types.TextContent(type="text", text=f"File not found: {file_path}")]
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Determine language from file extension
            ext = Path(file_path).suffix.lower()
            
            if ext == '.py':
                return await self._analyze_python_file(file_path, content, include_docstrings)
            else:
                # For non-Python files, provide basic analysis
                return await self._analyze_generic_file(file_path, content)
                
        except Exception as e:
            return [types.TextContent(type="text", text=f"Failed to analyze file: {str(e)}")]
    
    async def _analyze_python_file(self, file_path: str, content: str, include_docstrings: bool) -> List[types.TextContent]:
        """Analyze Python file using AST."""
        try:
            tree = ast.parse(content)
            analysis = []
            
            analysis.append(f"Analysis of {file_path}:")
            analysis.append("=" * 50)
            
            # Extract imports
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(f"import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        imports.append(f"from {module} import {alias.name}")
            
            if imports:
                analysis.append("\nImports:")
                analysis.extend(f"  {imp}" for imp in imports)
            
            # Extract classes
            classes = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_info = f"class {node.name}"
                    if node.bases:
                        bases = [self._get_name(base) for base in node.bases]
                        class_info += f"({', '.join(bases)})"
                    
                    if include_docstrings and ast.get_docstring(node):
                        class_info += f"\n    \"\"\"{ast.get_docstring(node)}\"\"\""
                    
                    # Get methods
                    methods = []
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            method_info = f"    def {item.name}("
                            args = [arg.arg for arg in item.args.args]
                            method_info += ", ".join(args) + ")"
                            methods.append(method_info)
                    
                    if methods:
                        class_info += "\n" + "\n".join(methods)
                    
                    classes.append(class_info)
            
            if classes:
                analysis.append("\nClasses:")
                analysis.extend(classes)
            
            # Extract standalone functions
            functions = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Skip methods (functions inside classes)
                    if not any(isinstance(parent, ast.ClassDef) for parent in ast.walk(tree) 
                              if any(child is node for child in ast.walk(parent))):
                        func_info = f"def {node.name}("
                        args = [arg.arg for arg in node.args.args]
                        func_info += ", ".join(args) + ")"
                        
                        if include_docstrings and ast.get_docstring(node):
                            func_info += f"\n    \"\"\"{ast.get_docstring(node)}\"\"\""
                        
                        functions.append(func_info)
            
            if functions:
                analysis.append("\nFunctions:")
                analysis.extend(functions)
            
            return [types.TextContent(type="text", text="\n".join(analysis))]
            
        except SyntaxError as e:
            return [types.TextContent(type="text", text=f"Syntax error in {file_path}: {str(e)}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error analyzing Python file: {str(e)}")]
    
    async def _analyze_generic_file(self, file_path: str, content: str) -> List[types.TextContent]:
        """Provide basic analysis for non-Python files."""
        lines = content.split('\n')
        
        analysis = [
            f"Basic analysis of {file_path}:",
            "=" * 50,
            f"Lines: {len(lines)}",
            f"Characters: {len(content)}",
            f"File type: {Path(file_path).suffix}"
        ]
        
        # Look for common patterns
        if any('function' in line.lower() for line in lines):
            analysis.append("Contains function definitions")
        if any('class' in line.lower() for line in lines):
            analysis.append("Contains class definitions")
        if any('import' in line.lower() or '#include' in line for line in lines):
            analysis.append("Contains imports/includes")
        
        return [types.TextContent(type="text", text="\n".join(analysis))]
    
    async def _find_function(self, function_name: str, search_path: str) -> List[types.TextContent]:
        """Find a function in the codebase."""
        results = []
        search_dir = Path(search_path)
        
        for file_path in search_dir.rglob("*.py"):  # Focus on Python for now
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and node.name == function_name:
                        # Get function signature
                        args = [arg.arg for arg in node.args.args]
                        signature = f"def {node.name}({', '.join(args)})"
                        
                        # Get docstring if available
                        docstring = ast.get_docstring(node)
                        
                        result = f"Found in {file_path}:\n  {signature}"
                        if docstring:
                            result += f"\n  \"\"\"{docstring}\"\"\""
                        
                        # Get line number
                        result += f"\n  Line: {node.lineno}"
                        
                        results.append(result)
                        
            except Exception:
                continue
        
        if not results:
            return [types.TextContent(type="text", text=f"Function '{function_name}' not found in {search_path}")]
        
        return [types.TextContent(type="text", text="\n\n".join(results))]
    
    async def _find_class(self, class_name: str, search_path: str) -> List[types.TextContent]:
        """Find a class in the codebase."""
        results = []
        search_dir = Path(search_path)
        
        for file_path in search_dir.rglob("*.py"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef) and node.name == class_name:
                        # Get class signature
                        class_sig = f"class {node.name}"
                        if node.bases:
                            bases = [self._get_name(base) for base in node.bases]
                            class_sig += f"({', '.join(bases)})"
                        
                        # Get docstring if available
                        docstring = ast.get_docstring(node)
                        
                        result = f"Found in {file_path}:\n  {class_sig}"
                        if docstring:
                            result += f"\n  \"\"\"{docstring}\"\"\""
                        
                        # Get line number
                        result += f"\n  Line: {node.lineno}"
                        
                        # List methods
                        methods = []
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef):
                                methods.append(item.name)
                        
                        if methods:
                            result += f"\n  Methods: {', '.join(methods)}"
                        
                        results.append(result)
                        
            except Exception:
                continue
        
        if not results:
            return [types.TextContent(type="text", text=f"Class '{class_name}' not found in {search_path}")]
        
        return [types.TextContent(type="text", text="\n\n".join(results))]
    
    async def _extract_code_chunks(self, directory: str, file_extensions: List[str], max_chunk_size: int) -> List[types.TextContent]:
        """Extract code chunks for RAG indexing."""
        chunks = []
        search_dir = Path(directory)
        
        for ext in file_extensions:
            for file_path in search_dir.rglob(f"*{ext}"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if ext == '.py':
                        file_chunks = self._extract_python_chunks(str(file_path), content, max_chunk_size)
                    else:
                        file_chunks = self._extract_generic_chunks(str(file_path), content, max_chunk_size)
                    
                    chunks.extend(file_chunks)
                    
                except Exception:
                    continue
        
        summary = f"Extracted {len(chunks)} code chunks from {directory}"
        if chunks:
            summary += f"\nExample chunks:\n"
            for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
                summary += f"\n{i+1}. {chunk.chunk_type} in {chunk.file_path}"
                if chunk.name:
                    summary += f" - {chunk.name}"
                summary += f" (lines {chunk.start_line}-{chunk.end_line})"
        
        return [types.TextContent(type="text", text=summary)]
    
    def _extract_python_chunks(self, file_path: str, content: str, max_size: int) -> List[CodeChunk]:
        """Extract semantic chunks from Python code."""
        chunks = []
        
        try:
            tree = ast.parse(content)
            lines = content.split('\n')
            
            # Extract imports as one chunk
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    imports.append(node.lineno)
            
            if imports:
                start_line = min(imports)
                end_line = max(imports)
                import_content = '\n'.join(lines[start_line-1:end_line])
                chunks.append(CodeChunk(
                    content=import_content,
                    file_path=file_path,
                    start_line=start_line,
                    end_line=end_line,
                    chunk_type="imports",
                    language="python"
                ))
            
            # Extract classes and functions
            for node in ast.walk(tree):
                if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                    start_line = node.lineno
                    end_line = node.end_lineno or start_line
                    
                    chunk_content = '\n'.join(lines[start_line-1:end_line])
                    
                    # Split large chunks
                    if len(chunk_content) > max_size:
                        # For large functions/classes, create multiple chunks
                        sub_chunks = self._split_large_chunk(chunk_content, max_size)
                        for i, sub_content in enumerate(sub_chunks):
                            chunks.append(CodeChunk(
                                content=sub_content,
                                file_path=file_path,
                                start_line=start_line,
                                end_line=end_line,
                                chunk_type=f"{type(node).__name__.lower()}_{i}",
                                name=node.name,
                                docstring=ast.get_docstring(node),
                                language="python"
                            ))
                    else:
                        chunks.append(CodeChunk(
                            content=chunk_content,
                            file_path=file_path,
                            start_line=start_line,
                            end_line=end_line,
                            chunk_type=type(node).__name__.lower(),
                            name=node.name,
                            docstring=ast.get_docstring(node),
                            language="python"
                        ))
                        
        except Exception:
            # Fallback to generic chunking
            return self._extract_generic_chunks(file_path, content, max_size)
        
        return chunks
    
    def _extract_generic_chunks(self, file_path: str, content: str, max_size: int) -> List[CodeChunk]:
        """Extract chunks from non-Python files using simple line-based approach."""
        chunks = []
        lines = content.split('\n')
        
        current_chunk = []
        current_size = 0
        start_line = 1
        
        for i, line in enumerate(lines, 1):
            current_chunk.append(line)
            current_size += len(line) + 1  # +1 for newline
            
            if current_size >= max_size or i == len(lines):
                if current_chunk:
                    chunks.append(CodeChunk(
                        content='\n'.join(current_chunk),
                        file_path=file_path,
                        start_line=start_line,
                        end_line=i,
                        chunk_type="code_block",
                        language=Path(file_path).suffix[1:] if Path(file_path).suffix else "text"
                    ))
                
                current_chunk = []
                current_size = 0
                start_line = i + 1
        
        return chunks
    
    def _split_large_chunk(self, content: str, max_size: int) -> List[str]:
        """Split a large code chunk into smaller pieces."""
        lines = content.split('\n')
        chunks = []
        current_chunk = []
        current_size = 0
        
        for line in lines:
            current_chunk.append(line)
            current_size += len(line) + 1
            
            if current_size >= max_size:
                chunks.append('\n'.join(current_chunk))
                current_chunk = []
                current_size = 0
        
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks
    
    async def _get_file_structure(self, file_path: str) -> List[types.TextContent]:
        """Get the structure of a code file."""
        try:
            if not os.path.exists(file_path):
                return [types.TextContent(type="text", text=f"File not found: {file_path}")]
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if Path(file_path).suffix == '.py':
                return await self._get_python_structure(file_path, content)
            else:
                return await self._get_generic_structure(file_path, content)
                
        except Exception as e:
            return [types.TextContent(type="text", text=f"Failed to get file structure: {str(e)}")]
    
    async def _get_python_structure(self, file_path: str, content: str) -> List[types.TextContent]:
        """Get Python file structure."""
        try:
            tree = ast.parse(content)
            structure = [f"Structure of {file_path}:", "=" * 40]
            
            # Module docstring
            module_docstring = ast.get_docstring(tree)
            if module_docstring:
                structure.append(f"Module: {module_docstring}")
            
            # Top-level items with line numbers
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    structure.append(f"Class {node.name} (line {node.lineno})")
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            structure.append(f"  Method {item.name} (line {item.lineno})")
                elif isinstance(node, ast.FunctionDef):
                    structure.append(f"Function {node.name} (line {node.lineno})")
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        structure.append(f"Import {alias.name} (line {node.lineno})")
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        structure.append(f"From {module} import {alias.name} (line {node.lineno})")
            
            return [types.TextContent(type="text", text="\n".join(structure))]
            
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error parsing Python structure: {str(e)}")]
    
    async def _get_generic_structure(self, file_path: str, content: str) -> List[types.TextContent]:
        """Get generic file structure."""
        lines = content.split('\n')
        structure = [
            f"Structure of {file_path}:",
            "=" * 40,
            f"Total lines: {len(lines)}",
            f"File size: {len(content)} characters",
            f"File type: {Path(file_path).suffix}"
        ]
        
        return [types.TextContent(type="text", text="\n".join(structure))]
    
    def _get_name(self, node: ast.expr) -> str:
        """Get name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        else:
            return str(node)
