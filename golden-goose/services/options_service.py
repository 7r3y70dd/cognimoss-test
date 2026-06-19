"""Options service layer for options chain analysis and scoring."""

from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field


@dataclass
class OptionSignalScore:
    """Structured output for an option contract signal score."""
    symbol: str
    strategy: str  # e.g., "call_candidate", "put_candidate"
    score: float  # 0-100
    grade: str  # "avoid", "watchlist", "interesting", "high_risk"
    breakdown: Dict[str, float] = field(default_factory=dict)  # factor -> points
    warnings: List[str] = field(default_factory=list)  # e.g., "wide_spread", "low_open_interest"
    explanation: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)  # bid, ask, strike, expiration, etc.


class OptionsSignalService:
    """Service for scoring and ranking option contracts with explainable factors.
    
    This service produces structured, explainable signals for options contracts
    based on liquidity, spread, moneyness, volatility, and other factors.
    Output is suitable for UI display, backtesting, or prediction pipelines.
    
    NOTE: This service does NOT provide financial advice or predict future prices.
    It surfaces structured, explainable candidates for further analysis.
    """

    # Scoring constants (heuristic thresholds)
    MAX_SCORE = 100.0
    LIQUIDITY_MAX_POINTS = 20.0
    SPREAD_MAX_POINTS = 15.0
    MONEYNESS_MAX_POINTS = 15.0
    EXPIRATION_MAX_POINTS = 15.0
    MOMENTUM_MAX_POINTS = 15.0
    DATA_QUALITY_MAX_POINTS = 20.0

    def score_option_contract(
        self,
        symbol: str,
        contract_type: str,
        strike: Optional[float] = None,
        expiration: Optional[str] = None,
        bid: Optional[float] = None,
        ask: Optional[float] = None,
        last: Optional[float] = None,
        volume: Optional[int] = None,
        open_interest: Optional[int] = None,
        implied_volatility: Optional[float] = None,
        underlying_price: Optional[float] = None,
        days_to_expiration: Optional[int] = None,
        recent_momentum: Optional[float] = None,
    ) -> OptionSignalScore:
        """Score an option contract using explainable factors.
        
        Args:
            symbol: Stock ticker symbol (e.g., "AAPL")
            contract_type: "call" or "put"
            strike: Strike price
            expiration: Expiration date (e.g., "2024-01-19")
            bid: Bid price
            ask: Ask price
            last: Last trade price
            volume: Trading volume
            open_interest: Open interest
            implied_volatility: IV as decimal (e.g., 0.25 for 25%)
            underlying_price: Current stock price
            days_to_expiration: Days until expiration
            recent_momentum: Recent price momentum of underlying (-1.0 to 1.0)
        
        Returns:
            OptionSignalScore with numeric score, breakdown, warnings, and explanation.
        """
        breakdown = {}
        warnings = []
        metadata = {
            "strike": strike,
            "expiration": expiration,
            "bid": bid,
            "ask": ask,
            "last": last,
            "volume": volume,
            "open_interest": open_interest,
            "implied_volatility": implied_volatility,
            "underlying_price": underlying_price,
            "days_to_expiration": days_to_expiration,
            "recent_momentum": recent_momentum,
        }

        # Score each factor
        breakdown["liquidity"] = self._score_liquidity(
            bid, ask, volume, open_interest, warnings
        )
        breakdown["spread"] = self._score_spread(bid, ask, last, warnings)
        breakdown["moneyness"] = self._score_moneyness(
            strike, underlying_price, contract_type, warnings
        )
        breakdown["expiration"] = self._score_expiration(days_to_expiration, warnings)
        breakdown["momentum"] = self._score_momentum(recent_momentum, warnings)
        breakdown["data_quality"] = self._score_data_quality(
            bid, ask, volume, open_interest, implied_volatility, underlying_price, warnings
        )

        # Aggregate score
        total_score = sum(breakdown.values())
        total_score = min(total_score, self.MAX_SCORE)  # Cap at 100

        # Determine grade based on score and warnings
        grade = self._determine_grade(total_score, warnings)

        # Generate explanation
        explanation = self._generate_explanation(
            symbol, contract_type, total_score, grade, breakdown, warnings
        )

        strategy = f"{contract_type}_candidate"

        return OptionSignalScore(
            symbol=symbol,
            strategy=strategy,
            score=round(total_score, 1),
            grade=grade,
            breakdown={k: round(v, 1) for k, v in breakdown.items()},
            warnings=warnings,
            explanation=explanation,
            metadata=metadata,
        )

    def _score_liquidity(
        self,
        bid: Optional[float],
        ask: Optional[float],
        volume: Optional[int],
        open_interest: Optional[int],
        warnings: List[str],
    ) -> float:
        """Score liquidity based on bid/ask presence, volume, and open interest.
        
        Heuristic: Presence of bid/ask is essential; volume and OI boost score.
        """
        score = 0.0

        # Bid/ask presence is baseline
        if bid is not None and ask is not None:
            score += 8.0
        elif bid is not None or ask is not None:
            score += 4.0
            warnings.append("missing_bid_or_ask")
        else:
            warnings.append("no_bid_ask")
            return 0.0

        # Volume bonus
        if volume is not None and volume > 0:
            if volume >= 100:
                score += 6.0
            elif volume >= 10:
                score += 3.0
            else:
                score += 1.0
        else:
            warnings.append("no_volume")

        # Open interest bonus
        if open_interest is not None and open_interest > 0:
            if open_interest >= 100:
                score += 6.0
            elif open_interest >= 10:
                score += 3.0
            else:
                score += 1.0
        else:
            warnings.append("no_open_interest")

        return min(score, self.LIQUIDITY_MAX_POINTS)

    def _score_spread(
        self,
        bid: Optional[float],
        ask: Optional[float],
        last: Optional[float],
        warnings: List[str],
    ) -> float:
        """Score spread width. Narrower spreads are better.
        
        Heuristic: Spread as % of mid-price; lower % = higher score.
        """
        if bid is None or ask is None:
            warnings.append("cannot_score_spread")
            return 0.0

        if bid >= ask:
            warnings.append("invalid_bid_ask")
            return 0.0

        spread = ask - bid
        mid = (bid + ask) / 2.0

        if mid <= 0:
            warnings.append("invalid_mid_price")
            return 0.0

        spread_pct = (spread / mid) * 100.0

        # Heuristic scoring: tight spread (< 1%) = full points, wide (> 5%) = low points
        if spread_pct < 1.0:
            score = self.SPREAD_MAX_POINTS
        elif spread_pct < 2.0:
            score = self.SPREAD_MAX_POINTS * 0.8
        elif spread_pct < 5.0:
            score = self.SPREAD_MAX_POINTS * 0.5
        else:
            score = self.SPREAD_MAX_POINTS * 0.2
            warnings.append("wide_spread")

        return score

    def _score_moneyness(
        self,
        strike: Optional[float],
        underlying_price: Optional[float],
        contract_type: str,
        warnings: List[str],
    ) -> float:
        """Score moneyness (how close strike is to underlying price).
        
        Heuristic: Near-the-money (ATM) contracts score higher.
        """
        if strike is None or underlying_price is None:
            warnings.append("cannot_score_moneyness")
            return 0.0

        if underlying_price <= 0:
            warnings.append("invalid_underlying_price")
            return 0.0

        # Moneyness: distance from ATM as % of underlying
        distance = abs(strike - underlying_price)
        moneyness_pct = (distance / underlying_price) * 100.0

        # Heuristic: ATM (< 2%) = full points, OTM (> 10%) = low points
        if moneyness_pct < 2.0:
            score = self.MONEYNESS_MAX_POINTS
        elif moneyness_pct < 5.0:
            score = self.MONEYNESS_MAX_POINTS * 0.7
        elif moneyness_pct < 10.0:
            score = self.MONEYNESS_MAX_POINTS * 0.4
        else:
            score = self.MONEYNESS_MAX_POINTS * 0.1

        return score

    def _score_expiration(
        self,
        days_to_expiration: Optional[int],
        warnings: List[str],
    ) -> float:
        """Score expiration. Prefer contracts with reasonable time decay.
        
        Heuristic: 7-60 days = good, < 7 or > 180 = lower score.
        """
        if days_to_expiration is None:
            warnings.append("no_expiration_data")
            return 0.0

        if days_to_expiration < 0:
            warnings.append("expired_contract")
            return 0.0

        # Heuristic: sweet spot is 7-60 days
        if 7 <= days_to_expiration <= 60:
            score = self.EXPIRATION_MAX_POINTS
        elif 1 <= days_to_expiration < 7:
            score = self.EXPIRATION_MAX_POINTS * 0.5
            warnings.append("short_expiration")
        elif 60 < days_to_expiration <= 180:
            score = self.EXPIRATION_MAX_POINTS * 0.7
        else:
            score = self.EXPIRATION_MAX_POINTS * 0.2
            warnings.append("long_expiration")

        return score

    def _score_momentum(
        self,
        recent_momentum: Optional[float],
        warnings: List[str],
    ) -> float:
        """Score recent momentum of underlying stock.
        
        Heuristic: Positive momentum for calls, negative for puts (not implemented here).
        Momentum range: -1.0 to 1.0.
        """
        if recent_momentum is None:
            warnings.append("no_momentum_data")
            return self.MOMENTUM_MAX_POINTS * 0.5  # Neutral score

        # Clamp to [-1, 1]
        momentum = max(-1.0, min(1.0, recent_momentum))

        # Heuristic: positive momentum = higher score
        # Map [-1, 1] to [0, MOMENTUM_MAX_POINTS]
        score = ((momentum + 1.0) / 2.0) * self.MOMENTUM_MAX_POINTS

        return score

    def _score_data_quality(
        self,
        bid: Optional[float],
        ask: Optional[float],
        volume: Optional[int],
        open_interest: Optional[int],
        implied_volatility: Optional[float],
        underlying_price: Optional[float],
        warnings: List[str],
    ) -> float:
        """Score data completeness and quality.
        
        Heuristic: Each present field contributes to quality score.
        """
        score = 0.0
        fields_present = 0
        fields_total = 6

        if bid is not None and ask is not None:
            fields_present += 1
        if volume is not None:
            fields_present += 1
        if open_interest is not None:
            fields_present += 1
        if implied_volatility is not None:
            fields_present += 1
        if underlying_price is not None:
            fields_present += 1
        # Expiration is assumed present in most cases
        fields_present += 1

        # Score based on % of fields present
        completeness = fields_present / fields_total
        score = completeness * self.DATA_QUALITY_MAX_POINTS

        if completeness < 0.5:
            warnings.append("incomplete_data")

        return score

    def _determine_grade(
        self,
        score: float,
        warnings: List[str],
    ) -> str:
        """Determine risk/quality grade based on score and warnings.
        
        Grades: "avoid", "watchlist", "interesting", "high_risk"
        """
        # If critical warnings, downgrade
        critical_warnings = {"expired_contract", "invalid_bid_ask", "no_bid_ask"}
        if any(w in critical_warnings for w in warnings):
            return "avoid"

        # Score-based grading
        if score >= 75:
            return "interesting"
        elif score >= 50:
            return "watchlist"
        elif score >= 25:
            return "watchlist"
        else:
            return "avoid"

    def _generate_explanation(
        self,
        symbol: str,
        contract_type: str,
        score: float,
        grade: str,
        breakdown: Dict[str, float],
        warnings: List[str],
    ) -> str:
        """Generate human-readable explanation of the score."""
        parts = []

        # Opening
        parts.append(
            f"{symbol} {contract_type.upper()} contract scored {score}/100 ({grade})."
        )

        # Strengths
        strengths = [k for k, v in breakdown.items() if v >= 10]
        if strengths:
            parts.append(
                f"Strengths: {', '.join(strengths)} are solid."
            )

        # Weaknesses
        weaknesses = [k for k, v in breakdown.items() if v < 5]
        if weaknesses:
            parts.append(
                f"Concerns: {', '.join(weaknesses)} are weak."
            )

        # Warnings
        if warnings:
            warning_str = ", ".join(warnings)
            parts.append(f"Warnings: {warning_str}.")

        # Disclaimer
        parts.append(
            "This is a structural signal, not financial advice or a price prediction."
        )

        return " ".join(parts)

    def rank_option_contracts(
        self,
        contracts: List[Dict[str, Any]],
    ) -> List[OptionSignalScore]:
        """Rank a list of option contracts by signal score.
        
        Args:
            contracts: List of dicts with keys matching score_option_contract() params.
        
        Returns:
            List of OptionSignalScore sorted by score (descending).
        """
        scores = []
        for contract in contracts:
            score = self.score_option_contract(**contract)
            scores.append(score)

        # Sort by score descending
        scores.sort(key=lambda x: x.score, reverse=True)
        return scores
