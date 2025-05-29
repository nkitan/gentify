"""
Configuration Loader Module

This module provides utilities for loading and managing configuration
from various sources including YAML, JSON, and environment variables.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union
import logging

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class ConfigLoaderError(Exception):
    """Custom exception for configuration loading operations."""
    pass


class ConfigLoader:
    """
    A utility class for loading configuration from various sources.
    
    Supports loading from YAML files, JSON files, environment variables,
    and provides configuration merging and validation capabilities.
    """
    
    def __init__(self, base_path: Optional[Union[str, Path]] = None):
        """
        Initialize the configuration loader.
        
        Args:
            base_path (Optional[Union[str, Path]]): Base path for relative config files
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.logger = logging.getLogger(__name__)
        self._cached_configs = {}
    
    def load_yaml_config(self, file_path: Union[str, Path], 
                        use_cache: bool = True) -> Dict[str, Any]:
        """
        Load configuration from a YAML file.
        
        Args:
            file_path (Union[str, Path]): Path to the YAML file
            use_cache (bool): Whether to use cached configuration
            
        Returns:
            Dict[str, Any]: Loaded configuration
            
        Raises:
            ConfigLoaderError: If YAML loading fails
        """
        if not YAML_AVAILABLE:
            raise ConfigLoaderError("PyYAML is not installed. Install it with: pip install pyyaml")
        
        file_path = self._resolve_path(file_path)
        cache_key = f"yaml:{file_path}"
        
        if use_cache and cache_key in self._cached_configs:
            self.logger.debug(f"Using cached YAML config: {file_path}")
            return self._cached_configs[cache_key]
        
        try:
            if not file_path.exists():
                raise ConfigLoaderError(f"YAML config file not found: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
            
            if config is None:
                config = {}
            
            self._cached_configs[cache_key] = config
            self.logger.info(f"Loaded YAML config from: {file_path}")
            
            return config
            
        except yaml.YAMLError as e:
            raise ConfigLoaderError(f"Invalid YAML in {file_path}: {e}")
        except Exception as e:
            raise ConfigLoaderError(f"Error loading YAML config {file_path}: {e}")
    
    def load_json_config(self, file_path: Union[str, Path], 
                        use_cache: bool = True) -> Dict[str, Any]:
        """
        Load configuration from a JSON file.
        
        Args:
            file_path (Union[str, Path]): Path to the JSON file
            use_cache (bool): Whether to use cached configuration
            
        Returns:
            Dict[str, Any]: Loaded configuration
            
        Raises:
            ConfigLoaderError: If JSON loading fails
        """
        file_path = self._resolve_path(file_path)
        cache_key = f"json:{file_path}"
        
        if use_cache and cache_key in self._cached_configs:
            self.logger.debug(f"Using cached JSON config: {file_path}")
            return self._cached_configs[cache_key]
        
        try:
            if not file_path.exists():
                raise ConfigLoaderError(f"JSON config file not found: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as file:
                config = json.load(file)
            
            self._cached_configs[cache_key] = config
            self.logger.info(f"Loaded JSON config from: {file_path}")
            
            return config
            
        except json.JSONDecodeError as e:
            raise ConfigLoaderError(f"Invalid JSON in {file_path}: {e}")
        except Exception as e:
            raise ConfigLoaderError(f"Error loading JSON config {file_path}: {e}")
    
    def load_env_config(self, prefix: str = "", 
                       default_values: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Load configuration from environment variables.
        
        Args:
            prefix (str): Prefix for environment variable names
            default_values (Optional[Dict[str, Any]]): Default values for missing env vars
            
        Returns:
            Dict[str, Any]: Configuration from environment variables
        """
        config = default_values.copy() if default_values else {}
        
        for key, value in os.environ.items():
            if prefix and not key.startswith(prefix):
                continue
            
            # Remove prefix and convert to lowercase
            config_key = key[len(prefix):].lower() if prefix else key.lower()
            
            # Try to parse as JSON for complex values
            try:
                parsed_value = json.loads(value)
                config[config_key] = parsed_value
            except json.JSONDecodeError:
                # Treat as string
                config[config_key] = value
        
        self.logger.info(f"Loaded {len(config)} environment variables with prefix '{prefix}'")
        return config
    
    def merge_configs(self, *configs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge multiple configuration dictionaries.
        
        Args:
            *configs: Configuration dictionaries to merge
            
        Returns:
            Dict[str, Any]: Merged configuration
        """
        merged = {}
        
        for config in configs:
            merged.update(config)
        
        self.logger.debug(f"Merged {len(configs)} configuration dictionaries")
        return merged
    
    def load_layered_config(self, base_config: Union[str, Path], 
                          env_prefix: str = "", 
                          override_config: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        """
        Load configuration with layered approach: base -> environment -> override.
        
        Args:
            base_config (Union[str, Path]): Base configuration file
            env_prefix (str): Prefix for environment variables
            override_config (Optional[Union[str, Path]]): Override configuration file
            
        Returns:
            Dict[str, Any]: Layered configuration
        """
        configs = []
        
        # Load base configuration
        base_path = Path(base_config)
        if base_path.suffix.lower() == '.yaml':
            base_conf = self.load_yaml_config(base_config)
        elif base_path.suffix.lower() == '.json':
            base_conf = self.load_json_config(base_config)
        else:
            raise ConfigLoaderError(f"Unsupported config file format: {base_path.suffix}")
        
        configs.append(base_conf)
        
        # Load environment configuration
        env_conf = self.load_env_config(env_prefix, {})
        if env_conf:
            configs.append(env_conf)
        
        # Load override configuration if provided
        if override_config:
            override_path = Path(override_config)
            if override_path.exists():
                if override_path.suffix.lower() == '.yaml':
                    override_conf = self.load_yaml_config(override_config)
                elif override_path.suffix.lower() == '.json':
                    override_conf = self.load_json_config(override_config)
                else:
                    raise ConfigLoaderError(f"Unsupported override config format: {override_path.suffix}")
                
                configs.append(override_conf)
        
        merged_config = self.merge_configs(*configs)
        self.logger.info(f"Loaded layered configuration with {len(configs)} layers")
        
        return merged_config
    
    def validate_config(self, config: Dict[str, Any], 
                       required_keys: List[str]) -> bool:
        """
        Validate that configuration contains required keys.
        
        Args:
            config (Dict[str, Any]): Configuration to validate
            required_keys (List[str]): List of required keys
            
        Returns:
            bool: True if configuration is valid
            
        Raises:
            ConfigLoaderError: If validation fails
        """
        missing_keys = []
        
        for key in required_keys:
            if key not in config:
                missing_keys.append(key)
        
        if missing_keys:
            raise ConfigLoaderError(f"Missing required configuration keys: {missing_keys}")
        
        self.logger.info("Configuration validation passed")
        return True
    
    def get_config_value(self, config: Dict[str, Any], key_path: str, 
                        default: Any = None) -> Any:
        """
        Get a configuration value using dot notation (e.g., 'database.host').
        
        Args:
            config (Dict[str, Any]): Configuration dictionary
            key_path (str): Dot-separated key path
            default: Default value if key not found
            
        Returns:
            Any: Configuration value
        """
        keys = key_path.split('.')
        current = config
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    def set_config_value(self, config: Dict[str, Any], key_path: str, value: Any) -> None:
        """
        Set a configuration value using dot notation.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary to modify
            key_path (str): Dot-separated key path
            value: Value to set
        """
        keys = key_path.split('.')
        current = config
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the value
        current[keys[-1]] = value
    
    def save_config(self, config: Dict[str, Any], file_path: Union[str, Path]) -> None:
        """
        Save configuration to a file.
        
        Args:
            config (Dict[str, Any]): Configuration to save
            file_path (Union[str, Path]): Output file path
            
        Raises:
            ConfigLoaderError: If saving fails
        """
        file_path = self._resolve_path(file_path)
        
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            if file_path.suffix.lower() == '.yaml':
                if not YAML_AVAILABLE:
                    raise ConfigLoaderError("PyYAML is not installed")
                
                with open(file_path, 'w', encoding='utf-8') as file:
                    yaml.dump(config, file, default_flow_style=False, indent=2)
                    
            elif file_path.suffix.lower() == '.json':
                with open(file_path, 'w', encoding='utf-8') as file:
                    json.dump(config, file, indent=2, ensure_ascii=False)
            else:
                raise ConfigLoaderError(f"Unsupported config file format: {file_path.suffix}")
            
            self.logger.info(f"Saved configuration to: {file_path}")
            
        except Exception as e:
            raise ConfigLoaderError(f"Error saving config to {file_path}: {e}")
    
    def clear_cache(self) -> None:
        """Clear the configuration cache."""
        self._cached_configs.clear()
        self.logger.debug("Configuration cache cleared")
    
    def _resolve_path(self, file_path: Union[str, Path]) -> Path:
        """
        Resolve file path relative to base path.
        
        Args:
            file_path (Union[str, Path]): File path to resolve
            
        Returns:
            Path: Resolved absolute path
        """
        path = Path(file_path)
        if not path.is_absolute():
            path = self.base_path / path
        return path.resolve()
