"""
Shared utility functions for the bookbuilder package.

BookBuilder is a standalone tool for building PDF books from markdown files.
All paths are provided by the user - no hardcoded project structure assumptions.
"""

import os
import fnmatch


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
