from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Register blueprints
    from routes import main_bp
    app.register_blueprint(main_bp)
    
    # Simple hello world route
    @app.route('/hello')
    def hello():
        return 'Hello World from Golden Goose!'
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
