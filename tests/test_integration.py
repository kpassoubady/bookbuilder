"""
Integration tests for bookbuilder.

Tests cover end-to-end workflows:
- Full book building process
- Configuration loading and application
- CLI argument handling
"""

import os
import json
import subprocess
import pytest

from bookbuilder import build_book
from bookbuilder.utils import load_config, deep_merge


class TestConfigurationIntegration:
    """Integration tests for configuration system."""
    
    def test_default_config_loads(self):
        """Default configuration loads without errors."""
        config = load_config()
        
        assert config is not None
        assert "pageSettings" in config
        assert "styleSettings" in config
        assert "tocSettings" in config
        assert "defaults" in config
    
    def test_user_config_overrides_defaults(self, temp_dir):
        """User config properly overrides default values."""
        # Create user config with overrides
        user_config = {
            "pageSettings": {
                "footerRight": "Custom Footer"
            },
            "styleSettings": {
                "bodyFontSize": "14pt"
            }
        }
        config_path = os.path.join(temp_dir, "user-config.json")
        with open(config_path, 'w') as f:
            json.dump(user_config, f)
        
        config = load_config(config_path)
        
        # Override applied
        assert config["pageSettings"]["footerRight"] == "Custom Footer"
        assert config["styleSettings"]["bodyFontSize"] == "14pt"
        
        # Defaults preserved
        assert "header" in config["pageSettings"]
        assert "pageSize" in config["styleSettings"]
    
    def test_order_json_overrides_config(self, sample_config):
        """Order JSON pageSettings override config values."""
        order_settings = {
            "footerRight": "Order JSON Override"
        }
        
        merged = deep_merge(sample_config["pageSettings"], order_settings)
        
        assert merged["footerRight"] == "Order JSON Override"
        # Other settings preserved
        assert merged["header"] == "{title}"


class TestDeepMergeIntegration:
    """Integration tests for deep merge functionality."""
    
    def test_three_level_merge(self):
        """Test merging at three levels: defaults -> config -> order."""
        defaults = {
            "pageSettings": {
                "header": "Default Header",
                "footer": "Default Footer"
            }
        }
        
        user_config = {
            "pageSettings": {
                "footer": "User Footer"
            }
        }
        
        order_override = {
            "pageSettings": {
                "header": "Order Header"
            }
        }
        
        # First merge: defaults + user config
        merged1 = deep_merge(defaults, user_config)
        # Second merge: result + order override
        final = deep_merge(merged1, order_override)
        
        assert final["pageSettings"]["header"] == "Order Header"
        assert final["pageSettings"]["footer"] == "User Footer"


class TestProjectStructure:
    """Tests for project structure handling."""
    
    def test_package_exports(self):
        """All expected functions are exported from package."""
        import bookbuilder
        
        # Convert module exports
        assert hasattr(bookbuilder, 'convert_markdown_to_pdf')
        assert hasattr(bookbuilder, 'find_markdown_files')
        assert hasattr(bookbuilder, 'convert_file')
        
        # Combine module exports
        assert hasattr(bookbuilder, 'build_book')
        assert hasattr(bookbuilder, 'create_toc_page')
        
        # Cleanup module exports
        assert hasattr(bookbuilder, 'cleanup_output')
        
        # Utils module exports
        assert hasattr(bookbuilder, 'get_gitignore_patterns')
        assert hasattr(bookbuilder, 'ensure_dir')
    
    def test_version_defined(self):
        """Package version is defined."""
        import bookbuilder
        
        assert hasattr(bookbuilder, '__version__')
        assert isinstance(bookbuilder.__version__, str)
        assert len(bookbuilder.__version__) > 0


class TestCLIIntegration:
    """Integration tests for CLI commands."""
    
    def test_cli_help(self):
        """CLI help command works."""
        result = subprocess.run(
            ["python", "-m", "bookbuilder", "--help"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "bookbuilder" in result.stdout.lower() or "usage" in result.stdout.lower()
    
    def test_build_help(self):
        """Build subcommand help works."""
        result = subprocess.run(
            ["python", "-m", "bookbuilder", "build", "--help"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "--order" in result.stdout
        assert "--config" in result.stdout
    
    def test_cleanup_help(self):
        """Cleanup subcommand help works."""
        result = subprocess.run(
            ["python", "-m", "bookbuilder", "cleanup", "--help"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "--confirm" in result.stdout


class TestErrorHandling:
    """Tests for error handling scenarios."""
    
    def test_invalid_json_config(self, temp_dir):
        """Invalid JSON config should raise appropriate error."""
        invalid_config = os.path.join(temp_dir, "invalid.json")
        with open(invalid_config, 'w') as f:
            f.write("{ invalid json }")
        
        with pytest.raises(json.JSONDecodeError):
            load_config(invalid_config)
    
    def test_missing_order_file(self, temp_dir):
        """Missing order file should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            build_book(
                order_json_path=os.path.join(temp_dir, "nonexistent.json"),
                root_dir=temp_dir,
                verbose=False
            )


class TestPathHandling:
    """Tests for path resolution and handling."""
    
    def test_absolute_path_handling(self, temp_dir):
        """Absolute paths should be handled correctly."""
        abs_path = os.path.abspath(temp_dir)
        
        from bookbuilder.utils import get_default_output_dir
        output_dir = get_default_output_dir(abs_path)
        
        assert os.path.isabs(output_dir)
        assert abs_path in output_dir
    
    def test_relative_path_handling(self, temp_dir, monkeypatch):
        """Relative paths should be resolved correctly."""
        monkeypatch.chdir(temp_dir)
        
        from bookbuilder.utils import get_default_output_dir
        output_dir = get_default_output_dir(".")
        
        assert "bookbuilder-output" in output_dir
