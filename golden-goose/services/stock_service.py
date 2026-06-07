"""Stock service for fetching and managing stock market data"""

import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from app import db
from models import Stock, StockPrice

logger = logging.getLogger(__name__)

class StockService:
    """Service for interacting with stock market data APIs"""
    
    def __init__(self, api_key: str, api_provider: str = 'alphavantage'):
        """
        Initialize stock service
        
        Args:
            api_key: API key for the stock data provider
            api_provider: Provider name (alphavantage or finnhub)
        """
        self.api_key = api_key
        self.api_provider = api_provider.lower()
        self.base_url = self._get_base_url()
        
    def _get_base_url(self) -> str:
        """Get base URL for the API provider"""
        if self.api_provider == 'alphavantage':
            return 'https://www.alphavantage.co/query'
        elif self.api_provider == 'finnhub':
            return 'https://finnhub.io/api/v1'
        else:
            raise ValueError(f"Unsupported API provider: {self.api_provider}")
    
    def fetch_quote(self, symbol: str) -> Optional[Dict]:
        """
        Fetch current quote for a stock symbol
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            
        Returns:
            Dictionary with quote data or None if error
        """
        try:
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'Global Quote' not in data or not data['Global Quote']:
                logger.warning(f"No quote data found for {symbol}")
                return None
            
            quote = data['Global Quote']
            return {
                'symbol': quote.get('01. symbol'),
                'price': float(quote.get('05. price', 0)),
                'volume': int(quote.get('06. volume', 0)),
                'timestamp': quote.get('07. latest trading day'),
                'change': float(quote.get('09. change', 0)),
                'change_percent': quote.get('10. change percent', '0%')
            }
        except Exception as e:
            logger.error(f"Error fetching quote for {symbol}: {str(e)}")
            return None
    
    def fetch_intraday(self, symbol: str, interval: str = '5min') -> Optional[List[Dict]]:
        """
        Fetch intraday price data for a stock symbol
        
        Args:
            symbol: Stock symbol
            interval: Time interval (1min, 5min, 15min, 30min, 60min)
            
        Returns:
            List of price dictionaries or None if error
        """
        try:
            params = {
                'function': 'TIME_SERIES_INTRADAY',
                'symbol': symbol,
                'interval': interval,
                'apikey': self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            time_series_key = f'Time Series ({interval})'
            if time_series_key not in data:
                logger.warning(f"No intraday data found for {symbol}")
                return None
            
            prices = []
            for timestamp, values in data[time_series_key].items():
                prices.append({
                    'timestamp': timestamp,
                    'open': float(values['1. open']),
                    'high': float(values['2. high']),
                    'low': float(values['3. low']),
                    'close': float(values['4. close']),
                    'volume': int(values['5. volume'])
                })
            
            return prices
        except Exception as e:
            logger.error(f"Error fetching intraday data for {symbol}: {str(e)}")
            return None
    
    def fetch_daily(self, symbol: str, outputsize: str = 'compact') -> Optional[List[Dict]]:
        """
        Fetch daily price data for a stock symbol
        
        Args:
            symbol: Stock symbol
            outputsize: 'compact' (100 days) or 'full' (20+ years)
            
        Returns:
            List of price dictionaries or None if error
        """
        try:
            params = {
                'function': 'TIME_SERIES_DAILY',
                'symbol': symbol,
                'outputsize': outputsize,
                'apikey': self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'Time Series (Daily)' not in data:
                logger.warning(f"No daily data found for {symbol}")
                return None
            
            prices = []
            for timestamp, values in data['Time Series (Daily)'].items():
                prices.append({
                    'timestamp': timestamp,
                    'open': float(values['1. open']),
                    'high': float(values['2. high']),
                    'low': float(values['3. low']),
                    'close': float(values['4. close']),
                    'volume': int(values['5. volume'])
                })
            
            return prices
        except Exception as e:
            logger.error(f"Error fetching daily data for {symbol}: {str(e)}")
            return None
    
    def save_stock_data(self, symbol: str, name: str = None, exchange: str = None) -> Optional[Stock]:
        """
        Save or update stock information in database
        
        Args:
            symbol: Stock symbol
            name: Company name
            exchange: Exchange name
            
        Returns:
            Stock object or None if error
        """
        try:
            stock = Stock.query.filter_by(symbol=symbol).first()
            
            if stock:
                # Update existing stock
                if name:
                    stock.name = name
                if exchange:
                    stock.exchange = exchange
                stock.updated_at = datetime.utcnow()
            else:
                # Create new stock
                stock = Stock(
                    symbol=symbol,
                    name=name or symbol,
                    exchange=exchange or 'UNKNOWN'
                )
                db.session.add(stock)
            
            db.session.commit()
            return stock
        except Exception as e:
            logger.error(f"Error saving stock data for {symbol}: {str(e)}")
            db.session.rollback()
            return None
    
    def save_price_data(self, symbol: str, prices: List[Dict]) -> int:
        """
        Save price data to database
        
        Args:
            symbol: Stock symbol
            prices: List of price dictionaries
            
        Returns:
            Number of prices saved
        """
        try:
            stock = Stock.query.filter_by(symbol=symbol).first()
            if not stock:
                logger.error(f"Stock {symbol} not found in database")
                return 0
            
            saved_count = 0
            for price_data in prices:
                # Parse timestamp
                if isinstance(price_data['timestamp'], str):
                    timestamp = datetime.strptime(price_data['timestamp'], '%Y-%m-%d')
                else:
                    timestamp = price_data['timestamp']
                
                # Check if price already exists
                existing = StockPrice.query.filter_by(
                    stock_id=stock.id,
                    timestamp=timestamp
                ).first()
                
                if existing:
                    continue
                
                # Create new price record
                price = StockPrice(
                    stock_id=stock.id,
                    timestamp=timestamp,
                    open_price=price_data.get('open'),
                    high_price=price_data.get('high'),
                    low_price=price_data.get('low'),
                    close_price=price_data.get('close', price_data.get('price')),
                    volume=price_data.get('volume')
                )
                db.session.add(price)
                saved_count += 1
            
            db.session.commit()
            return saved_count
        except Exception as e:
            logger.error(f"Error saving price data for {symbol}: {str(e)}")
            db.session.rollback()
            return 0
    
    def import_stock_data(self, symbol: str, data_type: str = 'quote') -> bool:
        """
        Import stock data from API and save to database
        
        Args:
            symbol: Stock symbol
            data_type: Type of data to import ('quote', 'intraday', 'daily')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure stock exists in database
            stock = self.save_stock_data(symbol)
            if not stock:
                return False
            
            # Fetch and save data based on type
            if data_type == 'quote':
                quote = self.fetch_quote(symbol)
                if quote:
                    self.save_price_data(symbol, [quote])
                    return True
            elif data_type == 'intraday':
                prices = self.fetch_intraday(symbol)
                if prices:
                    self.save_price_data(symbol, prices)
                    return True
            elif data_type == 'daily':
                prices = self.fetch_daily(symbol)
                if prices:
                    self.save_price_data(symbol, prices)
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error importing {data_type} data for {symbol}: {str(e)}")
            return False
