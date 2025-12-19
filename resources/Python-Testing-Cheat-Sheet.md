# Python Testing Cheat Sheet

A comprehensive guide to testing Python projects using pytest and best practices.

---

## Table of Contents

1. [Test Heuristics](#test-heuristics)
2. [Pytest Basics](#pytest-basics)
3. [Test Structure](#test-structure)
4. [Fixtures](#fixtures)
5. [Assertions](#assertions)
6. [Parametrization](#parametrization)
7. [Mocking](#mocking)
8. [Coverage](#coverage)
9. [Test Categories](#test-categories)
10. [Common Patterns](#common-patterns)

---

## Test Heuristics

### ZOMBIES - Test Case Generation

| Letter | Heuristic | Description                                 |
|--------|-----------|---------------------------------------------|
| **Z**  | Zero      | Empty collections, zero values, null/None   |
| **O**  | One       | Single element, first item, boundary of one |
| **M**  | Many      | Multiple items, typical use cases           |
| **B**  | Boundary  | Edge cases, limits, off-by-one              |
| **I**  | Interface | API contracts, input/output types           |
| **E**  | Exception | Error handling, invalid inputs              |
| **S**  | Simple    | Happy path, basic functionality             |

### CORRECT Boundary Conditions

| Letter | Condition   | Examples                                 |
|--------|-------------|------------------------------------------|
| **C**  | Conformance | Does it conform to expected format?      |
| **O**  | Ordering    | Is ordering important? First/last/middle |
| **R**  | Range       | Within min/max bounds?                   |
| **R**  | Reference   | External dependencies, null refs         |
| **E**  | Existence   | Does it exist? Empty/null/missing        |
| **C**  | Cardinality | Right count? 0, 1, many                  |
| **T**  | Time        | Timing issues, timeouts, order of ops    |

### Right-BICEP

| Aspect    | Question                         |
|-----------|----------------------------------|
| **Right** | Are the results right?           |
| **B**     | Boundary conditions correct?     |
| **I**     | Inverse relationships checkable? |
| **C**     | Cross-check with other means?    |
| **E**     | Error conditions forced?         |
| **P**     | Performance within bounds?       |

---

## Pytest Basics

### Installation

```bash
pip install pytest pytest-cov pytest-mock
```

### Running Tests

```bash
# Run all tests
pytest

# Verbose output
pytest -v

# Run specific file
pytest tests/test_module.py

# Run specific test
pytest tests/test_module.py::test_function

# Run specific class
pytest tests/test_module.py::TestClass

# Run by marker
pytest -m "slow"
pytest -m "not slow"

# Run with coverage
pytest --cov=mypackage --cov-report=html

# Stop on first failure
pytest -x

# Show print statements
pytest -s

# Parallel execution
pytest -n auto  # requires pytest-xdist
```

### Configuration (pytest.ini)

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
markers =
    slow: marks tests as slow
    integration: marks integration tests
```

---

## Test Structure

### Arrange-Act-Assert (AAA) Pattern

```python
def test_user_creation():
    # Arrange - Set up test data and conditions
    name = "John Doe"
    email = "john@example.com"
    
    # Act - Execute the code under test
    user = User(name=name, email=email)
    
    # Assert - Verify the results
    assert user.name == name
    assert user.email == email
    assert user.is_active is True
```

### Given-When-Then (BDD Style)

```python
def test_withdraw_sufficient_funds():
    # Given: An account with $100
    account = Account(balance=100)
    
    # When: Withdrawing $50
    account.withdraw(50)
    
    # Then: Balance should be $50
    assert account.balance == 50
```

### Test Class Organization

```python
class TestUserAuthentication:
    """Tests for user authentication functionality."""
    
    def test_valid_login(self):
        """User can login with correct credentials."""
        pass
    
    def test_invalid_password(self):
        """Login fails with incorrect password."""
        pass
    
    def test_locked_account(self):
        """Login fails for locked accounts."""
        pass
```

---

## Fixtures

### Basic Fixtures

```python
import pytest

@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    return User(name="Test User", email="test@example.com")

def test_user_display(sample_user):
    assert sample_user.display_name == "Test User"
```

### Fixture Scopes

```python
@pytest.fixture(scope="function")  # Default - new for each test
def func_fixture():
    return create_resource()

@pytest.fixture(scope="class")  # Shared within test class
def class_fixture():
    return create_resource()

@pytest.fixture(scope="module")  # Shared within module
def module_fixture():
    return create_resource()

@pytest.fixture(scope="session")  # Shared across all tests
def session_fixture():
    return create_resource()
```

### Setup/Teardown with Fixtures

```python
@pytest.fixture
def database_connection():
    # Setup
    conn = create_connection()
    yield conn
    # Teardown
    conn.close()

@pytest.fixture
def temp_directory(tmp_path):
    """Create temp directory with test files."""
    test_dir = tmp_path / "test_data"
    test_dir.mkdir()
    (test_dir / "file.txt").write_text("content")
    yield test_dir
    # Cleanup happens automatically with tmp_path
```

### Fixture Factories

```python
@pytest.fixture
def make_user():
    """Factory fixture for creating users."""
    created_users = []
    
    def _make_user(name="Default", email="default@example.com"):
        user = User(name=name, email=email)
        created_users.append(user)
        return user
    
    yield _make_user
    
    # Cleanup all created users
    for user in created_users:
        user.delete()
```

### Built-in Fixtures

| Fixture            | Description                         |
|--------------------|-------------------------------------|
| `tmp_path`         | Temporary directory (pathlib.Path)  |
| `tmp_path_factory` | Factory for temp directories        |
| `tmpdir`           | Temporary directory (py.path.local) |
| `capsys`           | Capture stdout/stderr               |
| `capfd`            | Capture file descriptors            |
| `monkeypatch`      | Modify objects/environment          |
| `request`          | Test request context                |

---

## Assertions

### Basic Assertions

```python
# Equality
assert result == expected
assert result != unexpected

# Identity
assert result is None
assert result is not None

# Boolean
assert condition is True
assert not condition

# Containment
assert item in collection
assert item not in collection

# Type checking
assert isinstance(obj, MyClass)
```

### Approximate Comparisons

```python
# Float comparison
assert result == pytest.approx(3.14, rel=1e-3)
assert result == pytest.approx(3.14, abs=0.01)

# List of floats
assert [0.1, 0.2] == pytest.approx([0.1, 0.2])
```

### Exception Testing

```python
# Basic exception check
def test_raises_value_error():
    with pytest.raises(ValueError):
        function_that_raises()

# Check exception message
def test_exception_message():
    with pytest.raises(ValueError, match="invalid value"):
        function_that_raises()

# Access exception info
def test_exception_details():
    with pytest.raises(ValueError) as exc_info:
        function_that_raises()
    assert "specific message" in str(exc_info.value)
```

### Warning Testing

```python
def test_deprecation_warning():
    with pytest.warns(DeprecationWarning):
        deprecated_function()

def test_warning_message():
    with pytest.warns(UserWarning, match="be careful"):
        cautious_function()
```

---

## Parametrization

### Basic Parametrization

```python
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_double(input, expected):
    assert double(input) == expected
```

### Multiple Parameters

```python
@pytest.mark.parametrize("x", [1, 2, 3])
@pytest.mark.parametrize("y", [10, 20])
def test_multiply(x, y):
    # Tests all combinations: (1,10), (1,20), (2,10), (2,20), (3,10), (3,20)
    assert multiply(x, y) == x * y
```

### Named Test Cases

```python
@pytest.mark.parametrize("input,expected", [
    pytest.param(1, 1, id="one"),
    pytest.param(2, 4, id="two_squared"),
    pytest.param(3, 9, id="three_squared"),
])
def test_square(input, expected):
    assert square(input) == expected
```

### Conditional Skip

```python
@pytest.mark.parametrize("value", [
    pytest.param(1, id="normal"),
    pytest.param(None, marks=pytest.mark.skip(reason="not implemented")),
    pytest.param(-1, marks=pytest.mark.xfail(reason="negative not supported")),
])
def test_process(value):
    process(value)
```

---

## Mocking

### Using pytest-mock

```python
def test_api_call(mocker):
    # Mock a function
    mock_get = mocker.patch("requests.get")
    mock_get.return_value.json.return_value = {"data": "value"}
    
    result = fetch_data()
    
    mock_get.assert_called_once_with("https://api.example.com")
    assert result == {"data": "value"}
```

### Using unittest.mock

```python
from unittest.mock import Mock, patch, MagicMock

def test_with_mock():
    # Create a mock
    mock_service = Mock()
    mock_service.get_data.return_value = [1, 2, 3]
    
    result = process_data(mock_service)
    
    mock_service.get_data.assert_called_once()
    assert result == 6

@patch("mymodule.external_api")
def test_with_patch(mock_api):
    mock_api.return_value = "mocked"
    result = function_using_api()
    assert result == "mocked"
```

### Mocking Context Managers

```python
def test_file_read(mocker):
    mock_open = mocker.patch("builtins.open", mocker.mock_open(read_data="content"))
    
    result = read_file("test.txt")
    
    mock_open.assert_called_once_with("test.txt", "r")
    assert result == "content"
```

### Mocking Properties

```python
def test_property(mocker):
    mock_obj = Mock()
    type(mock_obj).property_name = mocker.PropertyMock(return_value="value")
    
    assert mock_obj.property_name == "value"
```

---

## Coverage

### Running Coverage

```bash
# Basic coverage
pytest --cov=mypackage

# With HTML report
pytest --cov=mypackage --cov-report=html

# With terminal report
pytest --cov=mypackage --cov-report=term-missing

# Fail if coverage below threshold
pytest --cov=mypackage --cov-fail-under=80
```

### Coverage Configuration (.coveragerc)

```ini
[run]
source = mypackage
omit = 
    */tests/*
    */__init__.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if __name__ == .__main__.:

[html]
directory = htmlcov
```

---

## Test Categories

### Unit Tests
- Test single functions/methods in isolation
- Fast execution
- No external dependencies (mocked)

```python
def test_calculate_total():
    items = [{"price": 10}, {"price": 20}]
    assert calculate_total(items) == 30
```

### Integration Tests
- Test multiple components together
- May use real databases, files, etc.

```python
@pytest.mark.integration
def test_save_and_retrieve(database):
    user = User(name="Test")
    database.save(user)
    retrieved = database.get_by_name("Test")
    assert retrieved.name == "Test"
```

### End-to-End Tests
- Test complete workflows
- Simulate real user scenarios

```python
@pytest.mark.e2e
def test_user_registration_flow(client):
    response = client.post("/register", data={"email": "test@example.com"})
    assert response.status_code == 201
    
    response = client.post("/login", data={"email": "test@example.com"})
    assert response.status_code == 200
```

---

## Common Patterns

### Testing Private Methods

```python
# Access private method for testing (use sparingly)
def test_private_method():
    obj = MyClass()
    result = obj._private_method()  # Direct access
    assert result == expected
```

### Testing Async Code

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await async_fetch_data()
    assert result == expected
```

### Snapshot Testing

```python
def test_html_output(snapshot):
    result = generate_html()
    snapshot.assert_match(result, "expected_output.html")
```

### Property-Based Testing

```python
from hypothesis import given, strategies as st

@given(st.integers(), st.integers())
def test_addition_commutative(a, b):
    assert add(a, b) == add(b, a)
```

### Test Data Builders

```python
class UserBuilder:
    def __init__(self):
        self.name = "Default"
        self.email = "default@example.com"
        self.active = True
    
    def with_name(self, name):
        self.name = name
        return self
    
    def inactive(self):
        self.active = False
        return self
    
    def build(self):
        return User(self.name, self.email, self.active)

def test_inactive_user():
    user = UserBuilder().with_name("John").inactive().build()
    assert not user.active
```

---

## Quick Reference Commands

| Command                 | Description                |
|-------------------------|----------------------------|
| `pytest`                | Run all tests              |
| `pytest -v`             | Verbose output             |
| `pytest -x`             | Stop on first failure      |
| `pytest -s`             | Show print output          |
| `pytest -k "pattern"`   | Run tests matching pattern |
| `pytest -m "marker"`    | Run tests with marker      |
| `pytest --lf`           | Run last failed tests      |
| `pytest --ff`           | Run failed tests first     |
| `pytest --collect-only` | Show tests without running |
| `pytest --durations=10` | Show 10 slowest tests      |

---

## Test Naming Conventions

```python
# Function naming
def test_<function>_<scenario>_<expected_result>():
    pass

# Examples
def test_calculate_total_with_empty_cart_returns_zero():
    pass

def test_login_with_invalid_password_raises_auth_error():
    pass

def test_user_creation_sets_default_role_to_member():
    pass
```

---

## Anti-Patterns to Avoid

| Anti-Pattern                   | Better Approach             |
|--------------------------------|-----------------------------|
| Testing implementation details | Test behavior/outcomes      |
| Large test methods             | Split into focused tests    |
| Tests depending on order       | Independent, isolated tests |
| Hard-coded test data           | Use fixtures/factories      |
| Ignoring flaky tests           | Fix or quarantine them      |
| Testing third-party code       | Mock external dependencies  |
| No assertions                  | Every test needs assertions |
| Testing multiple things        | One concept per test        |

---

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Python Testing with pytest (Book)](https://pragprog.com/titles/bopytest2/)
- [Test-Driven Development with Python](https://www.obeythetestinggoat.com/)
- [Hypothesis (Property-Based Testing)](https://hypothesis.readthedocs.io/)

---

*Created for BookBuilder Project - December 2024*
