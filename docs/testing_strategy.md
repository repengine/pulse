# Pulse Testing Strategy

## Overview

This document outlines the comprehensive testing strategy for the Pulse system, focusing on robustness, reliability, and critical path protection through multiple layers of testing.

## Testing Hierarchy

### 1. Unit Tests (`tests/unit/`)
- **Purpose**: Test individual functions and classes in isolation
- **Coverage**: All public functions, edge cases, error conditions
- **Location**: `tests/unit/`
- **Execution**: `pytest tests/unit/`

### 2. Integration Tests (`tests/integration/`)
- **Purpose**: Test interactions between system components
- **Focus Areas**:
  - FastAPI + Celery workflow integration
  - Engine + Rules system integration
  - Analytics + Learning system integration
- **Location**: `tests/integration/`
- **Execution**: `pytest tests/integration/ -m integration`

### 3. End-to-End Tests (`tests/e2e/`)
- **Purpose**: Test complete user workflows from start to finish
- **Focus Areas**:
  - Retrodiction analysis workflows
  - Forecast generation pipelines
  - Autopilot engagement cycles
- **Location**: `tests/e2e/`
- **Execution**: `pytest tests/e2e/ -m e2e`

### 4. Guardrail Tests (`tests/guardrails/`)
- **Purpose**: Critical path protection - ensure core functionality never breaks
- **Focus Areas**:
  - Simulation engine operation
  - Rules engine functionality
  - API endpoint availability
  - Data ingestion safety
  - Autopilot system integrity
  - System configuration validation
- **Location**: `tests/guardrails/`
- **Execution**: `pytest tests/guardrails/ -m guardrail`

## Test Categories and Marks

### Pytest Marks
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.guardrail` - Guardrail tests
- `@pytest.mark.slow` - Tests that take longer to run
- `@pytest.mark.requires_db` - Tests requiring database connectivity
- `@pytest.mark.requires_celery` - Tests requiring Celery workers

### Test Execution Commands

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m e2e
pytest -m guardrail

# Run fast tests only (exclude slow tests)
pytest -m "not slow"

# Run tests with coverage
pytest --cov=. --cov-report=html

# Run tests in parallel
pytest -n auto
```

## Guardrail Testing Philosophy

Guardrail tests serve as the **last line of defense** against system failures. These tests:

1. **Must Never Fail**: If a guardrail test fails, it indicates a critical system issue
2. **Test Core Invariants**: Verify that fundamental system assumptions hold
3. **Provide Safety Nets**: Catch regressions in critical functionality
4. **Enable Confident Deployment**: Ensure system stability before releases

### Guardrail Test Categories

#### Simulation Engine Guardrails
- Basic simulation operation
- Forward simulation progression
- State consistency across operations

#### Rules Engine Guardrails
- Rules engine initialization
- Rules application safety
- Error handling robustness

#### API Endpoint Guardrails
- Status endpoint availability
- Core endpoint functionality
- Autopilot endpoint accessibility

#### Data Ingestion Guardrails
- Signal ingestion operation
- Data validation safety
- Input sanitization

#### Autopilot Guardrails
- Task registration
- State safety
- Error boundary protection

#### System Integrity Guardrails
- Critical module imports
- Configuration integrity
- Database connectivity safety

## Test Data Management

### Test Fixtures
- **Location**: `tests/fixtures/`
- **Purpose**: Reusable test data and mock objects
- **Organization**: By functional area (simulation, rules, api, etc.)

### Mock Strategy
- **External Dependencies**: Always mocked in unit tests
- **Database Operations**: Mocked unless specifically testing DB integration
- **Network Calls**: Mocked to ensure test reliability
- **File System**: Use temporary directories for file operations

## Continuous Integration

### Pre-commit Hooks
```bash
# Style checking
flake8 --max-line-length=100
black --check .
isort --check-only .

# Type checking
mypy --strict

# Fast test suite
pytest -m "not slow" --maxfail=5
```

### CI Pipeline Stages

1. **Lint & Format Check**
   - flake8, black, isort
   - Documentation checks

2. **Type Checking**
   - mypy with strict settings

3. **Unit Tests**
   - Fast, isolated tests
   - High coverage requirements

4. **Integration Tests**
   - Component interaction tests
   - Database integration tests

5. **Guardrail Tests**
   - Critical path verification
   - Must pass for deployment

6. **E2E Tests**
   - Full workflow validation
   - Performance benchmarks

## Coverage Requirements

### Minimum Coverage Targets
- **Overall**: 85%
- **Core Modules**: 90%
- **Critical Paths**: 95%

### Coverage Exclusions
- Test files themselves
- Configuration files
- Migration scripts
- Development utilities

## Performance Testing

### Load Testing
- **Tool**: pytest-benchmark
- **Focus**: Critical path performance
- **Thresholds**: Defined per operation type

### Memory Testing
- **Tool**: memory_profiler
- **Focus**: Memory leak detection
- **Monitoring**: Long-running operations

## Test Environment Setup

### Local Development
```bash
# Install test dependencies
pip install -r requirements-test.txt

# Set up test database
export PULSE_TEST_DB_URL="sqlite:///test.db"

# Run test suite
pytest
```

### Docker Testing
```bash
# Build test environment
docker-compose -f docker-compose.test.yml up --build

# Run tests in container
docker-compose -f docker-compose.test.yml run tests
```

## Debugging Failed Tests

### Common Issues
1. **Import Errors**: Check module paths and dependencies
2. **Mock Failures**: Verify mock setup and expectations
3. **Timing Issues**: Use proper async/await patterns
4. **State Pollution**: Ensure test isolation

### Debugging Tools
```bash
# Run with verbose output
pytest -v

# Run with debugging
pytest --pdb

# Run specific test with output
pytest -s tests/path/to/test.py::test_function

# Run with coverage and missing lines
pytest --cov=. --cov-report=term-missing
```

## Best Practices

### Test Writing Guidelines
1. **Arrange-Act-Assert**: Clear test structure
2. **Descriptive Names**: Test names should describe the scenario
3. **Single Responsibility**: One assertion per test when possible
4. **Independent Tests**: No dependencies between tests
5. **Fast Execution**: Keep tests fast and focused

### Mock Guidelines
1. **Mock External Dependencies**: Always mock external services
2. **Verify Interactions**: Use mock assertions to verify calls
3. **Realistic Mocks**: Mocks should behave like real objects
4. **Clear Mock Setup**: Make mock configuration obvious

### Fixture Guidelines
1. **Reusable Fixtures**: Create fixtures for common test data
2. **Scope Appropriately**: Use correct fixture scope (function, class, module)
3. **Clean Teardown**: Ensure proper cleanup after tests
4. **Parameterized Fixtures**: Use parametrization for test variations

## Maintenance

### Regular Tasks
- **Weekly**: Review test coverage reports
- **Monthly**: Update test dependencies
- **Quarterly**: Review and refactor slow tests
- **Release**: Full test suite validation

### Test Debt Management
- **Identify Flaky Tests**: Track and fix unreliable tests
- **Remove Obsolete Tests**: Clean up tests for removed features
- **Update Test Data**: Keep test fixtures current
- **Performance Optimization**: Optimize slow test suites

## Conclusion

This testing strategy ensures the Pulse system maintains high quality and reliability through comprehensive test coverage, critical path protection, and continuous validation. The guardrail testing approach provides confidence in system stability while the layered testing strategy catches issues at appropriate levels of granularity.