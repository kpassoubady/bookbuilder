"""
BookBuilder - A standalone tool for building PDF books from markdown files.

Features:
- Convert markdown files to PDF with caching
- Combine PDFs into a single book with TOC and bookmarks
- Support for MD files, PDF files, and directories in order files
- Works with any project - no hardcoded paths

Installation:
    pip install bookbuilder
    # or
    pip install git+https://github.com/yourusername/bookbuilder.git

Usage:
    # Build a book from an order JSON file
    bookbuilder build --order ./book-order.json
    
    # Build with explicit root directory
    bookbuilder build --root /path/to/project --order book-order.json
    
    # Build with custom output directory
    bookbuilder build --order ./order.json --output-dir ./my-output
    
    # Cleanup output directory
    bookbuilder cleanup --output-dir ./bookbuilder-output --confirm

Order JSON Format:
    {
        "bookTitle": "My Book Title",
        "outputFilename": "my-book.pdf",
        "chapters": [
            {"section": "Chapter 1", "files": ["intro.md", "chapter1.md"]},
            {"section": "Chapter 2", "files": ["chapter2.pdf"]}
        ]
    }
"""

__version__ = "2.0.0"
__author__ = "Kangeyan Passoubady"

from .convert import (
    convert_markdown_to_pdf, 
    find_markdown_files,
    convert_file,
    convert_files_parallel,
    convert_all,
    get_output_pdf_path,
    is_conversion_needed
)
from .combine import (
    build_book, 
    create_toc_page,
    resolve_file_path,
    find_files_in_directory,
    collect_files_for_chapter
)
from .cleanup import (
    cleanup_output
)
from .utils import (
    get_gitignore_patterns, 
    is_ignored, 
    get_default_output_dir,
    ensure_dir
)

__all__ = [
    # Convert module
    "convert_markdown_to_pdf",
    "find_markdown_files",
    "convert_file",
    "convert_files_parallel",
    "convert_all",
    "get_output_pdf_path",
    "is_conversion_needed",
    # Combine module
    "build_book",
    "create_toc_page",
    "resolve_file_path",
    "find_files_in_directory",
    "collect_files_for_chapter",
    # Cleanup module
    "cleanup_output",
    # Utils module
    "get_gitignore_patterns",
    "is_ignored",
    "get_default_output_dir",
    "ensure_dir",
]
