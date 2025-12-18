"""
Markdown to PDF conversion module with optimized workflow.

Features:
- Converts MD files to centralized output directory
- Timestamp-based caching (skips if PDF is newer than MD)
- Parallel conversion for speed
- Lazy conversion (only converts files needed for the book)
"""

import os
import datetime
import markdown
from weasyprint import HTML

from .utils import (
    get_gitignore_patterns, 
    is_ignored, 
    get_default_output_dir,
    ensure_dir
)

# Default header/footer configuration
DEFAULT_HEADER_TEXT = "GitHub Copilot Training Material"
DEFAULT_FOOTER_LEFT = datetime.date.today().strftime("%B %d, %Y")
DEFAULT_FOOTER_RIGHT = "Kangeyan Passoubady | Kangs | Kavin School"

# WeasyPrint is NOT thread-safe, so we use sequential conversion
# See: https://github.com/Kozea/WeasyPrint/issues/677


def find_markdown_files(root_dir: str, ignore_patterns: list[str] = None) -> list[str]:
    """
    Find all markdown files in a directory tree, excluding ignored paths.
    
    Args:
        root_dir: Root directory to search
        ignore_patterns: List of gitignore-style patterns to exclude
        
    Returns:
        List of absolute paths to markdown files
    """
    if ignore_patterns is None:
        ignore_patterns = get_gitignore_patterns(root_dir)
    
    md_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Remove ignored directories in-place
        dirnames[:] = [d for d in dirnames if not is_ignored(
            os.path.relpath(os.path.join(dirpath, d), root_dir), 
            ignore_patterns
        )]
        for filename in filenames:
            if filename.endswith('.md'):
                rel_path = os.path.relpath(os.path.join(dirpath, filename), root_dir)
                if not is_ignored(rel_path, ignore_patterns):
                    md_files.append(os.path.join(dirpath, filename))
    return md_files


def get_output_pdf_path(md_path: str, root_dir: str = None, output_dir: str = None) -> str:
    """
    Get the output PDF path for a markdown file, preserving directory structure.
    
    Args:
        md_path: Absolute path to markdown file
        root_dir: Project root directory
        output_dir: Output directory for PDFs
        
    Returns:
        Absolute path where PDF should be written
    """
    if root_dir is None:
        root_dir = os.getcwd()
    if output_dir is None:
        output_dir = get_default_output_dir(root_dir)
    
    # Get relative path from project root
    rel_path = os.path.relpath(md_path, root_dir)
    # Change extension to .pdf
    rel_pdf_path = rel_path[:-3] + '.pdf' if rel_path.endswith('.md') else rel_path + '.pdf'
    # Join with output directory
    return os.path.join(output_dir, rel_pdf_path)


def is_conversion_needed(md_path: str, pdf_path: str, force: bool = False) -> bool:
    """
    Check if conversion is needed based on file timestamps.
    
    Args:
        md_path: Path to source markdown file
        pdf_path: Path to target PDF file
        force: If True, always return True (force reconversion)
        
    Returns:
        True if conversion is needed, False if cached PDF is still valid
    """
    if force:
        return True
    
    if not os.path.exists(pdf_path):
        return True
    
    # Check if MD file is newer than PDF
    md_mtime = os.path.getmtime(md_path)
    pdf_mtime = os.path.getmtime(pdf_path)
    
    return md_mtime > pdf_mtime


def convert_markdown_to_pdf(
    md_path: str, 
    pdf_path: str = None,
    header_text: str = DEFAULT_HEADER_TEXT,
    footer_left: str = DEFAULT_FOOTER_LEFT,
    footer_right: str = DEFAULT_FOOTER_RIGHT,
    force: bool = False
) -> tuple[str, bool]:
    """
    Convert a markdown file to PDF with header and footer.
    
    Args:
        md_path: Path to markdown file
        pdf_path: Output PDF path (defaults to output directory with same structure)
        header_text: Text for page header
        footer_left: Text for left footer
        footer_right: Text for right footer
        force: Force reconversion even if cached
        
    Returns:
        Tuple of (pdf_path, was_converted) - was_converted is False if cached
    """
    if pdf_path is None:
        pdf_path = get_output_pdf_path(md_path)
    
    # Check if conversion is needed (caching)
    if not is_conversion_needed(md_path, pdf_path, force):
        return pdf_path, False
    
    # Ensure output directory exists
    ensure_dir(os.path.dirname(pdf_path))
    
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    html_content = markdown.markdown(
        md_content, 
        extensions=['extra', 'toc', 'tables']
    )
    
    html_template = f'''
    <html>
    <head>
        <style>
            @page {{
                size: A4;
                margin: 1in 0.8in 1in 0.8in;
                @top-center {{
                    content: '{header_text}';
                    font-size: 14px;
                    font-weight: bold;
                    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
                }}
                @bottom-left {{
                    content: '{footer_left}';
                    font-size: 12px;
                    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
                }}
                @bottom-right {{
                    content: '{footer_right}';
                    font-size: 12px;
                    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
                }}
            }}
            
            /* Base font for all text */
            body {{
                font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
                font-size: 11pt;
                line-height: 1.6;
                color: #333;
            }}
            
            /* Headings */
            h1, h2, h3, h4, h5, h6 {{
                font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
                font-weight: 600;
                margin-top: 1.5em;
                margin-bottom: 0.5em;
                color: #222;
            }}
            h1 {{ font-size: 24pt; }}
            h2 {{ font-size: 18pt; }}
            h3 {{ font-size: 14pt; }}
            h4 {{ font-size: 12pt; }}
            
            /* Paragraphs */
            p {{
                margin: 0.8em 0;
            }}
            
            /* Code - inline and blocks */
            code, pre, kbd, samp {{
                font-family: "SF Mono", "Monaco", "Menlo", "Consolas", "Liberation Mono", monospace;
                font-size: 10pt;
            }}
            
            code {{
                background-color: #f5f5f5;
                padding: 0.2em 0.4em;
                border-radius: 3px;
            }}
            
            pre {{
                background-color: #f5f5f5;
                padding: 1em;
                border-radius: 5px;
                overflow-x: auto;
                line-height: 1.4;
            }}
            
            pre code {{
                background-color: transparent;
                padding: 0;
            }}
            
            /* Tables */
            table {{
                font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
                border-collapse: collapse;
                width: 100%;
                margin: 1em 0;
                font-size: 10pt;
            }}
            
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            
            th {{
                background-color: #f5f5f5;
                font-weight: 600;
            }}
            
            tr:nth-child(even) {{
                background-color: #fafafa;
            }}
            
            /* Lists */
            ul, ol {{
                margin: 0.8em 0;
                padding-left: 2em;
            }}
            
            li {{
                margin: 0.3em 0;
            }}
            
            /* Blockquotes */
            blockquote {{
                font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
                font-style: italic;
                margin: 1em 0;
                padding: 0.5em 1em;
                border-left: 4px solid #ddd;
                color: #666;
            }}
            
            /* Links */
            a {{
                color: #0066cc;
                text-decoration: none;
            }}
            
            /* Images */
            img {{
                max-width: 100%;
                height: auto;
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    '''
    
    HTML(string=html_template, base_url=os.path.dirname(md_path)).write_pdf(pdf_path)
    return pdf_path, True


def convert_file(
    file_path: str,
    root_dir: str = None,
    output_dir: str = None,
    force: bool = False,
    verbose: bool = False
) -> tuple[str, bool, str]:
    """
    Convert a single file (MD or PDF) and return the PDF path.
    
    If file is already a PDF, returns the path directly.
    If file is MD, converts to PDF in output directory.
    
    Args:
        file_path: Path to file (.md or .pdf)
        root_dir: Project root directory
        output_dir: Output directory for converted PDFs
        force: Force reconversion
        verbose: Print progress
        
    Returns:
        Tuple of (pdf_path, was_converted, error_message)
        error_message is None on success
    """
    if root_dir is None:
        root_dir = os.getcwd()
    if output_dir is None:
        output_dir = get_default_output_dir(root_dir)
    
    try:
        # If it's already a PDF, just return the path
        if file_path.lower().endswith('.pdf'):
            if os.path.exists(file_path):
                return file_path, False, None
            else:
                return None, False, f"PDF not found: {file_path}"
        
        # If it's a markdown file, convert it
        if file_path.lower().endswith('.md'):
            if not os.path.exists(file_path):
                return None, False, f"MD file not found: {file_path}"
            
            pdf_path = get_output_pdf_path(file_path, root_dir, output_dir)
            pdf_path, was_converted = convert_markdown_to_pdf(file_path, pdf_path, force=force)
            
            if verbose and was_converted:
                print(f"  Converted: {os.path.relpath(file_path, root_dir)}")
            elif verbose:
                print(f"  Cached: {os.path.relpath(file_path, root_dir)}")
            
            return pdf_path, was_converted, None
        
        return None, False, f"Unsupported file type: {file_path}"
        
    except Exception as e:
        return None, False, str(e)


def convert_files_parallel(
    file_paths: list[str],
    root_dir: str = None,
    output_dir: str = None,
    force: bool = False,
    verbose: bool = True,
    max_workers: int = 1  # WeasyPrint is not thread-safe
) -> tuple[list[str], int, int]:
    """
    Convert multiple files sequentially.
    
    Note: WeasyPrint is not thread-safe, so parallel conversion is disabled.
    
    Args:
        file_paths: List of file paths to convert
        root_dir: Project root directory
        output_dir: Output directory for PDFs
        force: Force reconversion
        verbose: Print progress
        max_workers: Ignored (kept for API compatibility)
        
    Returns:
        Tuple of (pdf_paths, converted_count, failed_count)
    """
    if root_dir is None:
        root_dir = os.getcwd()
    if output_dir is None:
        output_dir = get_default_output_dir(root_dir)
    
    pdf_paths = []
    converted_count = 0
    failed_count = 0
    
    # Filter to only MD files that need conversion
    md_files = [f for f in file_paths if f.lower().endswith('.md')]
    pdf_files = [f for f in file_paths if f.lower().endswith('.pdf')]
    
    # Add existing PDFs directly
    for pdf_file in pdf_files:
        if os.path.exists(pdf_file):
            pdf_paths.append(pdf_file)
        else:
            if verbose:
                print(f"  Warning: PDF not found: {pdf_file}")
            failed_count += 1
    
    if not md_files:
        return pdf_paths, converted_count, failed_count
    
    # Convert MD files sequentially (WeasyPrint is not thread-safe)
    for md_file in md_files:
        try:
            pdf_path, was_converted, error = convert_file(
                md_file, root_dir, output_dir, force, False
            )
            if error:
                if verbose:
                    print(f"  Failed: {os.path.relpath(md_file, root_dir)} - {error}")
                failed_count += 1
            else:
                pdf_paths.append(pdf_path)
                if was_converted:
                    converted_count += 1
                    if verbose:
                        print(f"  Converted: {os.path.relpath(md_file, root_dir)}")
                elif verbose:
                    print(f"  Cached: {os.path.relpath(md_file, root_dir)}")
        except Exception as e:
            if verbose:
                print(f"  Error: {os.path.relpath(md_file, root_dir)} - {e}")
            failed_count += 1
    
    return pdf_paths, converted_count, failed_count


def convert_all(
    root_dir: str = None,
    output_dir: str = None,
    force: bool = False,
    verbose: bool = True,
    parallel: bool = True
) -> tuple[int, int, int]:
    """
    Convert all markdown files in a directory tree to PDF.
    
    Args:
        root_dir: Root directory to process (defaults to project root)
        output_dir: Output directory for PDFs (defaults to bookbuilder/output)
        force: Force reconversion of all files
        verbose: Print progress messages
        parallel: Use parallel conversion
        
    Returns:
        Tuple of (total_count, converted_count, failed_count)
    """
    if root_dir is None:
        root_dir = os.getcwd()
    if output_dir is None:
        output_dir = get_default_output_dir(root_dir)
    
    ignore_patterns = get_gitignore_patterns(root_dir)
    md_files = find_markdown_files(root_dir, ignore_patterns)
    
    if verbose:
        print(f"Found {len(md_files)} markdown files.")
    
    if parallel:
        pdf_paths, converted_count, failed_count = convert_files_parallel(
            md_files, root_dir, output_dir, force, verbose
        )
        cached_count = len(pdf_paths) - converted_count
    else:
        converted_count = 0
        failed_count = 0
        cached_count = 0
        
        for md_file in md_files:
            pdf_path, was_converted, error = convert_file(
                md_file, root_dir, output_dir, force, verbose
            )
            if error:
                failed_count += 1
            elif was_converted:
                converted_count += 1
            else:
                cached_count += 1
    
    if verbose:
        print(f"\nConversion complete:")
        print(f"  Converted: {converted_count}")
        print(f"  Cached: {cached_count}")
        print(f"  Failed: {failed_count}")
    
    return len(md_files), converted_count, failed_count
