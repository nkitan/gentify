from typing import cast
import asyncio
import os
from pathlib import Path

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from pydantic import AnyUrl
import mcp.server.stdio

from .git_tools import GitTools
from .code_analyzer import CodeAnalyzer
from .rag_system import CodeRAG
from .llm_client import CodeLLM
from .coder_agent import CoderAgent

# Initialize components
git_tools = GitTools()
code_analyzer = CodeAnalyzer()
rag_system = CodeRAG()
llm_client = CodeLLM()
coder_agent = CoderAgent(llm_client, rag_system, code_analyzer, git_tools)

server = Server("code-dev-assistant")

@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """
    List available resources from the codebase.
    """
    resources = []
    
    # Add Git repository as a resource
    try:
        repo_path = git_tools.repo_path
        if os.path.exists(os.path.join(repo_path, '.git')):
            resources.append(
                types.Resource(
                    uri=AnyUrl(f"git://repository/{repo_path}"),
                    name="Git Repository",
                    description=f"Git repository at {repo_path}",
                    mimeType="application/json",
                )
            )
    except Exception:
        pass
    
    # Add current directory structure as resource
    try:
        cwd = os.getcwd()
        resources.append(
            types.Resource(
                uri=AnyUrl(f"file://directory/{cwd}"),
                name="Current Directory",
                description=f"Current working directory: {cwd}",
                mimeType="application/json",
            )
        )
    except Exception:
        pass
    
    return resources

@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    """
    Read a specific resource.
    """
    if uri.scheme == "git":
        # Return Git repository information
        try:
            repo = git_tools.repo
            info = {
                "current_branch": repo.active_branch.name,
                "remote_url": list(repo.remotes[0].urls)[0] if repo.remotes else None,
                "last_commit": {
                    "hash": repo.head.commit.hexsha[:8],
                    "message": repo.head.commit.message.strip(),
                    "author": str(repo.head.commit.author),
                    "date": repo.head.commit.committed_datetime.isoformat()
                }
            }
            return str(info)
        except Exception as e:
            return f"Error reading Git repository: {str(e)}"
    
    elif uri.scheme == "file":
        # Return directory information
        try:
            path = str(uri.path).lstrip("/directory/") if uri.path else ""
            if os.path.isdir(path):
                files = []
                for item in os.listdir(path):
                    item_path = os.path.join(path, item)
                    files.append({
                        "name": item,
                        "type": "directory" if os.path.isdir(item_path) else "file",
                        "size": os.path.getsize(item_path) if os.path.isfile(item_path) else None
                    })
                return str({"path": path, "contents": files})
            else:
                return f"Path not found: {path}"
        except Exception as e:
            return f"Error reading directory: {str(e)}"
    
    raise ValueError(f"Unsupported URI scheme: {uri.scheme}")

@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    """
    List available prompts for code development assistance.
    """
    return [
        types.Prompt(
            name="analyze_codebase",
            description="Analyze the current codebase and provide insights",
            arguments=[
                types.PromptArgument(
                    name="focus",
                    description="Focus area (structure, quality, patterns, dependencies)",
                    required=False,
                )
            ],
        ),
        types.Prompt(
            name="code_review",
            description="Perform a comprehensive code review",
            arguments=[
                types.PromptArgument(
                    name="files",
                    description="Specific files to review (comma-separated)",
                    required=False,
                ),
                types.PromptArgument(
                    name="criteria",
                    description="Review criteria (security, performance, style, all)",
                    required=False,
                )
            ],
        ),
        types.Prompt(
            name="git_workflow",
            description="Get guidance on Git workflow and best practices",
            arguments=[
                types.PromptArgument(
                    name="scenario",
                    description="Specific Git scenario or operation",
                    required=False,
                )
            ],
        ),
    ]

@server.get_prompt()
async def handle_get_prompt(
    name: str, arguments: dict[str, str] | None
) -> types.GetPromptResult:
    """
    Generate prompts for code development assistance.
    """
    args = arguments or {}
    
    if name == "analyze_codebase":
        focus = args.get("focus", "general")
        
        # Get basic codebase information
        cwd = os.getcwd()
        try:
            # Count files by extension
            file_counts = {}
            for file_path in Path(cwd).rglob("*"):
                if file_path.is_file():
                    ext = file_path.suffix.lower()
                    file_counts[ext] = file_counts.get(ext, 0) + 1
            
            content = f"Analyze the codebase at {cwd}\n\n"
            content += f"Focus area: {focus}\n\n"
            content += "File statistics:\n"
            for ext, count in sorted(file_counts.items()):
                content += f"  {ext or 'no extension'}: {count} files\n"
            
            if focus == "structure":
                content += "\nPlease analyze the overall project structure, organization, and architecture."
            elif focus == "quality":
                content += "\nPlease analyze code quality, maintainability, and potential issues."
            elif focus == "patterns":
                content += "\nPlease identify design patterns, code patterns, and architectural decisions."
            elif focus == "dependencies":
                content += "\nPlease analyze dependencies, imports, and module relationships."
            else:
                content += "\nPlease provide a general analysis covering structure, quality, and recommendations."
                
        except Exception as e:
            content = f"Error analyzing codebase: {str(e)}"
        
        return types.GetPromptResult(
            description=f"Codebase analysis with focus on {focus}",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(type="text", text=content),
                ),
            ],
        )
    
    elif name == "code_review":
        files = args.get("files", "")
        criteria = args.get("criteria", "all")
        
        content = f"Perform a code review with criteria: {criteria}\n\n"
        
        if files:
            content += f"Focus on these files: {files}\n\n"
            # Here you could read the actual file contents
        else:
            content += "Review the entire codebase.\n\n"
        
        content += "Please check for:\n"
        if criteria == "security" or criteria == "all":
            content += "- Security vulnerabilities and best practices\n"
        if criteria == "performance" or criteria == "all":
            content += "- Performance issues and optimization opportunities\n"
        if criteria == "style" or criteria == "all":
            content += "- Code style and formatting consistency\n"
        if criteria == "all":
            content += "- Best practices and maintainability\n"
            content += "- Error handling and edge cases\n"
            content += "- Documentation and comments\n"
        
        return types.GetPromptResult(
            description=f"Code review focusing on {criteria}",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(type="text", text=content),
                ),
            ],
        )
    
    elif name == "git_workflow":
        scenario = args.get("scenario", "general")
        
        content = f"Provide Git workflow guidance for: {scenario}\n\n"
        
        # Get current Git status
        try:
            repo = git_tools.repo
            current_branch = repo.active_branch.name
            
            # Check for uncommitted changes
            staged = len(list(repo.index.diff("HEAD")))
            unstaged = len(list(repo.index.diff(None)))
            untracked = len(repo.untracked_files)
            
            content += f"Current Git status:\n"
            content += f"- Branch: {current_branch}\n"
            content += f"- Staged changes: {staged}\n"
            content += f"- Unstaged changes: {unstaged}\n"
            content += f"- Untracked files: {untracked}\n\n"
            
        except Exception:
            content += "Could not read Git status.\n\n"
        
        if scenario == "branching":
            content += "Please provide guidance on Git branching strategies and best practices."
        elif scenario == "merging":
            content += "Please provide guidance on Git merging, handling conflicts, and merge strategies."
        elif scenario == "collaboration":
            content += "Please provide guidance on collaborative Git workflows and team practices."
        else:
            content += "Please provide general Git workflow guidance and best practices."
        
        return types.GetPromptResult(
            description=f"Git workflow guidance for {scenario}",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(type="text", text=content),
                ),
            ],
        )
    
    raise ValueError(f"Unknown prompt: {name}")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List all available tools from different components.
    """
    tools = []
    
    # Add Git tools
    tools.extend(git_tools.get_git_tools())
    
    # Add code analysis tools
    tools.extend(code_analyzer.get_code_analysis_tools())
    
    # Add RAG tools
    tools.extend(rag_system.get_rag_tools())
    
    # Add LLM tools
    tools.extend(llm_client.get_llm_tools())
    
    # Add Coder Agent tools
    tools.extend(coder_agent.get_agent_tools())
    
    return tools

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution by routing to appropriate component.
    """
    if not arguments:
        arguments = {}
    
    # Route Git tools
    git_tool_names = [tool.name for tool in git_tools.get_git_tools()]
    if name in git_tool_names:
        result = await git_tools.execute_git_tool(name, arguments)
        return cast(list[types.TextContent | types.ImageContent | types.EmbeddedResource], result)
    
    # Route code analysis tools
    analysis_tool_names = [tool.name for tool in code_analyzer.get_code_analysis_tools()]
    if name in analysis_tool_names:
        result = await code_analyzer.execute_analysis_tool(name, arguments)
        return cast(list[types.TextContent | types.ImageContent | types.EmbeddedResource], result)
    
    # Route RAG tools
    rag_tool_names = [tool.name for tool in rag_system.get_rag_tools()]
    if name in rag_tool_names:
        result = await rag_system.execute_rag_tool(name, arguments)
        return cast(list[types.TextContent | types.ImageContent | types.EmbeddedResource], result)
    
    # Route LLM tools
    llm_tool_names = [tool.name for tool in llm_client.get_llm_tools()]
    if name in llm_tool_names:
        result = await llm_client.execute_llm_tool(name, arguments)
        return cast(list[types.TextContent | types.ImageContent | types.EmbeddedResource], result)
    
    # Route Coder Agent tools
    agent_tool_names = [tool.name for tool in coder_agent.get_agent_tools()]
    if name in agent_tool_names:
        result = await coder_agent.execute_agent_tool(name, arguments)
        return cast(list[types.TextContent | types.ImageContent | types.EmbeddedResource], result)
    
    raise ValueError(f"Unknown tool: {name}")

async def main():
    """Main entry point for the MCP server."""
    try:
        # Run the server using stdin/stdout streams
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="code-dev-assistant",
                    server_version="0.1.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error running server: {e}")
    finally:
        # Cleanup
        await llm_client.close()
