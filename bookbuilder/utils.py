"""
Shared utility functions for the bookbuilder package.

BookBuilder is a standalone tool for building PDF books from markdown files.
All paths are provided by the user - no hardcoded project structure assumptions.
"""

import os
import json
import fnmatch


def get_default_config_path() -> str:
    """Get the path to the default config file bundled with the package."""
    return os.path.join(os.path.dirname(__file__), 'default-config.json')


def load_config(config_path: str = None) -> dict:
    """
    Load configuration from a JSON file.
    
    Loads the default config first, then merges with user config if provided.
    
    Args:
        config_path: Path to user config file (optional)
        
    Returns:
        Merged configuration dictionary
    """
    # Load default config
    default_config_path = get_default_config_path()
    with open(default_config_path, 'r') as f:
        config = json.load(f)
    
    # Merge with user config if provided
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            user_config = json.load(f)
        config = deep_merge(config, user_config)
    
    return config


def deep_merge(base: dict, override: dict) -> dict:
    """
    Deep merge two dictionaries.
    
    Args:
        base: Base dictionary
        override: Dictionary with values to override
        
    Returns:
        Merged dictionary
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def get_gitignore_patterns(root_dir: str) -> list[str]:
    """
    Load patterns from .gitignore file.
    
    Args:
        root_dir: Root directory containing .gitignore
        
    Returns:
        List of gitignore patterns
    """
    gitignore_path = os.path.join(root_dir, '.gitignore')
    patterns = []
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    patterns.append(line)
    return patterns


def is_ignored(path: str, patterns: list[str]) -> bool:
    """
    Check if a path matches any of the ignore patterns.
    
    Args:
        path: Relative path to check
        patterns: List of gitignore-style patterns
        
    Returns:
        True if path should be ignored
    """
    for pattern in patterns:
        # Handle folder ignore (pattern ends with /)
        if pattern.endswith('/'):
            if os.path.commonpath([os.path.abspath(path), os.path.abspath(pattern.rstrip('/'))]) == os.path.abspath(pattern.rstrip('/')):
                return True
        # Handle file/folder pattern
        if fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(os.path.basename(path), pattern):
            return True
    return False


def get_default_output_dir(root_dir: str) -> str:
    """
    Get the default output directory for a given root directory.
    
    Args:
        root_dir: Project root directory
        
    Returns:
        Default output directory path (root_dir/bookbuilder-output)
    """
    return os.path.join(root_dir, 'bookbuilder-output')


def ensure_dir(path: str) -> None:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path to ensure exists
    """
    os.makedirs(path, exist_ok=True)
