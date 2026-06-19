"""Tests for options service layer."""

import pytest
from golden_goose.services.options_service import (
    OptionsSignalService,
    OptionSignalScore,
)


class TestOptionsSignalService:
    """Test suite for OptionsSignalService."""

    @pytest.fixture
    def service(self):
        """Fixture for OptionsSignalService instance."""
        return OptionsSignalService()

    def test_score_option_contract_basic(self, service):
        """Test basic scoring with complete data."""
        result = service.score_option_contract(
            symbol="AAPL",
            contract_type="call",
            strike=150.0,
            expiration="2024-01-19",
            bid=2.5,
            ask=2.7,
            last=2.6,
            volume=500,
            open_interest=1000,
            implied_volatility=0.25,
            underlying_price=151.0,
            days_to_expiration=30,
            recent_momentum=0.1,
        )

        assert isinstance(result, OptionSignalScore)
        assert result.symbol == "AAPL"
        assert result.strategy == "call_candidate"
        assert 0 <= result.score <= 100
        assert result.grade in ["avoid", "watchlist", "interesting", "high_risk"]
        assert "liquidity" in result.breakdown
        assert "spread" in result.breakdown
        assert "moneyness" in result.breakdown
        assert "expiration" in result.breakdown
        assert "momentum" in result.breakdown
        assert "data_quality" in result.breakdown

    def test_score_option_contract_missing_bid_ask(self, service):
        """Test scoring with missing bid/ask data."""
        result = service.score_option_contract(
            symbol="AAPL",
            contract_type="call",
            strike=150.0,
            expiration="2024-01-19",
            bid=None,
            ask=None,
            volume=500,
            open_interest=1000,
            underlying_price=151.0,
            days_to_expiration=30,
        )

        assert result.score == 0.0  # No bid/ask = no liquidity score
        assert "no_bid_ask" in result.warnings

    def test_score_option_contract_missing_strike(self, service):
        """Test scoring with missing strike data."""
        result = service.score_option_contract(
            symbol="AAPL",
            contract_type="call",
            strike=None,
            expiration="2024-01-19",
            bid=2.5,
            ask=2.7,
            underlying_price=151.0,
            days_to_expiration=30,
        )

        assert "cannot_score_moneyness" in result.warnings
        assert result.breakdown["moneyness"] == 0.0

    def test_score_option_contract_missing_underlying_price(self, service):
        """Test scoring with missing underlying price."""
        result = service.score_option_contract(
            symbol="AAPL",
            contract_type="call",
            strike=150.0,
            expiration="2024-01-19",
            bid=2.5,
            ask=2.7,
            underlying_price=None,
            days_to_expiration=30,
        )

        assert "cannot_score_moneyness" in result.warnings
        assert result.breakdown["moneyness"] == 0.0

    def test_score_option_contract_expired(self, service):
        """Test scoring with expired contract."""
        result = service.score_option_contract(
            symbol="AAPL",
            contract_type="call",
            strike=150.0,
            expiration="2024-01-01",
            bid=2.5,
            ask=2.7,
            underlying_price=151.0,
            days_to_expiration=-1,
        )

        assert "expired_contract" in result.warnings
        assert result.grade == "avoid"

    def test_score_option_contract_wide_spread(self, service):
        """Test scoring with wide bid-ask spread."""
        result = service.score_option_contract(
            symbol="AAPL",
            contract_type="call",
            strike=150.0,
            expiration="2024-01-19",
            bid=2.0,
            ask=5.0,  # Wide spread
            underlying_price=151.0,
            days_to_expiration=30,
        )

        assert "wide_spread" in result.warnings
        assert result.breakdown["spread"] < 5.0  # Low spread score

    def test_score_option_contract_short_expiration(self, service):
        """Test scoring with short time to expiration."""
        result = service.score_option_contract(
            symbol="AAPL",
            contract_type="call",
            strike=150.0,
            expiration="2024-01-19",
            bid=2.5,
            ask=2.7,
            underlying_price=151.0,
            days_to_expiration=3,
        )

        assert "short_expiration" in result.warnings
        assert result.breakdown["expiration"] < 10.0

    def test_score_option_contract_long_expiration(self, service):
        """Test scoring with long time to expiration."""
        result = service.score_option_contract(
            symbol="AAPL",
            contract_type="call",
            strike=150.0,
            expiration="2024-12-19",
            bid=2.5,
            ask=2.7,
            underlying_price=151.0,
            days_to_expiration=300,
        )

        assert "long_expiration" in result.warnings
        assert result.breakdown["expiration"] < 15.0

    def test_score_option_contract_atm(self, service):
        """Test scoring with at-the-money contract."""
        result = service.score_option_contract(
            symbol="AAPL",
            contract_type="call",
            strike=150.0,
            expiration="2024-01-19",
            bid=2.5,
            ask=2.7,
            underlying_price=150.0,  # ATM
            days_to_expiration=30,
        )

        assert result.breakdown["moneyness"] == 15.0  # Full points for ATM

    def test_score_option_contract_otm(self, service):
        """Test scoring with out-of-the-money contract."""
        result = service.score_option_contract(
            symbol="AAPL",
            contract_type="call",
            strike=160.0,
            expiration="2024-01-19",
            bid=2.5,
            ask=2.7,
            underlying_price=150.0,  # OTM
            days_to_expiration=30,
        )

        assert result.breakdown["moneyness"] < 15.0  # Lower score for OTM

    def test_score_option_contract_no_volume(self, service):
        """Test scoring with no volume."""
        result = service.score_option_contract(
            symbol="AAPL",
            contract_type="call",
            strike=150.0,
            expiration="2024-01-19",
            bid=2.5,
            ask=2.7,
            volume=None,
            open_interest=1000,
            underlying_price=151.0,
            days_to_expiration=30,
        )

        assert "no_volume" in result.warnings
        assert result.breakdown["liquidity"] < 20.0

    def test_score_option_contract_no_open_interest(self, service):
        """Test scoring with no open interest."""
        result = service.score_option_contract(
            symbol="AAPL",
            contract_type="call",
            strike=150.0,
            expiration="2024-01-19",
            bid=2.5,
            ask=2.7,
            volume=500,
            open_interest=None,
            underlying_price=151.0,
            days_to_expiration=30,
        )

        assert "no_open_interest" in result.warnings
        assert result.breakdown["liquidity"] < 20.0

    def test_score_option_contract_no_momentum(self, service):
        """Test scoring with no momentum data."""
        result = service.score_option_contract(
            symbol="AAPL",
            contract_type="call",
            strike=150.0,
            expiration="2024-01-19",
            bid=2.5,
            ask=2.7,
            underlying_price=151.0,
            days_to_expiration=30,
            recent_momentum=None,
        )

        assert "no_momentum_data" in result.warnings
        # Momentum should get neutral score
        assert 5.0 <= result.breakdown["momentum"] <= 10.0

    def test_score_option_contract_incomplete_data(self, service):
        """Test scoring with incomplete data."""
        result = service.score_option_contract(
            symbol="AAPL",
            contract_type="call",
            strike=150.0,
            expiration="2024-01-19",
            bid=2.5,
            ask=2.7,
            volume=None,
            open_interest=None,
            implied_volatility=None,
            underlying_price=151.0,
            days_to_expiration=30,
        )

        assert "incomplete_data" in result.warnings
        assert result.breakdown["data_quality"] < 20.0

    def test_rank_option_contracts(self, service):
        """Test ranking multiple option contracts."""
        contracts = [
            {
                "symbol": "AAPL",
                "contract_type": "call",
                "strike": 150.0,
                "expiration": "2024-01-19",
                "bid": 2.5,
                "ask": 2.7,
                "volume": 500,
                "open_interest": 1000,
                "underlying_price": 151.0,
                "days_to_expiration": 30,
            },
            {
                "symbol": "AAPL",
                "contract_type": "call",
                "strike": 160.0,
                "expiration": "2024-01-19",
                "bid": 1.0,
                "ask": 1.2,
                "volume": 100,
                "open_interest": 200,
                "underlying_price": 151.0,
                "days_to_expiration": 30,
            },
        ]

        results = service.rank_option_contracts(contracts)

        assert len(results) == 2
        # First contract should rank higher (better liquidity, closer to ATM)
        assert results[0].score >= results[1].score

    def test_score_option_contract_put(self, service):
        """Test scoring a put contract."""
        result = service.score_option_contract(
            symbol="AAPL",
            contract_type="put",
            strike=150.0,
            expiration="2024-01-19",
            bid=2.5,
            ask=2.7,
            volume=500,
            open_interest=1000,
            underlying_price=151.0,
            days_to_expiration=30,
        )

        assert result.strategy == "put_candidate"
        assert result.score > 0

    def test_score_option_contract_high_momentum(self, service):
        """Test scoring with high positive momentum."""
        result = service.score_option_contract(
            symbol="AAPL",
            contract_type="call",
            strike=150.0,
            expiration="2024-01-19",
            bid=2.5,
            ask=2.7,
            underlying_price=151.0,
            days_to_expiration=30,
            recent_momentum=0.9,  # High positive momentum
        )

        assert result.breakdown["momentum"] > 10.0

    def test_score_option_contract_negative_momentum(self, service):
        """Test scoring with negative momentum."""
        result = service.score_option_contract(
            symbol="AAPL",
            contract_type="call",
            strike=150.0,
            expiration="2024-01-19",
            bid=2.5,
            ask=2.7,
            underlying_price=151.0,
            days_to_expiration=30,
            recent_momentum=-0.9,  # High negative momentum
        )

        assert result.breakdown["momentum"] < 5.0

    def test_score_option_contract_tight_spread(self, service):
        """Test scoring with tight bid-ask spread."""
        result = service.score_option_contract(
            symbol="AAPL",
            contract_type="call",
            strike=150.0,
            expiration="2024-01-19",
            bid=2.50,
            ask=2.51,  # Very tight spread
            underlying_price=151.0,
            days_to_expiration=30,
        )

        assert result.breakdown["spread"] == 15.0  # Full points for tight spread

    def test_score_option_contract_high_volume(self, service):
        """Test scoring with high volume."""
        result = service.score_option_contract(
            symbol="AAPL",
            contract_type="call",
            strike=150.0,
            expiration="2024-01-19",
            bid=2.5,
            ask=2.7,
            volume=5000,  # High volume
            open_interest=10000,  # High OI
            underlying_price=151.0,
            days_to_expiration=30,
        )

        assert result.breakdown["liquidity"] == 20.0  # Full points for high liquidity

    def test_score_option_contract_explanation_present(self, service):
        """Test that explanation is generated."""
        result = service.score_option_contract(
            symbol="AAPL",
            contract_type="call",
            strike=150.0,
            expiration="2024-01-19",
            bid=2.5,
            ask=2.7,
            underlying_price=151.0,
            days_to_expiration=30,
        )

        assert len(result.explanation) > 0
        assert "AAPL" in result.explanation
        assert "CALL" in result.explanation
        assert "financial advice" in result.explanation.lower()
