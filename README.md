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
  "pageSettings": {
    "header": "{title}",
    "headerFallback": "{bookTitle}",
    "footerLeft": "{date}",
    "footerCenter": "Page {page} of {pages}",
    "footerRight": "Kangs | Kavin School",
    "dateFormat": "%B %d, %Y"
  },
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

### Page Settings

Configure dynamic headers and footers using the `pageSettings` object:

| Setting | Description | Default |
|---------|-------------|---------|
| `header` | Page header text with placeholders | `{title}` |
| `headerFallback` | Fallback if title not found | `Document` |
| `footerLeft` | Left footer text | `{date}` |
| `footerCenter` | Center footer text | `Page {page} of {pages}` |
| `footerRight` | Right footer text | `Kangs \| Kavin School` |
| `dateFormat` | Python strftime format | `%B %d, %Y` |

**Supported Placeholders:**

| Placeholder | Description |
|-------------|-------------|
| `{title}` | First H1 heading from the markdown file |
| `{filename}` | Name of the source file |
| `{date}` | Current date (formatted per `dateFormat`) |
| `{page}` | Current page number |
| `{pages}` | Total page count |
| `{bookTitle}` | Book title from JSON |

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
| `--config`, `-C`     | Path to custom config file (overrides defaults)                               |
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

## Configuration

BookBuilder uses a layered configuration system:

1. **Built-in defaults** - Bundled with the package
2. **Custom config file** - Specified via `--config` CLI option
3. **Order JSON overrides** - `pageSettings` in your order JSON

Later layers override earlier ones, allowing you to set organization-wide defaults in a config file while still customizing per-book settings in the order JSON.

### Using a Custom Config File

```bash
# Build with custom config
bookbuilder build --order ./order.json --config ./my-config.json
```

### Config File Structure

Create a `bookbuilder-config.json` file (see `examples/bookbuilder-config.json`):

```json
{
  "pageSettings": {
    "header": "{title}",
    "headerFallback": "{bookTitle}",
    "footerLeft": "{date}",
    "footerCenter": "Page {page} of {pages}",
    "footerRight": "Your Company",
    "dateFormat": "%B %d, %Y"
  },
  "styleSettings": {
    "pageSize": "A4",
    "margins": "1in 0.8in 1in 0.8in",
    "fontFamily": "Helvetica Neue, Helvetica, Arial, sans-serif",
    "monoFontFamily": "SF Mono, Monaco, Menlo, Consolas, Liberation Mono, monospace",
    "bodyFontSize": "11pt",
    "bodyLineHeight": "1.6",
    "bodyColor": "#333333",
    "headingColor": "#222222",
    "h1FontSize": "18pt",
    "h2FontSize": "16pt",
    "h3FontSize": "14pt",
    "h4FontSize": "12pt",
    "codeFontSize": "10pt",
    "tableFontSize": "10pt",
    "codeBackground": "#f5f5f5",
    "linkColor": "#0066cc"
  },
  "tocSettings": {
    "titleFontSize": 24,
    "subtitleFontSize": 14,
    "subtitleText": "Table of Contents",
    "entryFontSize": 11,
    "lineColor": "#0066CC",
    "entryColor": "#0066CC"
  },
  "defaults": {
    "bookTitle": "Untitled Book",
    "outputFilename": "book.pdf"
  }
}
```

### Configuration Sections

| Section | Description |
|---------|-------------|
| `pageSettings` | Header/footer text and placeholders |
| `styleSettings` | PDF styling (fonts, colors, sizes, margins) |
| `tocSettings` | Table of Contents styling |
| `defaults` | Default book title and output filename |

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
    verbose=True,
    config_path="./my-config.json"  # Optional custom config
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
│   ├── utils.py           # Shared utility functions
│   └── default-config.json # Built-in default configuration
├── examples/              # Example order and config files
│   ├── fullBookOrderPdfs.json
│   ├── shortBookOrderPdfs.json
│   └── bookbuilder-config.json  # Example config file
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
