# BookBuilder

A standalone tool for building PDF books from markdown files.

## Features

- **Convert**: Transform markdown files to PDF with customizable headers/footers
- **Combine**: Merge PDFs into a single book with Table of Contents and bookmarks
- **Caching**: Skip conversion of unchanged files (timestamp-based)
- **Flexible**: Works with any project structure

## Installation

### From PyPI (when published)

```bash
pip install bookbuilder
```

### From Git

```bash
pip install git+https://github.com/kpassoubady/bookbuilder.git
```

### From Source

```bash
cd bookbuilder
pip install -e .
```

### Dependencies

```bash
pip install markdown weasyprint PyPDF2 reportlab
```

## Quick Start

```bash
# Build a book with root directory, output directory, and order file
bookbuilder build \
  --root /Users/kangs/github/copilot-United \
  --output-dir /Users/kangs/finished-books \
  --order /Users/kangs/github/bookbuilder/examples/shortBookOrderPdfs.json

# Build from current directory with order file
bookbuilder build --order ./book-order.json

# Build with custom output filename
bookbuilder build --root ./my-project --order ./order.json --output MyBook.pdf

# Force reconvert all files (ignore cache)
bookbuilder build --order ./order.json --force

# Cleanup output directory (dry run - shows what would be deleted)
bookbuilder cleanup --output-dir ./bookbuilder-output

# Cleanup output directory (actually delete)
bookbuilder cleanup --output-dir ./bookbuilder-output --confirm
```

## Order JSON Format

Create a JSON file that defines your book structure:

```json
{
  "bookTitle": "My Book Title",
  "outputFilename": "my-book.pdf",
  "chapters": [
    {
      "section": "Front Cover",
      "files": ["docs/FrontCoverPage.pdf"]
    },
    {
      "section": "Introduction",
      "files": [
        "intro.md",
        "getting-started.md"
      ]
    },
    {
      "section": "Chapter 1",
      "files": [
        "chapter1/overview.md",
        "chapter1/details.md"
      ]
    },
    {
      "section": "Back Cover",
      "files": ["docs/BackCoverPage.pdf"]
    }
  ]
}
```

### File References

Order files support:
- **`.md` files**: Automatically converted to PDF
- **`.pdf` files**: Used directly
- **Relative paths**: Resolved from project root

## Command Reference

### Build Command

```bash
bookbuilder build --order <path> [options]
```

| Option               | Description                                                                   |
|----------------------|-------------------------------------------------------------------------------|
| `--order`, `-o`      | Path to order JSON file (required)                                            |
| `--root`, `-r`       | Root directory containing source files (defaults to current directory)        |
| `--output-dir`, `-d` | Output directory for converted PDFs (defaults to `<root>/bookbuilder-output`) |
| `--output`, `-O`     | Custom output filename (overrides JSON `outputFilename`)                      |
| `--cleanup`, `-c`    | Delete output directory after building                                        |
| `--force`, `-f`      | Force reconversion of all MD files (ignore cache)                             |
| `--quiet`, `-q`      | Suppress output messages                                                      |

### Cleanup Command

```bash
bookbuilder cleanup [options]
```

| Option               | Description                                                      |
|----------------------|------------------------------------------------------------------|
| `--output-dir`, `-d` | Output directory to clean                                        |
| `--root`, `-r`       | Root directory (used to derive default output-dir)               |
| `--confirm`          | Actually delete (without this, only shows what would be deleted) |
| `--quiet`, `-q`      | Suppress output messages                                         |

## Output Structure

```
project/
├── bookbuilder-output/           # Default output directory
│   ├── intro.pdf                 # Converted from intro.md
│   ├── chapter1/
│   │   ├── overview.pdf
│   │   └── details.pdf
│   ├── toc.pdf                   # Generated TOC
│   └── my-book.pdf               # Final combined book
├── intro.md                      # Source files (unchanged)
├── chapter1/
│   ├── overview.md
│   └── details.md
└── book-order.json               # Order file
```

## API Usage

```python
from bookbuilder import build_book, cleanup_output

# Build a book
output_pdf = build_book(
    order_json_path="./book-order.json",
    root_dir="/path/to/project",
    output_dir="/path/to/output",
    output_filename="MyBook.pdf",
    force=False,
    verbose=True
)

# Cleanup
cleanup_output(
    output_dir="/path/to/output",
    dry_run=False,
    verbose=True
)
```

## Package Structure

```
bookbuilder/               # Repository root
├── bookbuilder/           # Python package
│   ├── __init__.py        # Package exports
│   ├── __main__.py        # Entry point for python -m
│   ├── cli.py             # Command-line interface
│   ├── convert.py         # Markdown to PDF conversion
│   ├── combine.py         # PDF combining and book building
│   ├── cleanup.py         # PDF cleanup/deletion
│   └── utils.py           # Shared utility functions
├── examples/              # Example order files
│   ├── fullBookOrderPdfs.json
│   └── shortBookOrderPdfs.json
├── pyproject.toml         # Package configuration
├── requirements.txt       # Dependencies
├── README.md              # This file
├── LICENSE.md             # MIT License
├── CHANGELOG.md           # Version history
├── CONTRIBUTING.md        # Contribution guidelines
├── CODE_OF_CONDUCT.md     # Community guidelines
├── SECURITY.md            # Security policy
├── .gitignore             # Git ignore rules
└── .github/               # GitHub templates
    ├── PULL_REQUEST_TEMPLATE.md
    └── ISSUE_TEMPLATE/
        ├── bug_report.md
        └── feature_request.md
```

## License

MIT License - Kangeyan Passoubady
