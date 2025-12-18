# Contributing to bookbuilder

Thank you for your interest in contributing to bookbuilder! This document provides guidelines and instructions for contributing.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

### Prerequisites

- Python 3.8 or higher
- mdpdf (for Markdown to PDF conversion)
- PyPDF2 (for PDF manipulation)

### Running Locally

```bash
# Run from the project directory
python -m bookbuilder build --order examples/shortBookOrderPdfs.json

# Or install in development mode
pip install -e .
bookbuilder build --order examples/shortBookOrderPdfs.json
```

## How to Contribute

### Reporting Bugs

- Check existing issues to avoid duplicates
- Use the bug report template
- Include steps to reproduce, expected behavior, and actual behavior
- Include your environment details (Python version, OS, etc.)

### Suggesting Features

- Check existing issues and discussions first
- Use the feature request template
- Explain the use case and why it would benefit others

### Submitting Changes

1. Make your changes in a feature branch
2. Write clear, concise commit messages
3. Add tests for new functionality
4. Ensure all tests pass
5. Update documentation as needed
6. Submit a pull request

## Code Style

- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and small

## Pull Request Process

1. Update the README.md if needed
2. Update the CHANGELOG.md with your changes
3. Ensure your PR description clearly describes the problem and solution
4. Link any related issues
5. Request review from maintainers

## Questions?

Feel free to open an issue for any questions about contributing.

Thank you for contributing!
