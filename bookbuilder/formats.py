"""
Multi-format output support for BookBuilder.

Supports converting markdown to various output formats:
- PDF (via WeasyPrint - existing implementation)
- EPUB (via Pandoc - for Kindle/eBooks)
- DOCX (via Pandoc - for Word documents)
- HTML (via markdown library - standalone HTML)

For Amazon KDP:
- Use EPUB for Kindle eBooks
- Use PDF for print-on-demand paperbacks
"""

import os
import subprocess
import tempfile
import shutil
from enum import Enum
from typing import Optional

from .utils import ensure_dir, process_details_tags


class OutputFormat(Enum):
    """Supported output formats."""
    PDF = 'pdf'
    EPUB = 'epub'
    HTML = 'html'
    DOCX = 'docx'
    
    @classmethod
    def from_string(cls, value: str) -> 'OutputFormat':
        """Convert string to OutputFormat enum."""
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(f"Unsupported format: {value}. Supported: {[f.value for f in cls]}")


def get_format_extension(fmt: OutputFormat) -> str:
    """Get file extension for a format."""
    return f".{fmt.value}"


def check_pandoc_installed() -> bool:
    """Check if Pandoc is installed and available."""
    try:
        result = subprocess.run(
            ['pandoc', '--version'],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def get_pandoc_version() -> Optional[str]:
    """Get Pandoc version string."""
    try:
        result = subprocess.run(
            ['pandoc', '--version'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            # First line contains version
            return result.stdout.split('\n')[0]
        return None
    except FileNotFoundError:
        return None


def get_resource_paths(input_files: list[str]) -> list[str]:
    """
    Get unique directory paths from input files for Pandoc resource resolution.
    
    This allows Pandoc to find images referenced with relative paths in markdown files.
    
    Args:
        input_files: List of input file paths
        
    Returns:
        List of unique directory paths
    """
    dirs = set()
    for f in input_files:
        if os.path.exists(f):
            dirs.add(os.path.dirname(os.path.abspath(f)))
    return list(dirs)


def convert_with_pandoc(
    input_files: list[str],
    output_path: str,
    output_format: str,
    title: str = None,
    toc: bool = True,
    cover_image: str = None,
    css_file: str = None,
    metadata: dict = None,
    extra_args: list = None,
    resource_paths: list[str] = None
) -> tuple[str, bool, Optional[str]]:
    """
    Convert files using Pandoc.
    
    Args:
        input_files: List of input file paths (markdown) - Pandoc handles multiple files natively
        output_path: Path to output file
        output_format: Output format (epub, docx, html)
        title: Document title
        toc: Include table of contents
        cover_image: Path to cover image (for EPUB)
        css_file: Path to CSS file for styling
        metadata: Dictionary of metadata to include
        extra_args: Additional Pandoc arguments
        resource_paths: List of directories where Pandoc should look for images
        
    Returns:
        Tuple of (output_path, success, error_message)
    """
    if not check_pandoc_installed():
        return None, False, "Pandoc is not installed. Install with: brew install pandoc"
    
    ensure_dir(os.path.dirname(output_path))
    
    # Pandoc handles multiple input files natively
    cmd = ['pandoc'] + input_files + ['-o', output_path, '--standalone']
    
    # Add resource paths for image resolution
    # This tells Pandoc where to find images referenced with relative paths
    if resource_paths is None:
        resource_paths = get_resource_paths(input_files)
    
    if resource_paths:
        # Join paths with : on Unix, ; on Windows
        path_sep = ':' if os.name != 'nt' else ';'
        cmd.extend(['--resource-path', path_sep.join(resource_paths)])
    
    # Add TOC if requested
    if toc:
        cmd.append('--toc')
    
    # Add title metadata
    if title:
        cmd.extend(['--metadata', f'title={title}'])
    
    # Add cover image for EPUB
    if cover_image and output_format == 'epub' and os.path.exists(cover_image):
        cmd.extend(['--epub-cover-image', cover_image])
    
    # Add CSS styling
    if css_file and os.path.exists(css_file):
        cmd.extend(['--css', css_file])
    
    # Add additional metadata
    if metadata:
        for key, value in metadata.items():
            cmd.extend(['--metadata', f'{key}={value}'])
    
    # Add extra arguments
    if extra_args:
        cmd.extend(extra_args)
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            error_msg = result.stderr or "Unknown Pandoc error"
            return None, False, f"Pandoc conversion failed: {error_msg}"
        
        if os.path.exists(output_path):
            return output_path, True, None
        else:
            return None, False, "Output file was not created"
            
    except subprocess.TimeoutExpired:
        return None, False, "Pandoc conversion timed out"
    except Exception as e:
        return None, False, str(e)


def combine_markdown_files(
    md_files: list[str],
    output_path: str,
    chapter_breaks: bool = True
) -> str:
    """
    Combine multiple markdown files into a single file.
    
    Args:
        md_files: List of markdown file paths
        output_path: Path to output combined markdown file
        chapter_breaks: Add page breaks between chapters
        
    Returns:
        Path to combined markdown file
    """
    ensure_dir(os.path.dirname(output_path))
    
    with open(output_path, 'w', encoding='utf-8') as outfile:
        for i, md_file in enumerate(md_files):
            if os.path.exists(md_file):
                with open(md_file, 'r', encoding='utf-8') as infile:
                    content = infile.read()
                    outfile.write(content)
                    
                    # Add separator between files
                    if i < len(md_files) - 1:
                        if chapter_breaks:
                            # Pandoc-style page break
                            outfile.write('\n\n\\newpage\n\n')
                        else:
                            outfile.write('\n\n---\n\n')
    
    return output_path


def build_book_epub(
    md_files: list[str],
    output_path: str,
    title: str = "Untitled Book",
    author: str = None,
    cover_image: str = None,
    css_file: str = None,
    toc: bool = True,
    verbose: bool = True
) -> tuple[str, bool, Optional[str]]:
    """
    Build an EPUB book from markdown files.
    
    Args:
        md_files: List of markdown file paths in order
        output_path: Path to output EPUB file
        title: Book title
        author: Book author
        cover_image: Path to cover image
        css_file: Path to CSS file for styling
        toc: Include table of contents
        verbose: Print progress messages
        
    Returns:
        Tuple of (output_path, success, error_message)
    """
    if verbose:
        print(f"Building EPUB: {output_path}")
        print(f"  Files: {len(md_files)}")
    
    # Pass files directly to Pandoc with resource paths for image resolution
    metadata = {'title': title}
    if author:
        metadata['author'] = author
    
    # Get all directories containing source files for image resolution
    resource_paths = get_resource_paths(md_files)
    
    result = convert_with_pandoc(
        md_files,
        output_path,
        'epub',
        title=title,
        toc=toc,
        cover_image=cover_image,
        css_file=css_file,
        metadata=metadata,
        resource_paths=resource_paths
    )
    
    if verbose and result[1]:
        print(f"  ✓ EPUB created: {output_path}")
    
    return result


def build_book_docx(
    md_files: list[str],
    output_path: str,
    title: str = "Untitled Book",
    author: str = None,
    toc: bool = True,
    reference_doc: str = None,
    verbose: bool = True,
    content_settings: dict = None
) -> tuple[str, bool, Optional[str]]:
    """
    Build a DOCX document from markdown files.
    
    Args:
        md_files: List of markdown file paths in order
        output_path: Path to output DOCX file
        title: Document title
        author: Document author
        toc: Include table of contents
        reference_doc: Path to reference DOCX for styling
        verbose: Print progress messages
        
    Returns:
        Tuple of (output_path, success, error_message)
    """
    if verbose:
        print(f"Building DOCX: {output_path}")
        print(f"  Files: {len(md_files)}")
    
    # Pass files directly to Pandoc with resource paths for image resolution
    metadata = {'title': title}
    if author:
        metadata['author'] = author
    
    extra_args = []
    if reference_doc and os.path.exists(reference_doc):
        extra_args.extend(['--reference-doc', reference_doc])
    
    # Get all directories containing source files for image resolution
    resource_paths = get_resource_paths(md_files)
    
    # Preprocess files for DOCX (static format) - handle details tags
    details_settings = (content_settings or {}).get('detailsTagHandling', {})
    files_to_convert = md_files
    temp_dir = None
    
    if details_settings.get('enabled', False):
        # Check if DOCX is in static formats
        static_formats = details_settings.get('staticFormats', ['pdf', 'docx'])
        if 'docx' in static_formats:
            # Create temp copies with processed content
            temp_dir = tempfile.mkdtemp(prefix='bookbuilder_docx_')
            files_to_convert = []
            for md_file in md_files:
                if os.path.exists(md_file):
                    with open(md_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    processed = process_details_tags(content, 'docx', details_settings)
                    temp_file = os.path.join(temp_dir, os.path.basename(md_file))
                    with open(temp_file, 'w', encoding='utf-8') as f:
                        f.write(processed)
                    files_to_convert.append(temp_file)
    
    try:
        result = convert_with_pandoc(
            files_to_convert,
            output_path,
            'docx',
            title=title,
            toc=toc,
            metadata=metadata,
            extra_args=extra_args if extra_args else None,
            resource_paths=resource_paths
        )
    finally:
        # Clean up temp directory if created
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    
    if verbose and result[1]:
        print(f"  ✓ DOCX created: {output_path}")
    
    return result


def build_book_html(
    md_files: list[str],
    output_path: str,
    title: str = "Untitled Book",
    css_file: str = None,
    toc: bool = True,
    standalone: bool = True,
    verbose: bool = True
) -> tuple[str, bool, Optional[str]]:
    """
    Build a standalone HTML document from markdown files.
    
    Args:
        md_files: List of markdown file paths in order
        output_path: Path to output HTML file
        title: Document title
        css_file: Path to CSS file for styling
        toc: Include table of contents
        standalone: Create standalone HTML with full <html> structure
        verbose: Print progress messages
        
    Returns:
        Tuple of (output_path, success, error_message)
    """
    if verbose:
        print(f"Building HTML: {output_path}")
        print(f"  Files: {len(md_files)}")
    
    # Pass files directly to Pandoc with resource paths for image resolution
    extra_args = []
    if standalone:
        extra_args.append('--standalone')
    
    # Get all directories containing source files for image resolution
    resource_paths = get_resource_paths(md_files)
    
    result = convert_with_pandoc(
        md_files,
        output_path,
        'html',
        title=title,
        toc=toc,
        css_file=css_file,
        extra_args=extra_args if extra_args else None,
        resource_paths=resource_paths
    )
    
    if verbose and result[1]:
        print(f"  ✓ HTML created: {output_path}")
    
    return result


def get_supported_formats() -> list[str]:
    """Get list of supported output formats."""
    return [fmt.value for fmt in OutputFormat]


def format_requires_pandoc(fmt: OutputFormat) -> bool:
    """Check if a format requires Pandoc."""
    return fmt in (OutputFormat.EPUB, OutputFormat.DOCX, OutputFormat.HTML)
