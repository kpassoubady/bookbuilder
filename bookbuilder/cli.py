"""
Command-line interface for the bookbuilder package.

BookBuilder - A standalone tool for building PDF books from markdown files.

Usage:
    bookbuilder build --root /path/to/project --order /path/to/order.json
    bookbuilder cleanup --output-dir /path/to/output
"""

import argparse
import sys
import os

from . import __version__
from .combine import build_book
from .cleanup import cleanup_output
from .utils import get_default_output_dir
from .formats import OutputFormat, check_pandoc_installed, get_supported_formats


def resolve_paths(args):
    """Resolve and validate paths from arguments.
    
    Returns:
        Tuple of (root_dir, order_path, output_dir, output_filename)
    """
    # Root directory (required or current directory)
    root_dir = os.path.abspath(args.root) if args.root else os.getcwd()
    
    if not os.path.isdir(root_dir):
        print(f"Error: Root directory does not exist: {root_dir}")
        sys.exit(1)
    
    # Order file path (required)
    order_path = args.order
    if not os.path.isabs(order_path):
        # Try relative to current directory first, then root
        if os.path.exists(order_path):
            order_path = os.path.abspath(order_path)
        else:
            order_path = os.path.join(root_dir, order_path)
    
    if not os.path.isfile(order_path):
        print(f"Error: Order file does not exist: {order_path}")
        sys.exit(1)
    
    # Output directory
    if hasattr(args, 'output_dir') and args.output_dir:
        output_dir = os.path.abspath(args.output_dir)
    else:
        output_dir = get_default_output_dir(root_dir)
    
    # Output filename (optional, can be in JSON)
    output_filename = args.output if hasattr(args, 'output') and args.output else None
    
    return root_dir, order_path, output_dir, output_filename


def cmd_cleanup(args):
    """Handle the 'cleanup' subcommand - deletes output directory."""
    print("=" * 60)
    print("Cleaning Up Generated Files")
    print("=" * 60)
    
    # Determine output directory
    if args.output_dir:
        output_dir = os.path.abspath(args.output_dir)
    elif args.root:
        output_dir = get_default_output_dir(os.path.abspath(args.root))
    else:
        output_dir = get_default_output_dir(os.getcwd())
    
    success = cleanup_output(
        output_dir=output_dir,
        dry_run=not args.confirm,
        verbose=not args.quiet
    )
    
    return 0 if success else 1


def cmd_build(args):
    """
    Handle the 'build' subcommand - build a book in the specified format.
    
    The workflow:
    1. Read order JSON
    2. Convert only needed MD files (lazy, cached)
    3. Create TOC (for PDF)
    4. Combine into final book
    5. Optionally cleanup output directory
    """
    # Get output format
    output_format = OutputFormat.from_string(args.format) if hasattr(args, 'format') and args.format else OutputFormat.PDF
    
    # Check Pandoc for non-PDF formats
    if output_format != OutputFormat.PDF and not check_pandoc_installed():
        print("Error: Pandoc is required for non-PDF formats.")
        print("Install with: brew install pandoc")
        return 1
    
    print("=" * 60)
    print(f"BookBuilder - Building Book ({output_format.value.upper()})")
    print("=" * 60)
    
    root_dir, order_path, output_dir, output_filename = resolve_paths(args)
    
    # Resolve config path if provided
    config_path = None
    if hasattr(args, 'config') and args.config:
        config_path = args.config
        if not os.path.isabs(config_path):
            if os.path.exists(config_path):
                config_path = os.path.abspath(config_path)
            else:
                config_path = os.path.join(root_dir, config_path)
    
    # Resolve temp directory for intermediate files
    temp_dir = None
    if hasattr(args, 'temp') and args.temp:
        temp_dir = os.path.abspath(args.temp)
    
    if not args.quiet:
        print(f"Root directory: {root_dir}")
        print(f"Order file: {order_path}")
        print(f"Output directory: {output_dir}")
        if temp_dir:
            print(f"Temp directory: {temp_dir}")
        print(f"Output format: {output_format.value.upper()}")
        if config_path:
            print(f"Config file: {config_path}")
        print("=" * 60)
    
    output_file = build_book(
        order_json_path=order_path,
        output_filename=output_filename,
        root_dir=root_dir,
        output_dir=output_dir,
        temp_dir=temp_dir,
        force=args.force if hasattr(args, 'force') else False,
        verbose=not args.quiet,
        config_path=config_path,
        output_format=output_format
    )
    
    # Cleanup output directory if requested
    if args.cleanup:
        if not args.quiet:
            print()
            print("=" * 60)
            print("Cleaning Up Output Directory")
            print("=" * 60)
        
        cleanup_output(output_dir=output_dir, dry_run=False, verbose=not args.quiet)
    
    if not args.quiet:
        print()
        print("=" * 60)
        print("✓ Build Complete!")
        print(f"✓ Output: {output_file}")
        cache_dir = temp_dir if temp_dir else output_dir
        if os.path.exists(cache_dir) and not args.cleanup:
            print(f"✓ Intermediate files cached in: {cache_dir}")
            print("  (Use --cleanup to delete after build)")
        print("=" * 60)
    
    return 0


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog='bookbuilder',
        description='BookBuilder - Build books from markdown files (PDF, EPUB, DOCX, HTML).',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build a book from an order JSON file
  bookbuilder build --order ./book-order.json
  
  # Build with explicit root directory
  bookbuilder build --root /path/to/project --order book-order.json
  
  # Build with custom output directory
  bookbuilder build --order ./order.json --output-dir ./my-output
  
  # Build and cleanup temp files after
  bookbuilder build --order ./order.json --cleanup
  
  # Force reconversion of all MD files
  bookbuilder build --order ./order.json --force
  
  # Build with custom config file
  bookbuilder build --order ./order.json --config ./my-config.json
  
  # Build EPUB for Kindle (Amazon KDP)
  bookbuilder build --order ./order.json --format epub
  
  # Build DOCX for Word
  bookbuilder build --order ./order.json --format docx
  
  # Build standalone HTML
  bookbuilder build --order ./order.json --format html
  
  # Cleanup output directory (dry run)
  bookbuilder cleanup --root /path/to/project
  
  # Cleanup output directory (actually delete)
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
    )
    
    parser.add_argument(
        '--version', '-V',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    
    # Create subparsers
    subparsers = parser.add_subparsers(
        title='commands',
        description='Available commands',
        dest='command'
    )
    
    # Common arguments
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument(
        '--root', '-r',
        type=str,
        default=None,
        help='Root directory containing source files (defaults to current directory)'
    )
    common_parser.add_argument(
        '--output-dir', '-d',
        type=str,
        default=None,
        help='Output directory for converted PDFs (defaults to <root>/bookbuilder-output)'
    )
    common_parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress output messages'
    )
    
    # Build command
    build_parser = subparsers.add_parser(
        'build',
        parents=[common_parser],
        help='Build a book from an order JSON file (supports PDF, EPUB, DOCX, HTML)',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    build_parser.add_argument(
        '--order', '-o',
        type=str,
        required=True,
        help='Path to order JSON file (required)'
    )
    build_parser.add_argument(
        '--output', '-O',
        type=str,
        help='Custom output filename for the generated book (overrides JSON)'
    )
    build_parser.add_argument(
        '--format', '-F',
        type=str,
        choices=['pdf', 'epub', 'docx', 'html'],
        default='pdf',
        help='Output format: pdf (default), epub (Kindle), docx (Word), html'
    )
    build_parser.add_argument(
        '--cleanup', '-c',
        action='store_true',
        help='Delete output directory after building'
    )
    build_parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Force reconversion of all MD files (ignore cache)'
    )
    build_parser.add_argument(
        '--config', '-C',
        type=str,
        help='Path to custom config file (overrides defaults)'
    )
    build_parser.add_argument(
        '--temp', '-t',
        type=str,
        default=None,
        help='Directory for intermediate files (converted PDFs). If not specified, uses --output-dir'
    )
    build_parser.set_defaults(func=cmd_build)
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser(
        'cleanup',
        parents=[common_parser],
        help='Delete output directory (converted PDFs and temp files)'
    )
    cleanup_parser.add_argument(
        '--confirm',
        action='store_true',
        help='Actually delete (without this, only shows what would be deleted)'
    )
    cleanup_parser.set_defaults(func=cmd_cleanup)
    
    # Parse arguments
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
