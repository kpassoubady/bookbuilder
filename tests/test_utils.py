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
    ensure_dir,
    filename_to_anchor,
    build_anchor_map,
    rewrite_markdown_links,
    inject_document_anchor
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


class TestFilenameToAnchor:
    """Tests for filename_to_anchor function."""
    
    def test_simple_filename(self):
        """Convert simple filename to anchor."""
        assert filename_to_anchor("chapter1.md") == "chapter1"
    
    def test_filename_without_extension(self):
        """Handle filename without .md extension."""
        assert filename_to_anchor("chapter1") == "chapter1"
    
    def test_uppercase_converted_to_lowercase(self):
        """Convert uppercase to lowercase."""
        assert filename_to_anchor("Chapter-ONE.md") == "chapter-one"
    
    def test_spaces_replaced_with_hyphens(self):
        """Replace spaces with hyphens."""
        assert filename_to_anchor("my chapter.md") == "my-chapter"
    
    def test_special_chars_replaced(self):
        """Replace special characters with hyphens."""
        assert filename_to_anchor("chapter_1@test!.md") == "chapter-1-test"
    
    def test_url_encoded_spaces(self):
        """Handle URL-encoded spaces (%20)."""
        assert filename_to_anchor("my%20chapter.md") == "my-chapter"
    
    def test_multiple_special_chars_single_hyphen(self):
        """Multiple consecutive special chars become single hyphen."""
        assert filename_to_anchor("chapter---test.md") == "chapter-test"
    
    def test_leading_trailing_hyphens_removed(self):
        """Remove leading and trailing hyphens."""
        assert filename_to_anchor("--chapter--.md") == "chapter"
    
    def test_empty_filename(self):
        """Handle empty filename."""
        assert filename_to_anchor("") == ""
    
    def test_only_extension(self):
        """Handle filename that is only extension."""
        assert filename_to_anchor(".md") == ""
    
    def test_numbers_preserved(self):
        """Numbers should be preserved."""
        assert filename_to_anchor("chapter123.md") == "chapter123"


class TestBuildAnchorMap:
    """Tests for build_anchor_map function."""
    
    def test_empty_file_list(self):
        """Empty file list returns empty map."""
        result = build_anchor_map([])
        assert result == {}
    
    def test_single_md_file(self):
        """Single markdown file creates multiple mappings."""
        files = ["/path/to/chapter1.md"]
        result = build_anchor_map(files)
        
        assert "chapter1.md" in result
        assert "chapter1" in result
        assert result["chapter1.md"] == "chapter1"
        assert result["chapter1"] == "chapter1"
    
    def test_non_md_files_ignored(self):
        """Non-markdown files are ignored."""
        files = ["/path/to/image.png", "/path/to/doc.pdf"]
        result = build_anchor_map(files)
        
        assert result == {}
    
    def test_mixed_files(self):
        """Mix of MD and non-MD files."""
        files = ["/path/chapter1.md", "/path/image.png", "/path/chapter2.md"]
        result = build_anchor_map(files)
        
        assert "chapter1.md" in result
        assert "chapter2.md" in result
        assert "image.png" not in result
    
    def test_url_encoded_filename(self):
        """Handle URL-encoded filenames."""
        files = ["/path/my chapter.md"]
        result = build_anchor_map(files)
        
        assert "my chapter.md" in result
        assert "my%20chapter.md" in result
        assert result["my chapter.md"] == "my-chapter"
    
    def test_with_root_dir(self, temp_dir):
        """Include relative paths when root_dir provided."""
        file_path = os.path.join(temp_dir, "docs", "chapter1.md")
        result = build_anchor_map([file_path], root_dir=temp_dir)
        
        rel_path = os.path.join("docs", "chapter1.md")
        assert rel_path in result
    
    def test_multiple_files_unique_anchors(self):
        """Multiple files get unique anchors."""
        files = ["/path/intro.md", "/path/setup.md", "/path/usage.md"]
        result = build_anchor_map(files)
        
        anchors = [result["intro.md"], result["setup.md"], result["usage.md"]]
        assert len(anchors) == len(set(anchors))  # All unique


class TestRewriteMarkdownLinks:
    """Tests for rewrite_markdown_links function."""
    
    def test_simple_md_link_rewritten(self):
        """Simple .md link is rewritten to anchor."""
        content = "See [Chapter 1](chapter1.md) for details."
        anchor_map = {"chapter1.md": "chapter1"}
        
        result = rewrite_markdown_links(content, anchor_map)
        
        assert result == "See [Chapter 1](#chapter1) for details."
    
    def test_external_links_preserved(self):
        """External HTTP links are not modified."""
        content = "Visit [Google](https://google.com) for more."
        anchor_map = {}
        
        result = rewrite_markdown_links(content, anchor_map)
        
        assert result == content
    
    def test_anchor_only_links_preserved(self):
        """Anchor-only links (#section) are not modified."""
        content = "See [Section](#existing-section) above."
        anchor_map = {}
        
        result = rewrite_markdown_links(content, anchor_map)
        
        assert result == content
    
    def test_non_md_links_preserved(self):
        """Non-markdown file links are not modified."""
        content = "See [image](image.png) and [doc](file.pdf)."
        anchor_map = {}
        
        result = rewrite_markdown_links(content, anchor_map)
        
        assert result == content
    
    def test_link_not_in_map_preserved(self):
        """Links to files not in anchor map are preserved."""
        content = "See [Other](other.md) file."
        anchor_map = {"chapter1.md": "chapter1"}  # other.md not in map
        
        result = rewrite_markdown_links(content, anchor_map)
        
        assert result == content
    
    def test_multiple_links_rewritten(self):
        """Multiple links in content are all processed."""
        content = "See [Ch1](ch1.md) and [Ch2](ch2.md)."
        anchor_map = {"ch1.md": "ch1", "ch2.md": "ch2"}
        
        result = rewrite_markdown_links(content, anchor_map)
        
        assert result == "See [Ch1](#ch1) and [Ch2](#ch2)."
    
    def test_url_encoded_link(self):
        """Handle URL-encoded links."""
        content = "See [My Chapter](my%20chapter.md) here."
        anchor_map = {"my%20chapter.md": "my-chapter", "my chapter.md": "my-chapter"}
        
        result = rewrite_markdown_links(content, anchor_map)
        
        assert result == "See [My Chapter](#my-chapter) here."
    
    def test_relative_path_link(self):
        """Handle relative path links."""
        content = "See [Setup](../docs/setup.md) file."
        anchor_map = {"setup.md": "setup", "../docs/setup.md": "setup"}
        
        result = rewrite_markdown_links(content, anchor_map)
        
        assert result == "See [Setup](#setup) file."
    
    def test_mailto_links_preserved(self):
        """Mailto links are not modified."""
        content = "Contact [us](mailto:test@example.com)."
        anchor_map = {}
        
        result = rewrite_markdown_links(content, anchor_map)
        
        assert result == content
    
    def test_empty_content(self):
        """Handle empty content."""
        result = rewrite_markdown_links("", {})
        assert result == ""
    
    def test_no_links_in_content(self):
        """Content without links passes through unchanged."""
        content = "This is plain text without any links."
        anchor_map = {"chapter.md": "chapter"}
        
        result = rewrite_markdown_links(content, anchor_map)
        
        assert result == content


class TestInjectDocumentAnchor:
    """Tests for inject_document_anchor function."""
    
    def test_anchor_injected_at_start(self):
        """Anchor tag is injected at the start of content."""
        html = "<h1>Title</h1><p>Content</p>"
        result = inject_document_anchor(html, "my-section")
        
        assert result.startswith('<a id="my-section"></a>')
        assert "<h1>Title</h1>" in result
    
    def test_anchor_id_preserved(self):
        """Anchor ID is correctly set."""
        html = "<p>Content</p>"
        result = inject_document_anchor(html, "chapter-1")
        
        assert 'id="chapter-1"' in result
    
    def test_empty_html(self):
        """Handle empty HTML content."""
        result = inject_document_anchor("", "anchor")
        
        assert result == '<a id="anchor"></a>\n'
    
    def test_special_chars_in_anchor(self):
        """Handle anchor with special characters."""
        html = "<p>Content</p>"
        result = inject_document_anchor(html, "my-anchor-123")
        
        assert 'id="my-anchor-123"' in result
    
    def test_original_content_preserved(self):
        """Original HTML content is preserved after anchor."""
        html = "<div><p>Paragraph 1</p><p>Paragraph 2</p></div>"
        result = inject_document_anchor(html, "section")
        
        assert html in result
