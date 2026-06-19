"""Tests for options service layer."""

import pytest
from golden_goose.services.options_service import (
    OptionsSignalService,
    OptionSignalScore,
)


class TestOptionsSignalService:
    """Test suite for OptionsSignalService."""
    
    def test_score_option_contract_basic(self):
        """Test basic option contract scoring with complete data."""
        result = OptionsSignalService.score_option_contract(
            symbol="AAPL",
            contract_type="call",
            bid=2.50,
            ask=2.60,
            last=2.55,
            volume=500,
            open_interest=2000,
            implied_volatility=0.25,
            strike=150.0,
            underlying_price=150.5,
            days_to_expiration=30,
            recent_price_change=0.02,
        )
        
        assert isinstance(result, OptionSignalScore)
        assert result.symbol == "AAPL"
        assert result.strategy == "call_candidate"
        assert 0 <= result.score <= 100
        assert result.grade in ["avoid", "watchlist", "interesting", "high_risk"]
        assert isinstance(result.breakdown, dict)
        assert isinstance(result.warnings, list)
        assert isinstance(result.explanation, str)
        assert len(result.explanation) > 0
    
    def test_score_option_contract_put(self):
        """Test put option contract scoring."""
        result = OptionsSignalService.score_option_contract(
            symbol="SPY",
            contract_type="put",
            bid=1.50,
            ask=1.60,
            volume=1000,
            open_interest=5000,
            implied_volatility=0.30,
            strike=400.0,
            underlying_price=405.0,
            days_to_expiration=45,
        )
        
        assert result.strategy == "put_candidate"
        assert result.score > 0
    
    def test_score_option_contract_missing_data(self):
        """Test scoring with minimal/missing data."""
        result = OptionsSignalService.score_option_contract(
            symbol="TSLA",
            contract_type="call",
            strike=250.0,
            underlying_price=250.0,
        )
        
        assert isinstance(result, OptionSignalScore)
        assert result.score >= 0
        assert "missing_bid_ask" in result.warnings
        assert "missing_volume" in result.warnings
    
    def test_score_option_contract_wide_spread(self):
        """Test warning generation for wide spread."""
        result = OptionsSignalService.score_option_contract(
            symbol="AAPL",
            contract_type="call",
            bid=1.0,
            ask=5.0,  # Very wide spread
            underlying_price=150.0,
            volume=50,
            open_interest=100,
        )
        
        assert "wide_spread" in result.warnings
        assert "low_volume" in result.warnings
        assert "low_open_interest" in result.warnings
    
    def test_score_option_contract_low_volume(self):
        """Test warning for low volume."""
        result = OptionsSignalService.score_option_contract(
            symbol="AAPL",
            contract_type="call",
            bid=2.0,
            ask=2.1,
            volume=50,  # Low volume
            open_interest=200,
        )
        
        assert "low_volume" in result.warnings
    
    def test_score_option_contract_very_short_expiration(self):
        """Test warning for very short expiration."""
        result = OptionsSignalService.score_option_contract(
            symbol="AAPL",
            contract_type="call",
            bid=2.0,
            ask=2.1,
            days_to_expiration=2,  # Very short
        )
        
        assert "very_short_expiration" in result.warnings
    
    def test_score_option_contract_extreme_iv(self):
        """Test warnings for extreme implied volatility."""
        result_low_iv = OptionsSignalService.score_option_contract(
            symbol="AAPL",
            contract_type="call",
            implied_volatility=0.05,  # Very low
        )
        assert "very_low_iv" in result_low_iv.warnings
        
        result_high_iv = OptionsSignalService.score_option_contract(
            symbol="AAPL",
            contract_type="call",
            implied_volatility=1.5,  # Very high
        )
        assert "very_high_iv" in result_high_iv.warnings
    
    def test_score_breakdown_components(self):
        """Test that breakdown includes all expected components."""
        result = OptionsSignalService.score_option_contract(
            symbol="AAPL",
            contract_type="call",
            bid=2.50,
            ask=2.60,
            volume=500,
            open_interest=2000,
            implied_volatility=0.25,
            strike=150.0,
            underlying_price=150.5,
            days_to_expiration=30,
            recent_price_change=0.02,
        )
        
        expected_keys = {
            "liquidity",
            "spread",
            "moneyness",
            "expiration",
            "momentum",
            "data_quality",
        }
        assert set(result.breakdown.keys()) == expected_keys
        
        # All components should be non-negative and within reasonable bounds
        for key, value in result.breakdown.items():
            assert 0 <= value <= 100, f"{key} score {value} out of bounds"
    
    def test_score_sum_matches_total(self):
        """Test that breakdown sum equals total score."""
        result = OptionsSignalService.score_option_contract(
            symbol="AAPL",
            contract_type="call",
            bid=2.50,
            ask=2.60,
            volume=500,
            open_interest=2000,
            implied_volatility=0.25,
            strike=150.0,
            underlying_price=150.5,
            days_to_expiration=30,
            recent_price_change=0.02,
        )
        
        breakdown_sum = sum(result.breakdown.values())
        assert abs(breakdown_sum - result.score) < 0.2  # Allow small rounding error
    
    def test_grade_derivation_high_score(self):
        """Test grade derivation for high-quality contract."""
        result = OptionsSignalService.score_option_contract(
            symbol="AAPL",
            contract_type="call",
            bid=2.50,
            ask=2.55,  # Tight spread
            volume=5000,  # High volume
            open_interest=10000,  # High OI
            implied_volatility=0.25,
            strike=150.0,
            underlying_price=150.0,  # ATM
            days_to_expiration=30,
            recent_price_change=0.02,
        )
        
        # Should have good grade with high score and few warnings
        assert result.score > 60
        assert result.grade in ["interesting", "watchlist"]
    
    def test_grade_derivation_low_score(self):
        """Test grade derivation for low-quality contract."""
        result = OptionsSignalService.score_option_contract(
            symbol="AAPL",
            contract_type="call",
            bid=1.0,
            ask=10.0,  # Very wide spread
            volume=10,  # Very low volume
            open_interest=50,  # Very low OI
            days_to_expiration=2,  # Very short
        )
        
        # Should have poor grade
        assert result.grade in ["avoid", "watchlist"]
    
    def test_to_dict_serialization(self):
        """Test that OptionSignalScore can be serialized to dict."""
        result = OptionsSignalService.score_option_contract(
            symbol="AAPL",
            contract_type="call",
            bid=2.50,
            ask=2.60,
            volume=500,
            open_interest=2000,
        )
        
        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert result_dict["symbol"] == "AAPL"
        assert result_dict["strategy"] == "call_candidate"
        assert "score" in result_dict
        assert "breakdown" in result_dict
        assert "warnings" in result_dict
        assert "explanation" in result_dict
    
    def test_moneyness_scoring(self):
        """Test moneyness scoring for ATM vs OTM options."""
        # ATM option
        result_atm = OptionsSignalService.score_option_contract(
            symbol="AAPL",
            contract_type="call",
            strike=150.0,
            underlying_price=150.0,
        )
        
        # OTM option (20% out)
        result_otm = OptionsSignalService.score_option_contract(
            symbol="AAPL",
            contract_type="call",
            strike=180.0,
            underlying_price=150.0,
        )
        
        # ATM should have higher moneyness score
        assert result_atm.breakdown["moneyness"] > result_otm.breakdown["moneyness"]
    
    def test_expiration_scoring(self):
        """Test expiration scoring for different DTE."""
        # Preferred range (30 DTE)
        result_good = OptionsSignalService.score_option_contract(
            symbol="AAPL",
            contract_type="call",
            days_to_expiration=30,
        )
        
        # Too short (3 DTE)
        result_short = OptionsSignalService.score_option_contract(
            symbol="AAPL",
            contract_type="call",
            days_to_expiration=3,
        )
        
        # Too long (200 DTE)
        result_long = OptionsSignalService.score_option_contract(
            symbol="AAPL",
            contract_type="call",
            days_to_expiration=200,
        )
        
        assert result_good.breakdown["expiration"] > result_short.breakdown["expiration"]
        assert result_good.breakdown["expiration"] > result_long.breakdown["expiration"]
    
    def test_liquidity_scoring(self):
        """Test liquidity scoring with different volume/OI levels."""
        # High liquidity
        result_high = OptionsSignalService.score_option_contract(
            symbol="AAPL",
            contract_type="call",
            bid=2.50,
            ask=2.60,
            volume=5000,
            open_interest=10000,
        )
        
        # Low liquidity
        result_low = OptionsSignalService.score_option_contract(
            symbol="AAPL",
            contract_type="call",
            bid=2.50,
            ask=2.60,
            volume=50,
            open_interest=100,
        )
        
        assert result_high.breakdown["liquidity"] > result_low.breakdown["liquidity"]
    
    def test_spread_scoring(self):
        """Test spread scoring with different spread widths."""
        # Tight spread
        result_tight = OptionsSignalService.score_option_contract(
            symbol="AAPL",
            contract_type="call",
            bid=2.50,
            ask=2.51,
            underlying_price=150.0,
        )
        
        # Wide spread
        result_wide = OptionsSignalService.score_option_contract(
            symbol="AAPL",
            contract_type="call",
            bid=2.00,
            ask=3.00,
            underlying_price=150.0,
        )
        
        assert result_tight.breakdown["spread"] > result_wide.breakdown["spread"]
    
    def test_data_quality_scoring(self):
        """Test data quality scoring based on field completeness."""
        # Complete data
        result_complete = OptionsSignalService.score_option_contract(
            symbol="AAPL",
            contract_type="call",
            bid=2.50,
            ask=2.60,
            volume=500,
            open_interest=2000,
            implied_volatility=0.25,
            strike=150.0,
            underlying_price=150.5,
            days_to_expiration=30,
        )
        
        # Minimal data
        result_minimal = OptionsSignalService.score_option_contract(
            symbol="AAPL",
            contract_type="call",
        )
        
        assert result_complete.breakdown["data_quality"] > result_minimal.breakdown["data_quality"]
    
    def test_explanation_generation(self):
        """Test that explanations are generated appropriately."""
        result = OptionsSignalService.score_option_contract(
            symbol="AAPL",
            contract_type="call",
            bid=2.50,
            ask=2.60,
            volume=500,
            open_interest=2000,
            implied_volatility=0.25,
            strike=150.0,
            underlying_price=150.5,
            days_to_expiration=30,
            recent_price_change=0.02,
        )
        
        assert len(result.explanation) > 0
        assert isinstance(result.explanation, str)
        # Explanation should mention grade or key factors
        assert any(word in result.explanation.lower() for word in ["strong", "weak", "warning", "monitor", "recommended"])
