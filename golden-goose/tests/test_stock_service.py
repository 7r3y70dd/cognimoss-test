"""Tests for StockService"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from services.stock_service import StockService
from models import Stock, StockPrice


class TestStockServiceInit:
    """Tests for StockService initialization"""
    
    def test_init_alphavantage(self):
        """Test initialization with AlphaVantage provider"""
        service = StockService('test_key', 'alphavantage')
        assert service.api_key == 'test_key'
        assert service.api_provider == 'alphavantage'
        assert service.base_url == 'https://www.alphavantage.co/query'
    
    def test_init_finnhub(self):
        """Test initialization with Finnhub provider"""
        service = StockService('test_key', 'finnhub')
        assert service.api_key == 'test_key'
        assert service.api_provider == 'finnhub'
        assert service.base_url == 'https://finnhub.io/api/v1'
    
    def test_init_invalid_provider(self):
        """Test initialization with invalid provider"""
        with pytest.raises(ValueError):
            StockService('test_key', 'invalid_provider')


class TestStockServiceFetchQuote:
    """Tests for fetch_quote method"""
    
    @patch('services.stock_service.requests.get')
    def test_fetch_quote_success(self, mock_get):
        """Test successful quote fetch"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'Global Quote': {
                '01. symbol': 'AAPL',
                '05. price': '150.00',
                '06. volume': '1000000',
                '07. latest trading day': '2024-01-01',
                '09. change': '2.50',
                '10. change percent': '1.69%'
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        service = StockService('test_key', 'alphavantage')
        quote = service.fetch_quote('AAPL')
        
        assert quote is not None
        assert quote['symbol'] == 'AAPL'
        assert quote['price'] == 150.00
        assert quote['volume'] == 1000000
        assert quote['timestamp'] == '2024-01-01'
    
    @patch('services.stock_service.requests.get')
    def test_fetch_quote_empty_response(self, mock_get):
        """Test quote fetch with empty response"""
        mock_response = Mock()
        mock_response.json.return_value = {'Global Quote': {}}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        service = StockService('test_key', 'alphavantage')
        quote = service.fetch_quote('INVALID')
        
        assert quote is None
    
    @patch('services.stock_service.requests.get')
    def test_fetch_quote_request_error(self, mock_get):
        """Test quote fetch with request error"""
        mock_get.side_effect = Exception('Network error')
        
        service = StockService('test_key', 'alphavantage')
        quote = service.fetch_quote('AAPL')
        
        assert quote is None


class TestStockServiceFetchIntraday:
    """Tests for fetch_intraday method"""
    
    @patch('services.stock_service.requests.get')
    def test_fetch_intraday_success(self, mock_get):
        """Test successful intraday fetch"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'Time Series (5min)': {
                '2024-01-01 16:00:00': {
                    '1. open': '150.00',
                    '2. high': '151.00',
                    '3. low': '149.50',
                    '4. close': '150.50',
                    '5. volume': '100000'
                },
                '2024-01-01 15:55:00': {
                    '1. open': '149.00',
                    '2. high': '150.00',
                    '3. low': '148.50',
                    '4. close': '149.75',
                    '5. volume': '95000'
                }
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        service = StockService('test_key', 'alphavantage')
        prices = service.fetch_intraday('AAPL', '5min')
        
        assert prices is not None
        assert len(prices) == 2
        assert prices[0]['close'] == 150.50
        assert prices[1]['close'] == 149.75
    
    @patch('services.stock_service.requests.get')
    def test_fetch_intraday_empty_response(self, mock_get):
        """Test intraday fetch with empty response"""
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        service = StockService('test_key', 'alphavantage')
        prices = service.fetch_intraday('INVALID')
        
        assert prices is None


class TestStockServiceFetchDaily:
    """Tests for fetch_daily method"""
    
    @patch('services.stock_service.requests.get')
    def test_fetch_daily_success(self, mock_get):
        """Test successful daily fetch"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'Time Series (Daily)': {
                '2024-01-02': {
                    '1. open': '151.00',
                    '2. high': '153.00',
                    '3. low': '150.00',
                    '4. close': '152.00',
                    '5. volume': '5000000'
                },
                '2024-01-01': {
                    '1. open': '150.00',
                    '2. high': '151.00',
                    '3. low': '149.00',
                    '4. close': '150.50',
                    '5. volume': '4500000'
                }
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        service = StockService('test_key', 'alphavantage')
        prices = service.fetch_daily('AAPL')
        
        assert prices is not None
        assert len(prices) == 2
        assert prices[0]['close'] == 152.00
        assert prices[1]['close'] == 150.50


class TestStockServiceSaveData:
    """Tests for save_stock_data and save_price_data methods"""
    
    def test_save_stock_data_new(self, app, db):
        """Test saving new stock data"""
        with app.app_context():
            service = StockService('test_key', 'alphavantage')
            stock = service.save_stock_data('TSLA', 'Tesla Inc.', 'NASDAQ')
            
            assert stock is not None
            assert stock.symbol == 'TSLA'
            assert stock.name == 'Tesla Inc.'
            assert stock.exchange == 'NASDAQ'
    
    def test_save_stock_data_update(self, app, db, sample_stock):
        """Test updating existing stock data"""
        with app.app_context():
            service = StockService('test_key', 'alphavantage')
            stock = service.save_stock_data('AAPL', 'Apple Inc. Updated', 'NASDAQ')
            
            assert stock is not None
            assert stock.symbol == 'AAPL'
            assert stock.name == 'Apple Inc. Updated'
    
    def test_save_price_data(self, app, db, sample_stock):
        """Test saving price data"""
        with app.app_context():
            service = StockService('test_key', 'alphavantage')
            prices = [
                {
                    'timestamp': '2024-01-02',
                    'open': 151.0,
                    'high': 153.0,
                    'low': 150.0,
                    'close': 152.0,
                    'volume': 5000000
                },
                {
                    'timestamp': '2024-01-03',
                    'open': 152.0,
                    'high': 154.0,
                    'low': 151.0,
                    'close': 153.0,
                    'volume': 5500000
                }
            ]
            
            count = service.save_price_data('AAPL', prices)
            assert count == 2
            
            saved_prices = StockPrice.query.filter_by(stock_id=sample_stock.id).all()
            assert len(saved_prices) == 2
    
    def test_save_price_data_duplicate(self, app, db, sample_stock, sample_stock_price):
        """Test saving duplicate price data (should skip)"""
        with app.app_context():
            service = StockService('test_key', 'alphavantage')
            prices = [
                {
                    'timestamp': datetime(2024, 1, 1, 12, 0, 0),
                    'close': 160.0,  # Different price, same timestamp
                    'volume': 2000000
                }
            ]
            
            count = service.save_price_data('AAPL', prices)
            assert count == 0  # Should not save duplicate
    
    def test_save_price_data_stock_not_found(self, app, db):
        """Test saving price data for non-existent stock"""
        with app.app_context():
            service = StockService('test_key', 'alphavantage')
            prices = [{'timestamp': '2024-01-01', 'close': 100.0}]
            
            count = service.save_price_data('INVALID', prices)
            assert count == 0


class TestStockServiceImportData:
    """Tests for import_stock_data method"""
    
    @patch.object(StockService, 'fetch_quote')
    @patch.object(StockService, 'save_stock_data')
    @patch.object(StockService, 'save_price_data')
    def test_import_quote_data(self, mock_save_price, mock_save_stock, mock_fetch_quote, app, db):
        """Test importing quote data"""
        with app.app_context():
            mock_stock = Mock()
            mock_stock.symbol = 'AAPL'
            mock_save_stock.return_value = mock_stock
            mock_fetch_quote.return_value = {
                'timestamp': '2024-01-01',
                'price': 150.0,
                'volume': 1000000
            }
            mock_save_price.return_value = 1
            
            service = StockService('test_key', 'alphavantage')
            result = service.import_stock_data('AAPL', 'quote')
            
            assert result is True
            mock_save_stock.assert_called_once_with('AAPL')
            mock_fetch_quote.assert_called_once_with('AAPL')
    
    @patch.object(StockService, 'fetch_daily')
    @patch.object(StockService, 'save_stock_data')
    @patch.object(StockService, 'save_price_data')
    def test_import_daily_data(self, mock_save_price, mock_save_stock, mock_fetch_daily, app, db):
        """Test importing daily data"""
        with app.app_context():
            mock_stock = Mock()
            mock_stock.symbol = 'AAPL'
            mock_save_stock.return_value = mock_stock
            mock_fetch_daily.return_value = [
                {'timestamp': '2024-01-01', 'close': 150.0}
            ]
            mock_save_price.return_value = 1
            
            service = StockService('test_key', 'alphavantage')
            result = service.import_stock_data('AAPL', 'daily')
            
            assert result is True
            mock_fetch_daily.assert_called_once_with('AAPL')
