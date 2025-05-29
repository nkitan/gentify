"""
Git operation tools using GitPython for version control operations.
"""
import os
from pathlib import Path
from typing import List, Dict, Optional, Any, Sequence
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
    
    async def execute_git_tool(self, name: str, arguments: dict) -> List[types.TextContent]:
        """Execute a Git tool and return results."""
        try:
            if name == "git_status":
                return await self._git_status()
            elif name == "git_add":
                return await self._git_add(arguments.get("files", []))
            elif name == "git_commit":
                message = arguments.get("message")
                if not message:
                    raise ValueError("Commit message is required")
                return await self._git_commit(
                    message,
                    arguments.get("add_all", False)
                )
            elif name == "git_create_branch":
                branch_name = arguments.get("branch_name")
                if not branch_name:
                    raise ValueError("Branch name is required")
                return await self._git_create_branch(
                    branch_name,
                    arguments.get("checkout", True)
                )
            elif name == "git_checkout":
                branch_name = arguments.get("branch_name")
                if not branch_name:
                    raise ValueError("Branch name is required")
                return await self._git_checkout(branch_name)
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
            return [types.TextContent(type="text", text=f"Error executing {name}: {str(e)}")]

    async def _git_status(self) -> List[types.TextContent]:
        """Get Git repository status."""
        try:
            repo = self.repo
            status_info = {
                "branch": repo.active_branch.name,
                "ahead": repo.iter_commits('origin/HEAD..HEAD') if repo.remotes else 0,
                "behind": repo.iter_commits('HEAD..origin/HEAD') if repo.remotes else 0,
                "staged": list(repo.index.diff("HEAD")),
                "unstaged": list(repo.index.diff(None)),
                "untracked": repo.untracked_files
            }
            
            result = f"Current branch: {status_info['branch']}\n"
            result += f"Staged files: {len(status_info['staged'])}\n"
            result += f"Unstaged files: {len(status_info['unstaged'])}\n"
            result += f"Untracked files: {len(status_info['untracked'])}\n"
            
            if status_info['staged']:
                result += "\nStaged changes:\n"
                for item in status_info['staged']:
                    result += f"  {item.change_type}: {item.a_path}\n"
            
            if status_info['unstaged']:
                result += "\nUnstaged changes:\n"
                for item in status_info['unstaged']:
                    result += f"  {item.change_type}: {item.a_path}\n"
            
            if status_info['untracked']:
                result += "\nUntracked files:\n"
                for file in status_info['untracked']:
                    result += f"  {file}\n"
            
            return [types.TextContent(type="text", text=result)]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error getting status: {str(e)}")]

    async def _git_add(self, files: List[str]) -> List[types.TextContent]:
        """Add files to staging area."""
        try:
            repo = self.repo
            for file_pattern in files:
                if file_pattern == ".":
                    repo.git.add(A=True)
                else:
                    repo.index.add([file_pattern])
            
            result = f"Added files: {', '.join(files)}"
            return [types.TextContent(type="text", text=result)]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error adding files: {str(e)}")]

    async def _git_commit(self, message: str, add_all: bool = False) -> List[types.TextContent]:
        """Commit staged changes."""
        try:
            repo = self.repo
            if add_all:
                repo.git.add(A=True)
            
            commit = repo.index.commit(message)
            result = f"Committed: {commit.hexsha[:8]} - {message}"
            return [types.TextContent(type="text", text=result)]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error committing: {str(e)}")]

    async def _git_create_branch(self, branch_name: str, checkout: bool = True) -> List[types.TextContent]:
        """Create a new branch."""
        try:
            repo = self.repo
            new_branch = repo.create_head(branch_name)
            if checkout:
                new_branch.checkout()
            
            result = f"Created branch '{branch_name}'"
            if checkout:
                result += " and checked out"
            return [types.TextContent(type="text", text=result)]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error creating branch: {str(e)}")]

    async def _git_checkout(self, branch_name: str) -> List[types.TextContent]:
        """Checkout a branch."""
        try:
            repo = self.repo
            repo.git.checkout(branch_name)
            result = f"Checked out branch '{branch_name}'"
            return [types.TextContent(type="text", text=result)]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error checking out branch: {str(e)}")]

    async def _git_diff(self, target: str = "HEAD", staged: bool = False) -> List[types.TextContent]:
        """Show git diff."""
        try:
            repo = self.repo
            if staged:
                diff = repo.git.diff("--cached")
            else:
                diff = repo.git.diff(target)
            
            if not diff:
                result = "No differences found"
            else:
                result = f"Diff against {target}:\n{diff}"
            
            return [types.TextContent(type="text", text=result)]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error getting diff: {str(e)}")]

    async def _git_log(self, max_count: int = 10, oneline: bool = True) -> List[types.TextContent]:
        """Show commit history."""
        try:
            repo = self.repo
            commits = list(repo.iter_commits(max_count=max_count))
            
            result = f"Last {len(commits)} commits:\n"
            for commit in commits:
                if oneline:
                    result += f"{commit.hexsha[:8]} - {commit.summary}\n"
                else:
                    result += f"Commit: {commit.hexsha}\n"
                    result += f"Author: {commit.author}\n"
                    result += f"Date: {commit.committed_datetime}\n"
                    result += f"Message: {commit.message}\n\n"
            
            return [types.TextContent(type="text", text=result)]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error getting log: {str(e)}")]

    async def _git_branch_list(self, remote: bool = True) -> List[types.TextContent]:
        """List branches."""
        try:
            repo = self.repo
            result = "Branches:\n"
            
            # Local branches
            result += "Local:\n"
            for branch in repo.branches:
                marker = " * " if branch == repo.active_branch else "   "
                result += f"{marker}{branch.name}\n"
            
            # Remote branches
            if remote and repo.remotes:
                result += "\nRemote:\n"
                for remote_ref in repo.remotes.origin.refs:
                    result += f"   {remote_ref.name}\n"
            
            return [types.TextContent(type="text", text=result)]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error listing branches: {str(e)}")]

    async def _git_push(self, remote: str = "origin", branch: str = None, force: bool = False) -> List[types.TextContent]:
        """Push to remote repository."""
        try:
            repo = self.repo
            if not branch:
                branch = repo.active_branch.name
            
            if force:
                repo.git.push(remote, branch, force=True)
                result = f"Force pushed {branch} to {remote}"
            else:
                repo.git.push(remote, branch)
                result = f"Pushed {branch} to {remote}"
            
            return [types.TextContent(type="text", text=result)]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error pushing: {str(e)}")]

    async def _git_pull(self, remote: str = "origin", branch: str = None) -> List[types.TextContent]:
        """Pull from remote repository."""
        try:
            repo = self.repo
            if not branch:
                branch = repo.active_branch.name
            
            repo.git.pull(remote, branch)
            result = f"Pulled {branch} from {remote}"
            return [types.TextContent(type="text", text=result)]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error pulling: {str(e)}")]
