This is a test repository for the application cognimoss.  in this repository we will complete different basic coding or writing tests.  please keep repository organized with a update to the readme with each notable addition.

## Stage 1

### hello_world.py
A simple Python script that prints "Helo world" when executed.

## Stage 2

### golden-goose/
A complete Flask application skeleton called "Golden Goose" with the following components:

- **Flask Application Factory**: Scalable app structure using blueprints
- **Database Integration**: SQLAlchemy ORM with example models (User, Post, Stock, StockPrice)
- **Database Migrations**: Flask-Migrate for schema management
- **Form Handling**: Flask-WTF with validation examples (UserForm, PostForm)
- **Template System**: Jinja2 templates with base layout and multiple pages
- **Static Assets**: Organized CSS and JavaScript files
- **Configuration**: Environment-based config with .env support
- **API Endpoints**: RESTful JSON API examples
- **Blueprint Architecture**: Organized route structure
- **Service Layer**: StockService for external API integration
- **Background Tasks**: APScheduler for periodic stock data updates
- **Comprehensive Test Suite**: pytest-based testing with fixtures and mocks
  - Model tests (User, Post, Stock, StockPrice)
  - Route tests (HTML and API endpoints)
  - Form validation tests
  - Service layer tests with mocked external APIs
  - Scheduler tests with mocked background jobs
  - Test fixtures for common scenarios
  - Code coverage reporting
- **Code Formatting and Linting**: Black and Ruff for consistent code style

See `golden-goose/README.md` for detailed setup, usage instructions, and contribution guidelines including how to write and maintain tests.

**Running Tests Locally:**
```bash
cd golden-goose
pytest                    # Run all tests
pytest -v                 # Verbose output
pytest --cov=.           # With coverage report
```

**Code Formatting and Linting:**
```bash
cd golden-goose
black .                   # Format code with Black
ruff check .              # Check code with Ruff
ruff check . --fix        # Auto-fix Ruff issues
```

Configuration for Black and Ruff is defined in `pyproject.toml` at the repository root.

**Continuous Integration:**
This repository uses GitHub Actions to automatically run the test suite and code quality checks on all pull requests and pushes to main/develop branches. The CI workflow:
- Tests against Python 3.9, 3.10, and 3.11
- Installs dependencies from `requirements.txt`
- Runs pytest with coverage reporting
- Runs Ruff linting checks
- Blocks merging if tests or linting checks fail

See `.github/workflows/tests.yml` for the complete CI configuration.

### test_results.txt
Complete test suite execution results for the golden-goose application. This file contains the output from running the entire pytest test suite, including:
- Test pass/fail status for all test modules
- Coverage of models, routes, forms, and services
- Detailed error messages for any failing tests
- Test execution summary and statistics

To regenerate this file, run:
```bash
cd golden-goose && python -m pytest -v --tb=short > ../test_results.txt 2>&1
```

---

## A Poem About Logic

In circuits deep and branches true,
Where AND and OR decide what's new,
The IF will test, the ELSE will wait,
While WHILE loops spin to meet their fate.

With truth and false, we build our way,
Through nested thoughts that never sway,
For logic pure, though cold and stark,
Brings order to the coding dark.
