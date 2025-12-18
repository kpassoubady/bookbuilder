"""
Unit tests for bookbuilder.utils module.

Tests cover:
- Configuration loading and merging
- Gitignore pattern handling
- Directory utilities
"""

import os
import json
import pytest

from bookbuilder.utils import (
    get_default_config_path,
    load_config,
    deep_merge,
    get_gitignore_patterns,
    is_ignored,
    get_default_output_dir,
    ensure_dir
)


class TestDeepMerge:
    """Tests for deep_merge function."""
    
    def test_merge_flat_dicts(self):
        """Merge two flat dictionaries."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = deep_merge(base, override)
        
        assert result == {"a": 1, "b": 3, "c": 4}
    
    def test_merge_nested_dicts(self):
        """Merge nested dictionaries recursively."""
        base = {
            "level1": {
                "a": 1,
                "b": 2
            }
        }
        override = {
            "level1": {
                "b": 3,
                "c": 4
            }
        }
        result = deep_merge(base, override)
        
        assert result == {"level1": {"a": 1, "b": 3, "c": 4}}
    
    def test_merge_deeply_nested(self):
        """Merge deeply nested structures."""
        base = {
            "l1": {
                "l2": {
                    "l3": {"a": 1}
                }
            }
        }
        override = {
            "l1": {
                "l2": {
                    "l3": {"b": 2}
                }
            }
        }
        result = deep_merge(base, override)
        
        assert result["l1"]["l2"]["l3"] == {"a": 1, "b": 2}
    
    def test_override_replaces_non_dict(self):
        """Override value replaces base when types differ."""
        base = {"key": {"nested": 1}}
        override = {"key": "string_value"}
        result = deep_merge(base, override)
        
        assert result["key"] == "string_value"
    
    def test_empty_override(self):
        """Empty override returns copy of base."""
        base = {"a": 1, "b": 2}
        override = {}
        result = deep_merge(base, override)
        
        assert result == base
        assert result is not base  # Should be a copy
    
    def test_empty_base(self):
        """Empty base returns override values."""
        base = {}
        override = {"a": 1}
        result = deep_merge(base, override)
        
        assert result == {"a": 1}
    
    def test_base_unchanged(self):
        """Original base dict should not be modified."""
        base = {"a": 1}
        override = {"a": 2}
        deep_merge(base, override)
        
        assert base["a"] == 1


class TestLoadConfig:
    """Tests for load_config function."""
    
    def test_load_default_config(self):
        """Load default config when no user config provided."""
        config = load_config()
        
        assert "pageSettings" in config
        assert "styleSettings" in config
        assert "tocSettings" in config
        assert "defaults" in config
    
    def test_load_default_config_has_required_keys(self):
        """Default config contains all required settings."""
        config = load_config()
        
        # Check pageSettings
        assert "header" in config["pageSettings"]
        assert "footerLeft" in config["pageSettings"]
        assert "dateFormat" in config["pageSettings"]
        
        # Check styleSettings
        assert "pageSize" in config["styleSettings"]
        assert "fontFamily" in config["styleSettings"]
        
        # Check defaults
        assert "bookTitle" in config["defaults"]
        assert "outputFilename" in config["defaults"]
    
    def test_load_user_config_merges(self, temp_dir):
        """User config merges with default config."""
        # Create user config with partial override
        user_config = {
            "pageSettings": {
                "footerRight": "Custom Company"
            }
        }
        config_path = os.path.join(temp_dir, "user-config.json")
        with open(config_path, 'w') as f:
            json.dump(user_config, f)
        
        config = load_config(config_path)
        
        # User override applied
        assert config["pageSettings"]["footerRight"] == "Custom Company"
        # Default values preserved
        assert "header" in config["pageSettings"]
        assert "styleSettings" in config
    
    def test_load_nonexistent_user_config(self):
        """Nonexistent user config path returns default config."""
        config = load_config("/nonexistent/path/config.json")
        
        assert "pageSettings" in config
        assert "defaults" in config


class TestGetDefaultConfigPath:
    """Tests for get_default_config_path function."""
    
    def test_returns_path(self):
        """Returns a path string."""
        path = get_default_config_path()
        
        assert isinstance(path, str)
        assert path.endswith("default-config.json")
    
    def test_file_exists(self):
        """Default config file exists at returned path."""
        path = get_default_config_path()
        
        assert os.path.exists(path)
    
    def test_valid_json(self):
        """Default config file contains valid JSON."""
        path = get_default_config_path()
        
        with open(path, 'r') as f:
            config = json.load(f)
        
        assert isinstance(config, dict)


class TestGetGitignorePatterns:
    """Tests for get_gitignore_patterns function."""
    
    def test_load_patterns(self, temp_gitignore, temp_dir):
        """Load patterns from .gitignore file."""
        patterns = get_gitignore_patterns(temp_dir)
        
        assert "*.pyc" in patterns
        assert "__pycache__/" in patterns
        assert "node_modules/" in patterns
    
    def test_ignore_comments(self, temp_gitignore, temp_dir):
        """Comments should not be included in patterns."""
        patterns = get_gitignore_patterns(temp_dir)
        
        assert "# Comment line" not in patterns
        for pattern in patterns:
            assert not pattern.startswith("#")
    
    def test_ignore_empty_lines(self, temp_gitignore, temp_dir):
        """Empty lines should not be included."""
        patterns = get_gitignore_patterns(temp_dir)
        
        assert "" not in patterns
    
    def test_no_gitignore(self, temp_dir):
        """Return empty list if no .gitignore exists."""
        patterns = get_gitignore_patterns(temp_dir)
        
        assert patterns == []


class TestIsIgnored:
    """Tests for is_ignored function."""
    
    def test_match_extension_pattern(self):
        """Match file extension pattern."""
        patterns = ["*.pyc", "*.log"]
        
        assert is_ignored("file.pyc", patterns) is True
        assert is_ignored("debug.log", patterns) is True
        assert is_ignored("file.py", patterns) is False
    
    def test_match_directory_pattern(self):
        """Match directory patterns."""
        patterns = ["__pycache__/", "node_modules/"]
        
        assert is_ignored("__pycache__", patterns) is True
        assert is_ignored("node_modules", patterns) is True
    
    def test_match_filename(self):
        """Match exact filename."""
        patterns = [".env", "config.local.json"]
        
        assert is_ignored(".env", patterns) is True
        assert is_ignored("path/to/.env", patterns) is True
        assert is_ignored(".env.example", patterns) is False
    
    def test_no_patterns(self):
        """Empty patterns list matches nothing."""
        patterns = []
        
        assert is_ignored("any_file.txt", patterns) is False
    
    def test_nested_path(self):
        """Match patterns in nested paths."""
        patterns = ["*.pyc"]
        
        assert is_ignored("deep/nested/path/file.pyc", patterns) is True


class TestGetDefaultOutputDir:
    """Tests for get_default_output_dir function."""
    
    def test_returns_correct_path(self):
        """Return bookbuilder-output subdirectory."""
        root = "/path/to/project"
        result = get_default_output_dir(root)
        
        assert result == "/path/to/project/bookbuilder-output"
    
    def test_handles_trailing_slash(self):
        """Handle root path with trailing slash."""
        root = "/path/to/project/"
        result = get_default_output_dir(root)
        
        # os.path.join handles this correctly
        assert "bookbuilder-output" in result


class TestEnsureDir:
    """Tests for ensure_dir function."""
    
    def test_create_new_directory(self, temp_dir):
        """Create directory that doesn't exist."""
        new_dir = os.path.join(temp_dir, "new_directory")
        
        assert not os.path.exists(new_dir)
        ensure_dir(new_dir)
        assert os.path.exists(new_dir)
        assert os.path.isdir(new_dir)
    
    def test_create_nested_directories(self, temp_dir):
        """Create nested directory structure."""
        nested_dir = os.path.join(temp_dir, "level1", "level2", "level3")
        
        ensure_dir(nested_dir)
        assert os.path.exists(nested_dir)
    
    def test_existing_directory(self, temp_dir):
        """No error when directory already exists."""
        existing_dir = os.path.join(temp_dir, "existing")
        os.makedirs(existing_dir)
        
        # Should not raise exception
        ensure_dir(existing_dir)
        assert os.path.exists(existing_dir)
