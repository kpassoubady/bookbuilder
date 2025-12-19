"""
Unit tests for bookbuilder.cleanup module.

Tests cover:
- Dry run behavior
- Actual cleanup/deletion
- Error handling
- Edge cases
"""

import os
import pytest

from bookbuilder.cleanup import cleanup_output


class TestCleanupOutput:
    """Tests for cleanup_output function."""
    
    def test_dry_run_does_not_delete(self, temp_dir):
        """Dry run mode should not delete any files."""
        # Create files in output directory
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir)
        test_file = os.path.join(output_dir, "test.pdf")
        with open(test_file, 'w') as f:
            f.write("PDF content")
        
        result = cleanup_output(output_dir, dry_run=True, verbose=False)
        
        assert result is True
        assert os.path.exists(output_dir)
        assert os.path.exists(test_file)
    
    def test_actual_delete(self, temp_dir):
        """Confirm mode should actually delete files."""
        # Create files in output directory
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir)
        test_file = os.path.join(output_dir, "test.pdf")
        with open(test_file, 'w') as f:
            f.write("PDF content")
        
        result = cleanup_output(output_dir, dry_run=False, verbose=False)
        
        assert result is True
        assert not os.path.exists(output_dir)
    
    def test_nonexistent_directory(self, temp_dir):
        """Nonexistent directory should return True (nothing to delete)."""
        output_dir = os.path.join(temp_dir, "nonexistent")
        
        result = cleanup_output(output_dir, dry_run=False, verbose=False)
        
        assert result is True
    
    def test_nested_directory_cleanup(self, temp_dir):
        """Cleanup should remove nested directory structure."""
        output_dir = os.path.join(temp_dir, "output")
        nested_dir = os.path.join(output_dir, "chapter1", "section1")
        os.makedirs(nested_dir)
        
        # Create files at different levels
        with open(os.path.join(output_dir, "root.pdf"), 'w') as f:
            f.write("Root PDF")
        with open(os.path.join(nested_dir, "nested.pdf"), 'w') as f:
            f.write("Nested PDF")
        
        result = cleanup_output(output_dir, dry_run=False, verbose=False)
        
        assert result is True
        assert not os.path.exists(output_dir)
    
    def test_returns_true_on_success(self, temp_dir):
        """Should return True when cleanup succeeds."""
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir)
        
        result = cleanup_output(output_dir, dry_run=False, verbose=False)
        
        assert result is True
    
    def test_verbose_output(self, temp_dir, capsys):
        """Verbose mode should print progress messages."""
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir)
        with open(os.path.join(output_dir, "file.pdf"), 'w') as f:
            f.write("content")
        
        cleanup_output(output_dir, dry_run=True, verbose=True)
        
        captured = capsys.readouterr()
        assert "Output directory:" in captured.out
        assert "Files to delete:" in captured.out
    
    def test_dry_run_message(self, temp_dir, capsys):
        """Dry run should indicate it was a dry run."""
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir)
        with open(os.path.join(output_dir, "file.pdf"), 'w') as f:
            f.write("content")
        
        cleanup_output(output_dir, dry_run=True, verbose=True)
        
        captured = capsys.readouterr()
        assert "DRY RUN" in captured.out


class TestCleanupEdgeCases:
    """Edge case tests for cleanup functionality."""
    
    def test_empty_directory(self, temp_dir):
        """Empty directory should be cleaned up successfully."""
        output_dir = os.path.join(temp_dir, "empty_output")
        os.makedirs(output_dir)
        
        result = cleanup_output(output_dir, dry_run=False, verbose=False)
        
        assert result is True
        assert not os.path.exists(output_dir)
    
    def test_directory_with_hidden_files(self, temp_dir):
        """Should handle hidden files (dotfiles)."""
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir)
        
        # Create hidden file
        with open(os.path.join(output_dir, ".hidden"), 'w') as f:
            f.write("hidden content")
        
        result = cleanup_output(output_dir, dry_run=False, verbose=False)
        
        assert result is True
        assert not os.path.exists(output_dir)
    
    def test_counts_files_correctly(self, temp_dir, capsys):
        """Should correctly count files for reporting."""
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir)
        
        # Create exactly 3 files
        for i in range(3):
            with open(os.path.join(output_dir, f"file{i}.pdf"), 'w') as f:
                f.write("content")
        
        cleanup_output(output_dir, dry_run=True, verbose=True)
        
        captured = capsys.readouterr()
        assert "Files to delete: 3" in captured.out
