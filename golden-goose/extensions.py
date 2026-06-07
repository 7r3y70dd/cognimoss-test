"""Flask extensions initialization module

This module initializes Flask extensions to avoid circular imports.
Extensions are initialized here and then initialized with the app
in the application factory.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()
