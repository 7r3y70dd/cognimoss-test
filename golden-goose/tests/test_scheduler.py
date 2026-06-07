"""Tests for the stock data scheduler"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scheduler import StockDataScheduler
from models import Stock


class TestStockDataSchedulerInitialization:
    """Test scheduler initialization"""
    
    def test_scheduler_init_without_app(self):
        """Test scheduler can be initialized without Flask app"""
        scheduler = StockDataScheduler()
        assert scheduler.app is None
        assert scheduler.stock_service is None
        assert isinstance(scheduler.scheduler, BackgroundScheduler)
    
    def test_scheduler_init_with_app(self, app):
        """Test scheduler initialization with Flask app"""
        scheduler = StockDataScheduler(app)
        assert scheduler.app == app
        # Stock service may be None if no API key configured
        assert scheduler.scheduler is not None
    
    def test_init_app_with_api_key(self, app):
        """Test init_app with valid API key"""
        app.config['STOCK_API_KEY'] = 'test_key_123'
        app.config['STOCK_API_PROVIDER'] = 'alphavantage'
        
        scheduler = StockDataScheduler()
        scheduler.init_app(app)
        
        assert scheduler.app == app
        assert scheduler.stock_service is not None
    
    def test_init_app_without_api_key(self, app):
        """Test init_app without API key logs warning"""
        app.config['STOCK_API_KEY'] = None
        
        scheduler = StockDataScheduler()
        
        with patch('scheduler.logger') as mock_logger:
            scheduler.init_app(app)
            mock_logger.warning.assert_called_once()
            assert scheduler.stock_service is None
    
    def test_init_app_with_custom_provider(self, app):
        """Test init_app with custom API provider"""
        app.config['STOCK_API_KEY'] = 'test_key'
        app.config['STOCK_API_PROVIDER'] = 'finnhub'
        
        scheduler = StockDataScheduler()
        scheduler.init_app(app)
        
        assert scheduler.stock_service is not None
        assert scheduler.stock_service.api_provider == 'finnhub'


class TestSchedulerJobRegistration:
    """Test job registration in scheduler"""
    
    def test_start_registers_three_jobs(self, app):
        """Test that start() registers exactly three jobs"""
        app.config['STOCK_API_KEY'] = 'test_key'
        scheduler = StockDataScheduler(app)
        
        # Mock the BackgroundScheduler to prevent actual scheduling
        scheduler.scheduler.start = Mock()
        scheduler.scheduler.add_job = Mock()
        
        scheduler.start()
        
        # Verify three jobs were added
        assert scheduler.scheduler.add_job.call_count == 3
    
    def test_start_registers_quotes_job(self, app):
        """Test that quotes import job is registered with correct trigger"""
        app.config['STOCK_API_KEY'] = 'test_key'
        scheduler = StockDataScheduler(app)
        
        scheduler.scheduler.start = Mock()
        scheduler.scheduler.add_job = Mock()
        
        scheduler.start()
        
        # Find the quotes job call
        calls = scheduler.scheduler.add_job.call_args_list
        quotes_call = [c for c in calls if c[1].get('id') == 'import_quotes'][0]
        
        assert quotes_call[1]['id'] == 'import_quotes'
        assert quotes_call[1]['name'] == 'Import stock quotes'
        assert isinstance(quotes_call[1]['trigger'], IntervalTrigger)
    
    def test_start_registers_daily_job(self, app):
        """Test that daily import job is registered with correct trigger"""
        app.config['STOCK_API_KEY'] = 'test_key'
        scheduler = StockDataScheduler(app)
        
        scheduler.scheduler.start = Mock()
        scheduler.scheduler.add_job = Mock()
        
        scheduler.start()
        
        # Find the daily job call
        calls = scheduler.scheduler.add_job.call_args_list
        daily_call = [c for c in calls if c[1].get('id') == 'import_daily'][0]
        
        assert daily_call[1]['id'] == 'import_daily'
        assert daily_call[1]['name'] == 'Import daily stock data'
        assert isinstance(daily_call[1]['trigger'], CronTrigger)
    
    def test_start_registers_intraday_job(self, app):
        """Test that intraday import job is registered with correct trigger"""
        app.config['STOCK_API_KEY'] = 'test_key'
        scheduler = StockDataScheduler(app)
        
        scheduler.scheduler.start = Mock()
        scheduler.scheduler.add_job = Mock()
        
        scheduler.start()
        
        # Find the intraday job call
        calls = scheduler.scheduler.add_job.call_args_list
        intraday_call = [c for c in calls if c[1].get('id') == 'import_intraday'][0]
        
        assert intraday_call[1]['id'] == 'import_intraday'
        assert intraday_call[1]['name'] == 'Import intraday stock data'
        assert isinstance(intraday_call[1]['trigger'], IntervalTrigger)
    
    def test_start_calls_scheduler_start(self, app):
        """Test that start() calls scheduler.start()"""
        app.config['STOCK_API_KEY'] = 'test_key'
        scheduler = StockDataScheduler(app)
        
        scheduler.scheduler.start = Mock()
        scheduler.scheduler.add_job = Mock()
        
        scheduler.start()
        
        scheduler.scheduler.start.assert_called_once()
    
    def test_start_without_app_logs_error(self):
        """Test that start() without app logs error"""
        scheduler = StockDataScheduler()
        
        with patch('scheduler.logger') as mock_logger:
            scheduler.start()
            mock_logger.error.assert_called_once()


class TestSchedulerServiceCalls:
    """Test that scheduler calls correct service methods"""
    
    def test_import_stock_quotes_calls_service(self, app, db, sample_stock):
        """Test that import_stock_quotes calls stock service"""
        app.config['STOCK_API_KEY'] = 'test_key'
        scheduler = StockDataScheduler(app)
        
        # Mock the stock service
        mock_service = Mock()
        mock_service.import_stock_data = Mock(return_value=True)
        scheduler.stock_service = mock_service
        
        with app.app_context():
            scheduler.import_stock_quotes()
        
        # Verify service was called
        mock_service.import_stock_data.assert_called()
    
    def test_import_stock_quotes_iterates_all_stocks(self, app, db, multiple_stocks):
        """Test that import_stock_quotes processes all tracked stocks"""
        app.config['STOCK_API_KEY'] = 'test_key'
        scheduler = StockDataScheduler(app)
        
        mock_service = Mock()
        mock_service.import_stock_data = Mock(return_value=True)
        scheduler.stock_service = mock_service
        
        with app.app_context():
            scheduler.import_stock_quotes()
        
        # Should be called once for each stock
        assert mock_service.import_stock_data.call_count == len(multiple_stocks)
    
    def test_import_stock_quotes_calls_with_quote_type(self, app, db, sample_stock):
        """Test that import_stock_quotes calls service with 'quote' type"""
        app.config['STOCK_API_KEY'] = 'test_key'
        scheduler = StockDataScheduler(app)
        
        mock_service = Mock()
        mock_service.import_stock_data = Mock(return_value=True)
        scheduler.stock_service = mock_service
        
        with app.app_context():
            scheduler.import_stock_quotes()
        
        # Verify 'quote' type was passed
        mock_service.import_stock_data.assert_called_with(sample_stock.symbol, 'quote')
    
    def test_import_stock_daily_calls_service(self, app, db, sample_stock):
        """Test that import_stock_daily calls stock service"""
        app.config['STOCK_API_KEY'] = 'test_key'
        scheduler = StockDataScheduler(app)
        
        mock_service = Mock()
        mock_service.import_stock_data = Mock(return_value=True)
        scheduler.stock_service = mock_service
        
        with app.app_context():
            scheduler.import_stock_daily()
        
        mock_service.import_stock_data.assert_called()
    
    def test_import_stock_daily_calls_with_daily_type(self, app, db, sample_stock):
        """Test that import_stock_daily calls service with 'daily' type"""
        app.config['STOCK_API_KEY'] = 'test_key'
        scheduler = StockDataScheduler(app)
        
        mock_service = Mock()
        mock_service.import_stock_data = Mock(return_value=True)
        scheduler.stock_service = mock_service
        
        with app.app_context():
            scheduler.import_stock_daily()
        
        mock_service.import_stock_data.assert_called_with(sample_stock.symbol, 'daily')
    
    def test_import_stock_intraday_calls_service(self, app, db, sample_stock):
        """Test that import_stock_intraday calls stock service"""
        app.config['STOCK_API_KEY'] = 'test_key'
        scheduler = StockDataScheduler(app)
        
        mock_service = Mock()
        mock_service.import_stock_data = Mock(return_value=True)
        scheduler.stock_service = mock_service
        
        with app.app_context():
            scheduler.import_stock_intraday()
        
        mock_service.import_stock_data.assert_called()
    
    def test_import_stock_intraday_calls_with_intraday_type(self, app, db, sample_stock):
        """Test that import_stock_intraday calls service with 'intraday' type"""
        app.config['STOCK_API_KEY'] = 'test_key'
        scheduler = StockDataScheduler(app)
        
        mock_service = Mock()
        mock_service.import_stock_data = Mock(return_value=True)
        scheduler.stock_service = mock_service
        
        with app.app_context():
            scheduler.import_stock_intraday()
        
        mock_service.import_stock_data.assert_called_with(sample_stock.symbol, 'intraday')


class TestSchedulerFailureHandling:
    """Test graceful handling of service failures"""
    
    def test_import_quotes_handles_missing_service(self, app, db, sample_stock):
        """Test import_stock_quotes handles missing service gracefully"""
        app.config['STOCK_API_KEY'] = None
        scheduler = StockDataScheduler(app)
        
        with patch('scheduler.logger') as mock_logger:
            with app.app_context():
                scheduler.import_stock_quotes()
            
            # Should log error but not raise exception
            mock_logger.error.assert_called()
    
    def test_import_daily_handles_missing_service(self, app, db, sample_stock):
        """Test import_stock_daily handles missing service gracefully"""
        app.config['STOCK_API_KEY'] = None
        scheduler = StockDataScheduler(app)
        
        with patch('scheduler.logger') as mock_logger:
            with app.app_context():
                scheduler.import_stock_daily()
            
            mock_logger.error.assert_called()
    
    def test_import_intraday_handles_missing_service(self, app, db, sample_stock):
        """Test import_stock_intraday handles missing service gracefully"""
        app.config['STOCK_API_KEY'] = None
        scheduler = StockDataScheduler(app)
        
        with patch('scheduler.logger') as mock_logger:
            with app.app_context():
                scheduler.import_stock_intraday()
            
            mock_logger.error.assert_called()
    
    def test_import_quotes_handles_service_exception(self, app, db, sample_stock):
        """Test import_stock_quotes handles service exceptions"""
        app.config['STOCK_API_KEY'] = 'test_key'
        scheduler = StockDataScheduler(app)
        
        mock_service = Mock()
        mock_service.import_stock_data = Mock(side_effect=Exception('API Error'))
        scheduler.stock_service = mock_service
        
        with patch('scheduler.logger') as mock_logger:
            with app.app_context():
                # Should not raise exception
                scheduler.import_stock_quotes()
            
            # Should log error
            mock_logger.error.assert_called()
    
    def test_import_daily_handles_service_exception(self, app, db, sample_stock):
        """Test import_stock_daily handles service exceptions"""
        app.config['STOCK_API_KEY'] = 'test_key'
        scheduler = StockDataScheduler(app)
        
        mock_service = Mock()
        mock_service.import_stock_data = Mock(side_effect=Exception('API Error'))
        scheduler.stock_service = mock_service
        
        with patch('scheduler.logger') as mock_logger:
            with app.app_context():
                scheduler.import_stock_daily()
            
            mock_logger.error.assert_called()
    
    def test_import_intraday_handles_service_exception(self, app, db, sample_stock):
        """Test import_stock_intraday handles service exceptions"""
        app.config['STOCK_API_KEY'] = 'test_key'
        scheduler = StockDataScheduler(app)
        
        mock_service = Mock()
        mock_service.import_stock_data = Mock(side_effect=Exception('API Error'))
        scheduler.stock_service = mock_service
        
        with patch('scheduler.logger') as mock_logger:
            with app.app_context():
                scheduler.import_stock_intraday()
            
            mock_logger.error.assert_called()
    
    def test_import_quotes_handles_failed_import(self, app, db, sample_stock):
        """Test import_stock_quotes handles failed imports"""
        app.config['STOCK_API_KEY'] = 'test_key'
        scheduler = StockDataScheduler(app)
        
        mock_service = Mock()
        mock_service.import_stock_data = Mock(return_value=False)
        scheduler.stock_service = mock_service
        
        with patch('scheduler.logger') as mock_logger:
            with app.app_context():
                scheduler.import_stock_quotes()
            
            # Should log warning for failed import
            mock_logger.warning.assert_called()


class TestSchedulerShutdown:
    """Test scheduler shutdown behavior"""
    
    def test_shutdown_stops_running_scheduler(self, app):
        """Test shutdown stops the scheduler"""
        app.config['STOCK_API_KEY'] = 'test_key'
        scheduler = StockDataScheduler(app)
        
        # Mock scheduler as running
        scheduler.scheduler.running = True
        scheduler.scheduler.shutdown = Mock()
        
        scheduler.shutdown()
        
        scheduler.scheduler.shutdown.assert_called_once()
    
    def test_shutdown_does_not_error_if_not_running(self, app):
        """Test shutdown handles non-running scheduler gracefully"""
        app.config['STOCK_API_KEY'] = 'test_key'
        scheduler = StockDataScheduler(app)
        
        scheduler.scheduler.running = False
        scheduler.scheduler.shutdown = Mock()
        
        # Should not raise exception
        scheduler.shutdown()
        
        # Shutdown should not be called if not running
        scheduler.scheduler.shutdown.assert_not_called()
    
    def test_shutdown_logs_message(self, app):
        """Test shutdown logs appropriate message"""
        app.config['STOCK_API_KEY'] = 'test_key'
        scheduler = StockDataScheduler(app)
        
        scheduler.scheduler.running = True
        scheduler.scheduler.shutdown = Mock()
        
        with patch('scheduler.logger') as mock_logger:
            scheduler.shutdown()
            mock_logger.info.assert_called()


class TestSchedulerGetJobs:
    """Test get_jobs method"""
    
    def test_get_jobs_returns_list(self, app):
        """Test get_jobs returns list of jobs"""
        app.config['STOCK_API_KEY'] = 'test_key'
        scheduler = StockDataScheduler(app)
        
        mock_jobs = [Mock(), Mock()]
        scheduler.scheduler.get_jobs = Mock(return_value=mock_jobs)
        
        jobs = scheduler.get_jobs()
        
        assert jobs == mock_jobs
    
    def test_get_jobs_returns_empty_list_when_no_jobs(self, app):
        """Test get_jobs returns empty list when no jobs scheduled"""
        app.config['STOCK_API_KEY'] = 'test_key'
        scheduler = StockDataScheduler(app)
        
        scheduler.scheduler.get_jobs = Mock(return_value=[])
        
        jobs = scheduler.get_jobs()
        
        assert jobs == []
