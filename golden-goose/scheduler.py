"""Background scheduler for regular stock data imports"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from services.stock_service import StockService
from config import Config

logger = logging.getLogger(__name__)

class StockDataScheduler:
    """Scheduler for automated stock data imports"""
    
    def __init__(self, app=None):
        """
        Initialize scheduler
        
        Args:
            app: Flask application instance
        """
        self.scheduler = BackgroundScheduler()
        self.app = app
        self.stock_service = None
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app context"""
        self.app = app
        
        # Initialize stock service with API key from config
        api_key = app.config.get('STOCK_API_KEY')
        api_provider = app.config.get('STOCK_API_PROVIDER', 'alphavantage')
        
        if api_key:
            self.stock_service = StockService(api_key, api_provider)
        else:
            logger.warning("No STOCK_API_KEY configured. Stock data imports will not work.")
    
    def import_stock_quotes(self):
        """Import current quotes for tracked stocks"""
        if not self.stock_service:
            logger.error("Stock service not initialized")
            return
        
        with self.app.app_context():
            from models import Stock
            
            # Get all tracked stocks
            stocks = Stock.query.all()
            logger.info(f"Importing quotes for {len(stocks)} stocks")
            
            for stock in stocks:
                try:
                    success = self.stock_service.import_stock_data(stock.symbol, 'quote')
                    if success:
                        logger.info(f"Successfully imported quote for {stock.symbol}")
                    else:
                        logger.warning(f"Failed to import quote for {stock.symbol}")
                except Exception as e:
                    logger.error(f"Error importing quote for {stock.symbol}: {e}")
    
    def import_stock_daily(self):
        """Import daily data for tracked stocks"""
        if not self.stock_service:
            logger.error("Stock service not initialized")
            return
        
        with self.app.app_context():
            from models import Stock
            
            # Get all tracked stocks
            stocks = Stock.query.all()
            logger.info(f"Importing daily data for {len(stocks)} stocks")
            
            for stock in stocks:
                try:
                    success = self.stock_service.import_stock_data(stock.symbol, 'daily')
                    if success:
                        logger.info(f"Successfully imported daily data for {stock.symbol}")
                    else:
                        logger.warning(f"Failed to import daily data for {stock.symbol}")
                except Exception as e:
                    logger.error(f"Error importing daily data for {stock.symbol}: {e}")
    
    def import_stock_intraday(self):
        """Import intraday data for tracked stocks"""
        if not self.stock_service:
            logger.error("Stock service not initialized")
            return
        
        with self.app.app_context():
            from models import Stock
            
            # Get all tracked stocks
            stocks = Stock.query.all()
            logger.info(f"Importing intraday data for {len(stocks)} stocks")
            
            for stock in stocks:
                try:
                    success = self.stock_service.import_stock_data(stock.symbol, 'intraday')
                    if success:
                        logger.info(f"Successfully imported intraday data for {stock.symbol}")
                    else:
                        logger.warning(f"Failed to import intraday data for {stock.symbol}")
                except Exception as e:
                    logger.error(f"Error importing intraday data for {stock.symbol}: {e}")
    
    def start(self):
        """Start the scheduler with configured jobs"""
        if not self.app:
            logger.error("Scheduler not initialized with Flask app")
            return
        
        # Schedule quote imports every 15 minutes during market hours
        self.scheduler.add_job(
            func=self.import_stock_quotes,
            trigger=IntervalTrigger(minutes=15),
            id='import_quotes',
            name='Import stock quotes',
            replace_existing=True
        )
        
        # Schedule daily data import once per day at 6 PM
        self.scheduler.add_job(
            func=self.import_stock_daily,
            trigger=CronTrigger(hour=18, minute=0),
            id='import_daily',
            name='Import daily stock data',
            replace_existing=True
        )
        
        # Schedule intraday data import every hour during market hours
        self.scheduler.add_job(
            func=self.import_stock_intraday,
            trigger=IntervalTrigger(hours=1),
            id='import_intraday',
            name='Import intraday stock data',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("Stock data scheduler started")
    
    def shutdown(self):
        """Shutdown the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Stock data scheduler stopped")
    
    def get_jobs(self):
        """Get list of scheduled jobs"""
        return self.scheduler.get_jobs()
