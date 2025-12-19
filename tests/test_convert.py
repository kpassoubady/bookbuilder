"""
Unit tests for bookbuilder.convert module.

Tests cover:
- Markdown title extraction
- Placeholder processing
- CSS content building
- File path utilities
- Conversion caching logic
"""

import os
import time
import pytest

from bookbuilder.convert import (
    extract_title_from_markdown,
    process_placeholder,
    build_css_content,
    find_markdown_files,
    get_output_pdf_path,
    is_conversion_needed
)


class TestExtractTitleFromMarkdown:
    """Tests for extract_title_from_markdown function."""
    
    def test_extract_atx_style_h1(self):
        """Extract ATX-style H1 heading (# Title)."""
        content = "# My Document Title\n\nSome content here."
        
        title = extract_title_from_markdown(content)
        
        assert title == "My Document Title"
    
    def test_extract_atx_with_extra_spaces(self):
        """Handle extra spaces in ATX heading."""
        content = "#   Spaced Title   \n\nContent"
        
        title = extract_title_from_markdown(content)
        
        assert title == "Spaced Title"
    
    def test_extract_setext_style_h1(self):
        """Extract Setext-style H1 heading (underlined with =)."""
        content = "Setext Title\n============\n\nContent here."
        
        title = extract_title_from_markdown(content)
        
        assert title == "Setext Title"
    
    def test_no_h1_returns_none(self, sample_markdown_no_title):
        """Return None when no H1 heading exists."""
        title = extract_title_from_markdown(sample_markdown_no_title)
        
        assert title is None
    
    def test_h2_not_extracted(self):
        """H2 headings should not be extracted as title."""
        content = "## Section Header\n\nNo H1 here."
        
        title = extract_title_from_markdown(content)
        
        assert title is None
    
    def test_first_h1_extracted(self):
        """Only first H1 should be extracted."""
        content = "# First Title\n\n# Second Title\n\nContent"
        
        title = extract_title_from_markdown(content)
        
        assert title == "First Title"
    
    def test_h1_in_middle_of_document(self):
        """Extract H1 even if not at start of document."""
        content = "Some intro text\n\n# The Title\n\nMore content"
        
        title = extract_title_from_markdown(content)
        
        assert title == "The Title"
    
    def test_empty_content(self):
        """Empty content returns None."""
        title = extract_title_from_markdown("")
        
        assert title is None
    
    def test_h1_with_special_characters(self):
        """Handle special characters in title."""
        content = "# Title with 'quotes' & symbols!\n\nContent"
        
        title = extract_title_from_markdown(content)
        
        assert title == "Title with 'quotes' & symbols!"


class TestProcessPlaceholder:
    """Tests for process_placeholder function."""
    
    def test_replace_title_placeholder(self):
        """Replace {title} placeholder."""
        text = "Header: {title}"
        context = {"title": "My Document"}
        
        result = process_placeholder(text, context)
        
        assert result == "Header: My Document"
    
    def test_replace_multiple_placeholders(self):
        """Replace multiple different placeholders."""
        text = "{title} - {filename}"
        context = {"title": "Doc Title", "filename": "document.md"}
        
        result = process_placeholder(text, context)
        
        assert result == "Doc Title - document.md"
    
    def test_preserve_page_placeholders(self):
        """Page and pages placeholders should not be replaced."""
        text = "Page {page} of {pages}"
        context = {"page": "1", "pages": "10"}
        
        result = process_placeholder(text, context)
        
        # {page} and {pages} should remain for CSS counters
        assert "{page}" in result
        assert "{pages}" in result
    
    def test_missing_placeholder_value(self):
        """Placeholder without context value remains unchanged."""
        text = "Title: {title}"
        context = {}
        
        result = process_placeholder(text, context)
        
        assert result == "Title: {title}"
    
    def test_none_value_not_replaced(self):
        """None values should not replace placeholders."""
        text = "Title: {title}"
        context = {"title": None}
        
        result = process_placeholder(text, context)
        
        assert result == "Title: {title}"
    
    def test_empty_text(self):
        """Empty text returns empty string."""
        result = process_placeholder("", {"title": "Test"})
        
        assert result == ""
    
    def test_none_text(self):
        """None text returns empty string."""
        result = process_placeholder(None, {"title": "Test"})
        
        assert result == ""
    
    def test_date_placeholder(self):
        """Replace date placeholder."""
        text = "Generated: {date}"
        context = {"date": "2024-01-15"}
        
        result = process_placeholder(text, context)
        
        assert result == "Generated: 2024-01-15"
    
    def test_book_title_placeholder(self):
        """Replace bookTitle placeholder."""
        text = "{bookTitle}"
        context = {"bookTitle": "My Awesome Book"}
        
        result = process_placeholder(text, context)
        
        assert result == "My Awesome Book"


class TestBuildCssContent:
    """Tests for build_css_content function."""
    
    def test_simple_string(self):
        """Simple string wrapped in quotes."""
        result = build_css_content("Hello World")
        
        assert result == "'Hello World'"
    
    def test_page_counter(self):
        """Page placeholder becomes CSS counter."""
        result = build_css_content("Page {page}")
        
        assert "counter(page)" in result
        assert "'Page '" in result
    
    def test_pages_counter(self):
        """Pages placeholder becomes CSS counter."""
        result = build_css_content("{pages} total")
        
        assert "counter(pages)" in result
    
    def test_both_counters(self):
        """Both page and pages become counters."""
        result = build_css_content("Page {page} of {pages}")
        
        assert "counter(page)" in result
        assert "counter(pages)" in result
        assert "' of '" in result
    
    def test_empty_text(self):
        """Empty text returns empty quotes."""
        result = build_css_content("")
        
        assert result == "''"
    
    def test_none_text(self):
        """None text returns empty quotes."""
        result = build_css_content(None)
        
        assert result == "''"
    
    def test_no_placeholders(self):
        """Text without placeholders is simply quoted."""
        result = build_css_content("Static Footer Text")
        
        assert result == "'Static Footer Text'"


class TestFindMarkdownFiles:
    """Tests for find_markdown_files function."""
    
    def test_find_md_files(self, project_structure):
        """Find all markdown files in directory tree."""
        root = project_structure["root"]
        
        md_files = find_markdown_files(root)
        
        assert len(md_files) >= 4  # intro.md, overview.md, details.md, appendix.md
        assert all(f.endswith('.md') for f in md_files)
    
    def test_returns_absolute_paths(self, project_structure):
        """Returned paths should be absolute."""
        root = project_structure["root"]
        
        md_files = find_markdown_files(root)
        
        assert all(os.path.isabs(f) for f in md_files)
    
    def test_respects_ignore_patterns(self, project_structure):
        """Files matching ignore patterns should be excluded."""
        root = project_structure["root"]
        
        # Create an ignored file
        ignored_dir = os.path.join(root, "node_modules")
        os.makedirs(ignored_dir, exist_ok=True)
        with open(os.path.join(ignored_dir, "ignored.md"), 'w') as f:
            f.write("# Ignored")
        
        md_files = find_markdown_files(root, ["node_modules/"])
        
        assert not any("node_modules" in f for f in md_files)
    
    def test_empty_directory(self, temp_dir):
        """Empty directory returns empty list."""
        md_files = find_markdown_files(temp_dir)
        
        assert md_files == []


class TestGetOutputPdfPath:
    """Tests for get_output_pdf_path function."""
    
    def test_converts_extension(self, temp_dir):
        """MD extension converted to PDF."""
        md_path = os.path.join(temp_dir, "document.md")
        
        pdf_path = get_output_pdf_path(md_path, temp_dir, temp_dir)
        
        assert pdf_path.endswith(".pdf")
        assert "document.pdf" in pdf_path
    
    def test_preserves_directory_structure(self, temp_dir):
        """Subdirectory structure is preserved in output."""
        md_path = os.path.join(temp_dir, "chapter1", "section1", "doc.md")
        output_dir = os.path.join(temp_dir, "output")
        
        pdf_path = get_output_pdf_path(md_path, temp_dir, output_dir)
        
        assert "chapter1" in pdf_path
        assert "section1" in pdf_path
        assert pdf_path.startswith(output_dir)
    
    def test_default_output_dir(self, temp_dir):
        """Uses default output dir when not specified."""
        md_path = os.path.join(temp_dir, "doc.md")
        
        pdf_path = get_output_pdf_path(md_path, temp_dir)
        
        assert "bookbuilder-output" in pdf_path


class TestIsConversionNeeded:
    """Tests for is_conversion_needed function."""
    
    def test_force_always_returns_true(self, temp_markdown_file, temp_dir):
        """Force flag always returns True."""
        pdf_path = os.path.join(temp_dir, "test.pdf")
        
        # Create a newer PDF
        with open(pdf_path, 'w') as f:
            f.write("PDF content")
        
        result = is_conversion_needed(temp_markdown_file, pdf_path, force=True)
        
        assert result is True
    
    def test_missing_pdf_needs_conversion(self, temp_markdown_file, temp_dir):
        """Missing PDF file needs conversion."""
        pdf_path = os.path.join(temp_dir, "nonexistent.pdf")
        
        result = is_conversion_needed(temp_markdown_file, pdf_path)
        
        assert result is True
    
    def test_newer_md_needs_conversion(self, temp_markdown_file, temp_dir):
        """MD file newer than PDF needs conversion."""
        pdf_path = os.path.join(temp_dir, "test.pdf")
        
        # Create older PDF
        with open(pdf_path, 'w') as f:
            f.write("Old PDF")
        
        # Make MD newer
        time.sleep(0.1)
        with open(temp_markdown_file, 'a') as f:
            f.write("\nNew content")
        
        result = is_conversion_needed(temp_markdown_file, pdf_path)
        
        assert result is True
    
    def test_newer_pdf_skips_conversion(self, temp_markdown_file, temp_dir):
        """PDF newer than MD doesn't need conversion."""
        pdf_path = os.path.join(temp_dir, "test.pdf")
        
        # Wait to ensure time difference
        time.sleep(0.1)
        
        # Create newer PDF
        with open(pdf_path, 'w') as f:
            f.write("New PDF")
        
        result = is_conversion_needed(temp_markdown_file, pdf_path)
        
        assert result is False
