"""Tests for OptionsSignalService"""

import pytest
from datetime import datetime, timedelta
from services.options_signal_service import OptionsSignalService, OptionSignalScore


class TestOptionsSignalServiceInit:
    """Tests for OptionsSignalService initialization"""
    
    def test_init(self):
        """Test OptionsSignalService initialization"""
        service = OptionsSignalService()
        assert service is not None


class TestOptionsSignalServiceScoreOptionContract:
    """Tests for score_option_contract method"""
    
    def test_score_complete_option_data(self):
        """Test scoring with complete option data"""
        service = OptionsSignalService()
        option_data = {
            'symbol': 'AAPL',
            'bid': 5.0,
            'ask': 5.10,
            'volume': 1000,
            'open_interest': 500,
            'implied_volatility': 0.25,
            'strike': 150.0,
            'underlying_price': 150.0,
            'expiration_date': datetime.utcnow() + timedelta(days=30),
            'contract_type': 'call',
            'recent_move_percent': 5.0
        }
        
        score = service.score_option_contract(option_data)
        
        assert isinstance(score, OptionSignalScore)
        assert score.symbol == 'AAPL'
        assert score.strategy == 'call_candidate'
        assert 0 <= score.score <= 100
        assert score.grade in ['avoid', 'watchlist', 'interesting', 'high_risk']
        assert isinstance(score.breakdown, dict)
        assert 'liquidity' in score.breakdown
        assert 'spread' in score.breakdown
        assert 'moneyness' in score.breakdown
        assert 'expiration' in score.breakdown
        assert 'momentum' in score.breakdown
        assert 'data_quality' in score.breakdown
        assert isinstance(score.warnings, list)
        assert isinstance(score.explanation, str)
    
    def test_score_missing_bid_ask(self):
        """Test scoring with missing bid/ask"""
        service = OptionsSignalService()
        option_data = {
            'symbol': 'AAPL',
            'volume': 1000,
            'open_interest': 500,
            'implied_volatility': 0.25,
            'strike': 150.0,
            'underlying_price': 150.0,
            'expiration_date': datetime.utcnow() + timedelta(days=30),
            'contract_type': 'call'
        }
        
        score = service.score_option_contract(option_data)
        
        assert isinstance(score, OptionSignalScore)
        assert 'missing_bid_ask' in score.warnings
        assert score.score >= 0  # Should not crash
    
    def test_score_low_open_interest(self):
        """Test scoring with low open interest"""
        service = OptionsSignalService()
        option_data = {
            'symbol': 'AAPL',
            'bid': 5.0,
            'ask': 5.10,
            'volume': 100,
            'open_interest': 10,  # Low
            'implied_volatility': 0.25,
            'strike': 150.0,
            'underlying_price': 150.0,
            'expiration_date': datetime.utcnow() + timedelta(days=30),
            'contract_type': 'call'
        }
        
        score = service.score_option_contract(option_data)
        
        assert 'low_open_interest' in score.warnings
        assert 'low_volume' in score.warnings
    
    def test_score_missing_implied_volatility(self):
        """Test scoring with missing implied volatility"""
        service = OptionsSignalService()
        option_data = {
            'symbol': 'AAPL',
            'bid': 5.0,
            'ask': 5.10,
            'volume': 1000,
            'open_interest': 500,
            'strike': 150.0,
            'underlying_price': 150.0,
            'expiration_date': datetime.utcnow() + timedelta(days=30),
            'contract_type': 'call'
        }
        
        score = service.score_option_contract(option_data)
        
        assert 'missing_iv' in score.warnings
    
    def test_score_expired_contract(self):
        """Test scoring with expired contract"""
        service = OptionsSignalService()
        option_data = {
            'symbol': 'AAPL',
            'bid': 5.0,
            'ask': 5.10,
            'volume': 1000,
            'open_interest': 500,
            'implied_volatility': 0.25,
            'strike': 150.0,
            'underlying_price': 150.0,
            'expiration_date': datetime.utcnow() - timedelta(days=1),  # Expired
            'contract_type': 'call'
        }
        
        score = service.score_option_contract(option_data)
        
        assert 'expired' in score.warnings
        assert score.grade == 'avoid'
    
    def test_score_expiring_soon(self):
        """Test scoring with contract expiring soon"""
        service = OptionsSignalService()
        option_data = {
            'symbol': 'AAPL',
            'bid': 5.0,
            'ask': 5.10,
            'volume': 1000,
            'open_interest': 500,
            'implied_volatility': 0.25,
            'strike': 150.0,
            'underlying_price': 150.0,
            'expiration_date': datetime.utcnow() + timedelta(hours=12),  # Expiring soon
            'contract_type': 'call'
        }
        
        score = service.score_option_contract(option_data)
        
        assert 'expiring_soon' in score.warnings
    
    def test_score_wide_spread(self):
        """Test scoring with wide bid/ask spread"""
        service = OptionsSignalService()
        option_data = {
            'symbol': 'AAPL',
            'bid': 5.0,
            'ask': 6.0,  # 10% spread - wide
            'volume': 1000,
            'open_interest': 500,
            'implied_volatility': 0.25,
            'strike': 150.0,
            'underlying_price': 150.0,
            'expiration_date': datetime.utcnow() + timedelta(days=30),
            'contract_type': 'call'
        }
        
        score = service.score_option_contract(option_data)
        
        assert 'wide_spread' in score.warnings
    
    def test_score_atm_contract(self):
        """Test scoring with at-the-money contract"""
        service = OptionsSignalService()
        option_data = {
            'symbol': 'AAPL',
            'bid': 5.0,
            'ask': 5.10,
            'volume': 1000,
            'open_interest': 500,
            'implied_volatility': 0.25,
            'strike': 150.0,
            'underlying_price': 150.0,  # ATM
            'expiration_date': datetime.utcnow() + timedelta(days=30),
            'contract_type': 'call'
        }
        
        score = service.score_option_contract(option_data)
        
        # ATM should have good moneyness score
        assert score.breakdown['moneyness'] > 10
    
    def test_score_otm_contract(self):
        """Test scoring with out-of-the-money contract"""
        service = OptionsSignalService()
        option_data = {
            'symbol': 'AAPL',
            'bid': 1.0,
            'ask': 1.10,
            'volume': 500,
            'open_interest': 200,
            'implied_volatility': 0.25,
            'strike': 160.0,
            'underlying_price': 150.0,  # OTM call
            'expiration_date': datetime.utcnow() + timedelta(days=30),
            'contract_type': 'call'
        }
        
        score = service.score_option_contract(option_data)
        
        # OTM should have lower moneyness score
        assert score.breakdown['moneyness'] < 10
    
    def test_score_short_expiration(self):
        """Test scoring with short time to expiration"""
        service = OptionsSignalService()
        option_data = {
            'symbol': 'AAPL',
            'bid': 5.0,
            'ask': 5.10,
            'volume': 1000,
            'open_interest': 500,
            'implied_volatility': 0.25,
            'strike': 150.0,
            'underlying_price': 150.0,
            'expiration_date': datetime.utcnow() + timedelta(days=2),  # Short
            'contract_type': 'call'
        }
        
        score = service.score_option_contract(option_data)
        
        # Short expiration should have lower expiration score
        assert score.breakdown['expiration'] < 10
    
    def test_score_long_expiration(self):
        """Test scoring with long time to expiration"""
        service = OptionsSignalService()
        option_data = {
            'symbol': 'AAPL',
            'bid': 5.0,
            'ask': 5.10,
            'volume': 1000,
            'open_interest': 500,
            'implied_volatility': 0.25,
            'strike': 150.0,
            'underlying_price': 150.0,
            'expiration_date': datetime.utcnow() + timedelta(days=120),  # Long
            'contract_type': 'call'
        }
        
        score = service.score_option_contract(option_data)
        
        # Long expiration should have moderate expiration score
        assert score.breakdown['expiration'] > 5
    
    def test_score_high_volume(self):
        """Test scoring with high volume"""
        service = OptionsSignalService()
        option_data = {
            'symbol': 'AAPL',
            'bid': 5.0,
            'ask': 5.10,
            'volume': 10000,  # High
            'open_interest': 5000,  # High
            'implied_volatility': 0.25,
            'strike': 150.0,
            'underlying_price': 150.0,
            'expiration_date': datetime.utcnow() + timedelta(days=30),
            'contract_type': 'call'
        }
        
        score = service.score_option_contract(option_data)
        
        # High volume should have good liquidity score
        assert score.breakdown['liquidity'] > 15
    
    def test_score_low_volume(self):
        """Test scoring with low volume"""
        service = OptionsSignalService()
        option_data = {
            'symbol': 'AAPL',
            'bid': 5.0,
            'ask': 5.10,
            'volume': 10,  # Low
            'open_interest': 5,  # Low
            'implied_volatility': 0.25,
            'strike': 150.0,
            'underlying_price': 150.0,
            'expiration_date': datetime.utcnow() + timedelta(days=30),
            'contract_type': 'call'
        }
        
        score = service.score_option_contract(option_data)
        
        # Low volume should have poor liquidity score
        assert score.breakdown['liquidity'] < 5
    
    def test_score_high_momentum(self):
        """Test scoring with high recent momentum"""
        service = OptionsSignalService()
        option_data = {
            'symbol': 'AAPL',
            'bid': 5.0,
            'ask': 5.10,
            'volume': 1000,
            'open_interest': 500,
            'implied_volatility': 0.25,
            'strike': 150.0,
            'underlying_price': 150.0,
            'expiration_date': datetime.utcnow() + timedelta(days=30),
            'contract_type': 'call',
            'recent_move_percent': 15.0  # Good momentum
        }
        
        score = service.score_option_contract(option_data)
        
        # Good momentum should have high momentum score
        assert score.breakdown['momentum'] > 10
    
    def test_score_low_momentum(self):
        """Test scoring with low recent momentum"""
        service = OptionsSignalService()
        option_data = {
            'symbol': 'AAPL',
            'bid': 5.0,
            'ask': 5.10,
            'volume': 1000,
            'open_interest': 500,
            'implied_volatility': 0.25,
            'strike': 150.0,
            'underlying_price': 150.0,
            'expiration_date': datetime.utcnow() + timedelta(days=30),
            'contract_type': 'call',
            'recent_move_percent': 0.5  # Low momentum
        }
        
        score = service.score_option_contract(option_data)
        
        # Low momentum should have low momentum score
        assert score.breakdown['momentum'] < 10
    
    def test_score_put_contract(self):
        """Test scoring with put contract"""
        service = OptionsSignalService()
        option_data = {
            'symbol': 'AAPL',
            'bid': 5.0,
            'ask': 5.10,
            'volume': 1000,
            'open_interest': 500,
            'implied_volatility': 0.25,
            'strike': 150.0,
            'underlying_price': 150.0,
            'expiration_date': datetime.utcnow() + timedelta(days=30),
            'contract_type': 'put'
        }
        
        score = service.score_option_contract(option_data)
        
        assert score.strategy == 'put_candidate'
    
    def test_score_incomplete_option_data(self):
        """Test scoring with incomplete option data - should not crash"""
        service = OptionsSignalService()
        option_data = {
            'symbol': 'AAPL',
            # Missing bid, ask, volume, open_interest, implied_volatility
            'strike': 150.0,
            'underlying_price': 150.0,
            'expiration_date': datetime.utcnow() + timedelta(days=30),
            'contract_type': 'call'
        }
        
        score = service.score_option_contract(option_data)
        
        # Should not crash and should have warnings
        assert isinstance(score, OptionSignalScore)
        assert len(score.warnings) > 0
        assert 'missing_bid_ask' in score.warnings
        assert 'missing_iv' in score.warnings
        assert score.score >= 0
    
    def test_score_minimal_option_data(self):
        """Test scoring with minimal option data"""
        service = OptionsSignalService()
        option_data = {
            'symbol': 'AAPL',
            'contract_type': 'call'
        }
        
        score = service.score_option_contract(option_data)
        
        # Should not crash
        assert isinstance(score, OptionSignalScore)
        assert score.symbol == 'AAPL'
        assert score.score >= 0
    
    def test_score_missing_underlying_price(self):
        """Test scoring with missing underlying price"""
        service = OptionsSignalService()
        option_data = {
            'symbol': 'AAPL',
            'bid': 5.0,
            'ask': 5.10,
            'volume': 1000,
            'open_interest': 500,
            'implied_volatility': 0.25,
            'strike': 150.0,
            'expiration_date': datetime.utcnow() + timedelta(days=30),
            'contract_type': 'call'
        }
        
        score = service.score_option_contract(option_data)
        
        assert 'missing_underlying_price' in score.warnings
        assert score.grade == 'avoid'  # Critical warning
    
    def test_score_missing_expiration(self):
        """Test scoring with missing expiration date"""
        service = OptionsSignalService()
        option_data = {
            'symbol': 'AAPL',
            'bid': 5.0,
            'ask': 5.10,
            'volume': 1000,
            'open_interest': 500,
            'implied_volatility': 0.25,
            'strike': 150.0,
            'underlying_price': 150.0,
            'contract_type': 'call'
        }
        
        score = service.score_option_contract(option_data)
        
        assert 'missing_expiration' in score.warnings
        assert score.grade == 'avoid'  # Critical warning
    
    def test_score_to_dict(self):
        """Test OptionSignalScore.to_dict() method"""
        service = OptionsSignalService()
        option_data = {
            'symbol': 'AAPL',
            'bid': 5.0,
            'ask': 5.10,
            'volume': 1000,
            'open_interest': 500,
            'implied_volatility': 0.25,
            'strike': 150.0,
            'underlying_price': 150.0,
            'expiration_date': datetime.utcnow() + timedelta(days=30),
            'contract_type': 'call'
        }
        
        score = service.score_option_contract(option_data)
        score_dict = score.to_dict()
        
        assert isinstance(score_dict, dict)
        assert 'symbol' in score_dict
        assert 'strategy' in score_dict
        assert 'score' in score_dict
        assert 'grade' in score_dict
        assert 'breakdown' in score_dict
        assert 'warnings' in score_dict
        assert 'explanation' in score_dict
