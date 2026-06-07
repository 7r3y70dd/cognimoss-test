# Golden Goose - Flask Application Skeleton

A complete Flask application framework with all the essential components for building modern web applications.

## Features

- **Flask Application Factory Pattern**: Scalable and testable application structure
- **Database Integration**: SQLAlchemy ORM with Flask-Migrate for migrations
- **Form Handling**: Flask-WTF with validation
- **Blueprint Architecture**: Organized route structure
- **Template System**: Jinja2 templates with base layout
- **Static Assets**: CSS and JavaScript organization
- **Configuration Management**: Environment-based configuration
- **API Endpoints**: RESTful JSON API examples
- **Comprehensive Test Suite**: pytest-based testing with high coverage

## Project Structure

```
golden-goose/
├── app.py                 # Application factory and initialization
├── config.py              # Configuration classes
├── models.py              # Database models (User, Post, Stock, StockPrice)
├── routes.py              # Blueprint with routes
├── forms.py               # WTForms form classes
├── scheduler.py           # APScheduler for background tasks
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── services/             # Service layer
│   ├── __init__.py
│   └── stock_service.py  # Stock data service
├── templates/            # Jinja2 templates
│   ├── base.html         # Base template
│   ├── index.html        # Home page
│   ├── users.html        # User list
│   ├── create_user.html  # User creation form
│   └── about.html        # About page
├── static/               # Static files
│   ├── css/
│   │   └── style.css     # Main stylesheet
│   └── js/
│       └── main.js       # Main JavaScript
└── tests/                # Test suite
    ├── __init__.py
    ├── conftest.py       # Pytest fixtures
    ├── test_models.py    # Model tests
    ├── test_routes.py    # Route tests
    ├── test_forms.py     # Form tests
    └── test_stock_service.py  # Service tests
```

## Installation

1. **Clone or navigate to the golden-goose directory**

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize the database**
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

## Running the Application

### Development Mode

```bash
python app.py
```

Or using Flask CLI:

```bash
export FLASK_APP=app.py
export FLASK_ENV=development
flask run
```

The application will be available at `http://localhost:5000`

## Testing

The Golden Goose application includes a comprehensive test suite using pytest.

### Running Tests

**Run all tests:**
```bash
pytest
```

**Run tests with verbose output:**
```bash
pytest -v
```

**Run tests with coverage report:**
```bash
pytest --cov=. --cov-report=html
```

**Run specific test file:**
```bash
pytest tests/test_models.py
```

**Run specific test class or function:**
```bash
pytest tests/test_models.py::TestUserModel::test_create_user
```

### Test Structure

The test suite is organized into the following modules:

- **conftest.py**: Pytest fixtures and configuration
  - `app`: Application instance for testing
  - `db`: Database instance with automatic cleanup
  - `client`: Test client for making requests
  - `sample_user`, `sample_post`, `sample_stock`, etc.: Pre-populated test data

- **test_models.py**: Tests for database models
  - User model CRUD operations and validation
  - Post model relationships and serialization
  - Stock and StockPrice model functionality

- **test_routes.py**: Tests for application routes
  - HTML template rendering
  - API endpoint responses
  - Form submission handling
  - Error handling and edge cases

- **test_forms.py**: Tests for WTForms validation
  - Valid and invalid form data
  - Field validation rules
  - Error message generation

- **test_stock_service.py**: Tests for service layer
  - External API interaction (mocked)
  - Data transformation and storage
  - Error handling and edge cases

## Contributing

When contributing to Golden Goose, please follow these guidelines to maintain code quality and test coverage.

### Adding New Features

When adding a new feature, you **must** include corresponding tests:

1. **Models**: If you add or modify a model:
   - Add tests in `tests/test_models.py`
   - Test CRUD operations
   - Test relationships and constraints
   - Test the `to_dict()` serialization method
   - Test edge cases and validation

2. **Routes**: If you add or modify a route:
   - Add tests in `tests/test_routes.py`
   - Test successful responses (200, 201, etc.)
   - Test error responses (400, 404, 500, etc.)
   - Test with valid and invalid data
   - Test authentication/authorization if applicable
   - For API endpoints, verify JSON structure
   - For HTML routes, verify template rendering

3. **Forms**: If you add or modify a form:
   - Add tests in `tests/test_forms.py`
   - Test validation with valid data
   - Test validation with invalid data
   - Test each validator (required, length, email, etc.)
   - Test edge cases (empty strings, whitespace, etc.)

4. **Services**: If you add or modify a service:
   - Add tests in `tests/test_stock_service.py` or create a new test file
   - Mock external API calls
   - Test successful operations
   - Test error handling
   - Test data transformation logic

### Test Writing Guidelines

1. **Use descriptive test names**: Test names should clearly describe what is being tested
   ```python
   def test_user_creation_with_valid_data(self, db):
   def test_api_returns_404_for_nonexistent_stock(self, client):
   ```

2. **Follow the Arrange-Act-Assert pattern**:
   ```python
   def test_example(self, db):
       # Arrange: Set up test data
       user = User(username='test', email='test@example.com')
       
       # Act: Perform the action
       db.session.add(user)
       db.session.commit()
       
       # Assert: Verify the result
       assert user.id is not None
   ```

3. **Use fixtures for common setup**: Leverage pytest fixtures from `conftest.py`
   ```python
   def test_with_existing_user(self, sample_user):
       assert sample_user.username == 'testuser'
   ```

4. **Test both success and failure cases**: Don't just test the happy path
   ```python
   def test_create_user_success(self, client, db):
       # Test successful creation
       
   def test_create_user_duplicate_email(self, client, sample_user):
       # Test failure case
   ```

5. **Mock external dependencies**: Use `unittest.mock` for external API calls
   ```python
   @patch('services.stock_service.requests.get')
   def test_fetch_quote(self, mock_get):
       mock_get.return_value.json.return_value = {...}
   ```

6. **Keep tests isolated**: Each test should be independent and not rely on other tests

7. **Maintain test coverage**: Aim for >80% code coverage
   ```bash
   pytest --cov=. --cov-report=term-missing
   ```

### Modifying Existing Features

When modifying existing functionality:

1. **Update existing tests** to reflect the changes
2. **Add new tests** for new behavior or edge cases
3. **Ensure all tests pass** before submitting changes
4. **Update test documentation** if test structure changes

### Running Tests Before Committing

Always run the full test suite before committing:

```bash
# Run all tests
pytest

# Check coverage
pytest --cov=. --cov-report=term-missing

# Ensure no tests are skipped
pytest -v
```

### Continuous Integration

All pull requests should:
- Pass all existing tests
- Include tests for new functionality
- Maintain or improve code coverage
- Follow the project's coding standards

## API Endpoints

### User Endpoints
- `GET /users` - List all users (HTML)
- `GET /user/create` - User creation form (HTML)
- `POST /user/create` - Create new user
- `GET /api/users` - List all users (JSON)

### Post Endpoints
- `GET /api/posts` - List all posts (JSON)

### Stock Endpoints
- `GET /api/stocks` - List all tracked stocks
- `GET /api/stocks/<symbol>` - Get stock details
- `POST /api/stocks` - Add new stock to track
- `DELETE /api/stocks/<symbol>` - Remove stock from tracking
- `GET /api/stocks/<symbol>/prices` - Get price history
- `GET /api/stocks/<symbol>/latest` - Get latest price
- `POST /api/stocks/<symbol>/import` - Manually import stock data

## Database Models

### User
- `id`: Primary key
- `username`: Unique username (3-80 characters)
- `email`: Unique email address
- `created_at`: Timestamp

### Post
- `id`: Primary key
- `title`: Post title (1-200 characters)
- `content`: Post content (text)
- `user_id`: Foreign key to User
- `created_at`: Timestamp

### Stock
- `id`: Primary key
- `symbol`: Unique stock symbol
- `name`: Company name
- `exchange`: Exchange name
- `currency`: Currency code
- `created_at`: Timestamp
- `updated_at`: Timestamp

### StockPrice
- `id`: Primary key
- `stock_id`: Foreign key to Stock
- `timestamp`: Price timestamp
- `open_price`: Opening price
- `high_price`: High price
- `low_price`: Low price
- `close_price`: Closing price
- `volume`: Trading volume
- `created_at`: Timestamp

## Configuration

The application supports multiple configuration environments:

- **Development**: Debug mode enabled, SQLite database
- **Production**: Debug mode disabled, production database
- **Testing**: In-memory SQLite database, CSRF disabled

Set the environment using the `FLASK_ENV` variable or by passing the config class to `create_app()`.

## License

This is a test/example application for learning purposes.
