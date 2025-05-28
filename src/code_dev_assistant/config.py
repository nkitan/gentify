"""
Configuration management for the code development assistant.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
import json
from dataclasses import dataclass, asdict
from dotenv import load_dotenv


@dataclass
class GitConfig:
    """Git-related configuration."""
    default_branch: str = "main"
    auto_stage: bool = False
    push_after_commit: bool = False
    force_push_allowed: bool = False


@dataclass
class RAGConfig:
    """RAG system configuration."""
    db_path: str = "./code_rag_db"
    embedding_model: str = "all-MiniLM-L6-v2"
    max_chunk_size: int = 2000
    similarity_threshold: float = 0.7
    excluded_dirs: Optional[list] = None
    included_extensions: Optional[list] = None
    
    def __post_init__(self):
        if self.excluded_dirs is None:
            self.excluded_dirs = [".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build"]
        if self.included_extensions is None:
            self.included_extensions = [".py", ".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c", ".h"]


@dataclass
class LLMConfig:
    """LLM configuration."""
    base_url: str = "http://localhost:11434"
    model: str = "codellama:7b-instruct"
    timeout: int = 60
    temperature: float = 0.1
    max_tokens: int = 4096


@dataclass
class CodeAnalysisConfig:
    """Code analysis configuration."""
    max_file_size: int = 1024 * 1024  # 1MB
    analyze_binary_files: bool = False
    include_test_files: bool = True
    docstring_style: str = "google"  # google, numpy, sphinx


@dataclass
class AssistantConfig:
    """Main configuration for the code development assistant."""
    git: GitConfig
    rag: RAGConfig
    llm: LLMConfig
    code_analysis: CodeAnalysisConfig
    workspace_path: Optional[str] = None
    log_level: str = "INFO"
    
    @classmethod
    def from_file(cls, config_path: str) -> 'AssistantConfig':
        """Load configuration from JSON file."""
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                data = json.load(f)
            
            return cls(
                git=GitConfig(**data.get('git', {})),
                rag=RAGConfig(**data.get('rag', {})),
                llm=LLMConfig(**data.get('llm', {})),
                code_analysis=CodeAnalysisConfig(**data.get('code_analysis', {})),
                workspace_path=data.get('workspace_path'),
                log_level=data.get('log_level', 'INFO')
            )
        else:
            # Return default configuration
            return cls.default()
    
    @classmethod
    def default(cls) -> 'AssistantConfig':
        """Create default configuration."""
        return cls(
            git=GitConfig(),
            rag=RAGConfig(),
            llm=LLMConfig(),
            code_analysis=CodeAnalysisConfig()
        )
    
    def to_file(self, config_path: str):
        """Save configuration to JSON file."""
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(asdict(self), f, indent=2)
    
    @classmethod
    def from_env(cls) -> 'AssistantConfig':
        """Load configuration from environment variables."""
        load_dotenv()
        
        config = cls.default()
        
        # Override with environment variables
        workspace_env = os.getenv('CODE_ASSISTANT_WORKSPACE')
        if workspace_env:
            config.workspace_path = workspace_env
        
        ollama_url = os.getenv('OLLAMA_BASE_URL')
        if ollama_url:
            config.llm.base_url = ollama_url
        
        ollama_model = os.getenv('OLLAMA_MODEL')
        if ollama_model:
            config.llm.model = ollama_model
        
        rag_db_path = os.getenv('RAG_DB_PATH')
        if rag_db_path:
            config.rag.db_path = rag_db_path
        
        embedding_model = os.getenv('EMBEDDING_MODEL')
        if embedding_model:
            config.rag.embedding_model = embedding_model
        
        log_level = os.getenv('LOG_LEVEL')
        if log_level:
            config.log_level = log_level
        
        return config


def get_config() -> AssistantConfig:
    """Get configuration from various sources in order of precedence."""
    # 1. Check for config file in current directory
    if os.path.exists('.code-assistant.json'):
        return AssistantConfig.from_file('.code-assistant.json')
    
    # 2. Check for config file in home directory
    home_config = os.path.expanduser('~/.config/code-assistant/config.json')
    if os.path.exists(home_config):
        return AssistantConfig.from_file(home_config)
    
    # 3. Load from environment variables
    return AssistantConfig.from_env()


def create_sample_config(path: str = '.code-assistant.json'):
    """Create a sample configuration file."""
    config = AssistantConfig.default()
    config.to_file(path)
    print(f"Sample configuration created at {path}")


if __name__ == "__main__":
    # CLI for configuration management
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "create":
        path = sys.argv[2] if len(sys.argv) > 2 else '.code-assistant.json'
        create_sample_config(path)
    else:
        config = get_config()
        print("Current configuration:")
        print(json.dumps(asdict(config), indent=2))
