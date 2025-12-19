"""
Markdown to PDF conversion module with optimized workflow.

Features:
- Converts MD files to centralized output directory
- Timestamp-based caching (skips if PDF is newer than MD)
- Parallel conversion for speed
- Lazy conversion (only converts files needed for the book)
- Dynamic headers/footers with placeholder support
"""

import os
import re
import datetime
import markdown
from weasyprint import HTML

from .utils import (
    get_gitignore_patterns, 
    is_ignored, 
    get_default_output_dir,
    ensure_dir,
    filename_to_anchor,
    rewrite_markdown_links,
    inject_document_anchor
)

# Default page settings configuration
DEFAULT_PAGE_SETTINGS = {
    'header': '{title}',
    'headerFallback': 'Document',
    'footerLeft': '{date}',
    'footerCenter': 'Page {page} of {pages}',
    'footerRight': 'Kangs | Kavin School',
    'dateFormat': '%B %d, %Y'
}


def extract_title_from_markdown(md_content: str) -> str:
    """
    Extract the first H1 heading from markdown content.
    
    Args:
        md_content: Raw markdown content
        
    Returns:
        The title text, or None if no H1 found
    """
    # Try to find # heading (ATX style)
    match = re.search(r'^#\s+(.+?)\s*$', md_content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    
    # Try to find underlined heading (Setext style)
    match = re.search(r'^(.+?)\n=+\s*$', md_content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    
    return None


def process_placeholder(text: str, context: dict) -> str:
    """
    Replace placeholders in text with actual values.
    
    Supported placeholders:
    - {title}: First H1 from markdown file
    - {filename}: Name of the source file
    - {date}: Current date (format from dateFormat setting)
    - {page}: Current page number (CSS counter)
    - {pages}: Total page count (CSS counter)
    - {bookTitle}: Book title from JSON
    
    Args:
        text: Text containing placeholders
        context: Dictionary with values for placeholders
        
    Returns:
        Text with placeholders replaced
    """
    if not text:
        return ''
    
    # Replace simple placeholders
    result = text
    for key, value in context.items():
        if key not in ('page', 'pages'):  # These are CSS counters
            placeholder = '{' + key + '}'
            if value is not None:
                result = result.replace(placeholder, str(value))
    
    return result


def build_css_content(text: str) -> str:
    """
    Convert placeholder text to CSS content property value.
    
    Handles {page} and {pages} as CSS counters.
    
    Args:
        text: Text with placeholders already processed (except page/pages)
        
    Returns:
        CSS content property value
    """
    if not text:
        return "''"
    
    # Check if text contains page placeholders
    has_page = '{page}' in text
    has_pages = '{pages}' in text
    
    if not has_page and not has_pages:
        # Simple string, just quote it
        return f"'{text}'"
    
    # Build CSS content with counters
    parts = []
    remaining = text
    
    while remaining:
        if '{page}' in remaining:
            idx = remaining.index('{page}')
            if idx > 0:
                parts.append(f"'{remaining[:idx]}'")
            parts.append('counter(page)')
            remaining = remaining[idx + 6:]
        elif '{pages}' in remaining:
            idx = remaining.index('{pages}')
            if idx > 0:
                parts.append(f"'{remaining[:idx]}'")
            parts.append('counter(pages)')
            remaining = remaining[idx + 7:]
        else:
            parts.append(f"'{remaining}'")
            remaining = ''
    
    return ' '.join(parts)


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
    page_settings: dict = None,
    style_settings: dict = None,
    force: bool = False,
    anchor_map: dict = None
) -> tuple[str, bool]:
    """
    Convert a markdown file to PDF with dynamic header and footer.
    
    Args:
        md_path: Path to markdown file
        pdf_path: Output PDF path (defaults to output directory with same structure)
        page_settings: Dictionary with header/footer configuration
            - header: Header text with placeholders
            - headerFallback: Fallback if title not found
            - footerLeft: Left footer with placeholders
            - footerCenter: Center footer with placeholders
            - footerRight: Right footer with placeholders
            - dateFormat: Date format string (default: %B %d, %Y)
            - bookTitle: Book title for {bookTitle} placeholder
        style_settings: Dictionary with styling configuration
            - pageSize, margins, fonts, colors, sizes, etc.
        force: Force reconversion even if cached
        anchor_map: Dictionary mapping filenames to anchor IDs for internal linking
        
    Returns:
        Tuple of (pdf_path, was_converted) - was_converted is False if cached
    """
    if pdf_path is None:
        pdf_path = get_output_pdf_path(md_path)
    
    # Check if conversion is needed (caching)
    if not is_conversion_needed(md_path, pdf_path, force):
        return pdf_path, False
    
    # Merge with defaults
    settings = {**DEFAULT_PAGE_SETTINGS, **(page_settings or {})}
    styles = style_settings or {}
    
    # Ensure output directory exists
    ensure_dir(os.path.dirname(pdf_path))
    
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Rewrite internal .md links to anchor links if anchor_map provided
    if anchor_map:
        md_content = rewrite_markdown_links(md_content, anchor_map)
    
    # Extract title from markdown
    title = extract_title_from_markdown(md_content)
    if not title:
        title = settings.get('headerFallback', 'Document')
    
    # Build context for placeholder replacement
    context = {
        'title': title,
        'filename': os.path.basename(md_path),
        'date': datetime.date.today().strftime(settings.get('dateFormat', '%B %d, %Y')),
        'bookTitle': settings.get('bookTitle', ''),
    }
    
    # Process placeholders for header and footers
    header_text = process_placeholder(settings.get('header', '{title}'), context)
    footer_left = process_placeholder(settings.get('footerLeft', ''), context)
    footer_center = process_placeholder(settings.get('footerCenter', ''), context)
    footer_right = process_placeholder(settings.get('footerRight', ''), context)
    
    # Build CSS content values (handles {page} and {pages} counters)
    header_css = build_css_content(header_text)
    footer_left_css = build_css_content(footer_left)
    footer_center_css = build_css_content(footer_center)
    footer_right_css = build_css_content(footer_right)
    
    html_content = markdown.markdown(
        md_content, 
        extensions=['extra', 'toc', 'tables']
    )
    
    # Inject document anchor for internal linking
    doc_anchor = filename_to_anchor(os.path.basename(md_path))
    html_content = inject_document_anchor(html_content, doc_anchor)
    
    # Get style values with defaults
    page_size = styles.get('pageSize', 'A4')
    margins = styles.get('margins', '1in 0.8in 1in 0.8in')
    font_family = styles.get('fontFamily', 'Helvetica Neue, Helvetica, Arial, sans-serif')
    mono_font = styles.get('monoFontFamily', 'SF Mono, Monaco, Menlo, Consolas, Liberation Mono, monospace')
    body_font_size = styles.get('bodyFontSize', '11pt')
    body_line_height = styles.get('bodyLineHeight', '1.6')
    body_color = styles.get('bodyColor', '#333333')
    heading_color = styles.get('headingColor', '#222222')
    h1_size = styles.get('h1FontSize', '18pt')
    h2_size = styles.get('h2FontSize', '16pt')
    h3_size = styles.get('h3FontSize', '14pt')
    h4_size = styles.get('h4FontSize', '12pt')
    code_font_size = styles.get('codeFontSize', '10pt')
    table_font_size = styles.get('tableFontSize', '10pt')
    code_bg = styles.get('codeBackground', '#f5f5f5')
    link_color = styles.get('linkColor', '#0066cc')
    header_font_size = styles.get('headerFontSize', '14px')
    footer_font_size = styles.get('footerFontSize', '10px')
    
    html_template = f'''
    <html>
    <head>
        <style>
            @page {{
                size: {page_size};
                margin: {margins};
                @top-center {{
                    content: {header_css};
                    font-size: {header_font_size};
                    font-weight: bold;
                    font-family: "{font_family}";
                }}
                @bottom-left {{
                    content: {footer_left_css};
                    font-size: {footer_font_size};
                    font-family: "{font_family}";
                }}
                @bottom-center {{
                    content: {footer_center_css};
                    font-size: {footer_font_size};
                    font-family: "{font_family}";
                }}
                @bottom-right {{
                    content: {footer_right_css};
                    font-size: {footer_font_size};
                    font-family: "{font_family}";
                }}
            }}
            
            /* Base font for all text */
            body {{
                font-family: "{font_family}";
                font-size: {body_font_size};
                line-height: {body_line_height};
                color: {body_color};
            }}
            
            /* Headings */
            h1, h2, h3, h4, h5, h6 {{
                font-family: "{font_family}";
                font-weight: 600;
                margin-top: 1.5em;
                margin-bottom: 0.5em;
                color: {heading_color};
            }}
            h1 {{ font-size: {h1_size}; }}
            h2 {{ font-size: {h2_size}; }}
            h3 {{ font-size: {h3_size}; }}
            h4 {{ font-size: {h4_size}; }}
            
            /* Paragraphs */
            p {{
                margin: 0.8em 0;
            }}
            
            /* Code - inline and blocks */
            code, pre, kbd, samp {{
                font-family: "{mono_font}";
                font-size: {code_font_size};
            }}
            
            code {{
                background-color: {code_bg};
                padding: 0.2em 0.4em;
                border-radius: 3px;
            }}
            
            pre {{
                background-color: {code_bg};
                padding: 1em;
                border-radius: 5px;
                line-height: 1.4;
                white-space: pre-wrap;
                word-wrap: break-word;
                overflow-wrap: break-word;
            }}
            
            pre code {{
                background-color: transparent;
                padding: 0;
            }}
            
            /* Tables */
            table {{
                font-family: "{font_family}";
                border-collapse: collapse;
                width: 100%;
                margin: 1em 0;
                font-size: {table_font_size};
            }}
            
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            
            th {{
                background-color: {code_bg};
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
                font-family: "{font_family}";
                font-style: italic;
                margin: 1em 0;
                padding: 0.5em 1em;
                border-left: 4px solid #ddd;
                color: #666;
            }}
            
            /* Links */
            a {{
                color: {link_color};
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
    verbose: bool = False,
    page_settings: dict = None,
    style_settings: dict = None,
    anchor_map: dict = None
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
        page_settings: Header/footer configuration for PDF conversion
        style_settings: Styling configuration for PDF conversion
        anchor_map: Dictionary mapping filenames to anchor IDs for internal linking
        
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
            pdf_path, was_converted = convert_markdown_to_pdf(
                file_path, pdf_path, page_settings=page_settings, 
                style_settings=style_settings, force=force,
                anchor_map=anchor_map
            )
            
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
    max_workers: int = 1,  # WeasyPrint is not thread-safe
    page_settings: dict = None,
    style_settings: dict = None,
    anchor_map: dict = None
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
        page_settings: Header/footer configuration for PDF conversion
        style_settings: Styling configuration for PDF conversion
        anchor_map: Dictionary mapping filenames to anchor IDs for internal linking
        
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
                md_file, root_dir, output_dir, force, False, page_settings, style_settings, anchor_map
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
