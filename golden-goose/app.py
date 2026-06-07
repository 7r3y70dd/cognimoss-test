from flask import Flask, render_template
from extensions import db, migratedb
from config import Config
import logging

# Initialize scheduler (will be started after app creation)
from scheduler import StockDataScheduler
scheduler = StockDataScheduler()

def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize extensions with app
    db.init_app(app)
    migratedb.init_app(app, db)
    
    # Initialize scheduler with app
    scheduler.init_app(app)
    
    # Register blueprints
    from routes import main_bp
    app.register_blueprint(main_bp)
    
    # Simple hello world route
    @app.route('/hello')
    def hello():
        return 'Hello World from Golden Goose!'
    
    # Start scheduler if not in testing mode
    if not app.config.get('TESTING', False):
        with app.app_context():
            try:
                scheduler.start()
            except Exception as e:
                app.logger.error(f"Failed to start scheduler: {e}")
    
    return app

if __name__ == '__main__':
    app = create_app()
    try:
        app.run(debug=True)
    finally:
        # Ensure scheduler is shut down on exit
        scheduler.shutdown()
