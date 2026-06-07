"""Flask extensions initialization module

This module initializes Flask extensions to avoid circular imports.
Extensions are created here and initialized with the app in app.py.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Create extension instances without app context
db = SQLAlchemy()
migratedb = Migrate()
