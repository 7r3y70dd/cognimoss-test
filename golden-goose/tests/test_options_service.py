"""Tests for options service"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np
from services.options_service import OptionsService, OptionsSignalService
from models import Stock, StockPrice, StockOption


class TestOptionsService:
    """Tests for OptionsService"""
    
    def test_init(self):
        """Test OptionsService initialization"""
        service = OptionsService()
        assert service is not None
    
    def test_get_price_history_success(self, sample_stock, db):
        """Test successful price history retrieval"""
        service = OptionsService()
        
        # Add sample prices
        for i in range(30):
            price = StockPrice(
                stock_id=sample_stock.id,
                timestamp=datetime.utcnow() - timedelta(days=30-i),
                open_price=100.0 + i,
                high_price=101.0 + i,
                low_price=99.0 + i,
                close_price=100.5 + i,
                volume=1000000
            )
            db.session.add(price)
        db.session.commit()
        
        df = service.get_price_history(sample_stock.symbol)
        assert df is not None
        assert len(df) == 30
        assert 'close' in df.columns
    
    def test_get_price_history_not_found(self):
        """Test price history retrieval for non-existent stock"""
        service = OptionsService()
        df = service.get_price_history('NONEXISTENT')
        assert df is None
    
    def test_get_price_history_insufficient_data(self, sample_stock, db):
        """Test price history retrieval with insufficient data"""
        service = OptionsService()
        
        # Add only 10 prices (less than minimum of 20)
        for i in range(10):
            price = StockPrice(
                stock_id=sample_stock.id,
                timestamp=datetime.utcnow() - timedelta(days=10-i),
                open_price=100.0,
                high_price=101.0,
                low_price=99.0,
                close_price=100.5,
                volume=1000000
            )
            db.session.add(price)
        db.session.commit()
        
        df = service.get_price_history(sample_stock.symbol)
        assert df is None
    
    def test_calculate_rsi_success(self):
        """Test RSI calculation with valid data"""
        service = OptionsService()
        prices = pd.Series([100, 101, 102, 101, 100, 99, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107])
        rsi = service.calculate_rsi(prices)
        assert rsi is not None
        assert 0 <= rsi <= 100
    
    def test_calculate_rsi_insufficient_data(self):
        """Test RSI calculation with insufficient data"""
        service = OptionsService()
        prices = pd.Series([100, 101, 102])
        rsi = service.calculate_rsi(prices)
        assert rsi is None
    
    def test_calculate_macd_success(self):
        """Test MACD calculation with valid data"""
        service = OptionsService()
        prices = pd.Series(np.linspace(100, 110, 50))
        macd_data = service.calculate_macd(prices)
        assert macd_data is not None
        assert len(macd_data) == 3
        macd, signal, histogram = macd_data
        assert isinstance(macd, float)
        assert isinstance(signal, float)
        assert isinstance(histogram, float)
    
    def test_calculate_macd_insufficient_data(self):
        """Test MACD calculation with insufficient data"""
        service = OptionsService()
        prices = pd.Series([100, 101, 102])
        macd_data = service.calculate_macd(prices)
        assert macd_data is None
    
    def test_calculate_volatility_success(self):
        """Test volatility calculation with valid data"""
        service = OptionsService()
        prices = pd.Series(np.random.normal(100, 5, 50))
        volatility = service.calculate_volatility(prices)
        assert volatility is not None
        assert volatility >= 0
    
    def test_calculate_volatility_insufficient_data(self):
        """Test volatility calculation with insufficient data"""
        service = OptionsService()
        prices = pd.Series([100, 101, 102])
        volatility = service.calculate_volatility(prices)
        assert volatility is None
    
    def test_predict_price_movement_success(self, sample_stock, db):
        """Test price movement prediction with valid data"""
        service = OptionsService()
        
        # Add sufficient price history
        for i in range(50):
            price = StockPrice(
                stock_id=sample_stock.id,
                timestamp=datetime.utcnow() - timedelta(days=50-i),
                open_price=100.0 + (i % 10),
                high_price=101.0 + (i % 10),
                low_price=99.0 + (i % 10),
                close_price=100.5 + (i % 10),
                volume=1000000
            )
            db.session.add(price)
        db.session.commit()
        
        prediction = service.predict_price_movement(sample_stock.symbol)
        assert prediction is not None
        assert 'rsi' in prediction
        assert 'macd' in prediction
        assert 'volatility' in prediction
        assert 'prediction' in prediction
    
    def test_predict_price_movement_not_found(self):
        """Test price movement prediction for non-existent stock"""
        service = OptionsService()
        prediction = service.predict_price_movement('NONEXISTENT')
        assert prediction is None


class TestOptionsSignalService:
    """Tests for OptionsSignalService"""
    
    def test_init(self):
        """Test OptionsSignalService initialization"""
        service = OptionsSignalService()
        assert service is not None
        assert service.options_service is not None
    
    def test_score_liquidity_both_present(self):
        """Test liquidity scoring with both volume and open interest"""
        service = OptionsSignalService()
        score, warnings = service._score_liquidity(1500, 2000)
        assert score > 0
        assert len(warnings) == 0
    
    def test_score_liquidity_low_volume(self):
        """Test liquidity scoring with low volume"""
        service = OptionsSignalService()
        score, warnings = service._score_liquidity(10, 100)
        assert score > 0
        assert 'low_volume' in warnings
    
    def test_score_liquidity_missing_data(self):
        """Test liquidity scoring with missing data"""
        service = OptionsSignalService()
        score, warnings = service._score_liquidity(None, None)
        assert score == 0.0
        assert 'no_liquidity_data' in warnings
    
    def test_score_spread_tight(self):
        """Test spread scoring with tight spread"""
        service = OptionsSignalService()
        score, warnings = service._score_spread(10.0, 10.05, 100.0)
        assert score > 10.0
        assert len(warnings) == 0
    
    def test_score_spread_wide(self):
        """Test spread scoring with wide spread"""
        service = OptionsSignalService()
        score, warnings = service._score_spread(10.0, 10.50, 100.0)
        assert score > 0
        assert 'wide_spread' in warnings
    
    def test_score_spread_missing_data(self):
        """Test spread scoring with missing data"""
        service = OptionsSignalService()
        score, warnings = service._score_spread(None, None, 100.0)
        assert score == 0.0
        assert 'no_spread_data' in warnings
    
    def test_score_moneyness_atm(self):
        """Test moneyness scoring for at-the-money option"""
        service = OptionsSignalService()
        score, warnings = service._score_moneyness(100.0, 100.0, 'call')
        assert score == 12.0
        assert len(warnings) == 0
    
    def test_score_moneyness_otm(self):
        """Test moneyness scoring for out-of-the-money option"""
        service = OptionsSignalService()
        score, warnings = service._score_moneyness(110.0, 100.0, 'call')
        assert score > 0
        assert 'far_from_money' in warnings
    
    def test_score_moneyness_missing_data(self):
        """Test moneyness scoring with missing data"""
        service = OptionsSignalService()
        score, warnings = service._score_moneyness(None, 100.0, 'call')
        assert score == 0.0
        assert 'no_moneyness_data' in warnings
    
    def test_score_expiration_sweet_spot(self):
        """Test expiration scoring in sweet spot (20-60 days)"""
        service = OptionsSignalService()
        score, warnings = service._score_expiration(45)
        assert score == 10.0
        assert len(warnings) == 0
    
    def test_score_expiration_near(self):
        """Test expiration scoring for near-term option"""
        service = OptionsSignalService()
        score, warnings = service._score_expiration(5)
        assert score == 3.0
        assert 'near_expiration' in warnings
    
    def test_score_expiration_far(self):
        """Test expiration scoring for far-term option"""
        service = OptionsSignalService()
        score, warnings = service._score_expiration(120)
        assert score == 4.0
        assert 'far_expiration' in warnings
    
    def test_score_expiration_invalid(self):
        """Test expiration scoring with invalid data"""
        service = OptionsSignalService()
        score, warnings = service._score_expiration(None)
        assert score == 0.0
        assert 'invalid_expiration' in warnings
    
    def test_score_momentum_no_symbol(self):
        """Test momentum scoring without symbol"""
        service = OptionsSignalService()
        score, warnings = service._score_momentum(None, 100.0)
        assert score == 0.0
        assert 'no_symbol_for_momentum' in warnings
    
    def test_score_implied_volatility_moderate(self):
        """Test IV scoring with moderate IV"""
        service = OptionsSignalService()
        score, warnings = service._score_implied_volatility(0.35)
        assert score == 9.5
        assert len(warnings) == 0
    
    def test_score_implied_volatility_low(self):
        """Test IV scoring with very low IV"""
        service = OptionsSignalService()
        score, warnings = service._score_implied_volatility(0.10)
        assert score == 2.0
        assert 'very_low_iv' in warnings
    
    def test_score_implied_volatility_high(self):
        """Test IV scoring with very high IV"""
        service = OptionsSignalService()
        score, warnings = service._score_implied_volatility(0.80)
        assert score == 3.0
        assert 'very_high_iv' in warnings
    
    def test_score_implied_volatility_missing(self):
        """Test IV scoring with missing data"""
        service = OptionsSignalService()
        score, warnings = service._score_implied_volatility(None)
        assert score == 0.0
        assert 'no_iv_data' in warnings
    
    def test_score_data_quality_complete(self):
        """Test data quality scoring with complete data"""
        service = OptionsSignalService()
        score, warnings = service._score_data_quality([])
        assert score == 10.0
        assert len(warnings) == 0
    
    def test_score_data_quality_incomplete(self):
        """Test data quality scoring with missing fields"""
        service = OptionsSignalService()
        score, warnings = service._score_data_quality(['volume', 'open_interest'])
        assert score < 10.0
        assert 'incomplete_data' in warnings
    
    def test_derive_risk_label_avoid(self):
        """Test risk label derivation for avoid"""
        service = OptionsSignalService()
        label = service._derive_risk_label(30.0, [])
        assert label == 'avoid'
    
    def test_derive_risk_label_watchlist(self):
        """Test risk label derivation for watchlist"""
        service = OptionsSignalService()
        label = service._derive_risk_label(55.0, [])
        assert label == 'watchlist'
    
    def test_derive_risk_label_interesting(self):
        """Test risk label derivation for interesting"""
        service = OptionsSignalService()
        label = service._derive_risk_label(70.0, [])
        assert label == 'interesting'
    
    def test_derive_risk_label_high_risk(self):
        """Test risk label derivation for high_risk"""
        service = OptionsSignalService()
        label = service._derive_risk_label(85.0, [])
        assert label == 'high_risk'
    
    def test_derive_risk_label_critical_warning(self):
        """Test risk label derivation with critical warning"""
        service = OptionsSignalService()
        label = service._derive_risk_label(80.0, ['zero_volume'])
        assert label == 'avoid'
    
    def test_generate_explanation(self):
        """Test explanation generation"""
        service = OptionsSignalService()
        breakdown = {'liquidity': 10, 'spread': 8, 'moneyness': 5}
        explanation = service._generate_explanation(breakdown, ['low_volume'], 'watchlist')
        assert isinstance(explanation, str)
        assert len(explanation) > 0
        assert 'watchlist' in explanation.lower() or 'careful' in explanation.lower()
    
    def test_score_option_contract_complete_data(self):
        """Test option contract scoring with complete data"""
        service = OptionsSignalService()
        contract = {
            'symbol': 'AAPL',
            'expiration': (datetime.utcnow() + timedelta(days=45)).isoformat(),
            'strike': 150.0,
            'contract_type': 'call',
            'bid': 5.0,
            'ask': 5.10,
            'volume': 1000,
            'open_interest': 5000,
            'implied_volatility': 0.30,
            'underlying_price': 150.0
        }
        
        result = service.score_option_contract(contract)
        assert result['symbol'] == 'AAPL'
        assert result['strategy'] == 'call_candidate'
        assert 0 <= result['score'] <= 100
        assert result['grade'] in ['avoid', 'watchlist', 'interesting', 'high_risk']
        assert 'breakdown' in result
        assert 'warnings' in result
        assert 'explanation' in result
    
    def test_score_option_contract_minimal_data(self):
        """Test option contract scoring with minimal data"""
        service = OptionsSignalService()
        contract = {
            'symbol': 'AAPL',
            'strike': 150.0,
            'contract_type': 'put'
        }
        
        result = service.score_option_contract(contract)
        assert result['symbol'] == 'AAPL'
        assert result['strategy'] == 'put_candidate'
        assert result['score'] >= 0
        assert len(result['warnings']) > 0  # Should have warnings for missing data
    
    def test_score_option_contract_invalid_expiration(self):
        """Test option contract scoring with invalid expiration"""
        service = OptionsSignalService()
        contract = {
            'symbol': 'AAPL',
            'expiration': 'invalid-date',
            'strike': 150.0
        }
        
        result = service.score_option_contract(contract)
        assert result['symbol'] == 'AAPL'
        assert result['score'] >= 0
    
    def test_score_option_chain(self):
        """Test scoring multiple option contracts"""
        service = OptionsSignalService()
        contracts = [
            {
                'symbol': 'AAPL',
                'strike': 150.0,
                'bid': 5.0,
                'ask': 5.10,
                'volume': 100,
                'open_interest': 500
            },
            {
                'symbol': 'AAPL',
                'strike': 155.0,
                'bid': 2.0,
                'ask': 2.20,
                'volume': 5000,
                'open_interest': 10000
            }
        ]
        
        results = service.score_option_chain(contracts)
        assert len(results) == 2
        # Should be sorted by score descending
        assert results[0]['score'] >= results[1]['score']
    
    def test_score_option_chain_empty(self):
        """Test scoring empty option chain"""
        service = OptionsSignalService()
        results = service.score_option_chain([])
        assert results == []
    
    def test_score_option_contract_error_handling(self):
        """Test error handling in option contract scoring"""
        service = OptionsSignalService()
        # Pass invalid data that might cause errors
        contract = {
            'symbol': 'AAPL',
            'bid': 'invalid',  # Should be float
            'ask': 'invalid'
        }
        
        result = service.score_option_contract(contract)
        # Should not crash, should return error result
        assert result['grade'] == 'avoid'
        assert 'warnings' in result
