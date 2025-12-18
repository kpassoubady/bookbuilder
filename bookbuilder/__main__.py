"""
Entry point for running the package as a module.

Usage:
    python -m bookbuilder build --short --cleanup
    python -m bookbuilder convert
    python -m bookbuilder combine --short
    python -m bookbuilder cleanup --confirm
"""

from .cli import main

if __name__ == '__main__':
    main()
