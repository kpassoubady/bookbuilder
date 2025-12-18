"""
Pytest configuration and shared fixtures for BookBuilder tests.

Fixtures provide reusable test data and setup/teardown functionality.
"""

import os
import json
import tempfile
import shutil
import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    # Cleanup after test
    if os.path.exists(temp_path):
        shutil.rmtree(temp_path)


@pytest.fixture
def sample_markdown_content():
    """Sample markdown content for testing."""
    return """# Sample Title

This is a sample markdown document.

## Section 1

Some content here with **bold** and *italic* text.

### Subsection 1.1

- Item 1
- Item 2
- Item 3

## Section 2

```python
def hello():
    print("Hello, World!")
```

| Column 1 | Column 2 |
|----------|----------|
| Value 1  | Value 2  |
"""


@pytest.fixture
def sample_markdown_no_title():
    """Markdown content without H1 heading."""
    return """## Section Without Title

This document has no H1 heading.

Some paragraph text here.
"""


@pytest.fixture
def sample_markdown_setext_title():
    """Markdown with Setext-style title (underlined)."""
    return """Sample Setext Title
===================

This is content under a setext-style heading.
"""


@pytest.fixture
def sample_order_json():
    """Sample order JSON structure."""
    return {
        "bookTitle": "Test Book",
        "outputFilename": "test-book.pdf",
        "pageSettings": {
            "header": "{title}",
            "footerLeft": "{date}",
            "footerCenter": "Page {page} of {pages}",
            "footerRight": "Test Company"
        },
        "chapters": [
            {
                "section": "Introduction",
                "files": ["intro.md"]
            },
            {
                "section": "Chapter 1",
                "files": ["chapter1/overview.md", "chapter1/details.md"]
            }
        ]
    }


@pytest.fixture
def sample_config():
    """Sample configuration dictionary."""
    return {
        "pageSettings": {
            "header": "{title}",
            "headerFallback": "Document",
            "footerLeft": "{date}",
            "footerCenter": "Page {page} of {pages}",
            "footerRight": "Test Company",
            "dateFormat": "%Y-%m-%d"
        },
        "styleSettings": {
            "pageSize": "A4",
            "margins": "1in",
            "fontFamily": "Arial, sans-serif",
            "bodyFontSize": "12pt"
        },
        "tocSettings": {
            "titleFontSize": 24,
            "entryFontSize": 11
        },
        "defaults": {
            "bookTitle": "Untitled",
            "outputFilename": "book.pdf"
        }
    }


@pytest.fixture
def temp_markdown_file(temp_dir, sample_markdown_content):
    """Create a temporary markdown file."""
    md_path = os.path.join(temp_dir, "test.md")
    with open(md_path, 'w') as f:
        f.write(sample_markdown_content)
    return md_path


@pytest.fixture
def temp_gitignore(temp_dir):
    """Create a temporary .gitignore file."""
    gitignore_path = os.path.join(temp_dir, ".gitignore")
    with open(gitignore_path, 'w') as f:
        f.write("*.pyc\n")
        f.write("__pycache__/\n")
        f.write("node_modules/\n")
        f.write(".env\n")
        f.write("# Comment line\n")
        f.write("output/\n")
    return gitignore_path


@pytest.fixture
def temp_config_file(temp_dir, sample_config):
    """Create a temporary config JSON file."""
    config_path = os.path.join(temp_dir, "config.json")
    with open(config_path, 'w') as f:
        json.dump(sample_config, f)
    return config_path


@pytest.fixture
def temp_order_file(temp_dir, sample_order_json):
    """Create a temporary order JSON file."""
    order_path = os.path.join(temp_dir, "order.json")
    with open(order_path, 'w') as f:
        json.dump(sample_order_json, f)
    return order_path


@pytest.fixture
def project_structure(temp_dir, sample_markdown_content):
    """Create a complete project structure for integration tests."""
    # Create directories
    os.makedirs(os.path.join(temp_dir, "chapter1"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "docs"), exist_ok=True)
    
    # Create markdown files
    files = {
        "intro.md": "# Introduction\n\nThis is the intro.",
        "chapter1/overview.md": "# Chapter 1 Overview\n\nOverview content.",
        "chapter1/details.md": "# Chapter 1 Details\n\nDetailed content.",
        "docs/appendix.md": "# Appendix\n\nAppendix content."
    }
    
    for rel_path, content in files.items():
        full_path = os.path.join(temp_dir, rel_path)
        with open(full_path, 'w') as f:
            f.write(content)
    
    # Create order JSON
    order = {
        "bookTitle": "Test Book",
        "outputFilename": "test-book.pdf",
        "chapters": [
            {"section": "Introduction", "files": ["intro.md"]},
            {"section": "Chapter 1", "files": ["chapter1/overview.md", "chapter1/details.md"]}
        ]
    }
    order_path = os.path.join(temp_dir, "order.json")
    with open(order_path, 'w') as f:
        json.dump(order, f)
    
    return {
        "root": temp_dir,
        "order_path": order_path,
        "files": list(files.keys())
    }
