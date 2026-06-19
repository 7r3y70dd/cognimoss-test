"""Explainable options signal scoring service"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class OptionSignalScore:
    """Structured output for option signal scoring"""
    
    def __init__(
        self,
        symbol: str,
        strategy: str,
        score: float,
        grade: str,
        breakdown: Dict[str, float],
        warnings: List[str],
        explanation: str
    ):
        self.symbol = symbol
        self.strategy = strategy
        self.score = score
        self.grade = grade
        self.breakdown = breakdown
        self.warnings = warnings
        self.explanation = explanation
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'symbol': self.symbol,
            'strategy': self.strategy,
            'score': self.score,
            'grade': self.grade,
            'breakdown': self.breakdown,
            'warnings': self.warnings,
            'explanation': self.explanation
        }


class OptionsSignalService:
    """Service for scoring option contracts using explainable heuristic factors
    
    This service produces structured, explainable candidate scores for option contracts.
    It does not claim to predict profitable trades or provide financial advice.
    """
    
    # Scoring constants (heuristic thresholds)
    MAX_SCORE = 100.0
    LIQUIDITY_MAX = 20.0
    SPREAD_MAX = 20.0
    MONEYNESS_MAX = 15.0
    EXPIRATION_MAX = 15.0
    MOMENTUM_MAX = 15.0
    DATA_QUALITY_MAX = 15.0
    
    # Thresholds for warnings and scoring
    MIN_VOLUME = 100
    MIN_OPEN_INTEREST = 50
    MAX_SPREAD_PERCENT = 0.05  # 5% spread is considered wide
    MIN_DAYS_TO_EXPIRATION = 1
    MAX_DAYS_TO_EXPIRATION = 90
    
    def __init__(self):
        """Initialize options signal service"""
        pass
    
    def score_option_contract(self, option_data: Dict[str, Any]) -> OptionSignalScore:
        """Score a single option contract using explainable factors
        
        Args:
            option_data: Dictionary with option contract data. Expected keys:
                - symbol: Stock symbol (required)
                - bid: Bid price (optional)
                - ask: Ask price (optional)
                - volume: Trading volume (optional)
                - open_interest: Open interest (optional)
                - implied_volatility: IV as decimal (optional)
                - strike: Strike price (optional)
                - underlying_price: Current underlying stock price (optional)
                - expiration_date: Expiration date as datetime or string (optional)
                - contract_type: 'call' or 'put' (optional)
        
        Returns:
            OptionSignalScore with structured scoring breakdown
        """
        try:
            symbol = option_data.get('symbol', 'UNKNOWN').upper()
            contract_type = option_data.get('contract_type', 'unknown').lower()
            strategy = f"{contract_type}_candidate"
            
            # Calculate individual factor scores
            liquidity_score = self._score_liquidity(option_data)
            spread_score = self._score_spread(option_data)
            moneyness_score = self._score_moneyness(option_data)
            expiration_score = self._score_expiration(option_data)
            momentum_score = self._score_momentum(option_data)
            data_quality_score = self._score_data_quality(option_data)
            
            # Aggregate scores
            total_score = (
                liquidity_score +
                spread_score +
                moneyness_score +
                expiration_score +
                momentum_score +
                data_quality_score
            )
            
            # Generate warnings
            warnings = self._generate_warnings(option_data, total_score)
            
            # Determine grade
            grade = self._determine_grade(total_score, warnings)
            
            # Generate explanation
            explanation = self._generate_explanation(
                option_data, total_score, warnings, grade
            )
            
            breakdown = {
                'liquidity': round(liquidity_score, 1),
                'spread': round(spread_score, 1),
                'moneyness': round(moneyness_score, 1),
                'expiration': round(expiration_score, 1),
                'momentum': round(momentum_score, 1),
                'data_quality': round(data_quality_score, 1)
            }
            
            return OptionSignalScore(
                symbol=symbol,
                strategy=strategy,
                score=round(total_score, 1),
                grade=grade,
                breakdown=breakdown,
                warnings=warnings,
                explanation=explanation
            )
        except Exception as e:
            logger.error(f"Error scoring option contract: {e}")
            # Return neutral score on error
            return OptionSignalScore(
                symbol=option_data.get('symbol', 'UNKNOWN').upper(),
                strategy='unknown_candidate',
                score=0.0,
                grade='avoid',
                breakdown={
                    'liquidity': 0.0,
                    'spread': 0.0,
                    'moneyness': 0.0,
                    'expiration': 0.0,
                    'momentum': 0.0,
                    'data_quality': 0.0
                },
                warnings=['scoring_error'],
                explanation='Unable to score contract due to processing error.'
            )
    
    def _score_liquidity(self, option_data: Dict[str, Any]) -> float:
        """Score liquidity based on volume and open interest
        
        Heuristic: Higher volume and open interest indicate better liquidity.
        """
        volume = option_data.get('volume', 0)
        open_interest = option_data.get('open_interest', 0)
        
        if volume is None:
            volume = 0
        if open_interest is None:
            open_interest = 0
        
        # Normalize volume (assume 1000+ is good)
        volume_score = min(volume / 1000.0, 1.0) * 10.0
        
        # Normalize open interest (assume 500+ is good)
        oi_score = min(open_interest / 500.0, 1.0) * 10.0
        
        return volume_score + oi_score
    
    def _score_spread(self, option_data: Dict[str, Any]) -> float:
        """Score bid/ask spread width
        
        Heuristic: Tighter spreads indicate better liquidity and lower transaction costs.
        """
        bid = option_data.get('bid')
        ask = option_data.get('ask')
        
        if bid is None or ask is None or bid <= 0 or ask <= 0:
            return 0.0  # No data
        
        if bid > ask:
            bid, ask = ask, bid  # Swap if reversed
        
        spread = ask - bid
        mid = (bid + ask) / 2.0
        
        if mid <= 0:
            return 0.0
        
        spread_percent = spread / mid
        
        # Score inversely: tighter spread = higher score
        # 0.5% spread = 20 points, 5% spread = 0 points
        if spread_percent <= 0.005:
            return self.SPREAD_MAX
        elif spread_percent >= 0.05:
            return 0.0
        else:
            # Linear interpolation
            return self.SPREAD_MAX * (1.0 - (spread_percent - 0.005) / (0.05 - 0.005))
    
    def _score_moneyness(self, option_data: Dict[str, Any]) -> float:
        """Score moneyness (how close strike is to underlying price)
        
        Heuristic: At-the-money (ATM) options have better liquidity and defined risk.
        """
        strike = option_data.get('strike')
        underlying_price = option_data.get('underlying_price')
        
        if strike is None or underlying_price is None or underlying_price <= 0:
            return 0.0  # No data
        
        # Calculate moneyness ratio
        moneyness = strike / underlying_price
        
        # Score based on distance from ATM (1.0)
        # ATM (0.95-1.05) = 15 points
        # Slightly OTM/ITM (0.90-1.10) = 10 points
        # Far OTM/ITM (0.80-1.20) = 5 points
        # Very far (< 0.80 or > 1.20) = 0 points
        
        distance = abs(moneyness - 1.0)
        
        if distance <= 0.05:
            return self.MONEYNESS_MAX
        elif distance <= 0.10:
            return self.MONEYNESS_MAX * 0.67
        elif distance <= 0.20:
            return self.MONEYNESS_MAX * 0.33
        else:
            return 0.0
    
    def _score_expiration(self, option_data: Dict[str, Any]) -> float:
        """Score days to expiration
        
        Heuristic: Options with 7-60 days to expiration offer good time decay vs. movement.
        """
        expiration_date = option_data.get('expiration_date')
        
        if expiration_date is None:
            return 0.0  # No data
        
        # Parse expiration date if string
        if isinstance(expiration_date, str):
            try:
                expiration_date = datetime.strptime(expiration_date, '%Y-%m-%d')
            except (ValueError, TypeError):
                return 0.0
        
        # Calculate days to expiration
        now = datetime.utcnow()
        days_to_exp = (expiration_date - now).days
        
        # Score based on days to expiration
        # 7-60 days = 15 points (sweet spot)
        # 1-6 days = 5 points (too short)
        # 61-90 days = 10 points (acceptable)
        # > 90 days = 5 points (too much time decay)
        # <= 0 days = 0 points (expired)
        
        if days_to_exp <= 0:
            return 0.0
        elif 7 <= days_to_exp <= 60:
            return self.EXPIRATION_MAX
        elif 1 <= days_to_exp < 7:
            return self.EXPIRATION_MAX * 0.33
        elif 61 <= days_to_exp <= 90:
            return self.EXPIRATION_MAX * 0.67
        else:
            return self.EXPIRATION_MAX * 0.33
    
    def _score_momentum(self, option_data: Dict[str, Any]) -> float:
        """Score recent underlying stock movement
        
        Heuristic: Moderate recent movement (5-20%) indicates volatility opportunity.
        """
        recent_move = option_data.get('recent_move_percent')
        
        if recent_move is None:
            return 0.0  # No data
        
        # Use absolute value of move
        abs_move = abs(recent_move)
        
        # Score based on movement magnitude
        # 5-20% move = 15 points (good volatility)
        # 2-5% or 20-30% = 10 points (acceptable)
        # < 2% or > 30% = 5 points (too stable or too volatile)
        
        if 5.0 <= abs_move <= 20.0:
            return self.MOMENTUM_MAX
        elif (2.0 <= abs_move < 5.0) or (20.0 < abs_move <= 30.0):
            return self.MOMENTUM_MAX * 0.67
        else:
            return self.MOMENTUM_MAX * 0.33
    
    def _score_data_quality(self, option_data: Dict[str, Any]) -> float:
        """Score data completeness and quality
        
        Heuristic: More complete data = higher confidence in scoring.
        """
        required_fields = ['bid', 'ask', 'volume', 'open_interest', 'implied_volatility']
        present_fields = sum(1 for field in required_fields if option_data.get(field) is not None)
        
        # Score based on data completeness
        # All 5 fields = 15 points
        # 4 fields = 12 points
        # 3 fields = 9 points
        # 2 fields = 6 points
        # 1 field = 3 points
        # 0 fields = 0 points
        
        return (present_fields / len(required_fields)) * self.DATA_QUALITY_MAX
    
    def _generate_warnings(self, option_data: Dict[str, Any], score: float) -> List[str]:
        """Generate warning flags for data quality and risk factors"""
        warnings = []
        
        # Check for wide spread
        bid = option_data.get('bid')
        ask = option_data.get('ask')
        if bid is not None and ask is not None and bid > 0 and ask > 0:
            spread_percent = (ask - bid) / ((bid + ask) / 2.0)
            if spread_percent > self.MAX_SPREAD_PERCENT:
                warnings.append('wide_spread')
        
        # Check for low volume
        volume = option_data.get('volume')
        if volume is not None and volume < self.MIN_VOLUME:
            warnings.append('low_volume')
        
        # Check for low open interest
        open_interest = option_data.get('open_interest')
        if open_interest is not None and open_interest < self.MIN_OPEN_INTEREST:
            warnings.append('low_open_interest')
        
        # Check for missing implied volatility
        if option_data.get('implied_volatility') is None:
            warnings.append('missing_iv')
        
        # Check for missing bid/ask
        if bid is None or ask is None:
            warnings.append('missing_bid_ask')
        
        # Check for expiration soon
        expiration_date = option_data.get('expiration_date')
        if expiration_date is not None:
            if isinstance(expiration_date, str):
                try:
                    expiration_date = datetime.strptime(expiration_date, '%Y-%m-%d')
                except (ValueError, TypeError):
                    pass
            if isinstance(expiration_date, datetime):
                days_to_exp = (expiration_date - datetime.utcnow()).days
                if days_to_exp <= 1:
                    warnings.append('expiring_soon')
        
        # Check for expired contract
        if expiration_date is not None:
            if isinstance(expiration_date, str):
                try:
                    expiration_date = datetime.strptime(expiration_date, '%Y-%m-%d')
                except (ValueError, TypeError):
                    pass
            if isinstance(expiration_date, datetime):
                if expiration_date < datetime.utcnow():
                    warnings.append('expired')
        
        return warnings
    
    def _determine_grade(self, score: float, warnings: List[str]) -> str:
        """Determine grade based on score and warnings
        
        Grades:
        - avoid: score < 30 or has critical warnings
        - watchlist: score 30-60, minimal warnings
        - interesting: score 60-80, no critical warnings
        - high_risk: score > 80 but has warnings
        """
        critical_warnings = {'expired', 'expiring_soon', 'wide_spread', 'low_open_interest'}
        has_critical = any(w in critical_warnings for w in warnings)
        
        if score < 30 or (has_critical and score < 50):
            return 'avoid'
        elif score < 60:
            return 'watchlist'
        elif score < 80:
            if has_critical:
                return 'watchlist'
            return 'interesting'
        else:
            if has_critical:
                return 'interesting'
            return 'high_risk'
    
    def _generate_explanation(self, option_data: Dict[str, Any], score: float,
                             warnings: List[str], grade: str) -> str:
        """Generate human-readable explanation of the score"""
        symbol = option_data.get('symbol', 'contract').upper()
        
        # Build explanation based on score and warnings
        if grade == 'avoid':
            if 'expired' in warnings:
                return f"{symbol} contract has expired and cannot be traded."
            elif 'expiring_soon' in warnings:
                return f"{symbol} contract expires very soon, limiting time for movement."
            else:
                return f"{symbol} contract scores poorly ({score:.1f}/100) due to weak liquidity, wide spreads, or incomplete data."
        
        elif grade == 'watchlist':
            explanation = f"{symbol} contract has acceptable characteristics ({score:.1f}/100)"
            if 'wide_spread' in warnings:
                explanation += " but spread width is notable"
            if 'low_open_interest' in warnings:
                explanation += " and open interest is low"
            explanation += ". Monitor for improvement before trading."
            return explanation
        
        elif grade == 'interesting':
            explanation = f"{symbol} contract shows good signal quality ({score:.1f}/100)"
            if warnings:
                explanation += f" despite {', '.join(warnings)}"
            explanation += ". Consider for further analysis."
            return explanation
        
        else:  # high_risk
            return f"{symbol} contract scores very well ({score:.1f}/100) with strong liquidity and favorable characteristics. Suitable for active trading."
    
    def rank_option_contracts(self, option_list: List[Dict[str, Any]],
                             reverse: bool = True) -> List[OptionSignalScore]:
        """Score and rank multiple option contracts
        
        Args:
            option_list: List of option contract dictionaries
            reverse: If True, sort by score descending (highest first)
        
        Returns:
            List of OptionSignalScore objects sorted by score
        """
        scores = [self.score_option_contract(opt) for opt in option_list]
        scores.sort(key=lambda x: x.score, reverse=reverse)
        return scores
