"""Tests for OptionsService"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from services.options_service import OptionsService
from models import Stock, StockPrice, StockOption


class TestOptionsServiceInit:
    """Tests for OptionsService initialization"""
    
    def test_init(self):
        """Test OptionsService initialization"""
        service = OptionsService()
        assert service is not None


class TestOptionsServiceGetPriceHistory:
    """Tests for get_price_history method"""
    
    def test_get_price_history_success(self, app, db, sample_stock):
        """Test successful price history retrieval"""
        with app.app_context():
            # Add multiple price records
            for i in range(30):
                price = StockPrice(
                    stock_id=sample_stock.id,
                    timestamp=datetime(2024, 1, 1) + timedelta(days=i),
                    open_price=150.0 + i,
                    high_price=155.0 + i,
                    low_price=149.0 + i,
                    close_price=153.0 + i,
                    volume=1000000
                )
                db.session.add(price)
            db.session.commit()
            
            service = OptionsService()
            df = service.get_price_history('AAPL', days=60)
            
            assert df is not None
            assert isinstance(df, pd.DataFrame)
            assert len(df) == 30
            assert 'close' in df.columns
            assert 'open' in df.columns
            assert 'high' in df.columns
            assert 'low' in df.columns
            assert 'volume' in df.columns
    
    def test_get_price_history_stock_not_found(self, app, db):
        """Test price history retrieval for non-existent stock"""
        with app.app_context():
            service = OptionsService()
            df = service.get_price_history('INVALID', days=60)
            
            assert df is None
    
    def test_get_price_history_insufficient_data(self, app, db, sample_stock):
        """Test price history retrieval with insufficient data"""
        with app.app_context():
            # Add only 5 price records (less than minimum of 20)
            for i in range(5):
                price = StockPrice(
                    stock_id=sample_stock.id,
                    timestamp=datetime(2024, 1, 1) + timedelta(days=i),
                    open_price=150.0,
                    high_price=155.0,
                    low_price=149.0,
                    close_price=153.0,
                    volume=1000000
                )
                db.session.add(price)
            db.session.commit()
            
            service = OptionsService()
            df = service.get_price_history('AAPL', days=60)
            
            assert df is None
    
    def test_get_price_history_case_insensitive(self, app, db, sample_stock):
        """Test price history retrieval with different case symbols"""
        with app.app_context():
            # Add price records
            for i in range(25):
                price = StockPrice(
                    stock_id=sample_stock.id,
                    timestamp=datetime(2024, 1, 1) + timedelta(days=i),
                    open_price=150.0,
                    high_price=155.0,
                    low_price=149.0,
                    close_price=153.0,
                    volume=1000000
                )
                db.session.add(price)
            db.session.commit()
            
            service = OptionsService()
            df = service.get_price_history('aapl', days=60)  # lowercase
            
            assert df is not None
            assert len(df) == 25


class TestOptionsServiceCalculateRSI:
    """Tests for calculate_rsi method"""
    
    def test_calculate_rsi_success(self):
        """Test successful RSI calculation"""
        service = OptionsService()
        # Create sample price series
        prices = pd.Series([100, 102, 101, 103, 105, 104, 106, 108, 107, 109,
                           111, 110, 112, 114, 113, 115, 117, 116, 118, 120])
        
        rsi = service.calculate_rsi(prices)
        
        assert isinstance(rsi, float)
        assert 0 <= rsi <= 100
    
    def test_calculate_rsi_oversold(self):
        """Test RSI calculation with oversold prices"""
        service = OptionsService()
        # Downtrend prices
        prices = pd.Series([100, 99, 98, 97, 96, 95, 94, 93, 92, 91,
                           90, 89, 88, 87, 86, 85, 84, 83, 82, 81])
        
        rsi = service.calculate_rsi(prices)
        
        assert isinstance(rsi, float)
        assert rsi < 30  # Should be oversold
    
    def test_calculate_rsi_overbought(self):
        """Test RSI calculation with overbought prices"""
        service = OptionsService()
        # Uptrend prices
        prices = pd.Series([100, 101, 102, 103, 104, 105, 106, 107, 108, 109,
                           110, 111, 112, 113, 114, 115, 116, 117, 118, 119])
        
        rsi = service.calculate_rsi(prices)
        
        assert isinstance(rsi, float)
        assert rsi > 70  # Should be overbought
    
    def test_calculate_rsi_error_handling(self):
        """Test RSI calculation error handling"""
        service = OptionsService()
        # Empty series
        prices = pd.Series([])
        
        rsi = service.calculate_rsi(prices)
        
        assert rsi == 50.0  # Neutral value on error


class TestOptionsServiceCalculateMACD:
    """Tests for calculate_macd method"""
    
    def test_calculate_macd_success(self):
        """Test successful MACD calculation"""
        service = OptionsService()
        prices = pd.Series([100 + i for i in range(50)])
        
        macd, signal = service.calculate_macd(prices)
        
        assert isinstance(macd, float)
        assert isinstance(signal, float)
    
    def test_calculate_macd_bullish(self):
        """Test MACD calculation with bullish trend"""
        service = OptionsService()
        prices = pd.Series([100 + i*2 for i in range(50)])  # Strong uptrend
        
        macd, signal = service.calculate_macd(prices)
        
        assert macd > signal  # Bullish crossover
    
    def test_calculate_macd_bearish(self):
        """Test MACD calculation with bearish trend"""
        service = OptionsService()
        prices = pd.Series([200 - i*2 for i in range(50)])  # Strong downtrend
        
        macd, signal = service.calculate_macd(prices)
        
        assert macd < signal  # Bearish crossover
    
    def test_calculate_macd_error_handling(self):
        """Test MACD calculation error handling"""
        service = OptionsService()
        prices = pd.Series([])
        
        macd, signal = service.calculate_macd(prices)
        
        assert macd == 0.0
        assert signal == 0.0


class TestOptionsServiceCalculateVolatility:
    """Tests for calculate_volatility method"""
    
    def test_calculate_volatility_success(self):
        """Test successful volatility calculation"""
        service = OptionsService()
        prices = pd.Series([100 + i for i in range(50)])
        
        volatility = service.calculate_volatility(prices)
        
        assert isinstance(volatility, float)
        assert volatility >= 0
    
    def test_calculate_volatility_high_volatility(self):
        """Test volatility calculation with high volatility"""
        service = OptionsService()
        # Highly volatile prices
        prices = pd.Series([100, 110, 95, 115, 90, 120, 85, 125, 80, 130] * 5)
        
        volatility = service.calculate_volatility(prices)
        
        assert volatility > 10  # Should be high
    
    def test_calculate_volatility_low_volatility(self):
        """Test volatility calculation with low volatility"""
        service = OptionsService()
        # Stable prices
        prices = pd.Series([100.0 + i*0.01 for i in range(50)])
        
        volatility = service.calculate_volatility(prices)
        
        assert volatility < 5  # Should be low
    
    def test_calculate_volatility_error_handling(self):
        """Test volatility calculation error handling"""
        service = OptionsService()
        prices = pd.Series([])
        
        volatility = service.calculate_volatility(prices)
        
        assert volatility == 0.0


class TestOptionsServicePredictPriceMovement:
    """Tests for predict_price_movement method"""
    
    def test_predict_price_movement_success(self, app, db, sample_stock):
        """Test successful price movement prediction"""
        with app.app_context():
            # Add price history
            for i in range(60):
                price = StockPrice(
                    stock_id=sample_stock.id,
                    timestamp=datetime(2024, 1, 1) + timedelta(days=i),
                    open_price=150.0 + i*0.5,
                    high_price=155.0 + i*0.5,
                    low_price=149.0 + i*0.5,
                    close_price=153.0 + i*0.5,
                    volume=1000000
                )
                db.session.add(price)
            db.session.commit()
            
            service = OptionsService()
            df = service.get_price_history('AAPL', days=60)
            prediction = service.predict_price_movement(df)
            
            assert prediction is not None
            assert 'current_price' in prediction
            assert 'predicted_price' in prediction
            assert 'volatility' in prediction
            assert 'rsi' in prediction
            assert 'macd' in prediction
            assert 'bullish_probability' in prediction
            assert 'recommendation' in prediction
            assert 'confidence' in prediction
            assert 0 <= prediction['bullish_probability'] <= 1
            assert 0 <= prediction['confidence'] <= 1
            assert prediction['recommendation'] in ['buy', 'sell', 'hold']
    
    def test_predict_price_movement_bullish(self, app, db, sample_stock):
        """Test price movement prediction with bullish trend"""
        with app.app_context():
            # Add uptrend prices
            for i in range(60):
                price = StockPrice(
                    stock_id=sample_stock.id,
                    timestamp=datetime(2024, 1, 1) + timedelta(days=i),
                    open_price=150.0 + i*2,
                    high_price=155.0 + i*2,
                    low_price=149.0 + i*2,
                    close_price=153.0 + i*2,
                    volume=1000000
                )
                db.session.add(price)
            db.session.commit()
            
            service = OptionsService()
            df = service.get_price_history('AAPL', days=60)
            prediction = service.predict_price_movement(df)
            
            assert prediction is not None
            assert prediction['bullish_probability'] > 0.5
    
    def test_predict_price_movement_bearish(self, app, db, sample_stock):
        """Test price movement prediction with bearish trend"""
        with app.app_context():
            # Add downtrend prices
            for i in range(60):
                price = StockPrice(
                    stock_id=sample_stock.id,
                    timestamp=datetime(2024, 1, 1) + timedelta(days=i),
                    open_price=250.0 - i*2,
                    high_price=255.0 - i*2,
                    low_price=249.0 - i*2,
                    close_price=253.0 - i*2,
                    volume=1000000
                )
                db.session.add(price)
            db.session.commit()
            
            service = OptionsService()
            df = service.get_price_history('AAPL', days=60)
            prediction = service.predict_price_movement(df)
            
            assert prediction is not None
            assert prediction['bullish_probability'] < 0.5


class TestOptionsServiceGenerateOptionExplanation:
    """Tests for generate_option_explanation method"""
    
    def test_generate_explanation_strong_factors(self):
        """Test explanation generation with strong factors"""
        service = OptionsService()
        breakdown = {
            'liquidity': 18.0,
            'spread': 16.0,
            'moneyness': 10.0,
            'expiration': 12.0,
            'momentum': 8.0,
            'data_quality': 10.0
        }
        warnings = []
        
        explanation = service.generate_option_explanation(breakdown, warnings)
        
        assert isinstance(explanation, str)
        assert len(explanation) > 0
        assert 'liquidity' in explanation.lower() or 'spread' in explanation.lower()
    
    def test_generate_explanation_weak_factors(self):
        """Test explanation generation with weak factors"""
        service = OptionsService()
        breakdown = {
            'liquidity': 3.0,
            'spread': 2.0,
            'moneyness': 5.0,
            'expiration': 4.0,
            'momentum': 2.0,
            'data_quality': 3.0
        }
        warnings = ['low_volume', 'wide_spread']
        
        explanation = service.generate_option_explanation(breakdown, warnings)
        
        assert isinstance(explanation, str)
        assert len(explanation) > 0
        assert 'limited' in explanation.lower() or 'reduced' in explanation.lower()
    
    def test_generate_explanation_with_warnings(self):
        """Test explanation generation with warnings"""
        service = OptionsService()
        breakdown = {
            'liquidity': 10.0,
            'spread': 10.0,
            'moneyness': 10.0,
            'expiration': 10.0,
            'momentum': 10.0,
            'data_quality': 5.0
        }
        warnings = ['missing_iv', 'missing_data']
        
        explanation = service.generate_option_explanation(breakdown, warnings)
        
        assert isinstance(explanation, str)
        assert len(explanation) > 0
        assert 'confidence' in explanation.lower() or 'missing' in explanation.lower()
    
    def test_generate_explanation_empty_breakdown(self):
        """Test explanation generation with empty breakdown"""
        service = OptionsService()
        breakdown = {}
        warnings = []
        
        explanation = service.generate_option_explanation(breakdown, warnings)
        
        assert isinstance(explanation, str)
        assert 'missing' in explanation.lower() or 'unable' in explanation.lower()
    
    def test_generate_explanation_none_values(self):
        """Test explanation generation with None values in breakdown"""
        service = OptionsService()
        breakdown = {
            'liquidity': None,
            'spread': 15.0,
            'moneyness': None,
            'expiration': 12.0,
            'momentum': 8.0,
            'data_quality': None
        }
        warnings = []
        
        explanation = service.generate_option_explanation(breakdown, warnings)
        
        assert isinstance(explanation, str)
        assert len(explanation) > 0
    
    def test_generate_explanation_mixed_factors(self):
        """Test explanation generation with mixed strong and weak factors"""
        service = OptionsService()
        breakdown = {
            'liquidity': 18.0,
            'spread': 3.0,
            'moneyness': 14.0,
            'expiration': 5.0,
            'momentum': 12.0,
            'data_quality': 10.0
        }
        warnings = ['wide_spread']
        
        explanation = service.generate_option_explanation(breakdown, warnings)
        
        assert isinstance(explanation, str)
        assert len(explanation) > 0
        # Should mention both positives and negatives
        assert 'however' in explanation.lower() or 'but' in explanation.lower() or 'reduced' in explanation.lower()
