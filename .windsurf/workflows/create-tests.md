---
description: Create and run test cases for code changes
---

# Create Tests Workflow

Automates the creation and execution of test cases following pytest best practices from `resources/Python-Testing-Cheat-Sheet.md`.

## When to Use

Trigger this workflow when:
- New functionality has been added
- Bug fixes need regression tests
- Code refactoring requires test coverage verification
- Before creating a PR to ensure quality

## Trigger

Manual trigger via `/create-tests` command in Cascade chat.

---

## Instructions for Cascade

### Step 1: Identify Changes

First, identify what code has changed:

```bash
# Check git status for modified files
git status

# View recent changes
git diff --name-only HEAD~1
```

Ask the user:
1. Which module/function needs tests?
2. Is this a new feature, bug fix, or refactor?

### Step 2: Analyze Code Under Test

Read the source file to understand:
- Function signatures and parameters
- Return types and values
- Edge cases and error conditions
- Dependencies that may need mocking

### Step 3: Apply ZOMBIES Heuristic

Generate test cases using ZOMBIES pattern:

| Heuristic | Test Case Ideas |
|-----------|-----------------|
| **Z**ero | Empty inputs, None, zero values |
| **O**ne | Single element, first item |
| **M**any | Multiple items, typical usage |
| **B**oundary | Edge cases, limits, off-by-one |
| **I**nterface | Type checking, contracts |
| **E**xception | Error handling, invalid inputs |
| **S**imple | Happy path, basic functionality |

### Step 4: Create Test File

If test file doesn't exist, create it:

```python
"""
Unit tests for <module_name>.

Tests cover:
- <functionality 1>
- <functionality 2>
"""

import os
import pytest

from <package>.<module> import <function_or_class>


class Test<ClassName>:
    """Tests for <ClassName> functionality."""
    
    def test_<function>_<scenario>_<expected>(self):
        """<Description of what is being tested>."""
        # Arrange
        <setup test data>
        
        # Act
        result = <call function under test>
        
        # Assert
        assert result == expected
```

### Step 5: Write Test Cases

Follow Arrange-Act-Assert (AAA) pattern:

```python
def test_function_with_valid_input_returns_expected():
    """Function returns expected result for valid input."""
    # Arrange
    input_data = "test"
    expected = "TEST"
    
    # Act
    result = function_under_test(input_data)
    
    # Assert
    assert result == expected
```

### Step 6: Add Fixtures if Needed

Create fixtures in `conftest.py` for reusable test data:

```python
@pytest.fixture
def sample_data():
    """Provide sample data for tests."""
    return {"key": "value"}

@pytest.fixture
def temp_file(tmp_path):
    """Create temporary test file."""
    file_path = tmp_path / "test.txt"
    file_path.write_text("content")
    return file_path
```

### Step 7: Run Tests

// turbo
```bash
# Run all tests
pytest -v

# Run specific test file
pytest tests/test_<module>.py -v

# Run with coverage
pytest --cov=bookbuilder --cov-report=term-missing
```

### Step 8: Check Coverage

// turbo
```bash
# Generate coverage report
pytest --cov=bookbuilder --cov-report=html

# View coverage percentage
pytest --cov=bookbuilder --cov-report=term
```

### Step 9: Fix Failing Tests

If tests fail:
1. Read the error message carefully
2. Check if it's a test issue or code issue
3. Fix the appropriate file
4. Re-run tests

### Step 10: Report Results

Provide summary to user:
- Number of tests created
- Test coverage percentage
- Any failing tests and their causes
- Recommendations for additional tests

---

## Test Case Templates

### Unit Test Template

```python
class TestFunctionName:
    """Tests for function_name function."""
    
    def test_with_valid_input(self):
        """Returns expected result for valid input."""
        result = function_name("valid")
        assert result == "expected"
    
    def test_with_empty_input(self):
        """Handles empty input gracefully."""
        result = function_name("")
        assert result == ""
    
    def test_with_none_input(self):
        """Handles None input appropriately."""
        with pytest.raises(TypeError):
            function_name(None)
    
    def test_with_boundary_value(self):
        """Handles boundary conditions correctly."""
        result = function_name("x" * 1000)
        assert len(result) <= 1000
```

### Integration Test Template

```python
@pytest.mark.integration
class TestModuleIntegration:
    """Integration tests for module."""
    
    def test_end_to_end_workflow(self, temp_dir):
        """Complete workflow executes successfully."""
        # Setup
        input_file = temp_dir / "input.txt"
        input_file.write_text("data")
        
        # Execute
        result = process_workflow(str(input_file))
        
        # Verify
        assert result.success is True
        assert (temp_dir / "output.txt").exists()
```

### Parametrized Test Template

```python
@pytest.mark.parametrize("input_val,expected", [
    ("", ""),
    ("a", "A"),
    ("hello", "HELLO"),
    ("Hello World", "HELLO WORLD"),
])
def test_uppercase_conversion(input_val, expected):
    """Converts various inputs to uppercase correctly."""
    assert to_uppercase(input_val) == expected
```

### Exception Test Template

```python
class TestErrorHandling:
    """Tests for error handling."""
    
    def test_invalid_input_raises_value_error(self):
        """Raises ValueError for invalid input."""
        with pytest.raises(ValueError, match="invalid"):
            function_name("invalid_input")
    
    def test_missing_file_raises_file_not_found(self):
        """Raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            read_file("/nonexistent/path.txt")
```

---

## Checklist

Before completing, verify:

- [ ] All new functions have tests
- [ ] Edge cases are covered (ZOMBIES)
- [ ] Error handling is tested
- [ ] Tests follow AAA pattern
- [ ] Test names are descriptive
- [ ] No hard-coded paths or values
- [ ] Fixtures used for reusable data
- [ ] All tests pass
- [ ] Coverage is acceptable (>80%)

---

## Quick Commands

| Command | Description |
|---------|-------------|
| `pytest` | Run all tests |
| `pytest -v` | Verbose output |
| `pytest -x` | Stop on first failure |
| `pytest -k "pattern"` | Run matching tests |
| `pytest --lf` | Run last failed |
| `pytest --cov=pkg` | With coverage |

---

## Reference

See `resources/Python-Testing-Cheat-Sheet.md` for:
- ZOMBIES heuristic details
- CORRECT boundary conditions
- Right-BICEP testing approach
- Fixture patterns
- Mocking techniques
