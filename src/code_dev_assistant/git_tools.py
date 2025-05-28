"""
Git operation tools using GitPython for version control operations.
"""
import os
from pathlib import Path
from typing import List, Dict, Optional, Any, Sequence
import git
from git import Repo, InvalidGitRepositoryError
import mcp.types as types


class GitTools:
    """Provides Git operations through GitPython with MCP tool integration."""
    
    def __init__(self, repo_path: Optional[str] = None):
        """Initialize Git tools with repository path."""
        self.repo_path = repo_path or os.getcwd()
        self._repo = None
        
    @property
    def repo(self) -> Repo:
        """Get or initialize Git repository."""
        if self._repo is None:
            try:
                self._repo = Repo(self.repo_path)
            except InvalidGitRepositoryError:
                raise ValueError(f"Not a valid Git repository: {self.repo_path}")
        return self._repo
    
    def get_git_tools(self) -> List[types.Tool]:
        """Return list of Git-related MCP tools."""
        return [
            types.Tool(
                name="git_status",
                description="Get current Git repository status",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": [],
                }
            ),
            types.Tool(
                name="git_add",
                description="Add files to Git staging area",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "files": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of file paths to add (use '.' for all files)"
                        }
                    },
                    "required": ["files"],
                }
            ),
            types.Tool(
                name="git_commit",
                description="Commit staged changes with a message",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Commit message"
                        },
                        "add_all": {
                            "type": "boolean",
                            "description": "Add all modified files before committing",
                            "default": False
                        }
                    },
                    "required": ["message"],
                }
            ),
            types.Tool(
                name="git_create_branch",
                description="Create a new Git branch",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "branch_name": {
                            "type": "string",
                            "description": "Name of the new branch"
                        },
                        "checkout": {
                            "type": "boolean",
                            "description": "Whether to checkout the new branch",
                            "default": True
                        }
                    },
                    "required": ["branch_name"],
                }
            ),
            types.Tool(
                name="git_checkout",
                description="Switch to a different branch",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "branch_name": {
                            "type": "string",
                            "description": "Name of the branch to checkout"
                        }
                    },
                    "required": ["branch_name"],
                }
            ),
            types.Tool(
                name="git_diff",
                description="Show differences between commits, branches, or working directory",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "target": {
                            "type": "string",
                            "description": "Target to diff against (commit hash, branch name, or 'HEAD')",
                            "default": "HEAD"
                        },
                        "staged": {
                            "type": "boolean",
                            "description": "Show staged changes only",
                            "default": False
                        }
                    },
                    "required": [],
                }
            ),
            types.Tool(
                name="git_log",
                description="Show commit history",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "max_count": {
                            "type": "integer",
                            "description": "Maximum number of commits to show",
                            "default": 10
                        },
                        "oneline": {
                            "type": "boolean",
                            "description": "Show one line per commit",
                            "default": True
                        }
                    },
                    "required": [],
                }
            ),
            types.Tool(
                name="git_branch_list",
                description="List all local and remote branches",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "remote": {
                            "type": "boolean",
                            "description": "Include remote branches",
                            "default": True
                        }
                    },
                    "required": [],
                }
            ),
            types.Tool(
                name="git_push",
                description="Push commits to remote repository",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "remote": {
                            "type": "string",
                            "description": "Remote name",
                            "default": "origin"
                        },
                        "branch": {
                            "type": "string",
                            "description": "Branch name (defaults to current branch)"
                        },
                        "force": {
                            "type": "boolean",
                            "description": "Force push (use with caution)",
                            "default": False
                        }
                    },
                    "required": [],
                }
            ),
            types.Tool(
                name="git_pull",
                description="Pull changes from remote repository",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "remote": {
                            "type": "string",
                            "description": "Remote name",
                            "default": "origin"
                        },
                        "branch": {
                            "type": "string",
                            "description": "Branch name (defaults to current branch)"
                        }
                    },
                    "required": [],
                }
            )
        ]
    
    async def execute_git_tool(self, name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Execute a Git tool and return results."""
        try:
            if name == "git_status":
                return await self._git_status()
            elif name == "git_add":
                return await self._git_add(arguments["files"])
            elif name == "git_commit":
                return await self._git_commit(
                    arguments["message"], 
                    arguments.get("add_all", False)
                )
            elif name == "git_create_branch":
                return await self._git_create_branch(
                    arguments["branch_name"],
                    arguments.get("checkout", True)
                )
            elif name == "git_checkout":
                return await self._git_checkout(arguments["branch_name"])
            elif name == "git_diff":
                return await self._git_diff(
                    arguments.get("target", "HEAD"),
                    arguments.get("staged", False)
                )
            elif name == "git_log":
                return await self._git_log(
                    arguments.get("max_count", 10),
                    arguments.get("oneline", True)
                )
            elif name == "git_branch_list":
                return await self._git_branch_list(arguments.get("remote", True))
            elif name == "git_push":
                return await self._git_push(
                    arguments.get("remote", "origin"),
                    arguments.get("branch"),
                    arguments.get("force", False)
                )
            elif name == "git_pull":
                return await self._git_pull(
                    arguments.get("remote", "origin"),
                    arguments.get("branch")
                )
            else:
                raise ValueError(f"Unknown Git tool: {name}")
        except Exception as e:
            return [types.TextContent(type="text", text=f"Git operation failed: {str(e)}")]
    
    async def _git_status(self) -> List[types.TextContent]:
        """Get repository status."""
        status_lines = []
        
        # Current branch
        current_branch = self.repo.active_branch.name
        status_lines.append(f"On branch {current_branch}")
        
        # Check if there are staged changes
        if self.repo.index.diff("HEAD"):
            status_lines.append("\nChanges to be committed:")
            for item in self.repo.index.diff("HEAD"):
                status_lines.append(f"  {item.change_type}: {item.a_path}")
        
        # Check for unstaged changes
        if self.repo.index.diff(None):
            status_lines.append("\nChanges not staged for commit:")
            for item in self.repo.index.diff(None):
                status_lines.append(f"  {item.change_type}: {item.a_path}")
        
        # Check for untracked files
        untracked = self.repo.untracked_files
        if untracked:
            status_lines.append("\nUntracked files:")
            for file in untracked:
                status_lines.append(f"  {file}")
        
        if len(status_lines) == 1:  # Only branch info
            status_lines.append("nothing to commit, working tree clean")
        
        return [types.TextContent(type="text", text="\n".join(status_lines))]
    
    async def _git_add(self, files: List[str]) -> List[types.TextContent]:
        """Add files to staging area."""
        try:
            for file_path in files:
                if file_path == ".":
                    self.repo.git.add(A=True)  # Add all files
                else:
                    self.repo.index.add([file_path])
            
            files_str = "all files" if "." in files else ", ".join(files)
            return [types.TextContent(type="text", text=f"Added {files_str} to staging area")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Failed to add files: {str(e)}")]
    
    async def _git_commit(self, message: str, add_all: bool = False) -> List[types.TextContent]:
        """Commit changes."""
        try:
            if add_all:
                self.repo.git.add(A=True)
            
            commit = self.repo.index.commit(message)
            return [types.TextContent(
                type="text", 
                text=f"Committed changes with ID {commit.hexsha[:8]}: {message}"
            )]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Failed to commit: {str(e)}")]
    
    async def _git_create_branch(self, branch_name: str, checkout: bool = True) -> List[types.TextContent]:
        """Create a new branch."""
        try:
            new_branch = self.repo.create_head(branch_name)
            if checkout:
                new_branch.checkout()
                return [types.TextContent(
                    type="text", 
                    text=f"Created and switched to branch '{branch_name}'"
                )]
            else:
                return [types.TextContent(
                    type="text", 
                    text=f"Created branch '{branch_name}'"
                )]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Failed to create branch: {str(e)}")]
    
    async def _git_checkout(self, branch_name: str) -> List[types.TextContent]:
        """Switch to a branch."""
        try:
            self.repo.git.checkout(branch_name)
            return [types.TextContent(type="text", text=f"Switched to branch '{branch_name}'")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Failed to checkout branch: {str(e)}")]
    
    async def _git_diff(self, target: str = "HEAD", staged: bool = False) -> List[types.TextContent]:
        """Show diff."""
        try:
            if staged:
                diff = self.repo.git.diff("--cached")
            else:
                diff = self.repo.git.diff(target)
            
            if not diff:
                return [types.TextContent(type="text", text="No differences found")]
            
            return [types.TextContent(type="text", text=diff)]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Failed to get diff: {str(e)}")]
    
    async def _git_log(self, max_count: int = 10, oneline: bool = True) -> List[types.TextContent]:
        """Show commit log."""
        try:
            if oneline:
                log_output = self.repo.git.log("--oneline", f"-{max_count}")
            else:
                log_output = self.repo.git.log(f"-{max_count}")
            
            return [types.TextContent(type="text", text=log_output)]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Failed to get log: {str(e)}")]
    
    async def _git_branch_list(self, include_remote: bool = True) -> List[types.TextContent]:
        """List branches."""
        try:
            branches = []
            
            # Local branches
            for branch in self.repo.branches:
                marker = "* " if branch == self.repo.active_branch else "  "
                branches.append(f"{marker}{branch.name}")
            
            # Remote branches
            if include_remote:
                branches.append("\nRemote branches:")
                for ref in self.repo.remote().refs:
                    branches.append(f"  {ref.name}")
            
            return [types.TextContent(type="text", text="\n".join(branches))]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Failed to list branches: {str(e)}")]
    
    async def _git_push(self, remote: str = "origin", branch: Optional[str] = None, force: bool = False) -> List[types.TextContent]:
        """Push to remote."""
        try:
            if branch is None:
                branch = self.repo.active_branch.name
            
            if force:
                self.repo.git.push(remote, branch, "--force")
                return [types.TextContent(
                    type="text", 
                    text=f"Force pushed {branch} to {remote} (WARNING: This can overwrite remote history)"
                )]
            else:
                self.repo.git.push(remote, branch)
                return [types.TextContent(type="text", text=f"Pushed {branch} to {remote}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Failed to push: {str(e)}")]
    
    async def _git_pull(self, remote: str = "origin", branch: Optional[str] = None) -> List[types.TextContent]:
        """Pull from remote."""
        try:
            if branch is None:
                branch = self.repo.active_branch.name
            
            self.repo.git.pull(remote, branch)
            return [types.TextContent(type="text", text=f"Pulled latest changes from {remote}/{branch}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Failed to pull: {str(e)}")]
