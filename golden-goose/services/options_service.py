"""Options service layer for options data processing and analysis."""

from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict


@dataclass
class OptionSignalScore:
    """Structured output for an option contract signal score."""
    symbol: str
    strategy: str  # e.g., "call_candidate", "put_candidate"
    score: float  # 0-100
    grade: str  # "avoid", "watchlist", "interesting", "high_risk"
    breakdown: Dict[str, float]  # factor -> points
    warnings: List[str]  # warning flags
    explanation: str  # human-readable summary
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class OptionsSignalService:
    """Service for generating explainable option signal scores.
    
    This service scores option contracts using explainable factors such as
    liquidity, spread width, volume/open interest, implied volatility,
    moneyness, days to expiration, and recent underlying stock movement.
    
    The output is structured and testable, suitable for UI display, backtesting,
    or use in prediction pipelines. No financial advice is implied.
    """
    
    # Scoring constants (heuristic weights)
    MAX_LIQUIDITY_SCORE = 20
    MAX_SPREAD_SCORE = 15
    MAX_MONEYNESS_SCORE = 15
    MAX_EXPIRATION_SCORE = 15
    MAX_MOMENTUM_SCORE = 15
    MAX_DATA_QUALITY_SCORE = 20
    
    # Thresholds for warnings and grades
    SPREAD_WARNING_THRESHOLD = 0.02  # 2% of mid-price
    LOW_VOLUME_THRESHOLD = 100
    LOW_OI_THRESHOLD = 500
    LOW_IV_THRESHOLD = 0.15  # 15% annualized
    HIGH_IV_THRESHOLD = 1.0  # 100% annualized
    
    @staticmethod
    def score_option_contract(
        symbol: str,
        contract_type: str,
        bid: Optional[float] = None,
        ask: Optional[float] = None,
        last: Optional[float] = None,
        volume: Optional[int] = None,
        open_interest: Optional[int] = None,
        implied_volatility: Optional[float] = None,
        strike: Optional[float] = None,
        underlying_price: Optional[float] = None,
        days_to_expiration: Optional[int] = None,
        recent_price_change: Optional[float] = None,
    ) -> OptionSignalScore:
        """Score an option contract using explainable factors.
        
        Args:
            symbol: Stock ticker symbol (e.g., "AAPL")
            contract_type: "call" or "put"
            bid: Bid price (optional)
            ask: Ask price (optional)
            last: Last trade price (optional)
            volume: Trading volume (optional)
            open_interest: Open interest (optional)
            implied_volatility: IV as decimal (e.g., 0.25 for 25%) (optional)
            strike: Strike price (optional)
            underlying_price: Current underlying stock price (optional)
            days_to_expiration: Days until expiration (optional)
            recent_price_change: Recent price change as decimal (optional)
        
        Returns:
            OptionSignalScore with score, breakdown, warnings, and explanation.
        """
        service = OptionsSignalService()
        
        # Calculate individual factor scores
        liquidity_score = service._score_liquidity(bid, ask, volume, open_interest)
        spread_score = service._score_spread(bid, ask, underlying_price)
        moneyness_score = service._score_moneyness(strike, underlying_price, contract_type)
        expiration_score = service._score_expiration(days_to_expiration)
        momentum_score = service._score_momentum(recent_price_change, implied_volatility)
        data_quality_score = service._score_data_quality(
            bid, ask, volume, open_interest, implied_volatility, strike, underlying_price, days_to_expiration
        )
        
        # Aggregate scores
        breakdown = {
            "liquidity": liquidity_score,
            "spread": spread_score,
            "moneyness": moneyness_score,
            "expiration": expiration_score,
            "momentum": momentum_score,
            "data_quality": data_quality_score,
        }
        total_score = sum(breakdown.values())
        
        # Generate warnings
        warnings = service._generate_warnings(
            bid, ask, volume, open_interest, implied_volatility, underlying_price, days_to_expiration
        )
        
        # Derive grade from score and warnings
        grade = service._derive_grade(total_score, warnings)
        
        # Generate explanation
        explanation = service._generate_explanation(breakdown, warnings, grade)
        
        strategy = f"{contract_type}_candidate"
        
        return OptionSignalScore(
            symbol=symbol,
            strategy=strategy,
            score=round(total_score, 1),
            grade=grade,
            breakdown={k: round(v, 1) for k, v in breakdown.items()},
            warnings=warnings,
            explanation=explanation,
        )
    
    @staticmethod
    def _score_liquidity(
        bid: Optional[float],
        ask: Optional[float],
        volume: Optional[int],
        open_interest: Optional[int],
    ) -> float:
        """Score liquidity based on bid/ask presence, volume, and open interest.
        
        Heuristic: Presence of bid/ask (5 pts), volume (8 pts), open interest (7 pts).
        """
        score = 0.0
        
        # Bid/ask presence
        if bid is not None and ask is not None:
            score += 5.0
        
        # Volume
        if volume is not None:
            if volume >= 1000:
                score += 8.0
            elif volume >= 500:
                score += 6.0
            elif volume >= 100:
                score += 3.0
            else:
                score += 1.0
        
        # Open interest
        if open_interest is not None:
            if open_interest >= 5000:
                score += 7.0
            elif open_interest >= 2000:
                score += 5.0
            elif open_interest >= 500:
                score += 3.0
            else:
                score += 1.0
        
        return min(score, OptionsSignalService.MAX_LIQUIDITY_SCORE)
    
    @staticmethod
    def _score_spread(
        bid: Optional[float],
        ask: Optional[float],
        underlying_price: Optional[float],
    ) -> float:
        """Score spread width relative to underlying price.
        
        Heuristic: Narrow spread (15 pts), wide spread (5 pts), no data (0 pts).
        """
        if bid is None or ask is None:
            return 0.0
        
        spread = ask - bid
        
        # Use underlying price as reference if available, else use mid-price
        if underlying_price is not None:
            reference = underlying_price
        else:
            reference = (bid + ask) / 2.0
        
        if reference <= 0:
            return 0.0
        
        spread_pct = spread / reference
        
        # Heuristic: tight spread is good
        if spread_pct <= 0.005:  # 0.5%
            return OptionsSignalService.MAX_SPREAD_SCORE
        elif spread_pct <= 0.02:  # 2%
            return 12.0
        elif spread_pct <= 0.05:  # 5%
            return 8.0
        else:
            return 3.0
    
    @staticmethod
    def _score_moneyness(
        strike: Optional[float],
        underlying_price: Optional[float],
        contract_type: str,
    ) -> float:
        """Score moneyness (how close strike is to underlying price).
        
        Heuristic: Near-the-money is preferred (15 pts), out-of-money less so.
        """
        if strike is None or underlying_price is None or underlying_price <= 0:
            return 0.0
        
        moneyness = strike / underlying_price
        
        # For calls: moneyness near 1.0 is ATM (good)
        # For puts: moneyness near 1.0 is ATM (good)
        distance_from_atm = abs(moneyness - 1.0)
        
        if distance_from_atm <= 0.02:  # Within 2%
            return OptionsSignalService.MAX_MONEYNESS_SCORE
        elif distance_from_atm <= 0.05:  # Within 5%
            return 12.0
        elif distance_from_atm <= 0.10:  # Within 10%
            return 8.0
        elif distance_from_atm <= 0.20:  # Within 20%
            return 4.0
        else:
            return 1.0
    
    @staticmethod
    def _score_expiration(
        days_to_expiration: Optional[int],
    ) -> float:
        """Score based on days to expiration.
        
        Heuristic: 20-60 days is preferred (15 pts), too short or too long is less ideal.
        """
        if days_to_expiration is None or days_to_expiration <= 0:
            return 0.0
        
        # Prefer 20-60 days
        if 20 <= days_to_expiration <= 60:
            return OptionsSignalService.MAX_EXPIRATION_SCORE
        elif 10 <= days_to_expiration < 20:
            return 10.0
        elif 60 < days_to_expiration <= 90:
            return 10.0
        elif 5 <= days_to_expiration < 10:
            return 5.0
        elif 90 < days_to_expiration <= 180:
            return 5.0
        else:
            return 1.0
    
    @staticmethod
    def _score_momentum(
        recent_price_change: Optional[float],
        implied_volatility: Optional[float],
    ) -> float:
        """Score based on recent price movement and IV.
        
        Heuristic: Moderate IV and recent movement suggest active market (15 pts).
        """
        score = 0.0
        
        # Recent price change (as decimal, e.g., 0.05 for 5%)
        if recent_price_change is not None:
            abs_change = abs(recent_price_change)
            if 0.01 <= abs_change <= 0.10:  # 1-10% is moderate
                score += 8.0
            elif abs_change > 0.10:  # High volatility
                score += 5.0
            else:  # Very low change
                score += 2.0
        
        # Implied volatility
        if implied_volatility is not None:
            if OptionsSignalService.LOW_IV_THRESHOLD <= implied_volatility <= OptionsSignalService.HIGH_IV_THRESHOLD:
                score += 7.0
            elif implied_volatility < OptionsSignalService.LOW_IV_THRESHOLD:
                score += 3.0
            else:  # Very high IV
                score += 4.0
        
        return min(score, OptionsSignalService.MAX_MOMENTUM_SCORE)
    
    @staticmethod
    def _score_data_quality(
        bid: Optional[float],
        ask: Optional[float],
        volume: Optional[int],
        open_interest: Optional[int],
        implied_volatility: Optional[float],
        strike: Optional[float],
        underlying_price: Optional[float],
        days_to_expiration: Optional[int],
    ) -> float:
        """Score data completeness and quality.
        
        Heuristic: More complete data = higher score (max 20 pts).
        """
        fields_present = 0
        fields_total = 8
        
        if bid is not None:
            fields_present += 1
        if ask is not None:
            fields_present += 1
        if volume is not None:
            fields_present += 1
        if open_interest is not None:
            fields_present += 1
        if implied_volatility is not None:
            fields_present += 1
        if strike is not None:
            fields_present += 1
        if underlying_price is not None:
            fields_present += 1
        if days_to_expiration is not None:
            fields_present += 1
        
        # Linear scoring: 100% data = 20 pts
        return (fields_present / fields_total) * OptionsSignalService.MAX_DATA_QUALITY_SCORE
    
    @staticmethod
    def _generate_warnings(
        bid: Optional[float],
        ask: Optional[float],
        volume: Optional[int],
        open_interest: Optional[int],
        implied_volatility: Optional[float],
        underlying_price: Optional[float],
        days_to_expiration: Optional[int],
    ) -> List[str]:
        """Generate warning flags for data quality and risk factors."""
        warnings = []
        
        # Wide spread
        if bid is not None and ask is not None and underlying_price is not None and underlying_price > 0:
            spread_pct = (ask - bid) / underlying_price
            if spread_pct > OptionsSignalService.SPREAD_WARNING_THRESHOLD:
                warnings.append("wide_spread")
        
        # Low volume
        if volume is not None and volume < OptionsSignalService.LOW_VOLUME_THRESHOLD:
            warnings.append("low_volume")
        
        # Low open interest
        if open_interest is not None and open_interest < OptionsSignalService.LOW_OI_THRESHOLD:
            warnings.append("low_open_interest")
        
        # Extreme IV
        if implied_volatility is not None:
            if implied_volatility < OptionsSignalService.LOW_IV_THRESHOLD:
                warnings.append("very_low_iv")
            elif implied_volatility > OptionsSignalService.HIGH_IV_THRESHOLD:
                warnings.append("very_high_iv")
        
        # Very short expiration
        if days_to_expiration is not None and days_to_expiration < 5:
            warnings.append("very_short_expiration")
        
        # Missing critical data
        if bid is None or ask is None:
            warnings.append("missing_bid_ask")
        if volume is None:
            warnings.append("missing_volume")
        if open_interest is None:
            warnings.append("missing_open_interest")
        if implied_volatility is None:
            warnings.append("missing_iv")
        
        return warnings
    
    @staticmethod
    def _derive_grade(score: float, warnings: List[str]) -> str:
        """Derive risk/confidence grade from score and warnings.
        
        Grades: "avoid", "watchlist", "interesting", "high_risk"
        """
        # High warning count suggests caution
        critical_warnings = {
            "wide_spread", "low_volume", "low_open_interest",
            "very_short_expiration", "missing_bid_ask"
        }
        critical_count = sum(1 for w in warnings if w in critical_warnings)
        
        if critical_count >= 3 or score < 30:
            return "avoid"
        elif critical_count >= 2 or score < 50:
            return "watchlist"
        elif score >= 70 and critical_count == 0:
            return "interesting"
        elif "very_high_iv" in warnings or "very_low_iv" in warnings:
            return "high_risk"
        else:
            return "watchlist"
    
    @staticmethod
    def _generate_explanation(breakdown: Dict[str, float], warnings: List[str], grade: str) -> str:
        """Generate human-readable explanation of the score."""
        parts = []
        
        # Identify strongest factors
        sorted_factors = sorted(breakdown.items(), key=lambda x: x[1], reverse=True)
        top_factor = sorted_factors[0][0]
        top_score = sorted_factors[0][1]
        
        if top_score > 0:
            parts.append(f"Strong {top_factor} ({top_score:.1f} pts).")
        
        # Identify weakest factors
        weak_factors = [f for f, s in sorted_factors if s < 5]
        if weak_factors:
            parts.append(f"Weak {', '.join(weak_factors)}.")
        
        # Warnings summary
        if warnings:
            warning_summary = ", ".join(warnings[:3])
            if len(warnings) > 3:
                warning_summary += f" (+{len(warnings) - 3} more)"
            parts.append(f"Warnings: {warning_summary}.")
        
        # Grade-based guidance
        if grade == "avoid":
            parts.append("Not recommended for trading.")
        elif grade == "watchlist":
            parts.append("Monitor for improvement before trading.")
        elif grade == "interesting":
            parts.append("Meets quality criteria; consider further analysis.")
        elif grade == "high_risk":
            parts.append("High risk; requires careful consideration.")
        
        return " ".join(parts) if parts else "Insufficient data for detailed analysis."
