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

## Project Structure

```
golden-goose/
├── app.py                 # Application factory and initialization
├── config.py              # Configuration classes
├── models.py              # Database models (User, Post)
├── routes.py              # Blueprint with routes
├── forms.py               # WTForms form classes
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── templates/            # Jinja2 templates
│   ├── base.html         # Base template
│   ├── index.html        # Home page
│   ├── users.html        # User list
│   ├── create_user.html  # User creation form
│   └── about.html        # About page
└── static/               # Static files
    ├── css/
    │   └── style.css     # Main stylesheet
    └── js/
        └── main.js       # Main JavaScript
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

## Available Routes

### Web Routes
- `/` - Home page
- `/hello` - Simple hello world endpoint
- `/users` - List all users
- `/user/create` - Create new user form
- `/about` - About page

### API Routes
- `/api/users` - GET all users (JSON)
- `/api/posts` - GET all posts (JSON)

## Database Models

### User Model
- `id`: Integer, primary key
- `username`: String(80), unique
- `email`: String(120), unique
- `created_at`: DateTime

### Post Model
- `id`: Integer, primary key
- `title`: String(200)
- `content`: Text
- `created_at`: DateTime
- `user_id`: Foreign key to User

## Forms

### UserForm
- Username field with length validation
- Email field with email validation

### PostForm
- Title field with length validation
- Content textarea with required validation

## Configuration

The application supports multiple configuration environments:

- **Development**: Debug mode enabled, SQLite database
- **Production**: Debug mode disabled, configurable database
- **Testing**: In-memory SQLite database

Configure via environment variables in `.env` file.

## Technologies Used

- **Flask 3.0.0**: Web framework
- **Flask-SQLAlchemy 3.1.1**: ORM
- **Flask-Migrate 4.0.5**: Database migrations
- **Flask-WTF 1.2.1**: Form handling
- **WTForms 3.1.1**: Form validation
- **python-dotenv 1.0.0**: Environment variable management

## Next Steps

1. Add user authentication (Flask-Login)
2. Implement user registration and login
3. Add more complex models and relationships
4. Implement pagination for list views
5. Add unit and integration tests
6. Set up logging
7. Add error handlers (404, 500)
8. Implement CSRF protection
9. Add API authentication (JWT)
10. Deploy to production server

## License

This is a skeleton/template project for educational purposes.
