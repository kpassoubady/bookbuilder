"""
PDF combining and book building module with optimized workflow.

Features:
- Supports MD files, PDF files, and directories in order JSON
- Lazy conversion: only converts MD files that are needed
- Uses centralized output directory for converted PDFs
- Parallel conversion for speed
"""

import os
import gc
import json
import datetime
from PyPDF2 import PdfMerger, PdfReader
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor

from .utils import (
    get_gitignore_patterns,
    is_ignored,
    get_default_output_dir,
    ensure_dir,
    load_config,
    deep_merge,
    build_anchor_map
)
from .convert import (
    convert_file,
    convert_files_parallel,
    get_output_pdf_path
)
from .formats import (
    OutputFormat,
    build_book_epub,
    build_book_docx,
    build_book_html,
    get_format_extension
)


def safe_get_page_count(pdf_path: str) -> int:
    """
    Safely get page count from a PDF file.
    
    Returns 0 if the file cannot be read to allow skipping.
    Includes garbage collection to prevent macOS memory issues.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Number of pages, or 0 if error
    """
    try:
        reader = PdfReader(pdf_path)
        count = len(reader.pages)
        del reader
        gc.collect()
        return count
    except Exception as e:
        print(f"  Warning: Could not read PDF {os.path.basename(pdf_path)}: {e}")
        return 0


def resolve_file_path(file_ref: str, root_dir: str) -> str:
    """
    Resolve a file reference to an absolute path.
    
    Supports:
    - Absolute paths
    - Relative paths (from project root)
    - Paths with .md or .pdf extension
    - Paths without extension (tries .md then .pdf)
    
    Args:
        file_ref: File reference from order JSON
        root_dir: Project root directory
        
    Returns:
        Absolute path to the file
    """
    # If absolute path, return as-is
    if os.path.isabs(file_ref):
        return file_ref
    
    # Try as relative path from root
    abs_path = os.path.join(root_dir, file_ref)
    if os.path.exists(abs_path):
        return abs_path
    
    # If no extension, try .md then .pdf
    if not file_ref.endswith('.md') and not file_ref.endswith('.pdf'):
        md_path = os.path.join(root_dir, file_ref + '.md')
        if os.path.exists(md_path):
            return md_path
        pdf_path = os.path.join(root_dir, file_ref + '.pdf')
        if os.path.exists(pdf_path):
            return pdf_path
    
    return abs_path  # Return the path even if not found (will error later)


def find_files_in_directory(dir_path: str, root_dir: str) -> list[str]:
    """
    Find all MD and PDF files in a directory recursively.
    
    Args:
        dir_path: Directory to search
        root_dir: Project root for ignore patterns
        
    Returns:
        Sorted list of file paths (MD and PDF)
    """
    ignore_patterns = get_gitignore_patterns(root_dir)
    files = []
    
    if not os.path.isdir(dir_path):
        return files
    
    for dirpath, dirnames, filenames in os.walk(dir_path):
        # Filter ignored directories
        dirnames[:] = [d for d in dirnames if not is_ignored(
            os.path.relpath(os.path.join(dirpath, d), root_dir),
            ignore_patterns
        )]
        
        for filename in sorted(filenames):
            if filename.endswith('.md') or filename.endswith('.pdf'):
                rel_path = os.path.relpath(os.path.join(dirpath, filename), root_dir)
                if not is_ignored(rel_path, ignore_patterns):
                    files.append(os.path.join(dirpath, filename))
    
    return sorted(files)


def get_pdf_for_file(
    file_path: str,
    root_dir: str,
    output_dir: str,
    force: bool = False,
    verbose: bool = False
) -> tuple[str, bool, str]:
    """
    Get or create a PDF for a file (MD or PDF).
    
    Args:
        file_path: Path to source file
        root_dir: Project root directory
        output_dir: Output directory for converted PDFs
        force: Force reconversion
        verbose: Print progress
        
    Returns:
        Tuple of (pdf_path, was_converted, error_message)
    """
    if file_path.lower().endswith('.pdf'):
        # Already a PDF
        if os.path.exists(file_path):
            return file_path, False, None
        return None, False, f"PDF not found: {file_path}"
    
    if file_path.lower().endswith('.md'):
        # Convert MD to PDF
        return convert_file(file_path, root_dir, output_dir, force, verbose)
    
    return None, False, f"Unsupported file type: {file_path}"


def collect_files_for_chapter(
    chapter: dict,
    root_dir: str
) -> list[str]:
    """
    Collect all file paths for a chapter from the order JSON.
    
    Args:
        chapter: Chapter configuration from order JSON
        root_dir: Project root directory
        
    Returns:
        List of absolute file paths (MD or PDF)
    """
    files = []
    
    # Process individual files
    if 'files' in chapter:
        for file_ref in chapter['files']:
            file_path = resolve_file_path(file_ref, root_dir)
            files.append(file_path)
    
    # Process folders
    if 'folders' in chapter:
        for folder_ref in chapter['folders']:
            folder_path = resolve_file_path(folder_ref.rstrip('/'), root_dir)
            folder_files = find_files_in_directory(folder_path, root_dir)
            files.extend(folder_files)
    
    return files


def create_toc_page(
    chapter_info: list[dict], 
    book_title: str, 
    output_path: str,
    toc_settings: dict = None,
    page_settings: dict = None
) -> None:
    """
    Create a clickable Table of Contents page using ReportLab.
    
    Args:
        chapter_info: List of chapter information dictionaries
        book_title: Title for the TOC page
        output_path: Output PDF file path
        toc_settings: TOC styling configuration
        page_settings: Page header/footer configuration
    """
    # Default TOC settings
    toc = toc_settings or {}
    page = page_settings or {}
    
    title_font_size = toc.get('titleFontSize', 24)
    subtitle_font_size = toc.get('subtitleFontSize', 14)
    subtitle_text = toc.get('subtitleText', 'Table of Contents')
    entry_font_size = toc.get('entryFontSize', 11)
    footer_font_size = toc.get('footerFontSize', 9)
    line_color = toc.get('lineColor', '#0066CC')
    entry_color = toc.get('entryColor', '#0066CC')
    footer_color = toc.get('footerColor', '#666666')
    
    # Footer content from page settings
    footer_right = page.get('footerRight', 'Your Company')
    date_format = page.get('dateFormat', '%B %d, %Y')
    
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", title_font_size)
    c.drawCentredString(width / 2, height - 1.5 * inch, book_title)
    
    # Subtitle
    c.setFont("Helvetica", subtitle_font_size)
    c.drawCentredString(width / 2, height - 2 * inch, subtitle_text)
    
    # Draw a line
    c.setStrokeColor(HexColor(line_color))
    c.setLineWidth(2)
    c.line(1.5 * inch, height - 2.3 * inch, width - 1.5 * inch, height - 2.3 * inch)
    
    # TOC entries
    y_position = height - 3 * inch
    c.setFont("Helvetica", entry_font_size)
    
    for i, chapter in enumerate(chapter_info):
        section_name = chapter['section']
        page_num = chapter['page']
        
        c.setFillColor(HexColor(entry_color))
        c.drawString(1.5 * inch, y_position, section_name)
        c.setFillColor(HexColor("#000000"))
        c.drawRightString(width - 1.5 * inch, y_position, f"Page {page_num}")
        
        y_position -= 0.3 * inch
        
        if y_position < 1.5 * inch:
            c.showPage()
            y_position = height - 1.5 * inch
            c.setFont("Helvetica", entry_font_size)
    
    # Footer - match other pages: left=date, right=attribution
    c.setFont("Helvetica", footer_font_size)
    c.setFillColor(HexColor(footer_color))
    c.drawString(0.8 * inch, 0.5 * inch, datetime.date.today().strftime(date_format))
    c.drawRightString(width - 0.8 * inch, 0.5 * inch, footer_right)
    
    c.save()


def combine_pdfs_with_bookmarks(
    pdf_list: list[str], 
    chapter_info: list[dict], 
    output_pdf: str, 
    toc_pdf: str, 
    front_cover: str = None, 
    back_cover: str = None
) -> None:
    """
    Combine PDFs with bookmarks and clickable TOC.
    
    Args:
        pdf_list: List of PDF file paths to combine
        chapter_info: Chapter information for bookmarks
        output_pdf: Output file path
        toc_pdf: Path to TOC PDF
        front_cover: Path to front cover PDF (optional)
        back_cover: Path to back cover PDF (optional)
    """
    merger = PdfMerger()
    current_page = 0
    
    try:
        # Add front cover first
        if front_cover and os.path.isfile(front_cover):
            try:
                merger.append(front_cover)
                front_cover_pages = safe_get_page_count(front_cover)
                current_page += front_cover_pages
                print(f"Added front cover ({front_cover_pages} pages)")
            except Exception as e:
                print(f"  Warning: Could not add front cover: {e}")
        
        # Add TOC
        try:
            merger.append(toc_pdf)
            toc_pages = safe_get_page_count(toc_pdf)
            current_page += toc_pages
            print(f"Added TOC ({toc_pages} pages)")
        except Exception as e:
            print(f"  Warning: Could not add TOC: {e}")
        
        # Add all chapter PDFs with bookmarks
        pdf_index = 0
        
        for chapter in chapter_info:
            merger.add_outline_item(chapter['section'], current_page)
            
            for _ in range(chapter['files']):
                if pdf_index < len(pdf_list):
                    pdf = pdf_list[pdf_index]
                    try:
                        page_count = safe_get_page_count(pdf)
                        merger.append(pdf)
                        current_page += page_count
                    except Exception as e:
                        print(f"  Warning: Could not add {os.path.basename(pdf)}: {e}")
                    pdf_index += 1
            
            # Garbage collection after each chapter to prevent memory buildup
            gc.collect()
        
        # Add back cover last
        if back_cover and os.path.isfile(back_cover):
            try:
                merger.append(back_cover)
                back_cover_pages = safe_get_page_count(back_cover)
                print(f"Added back cover ({back_cover_pages} pages)")
            except Exception as e:
                print(f"  Warning: Could not add back cover: {e}")
        
        merger.write(output_pdf)
    finally:
        merger.close()
        gc.collect()


def build_book(
    order_json_path: str,
    output_filename: str = None,
    root_dir: str = None,
    output_dir: str = None,
    force: bool = False,
    verbose: bool = True,
    config_path: str = None,
    output_format: OutputFormat = None
) -> str:
    """
    Build a complete book from source files in the specified format.
    
    Supports MD files, PDF files, and directories in the order JSON.
    MD files are converted on-demand (lazy conversion) with caching.
    
    Args:
        order_json_path: Path to order JSON file (required)
        output_filename: Output filename for the book (optional, can be in JSON)
        root_dir: Project root directory (defaults to current directory)
        output_dir: Output directory for converted PDFs (defaults to <root>/bookbuilder-output)
        force: Force reconversion of all MD files
        verbose: Print progress messages
        config_path: Path to custom config file (optional)
        output_format: Output format (PDF, EPUB, DOCX, HTML). Defaults to PDF.
        
    Returns:
        Path to generated book file
    """
    # Default to PDF format
    if output_format is None:
        output_format = OutputFormat.PDF
    # Set defaults
    if root_dir is None:
        root_dir = os.getcwd()
    root_dir = os.path.abspath(root_dir)
    
    if output_dir is None:
        output_dir = get_default_output_dir(root_dir)
    output_dir = os.path.abspath(output_dir)
    
    # Resolve order JSON path
    if not os.path.isabs(order_json_path):
        if os.path.exists(order_json_path):
            order_json_path = os.path.abspath(order_json_path)
        else:
            order_json_path = os.path.join(root_dir, order_json_path)
    
    if verbose:
        print(f"Using order file: {order_json_path}")
        print(f"Output directory: {output_dir}")
    
    # Load configuration (default + user config if provided)
    config = load_config(config_path)
    defaults = config.get('defaults', {})
    
    # Load order JSON
    with open(order_json_path, 'r') as f:
        order_json = json.load(f)
    
    book_title = order_json.get('bookTitle', defaults.get('bookTitle', 'Untitled Book'))
    chapters = order_json.get('chapters', [])
    
    # Get page settings: merge config defaults with order JSON overrides
    page_settings = deep_merge(
        config.get('pageSettings', {}),
        order_json.get('pageSettings', {})
    )
    # Add bookTitle to page_settings so it can be used as a placeholder
    page_settings['bookTitle'] = book_title
    
    # Get style and TOC settings from config
    style_settings = config.get('styleSettings', {})
    toc_settings = config.get('tocSettings', {})
    # Get content processing settings: merge config defaults with order JSON overrides
    content_settings = deep_merge(
        config.get('contentProcessing', {}),
        order_json.get('contentProcessing', {})
    )
    
    # Get output filename from JSON if not provided via CLI
    if output_filename is None:
        output_filename = order_json.get('outputFilename', defaults.get('outputFilename', 'book.pdf'))
    
    # Adjust output filename extension based on format
    base_name = os.path.splitext(output_filename)[0]
    output_filename = base_name + get_format_extension(output_format)
    
    # Collect all files needed for the book
    if verbose:
        print(f"\nCollecting files for {len(chapters)} chapters...")
    
    # Process chapters and collect files
    chapter_data = []  # List of (section_name, file_list)
    front_cover_files = []
    back_cover_files = []
    all_files_to_convert = []  # MD files to convert
    
    for chapter in chapters:
        section_name = chapter.get('section', 'Untitled Section')
        files = collect_files_for_chapter(chapter, root_dir)
        
        if section_name == "Front Cover":
            front_cover_files = files
        elif section_name == "Back Cover":
            back_cover_files = files
        else:
            chapter_data.append((section_name, files))
        
        # Collect MD files for batch conversion
        for f in files:
            if f.lower().endswith('.md'):
                all_files_to_convert.append(f)
    
    if verbose:
        total_files = sum(len(files) for _, files in chapter_data)
        total_files += len(front_cover_files) + len(back_cover_files)
        md_count = len(all_files_to_convert)
        print(f"  Total files: {total_files}")
        print(f"  MD files to convert: {md_count}")
    
    # Build anchor map for internal linking across all book files
    all_book_files = []
    for _, files in chapter_data:
        all_book_files.extend(files)
    all_book_files.extend(front_cover_files)
    all_book_files.extend(back_cover_files)
    anchor_map = build_anchor_map(all_book_files, root_dir)
    
    if verbose:
        print(f"  Built anchor map with {len(anchor_map)} entries for internal linking")
    
    # Get author from order JSON or config
    author = order_json.get('author', defaults.get('author', None))
    
    # Get cover image path if specified
    cover_image = None
    if front_cover_files:
        for f in front_cover_files:
            # Look for image files for EPUB cover
            if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                if os.path.exists(f):
                    cover_image = f
                    break
    
    # Output file path
    ensure_dir(output_dir)
    output_file = os.path.join(output_dir, output_filename)
    
    # Handle non-PDF formats using Pandoc
    if output_format != OutputFormat.PDF:
        # Collect all MD files in order for Pandoc
        all_md_files = []
        for _, files in chapter_data:
            for f in files:
                if f.lower().endswith('.md') and os.path.exists(f):
                    all_md_files.append(f)
        
        if not all_md_files:
            raise ValueError("No markdown files found to convert")
        
        if verbose:
            print(f"\nBuilding {output_format.value.upper()} with Pandoc...")
            print(f"  Source files: {len(all_md_files)}")
        
        # Build based on format
        if output_format == OutputFormat.EPUB:
            result_path, success, error = build_book_epub(
                all_md_files,
                output_file,
                title=book_title,
                author=author,
                cover_image=cover_image,
                toc=True,
                verbose=verbose
            )
        elif output_format == OutputFormat.DOCX:
            result_path, success, error = build_book_docx(
                all_md_files,
                output_file,
                title=book_title,
                author=author,
                toc=True,
                verbose=verbose,
                content_settings=content_settings
            )
        elif output_format == OutputFormat.HTML:
            result_path, success, error = build_book_html(
                all_md_files,
                output_file,
                title=book_title,
                toc=True,
                verbose=verbose
            )
        else:
            raise ValueError(f"Unsupported format: {output_format}")
        
        if not success:
            raise RuntimeError(f"Failed to build {output_format.value}: {error}")
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"✓ Book created: {output_file}")
            print(f"✓ Format: {output_format.value.upper()}")
            print(f"✓ Total source files: {len(all_md_files)}")
            print(f"{'='*60}")
        
        return output_file
    
    # PDF format: use existing WeasyPrint + PyPDF2 workflow
    # Convert all MD files in parallel (lazy - only if needed)
    if all_files_to_convert:
        if verbose:
            print(f"\nConverting MD files (parallel, with caching)...")
        
        pdf_paths, converted_count, failed_count = convert_files_parallel(
            all_files_to_convert,
            root_dir,
            output_dir,
            force,
            verbose,
            page_settings=page_settings,
            style_settings=style_settings,
            anchor_map=anchor_map,
            content_settings=content_settings
        )
        
        if verbose:
            cached_count = len(pdf_paths) - converted_count
            print(f"  Converted: {converted_count}, Cached: {cached_count}, Failed: {failed_count}")
    
    # Build ordered PDF list with chapter info
    if verbose:
        print(f"\nBuilding book structure...")
    
    ordered_pdfs = []
    chapter_info = []
    front_cover = None
    back_cover = None
    
    # Process front cover
    for f in front_cover_files:
        pdf_path, _, _ = get_pdf_for_file(f, root_dir, output_dir, force, False)
        if pdf_path and os.path.exists(pdf_path):
            front_cover = pdf_path
            if verbose:
                print(f"  Front cover: {os.path.basename(pdf_path)}")
            break
    
    # Process chapters
    for section_name, files in chapter_data:
        page_start = sum(safe_get_page_count(pdf) for pdf in ordered_pdfs)
        chapter_pdfs = []
        
        for f in files:
            pdf_path, _, error = get_pdf_for_file(f, root_dir, output_dir, force, False)
            if pdf_path and os.path.exists(pdf_path):
                chapter_pdfs.append(pdf_path)
            elif verbose and error:
                print(f"  Warning: {error}")
        
        if chapter_pdfs:
            ordered_pdfs.extend(chapter_pdfs)
            chapter_info.append({
                'section': section_name,
                'page': page_start + 1,
                'files': len(chapter_pdfs)
            })
    
    # Process back cover
    for f in back_cover_files:
        pdf_path, _, _ = get_pdf_for_file(f, root_dir, output_dir, force, False)
        if pdf_path and os.path.exists(pdf_path):
            back_cover = pdf_path
            if verbose:
                print(f"  Back cover: {os.path.basename(pdf_path)}")
            break
    
    # Adjust page numbers for front cover and TOC
    front_cover_pages = safe_get_page_count(front_cover) if front_cover else 0
    toc_pages = 1
    offset = front_cover_pages + toc_pages
    
    for chapter in chapter_info:
        chapter['page'] += offset
    
    # Create TOC page
    toc_filename = defaults.get('tocFilename', '_toc.pdf')
    toc_pdf = os.path.join(output_dir, toc_filename)
    create_toc_page(chapter_info, book_title, toc_pdf, toc_settings, page_settings)
    
    if verbose:
        print(f"\nCreated TOC page")
    
    if verbose:
        print(f"\nCombining {len(ordered_pdfs)} PDFs...")
    
    combine_pdfs_with_bookmarks(
        ordered_pdfs, chapter_info, output_file, toc_pdf, front_cover, back_cover
    )
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"✓ Book created: {output_file}")
        print(f"✓ Front cover: {'Included' if front_cover else 'Not found'}")
        print(f"✓ Back cover: {'Included' if back_cover else 'Not found'}")
        print(f"✓ Total chapters: {len(chapter_info)}")
        print(f"✓ Total content PDFs: {len(ordered_pdfs)}")
        print(f"{'='*60}")
    
    return output_file
