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
            api_provider: Provider name (alphavantage, finnhub, etc.)
        """
        self.api_key = api_key
        self.api_provider = api_provider
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
            symbol: Stock symbol (e.g., 'AAPL', 'GOOGL')
            
        Returns:
            Dictionary with quote data or None if error
        """
        try:
            if self.api_provider == 'alphavantage':
                params = {
                    'function': 'GLOBAL_QUOTE',
                    'symbol': symbol,
                    'apikey': self.api_key
                }
                response = requests.get(self.base_url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if 'Global Quote' in data and data['Global Quote']:
                    quote = data['Global Quote']
                    return {
                        'symbol': quote.get('01. symbol'),
                        'price': float(quote.get('05. price', 0)),
                        'volume': int(quote.get('06. volume', 0)),
                        'timestamp': quote.get('07. latest trading day'),
                        'change': float(quote.get('09. change', 0)),
                        'change_percent': quote.get('10. change percent', '0%')
                    }
                else:
                    logger.warning(f"No quote data found for {symbol}")
                    return None
            else:
                logger.error(f"Provider {self.api_provider} not implemented for quotes")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Error fetching quote for {symbol}: {e}")
            return None
        except (KeyError, ValueError) as e:
            logger.error(f"Error parsing quote data for {symbol}: {e}")
            return None
    
    def fetch_intraday(self, symbol: str, interval: str = '5min') -> Optional[List[Dict]]:
        """
        Fetch intraday time series data
        
        Args:
            symbol: Stock symbol
            interval: Time interval (1min, 5min, 15min, 30min, 60min)
            
        Returns:
            List of price data dictionaries or None if error
        """
        try:
            if self.api_provider == 'alphavantage':
                params = {
                    'function': 'TIME_SERIES_INTRADAY',
                    'symbol': symbol,
                    'interval': interval,
                    'apikey': self.api_key,
                    'outputsize': 'compact'  # Last 100 data points
                }
                response = requests.get(self.base_url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                time_series_key = f'Time Series ({interval})'
                if time_series_key in data:
                    prices = []
                    for timestamp, values in data[time_series_key].items():
                        prices.append({
                            'timestamp': timestamp,
                            'open': float(values.get('1. open', 0)),
                            'high': float(values.get('2. high', 0)),
                            'low': float(values.get('3. low', 0)),
                            'close': float(values.get('4. close', 0)),
                            'volume': int(values.get('5. volume', 0))
                        })
                    return prices
                else:
                    logger.warning(f"No intraday data found for {symbol}")
                    return None
            else:
                logger.error(f"Provider {self.api_provider} not implemented for intraday")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Error fetching intraday data for {symbol}: {e}")
            return None
        except (KeyError, ValueError) as e:
            logger.error(f"Error parsing intraday data for {symbol}: {e}")
            return None
    
    def fetch_daily(self, symbol: str, outputsize: str = 'compact') -> Optional[List[Dict]]:
        """
        Fetch daily time series data
        
        Args:
            symbol: Stock symbol
            outputsize: 'compact' (100 days) or 'full' (20+ years)
            
        Returns:
            List of price data dictionaries or None if error
        """
        try:
            if self.api_provider == 'alphavantage':
                params = {
                    'function': 'TIME_SERIES_DAILY',
                    'symbol': symbol,
                    'apikey': self.api_key,
                    'outputsize': outputsize
                }
                response = requests.get(self.base_url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if 'Time Series (Daily)' in data:
                    prices = []
                    for timestamp, values in data['Time Series (Daily)'].items():
                        prices.append({
                            'timestamp': timestamp,
                            'open': float(values.get('1. open', 0)),
                            'high': float(values.get('2. high', 0)),
                            'low': float(values.get('3. low', 0)),
                            'close': float(values.get('4. close', 0)),
                            'volume': int(values.get('5. volume', 0))
                        })
                    return prices
                else:
                    logger.warning(f"No daily data found for {symbol}")
                    return None
            else:
                logger.error(f"Provider {self.api_provider} not implemented for daily")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Error fetching daily data for {symbol}: {e}")
            return None
        except (KeyError, ValueError) as e:
            logger.error(f"Error parsing daily data for {symbol}: {e}")
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
                    name=name,
                    exchange=exchange
                )
                db.session.add(stock)
            
            db.session.commit()
            logger.info(f"Saved stock data for {symbol}")
            return stock
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving stock data for {symbol}: {e}")
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
                timestamp_str = price_data.get('timestamp')
                if isinstance(timestamp_str, str):
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    except ValueError:
                        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                else:
                    timestamp = timestamp_str
                
                # Check if price already exists
                existing = StockPrice.query.filter_by(
                    stock_id=stock.id,
                    timestamp=timestamp
                ).first()
                
                if not existing:
                    price = StockPrice(
                        stock_id=stock.id,
                        timestamp=timestamp,
                        open_price=price_data.get('open'),
                        high_price=price_data.get('high'),
                        low_price=price_data.get('low'),
                        close_price=price_data.get('close'),
                        volume=price_data.get('volume')
                    )
                    db.session.add(price)
                    saved_count += 1
            
            db.session.commit()
            logger.info(f"Saved {saved_count} price records for {symbol}")
            return saved_count
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving price data for {symbol}: {e}")
            return 0
    
    def import_stock_data(self, symbol: str, data_type: str = 'daily') -> bool:
        """
        Import stock data from external API and save to database
        
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
            
            # Fetch and save price data
            if data_type == 'quote':
                quote = self.fetch_quote(symbol)
                if quote:
                    prices = [{
                        'timestamp': quote['timestamp'],
                        'close': quote['price'],
                        'volume': quote['volume']
                    }]
                    self.save_price_data(symbol, prices)
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
            logger.error(f"Error importing stock data for {symbol}: {e}")
            return False
