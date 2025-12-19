"""
Shared utility functions for the bookbuilder package.

BookBuilder is a standalone tool for building PDF books from markdown files.
All paths are provided by the user - no hardcoded project structure assumptions.
"""

import os
import re
import json
import fnmatch
from urllib.parse import unquote


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


def filename_to_anchor(filename: str) -> str:
    """
    Convert a filename to a URL-safe anchor ID.
    
    Args:
        filename: Filename (with or without .md extension)
        
    Returns:
        Lowercase anchor ID with special chars replaced by hyphens
    """
    # Remove .md extension if present
    name = filename
    if name.lower().endswith('.md'):
        name = name[:-3]
    
    # URL decode (handle %20 etc.)
    name = unquote(name)
    
    # Convert to lowercase and replace non-alphanumeric with hyphens
    anchor = re.sub(r'[^a-zA-Z0-9]+', '-', name.lower())
    # Remove leading/trailing hyphens
    anchor = anchor.strip('-')
    
    return anchor


def build_anchor_map(file_paths: list[str], root_dir: str = None) -> dict:
    """
    Build a mapping of markdown filenames to anchor IDs.
    
    Args:
        file_paths: List of markdown file paths included in the book
        root_dir: Optional root directory for relative path calculation
        
    Returns:
        Dictionary mapping various filename forms to anchor IDs
    """
    anchor_map = {}
    
    for file_path in file_paths:
        if not file_path.lower().endswith('.md'):
            continue
            
        filename = os.path.basename(file_path)
        anchor = filename_to_anchor(filename)
        
        # Map multiple forms of the filename to the same anchor
        # Full filename with extension
        anchor_map[filename] = anchor
        # Filename without extension
        anchor_map[filename[:-3]] = anchor
        # URL-encoded versions (spaces as %20)
        encoded_name = filename.replace(' ', '%20')
        anchor_map[encoded_name] = anchor
        encoded_name_no_ext = encoded_name[:-3] if encoded_name.endswith('.md') else encoded_name
        anchor_map[encoded_name_no_ext] = anchor
        
        # Also map relative paths if root_dir provided
        if root_dir:
            rel_path = os.path.relpath(file_path, root_dir)
            anchor_map[rel_path] = anchor
    
    return anchor_map


def rewrite_markdown_links(md_content: str, anchor_map: dict, current_file_dir: str = None) -> str:
    """
    Rewrite relative .md links in markdown content to internal anchor links.
    
    Args:
        md_content: Raw markdown content
        anchor_map: Dictionary mapping filenames to anchor IDs
        current_file_dir: Directory of the current markdown file (for resolving relative paths)
        
    Returns:
        Markdown content with links rewritten to anchors
    """
    # Pattern to match markdown links: [text](url)
    # Captures: group(1) = link text, group(2) = URL
    link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    
    def replace_link(match):
        link_text = match.group(1)
        url = match.group(2)
        
        # Skip external links (http, https, mailto, etc.)
        if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', url):
            return match.group(0)
        
        # Skip anchor-only links
        if url.startswith('#'):
            return match.group(0)
        
        # Extract the path part (before any #anchor or ?query)
        path_part = url.split('#')[0].split('?')[0]
        
        # Skip non-markdown links
        if not path_part.lower().endswith('.md'):
            # Check if it's a directory link or other file type
            return match.group(0)
        
        # Try to resolve the link to an anchor
        # First, try the path as-is
        filename = os.path.basename(path_part)
        
        # Look up in anchor map
        anchor = None
        
        # Try filename directly
        if filename in anchor_map:
            anchor = anchor_map[filename]
        # Try URL-decoded filename
        elif unquote(filename) in anchor_map:
            anchor = anchor_map[unquote(filename)]
        # Try the full relative path
        elif path_part in anchor_map:
            anchor = anchor_map[path_part]
        # Try URL-decoded path
        elif unquote(path_part) in anchor_map:
            anchor = anchor_map[unquote(path_part)]
        
        if anchor:
            return f'[{link_text}](#{anchor})'
        
        # Link target not in book, keep original
        return match.group(0)
    
    return link_pattern.sub(replace_link, md_content)


def inject_document_anchor(html_content: str, anchor_id: str) -> str:
    """
    Inject an anchor element at the start of HTML content for internal linking.
    
    Args:
        html_content: HTML content from markdown conversion
        anchor_id: Anchor ID for this document
        
    Returns:
        HTML content with anchor injected at the start
    """
    anchor_tag = f'<a id="{anchor_id}"></a>\n'
    return anchor_tag + html_content
