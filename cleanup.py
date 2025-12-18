"""
Cleanup module - manages the bookbuilder output directory.

Simplified cleanup: just delete the output folder which contains
both converted PDFs and the finished book.
"""

import os
import shutil


def cleanup_output(
    output_dir: str,
    dry_run: bool = True,
    verbose: bool = True
) -> bool:
    """
    Clean up the output directory containing converted PDFs and finished book.
    
    The output directory contains:
    - Converted PDFs (from MD files)
    - TOC PDF
    - Finished book PDF
    
    Args:
        output_dir: Output directory to clean (required)
        dry_run: If True, only show what would be deleted
        verbose: Print progress messages
        
    Returns:
        True if cleanup was successful
    """
    
    if not os.path.exists(output_dir):
        if verbose:
            print(f"Output directory does not exist: {output_dir}")
        return True
    
    # Count files in output directory
    file_count = 0
    total_size = 0
    for dirpath, _, filenames in os.walk(output_dir):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            file_count += 1
            total_size += os.path.getsize(file_path)
    
    size_mb = total_size / (1024 * 1024)
    
    if verbose:
        print(f"Output directory: {output_dir}")
        print(f"Files to delete: {file_count}")
        print(f"Total size: {size_mb:.2f} MB")
        print("=" * 60)
    
    if dry_run:
        if verbose:
            print(f"\n[DRY RUN] Would delete: {output_dir}")
            print(f"\nThis was a DRY RUN. No files were actually deleted.")
            print("Run with --confirm to actually delete.")
        return True
    
    try:
        shutil.rmtree(output_dir)
        if verbose:
            print(f"\n✓ Deleted output directory: {output_dir}")
            print(f"✓ Removed {file_count} files ({size_mb:.2f} MB)")
        return True
    except Exception as e:
        if verbose:
            print(f"\n✗ Failed to delete output directory: {e}")
        return False


