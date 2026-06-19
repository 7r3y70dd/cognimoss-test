"""Stock options analysis and prediction service"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from app import db
from models import Stock, StockPrice, StockOption

logger = logging.getLogger(__name__)

class OptionsService:
    """Service for analyzing stocks and predicting option trade success"""
    
    def __init__(self):
        """Initialize options service"""
        pass
    
    def get_price_history(self, symbol: str, days: int = 60) -> Optional[pd.DataFrame]:
        """
        Get price history for a stock as pandas DataFrame
        
        Args:
            symbol: Stock symbol
            days: Number of days of history to retrieve
            
        Returns:
            DataFrame with price history or None if insufficient data
        """
        try:
            stock = Stock.query.filter_by(symbol=symbol.upper()).first()
            if not stock:
                logger.warning(f"Stock {symbol} not found")
                return None
            
            # Get prices from last N days
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            prices = StockPrice.query.filter(
                StockPrice.stock_id == stock.id,
                StockPrice.timestamp >= cutoff_date
            ).order_by(StockPrice.timestamp.asc()).all()
            
            if len(prices) < 20:  # Need minimum data for analysis
                logger.warning(f"Insufficient price data for {symbol}: {len(prices)} records")
                return None
            
            # Convert to DataFrame
            data = [{
                'timestamp': p.timestamp,
                'open': p.open_price,
                'high': p.high_price,
                'low': p.low_price,
                'close': p.close_price,
                'volume': p.volume
            } for p in prices]
            
            df = pd.DataFrame(data)
            df.set_index('timestamp', inplace=True)
            return df
            
        except Exception as e:
            logger.error(f"Error retrieving price history for {symbol}: {str(e)}")
            return None
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> Optional[float]:
        """
        Calculate Relative Strength Index
        
        Args:
            prices: Series of closing prices
            period: RSI period (default 14)
            
        Returns:
            RSI value or None if insufficient data
        """
        try:
            if len(prices) < period + 1:
                return None
            
            deltas = np.diff(prices)
            seed = deltas[:period+1]
            up = seed[seed >= 0].sum() / period
            down = -seed[seed < 0].sum() / period
            rs = up / down if down != 0 else 0
            rsi = 100. - 100. / (1. + rs)
            return float(rsi)
        except Exception as e:
            logger.error(f"Error calculating RSI: {str(e)}")
            return None
    
    def calculate_macd(self, prices: pd.Series) -> Optional[Tuple[float, float, float]]:
        """
        Calculate MACD (Moving Average Convergence Divergence)
        
        Args:
            prices: Series of closing prices
            
        Returns:
            Tuple of (macd, signal, histogram) or None if insufficient data
        """
        try:
            if len(prices) < 26:
                return None
            
            ema_12 = prices.ewm(span=12).mean()
            ema_26 = prices.ewm(span=26).mean()
            macd = ema_12 - ema_26
            signal = macd.ewm(span=9).mean()
            histogram = macd - signal
            
            return (float(macd.iloc[-1]), float(signal.iloc[-1]), float(histogram.iloc[-1]))
        except Exception as e:
            logger.error(f"Error calculating MACD: {str(e)}")
            return None
    
    def calculate_volatility(self, prices: pd.Series, period: int = 20) -> Optional[float]:
        """
        Calculate historical volatility
        
        Args:
            prices: Series of closing prices
            period: Period for volatility calculation
            
        Returns:
            Volatility value or None if insufficient data
        """
        try:
            if len(prices) < period:
                return None
            
            returns = prices.pct_change()
            volatility = returns.std() * np.sqrt(252)  # Annualized
            return float(volatility)
        except Exception as e:
            logger.error(f"Error calculating volatility: {str(e)}")
            return None
    
    def predict_price_movement(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Predict price movement for a stock based on technical indicators
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with prediction data or None if error
        """
        try:
            df = self.get_price_history(symbol)
            if df is None or len(df) < 26:
                return None
            
            prices = df['close']
            rsi = self.calculate_rsi(prices)
            macd_data = self.calculate_macd(prices)
            volatility = self.calculate_volatility(prices)
            
            if rsi is None or macd_data is None:
                return None
            
            macd, signal, histogram = macd_data
            
            # Simple prediction logic
            bullish_signals = 0
            if rsi < 30:
                bullish_signals += 1
            if histogram > 0:
                bullish_signals += 1
            
            prediction = {
                'symbol': symbol,
                'rsi': rsi,
                'macd': macd,
                'signal': signal,
                'histogram': histogram,
                'volatility': volatility,
                'bullish_signals': bullish_signals,
                'prediction': 'bullish' if bullish_signals >= 2 else 'bearish'
            }
            
            return prediction
        except Exception as e:
            logger.error(f"Error predicting price movement for {symbol}: {str(e)}")
            return None


class OptionsSignalService:
    """
    Service for generating explainable option signal scores.
    
    Scores option contracts using explainable factors such as liquidity,
    spread width, volume/open interest, implied volatility, moneyness,
    days to expiration, and recent underlying stock movement.
    
    Returns structured output with numeric scores, factor breakdowns,
    warning flags, and human-readable explanations.
    """
    
    # Score thresholds for risk labels
    SCORE_THRESHOLDS = {
        'avoid': 40,
        'watchlist': 60,
        'interesting': 75,
        'high_risk': 100
    }
    
    def __init__(self):
        """Initialize options signal service"""
        self.options_service = OptionsService()
    
    def _score_liquidity(self, volume: Optional[float], open_interest: Optional[float]) -> Tuple[float, List[str]]:
        """
        Score liquidity based on volume and open interest.
        
        Args:
            volume: Trading volume for the contract
            open_interest: Open interest for the contract
            
        Returns:
            Tuple of (score, warnings)
        """
        warnings = []
        score = 0.0
        
        # Handle missing data
        if volume is None and open_interest is None:
            warnings.append('no_liquidity_data')
            return 0.0, warnings
        
        # Score based on volume
        if volume is not None:
            if volume >= 1000:
                score += 10.0
            elif volume >= 100:
                score += 6.0
            elif volume > 0:
                score += 2.0
                warnings.append('low_volume')
            else:
                warnings.append('zero_volume')
        
        # Score based on open interest
        if open_interest is not None:
            if open_interest >= 1000:
                score += 8.0
            elif open_interest >= 100:
                score += 4.0
            elif open_interest > 0:
                score += 1.0
                warnings.append('low_open_interest')
            else:
                warnings.append('zero_open_interest')
        
        return min(score, 20.0), warnings
    
    def _score_spread(self, bid: Optional[float], ask: Optional[float], underlying_price: Optional[float]) -> Tuple[float, List[str]]:
        """
        Score spread width relative to underlying price.
        
        Args:
            bid: Bid price
            ask: Ask price
            underlying_price: Current underlying stock price
            
        Returns:
            Tuple of (score, warnings)
        """
        warnings = []
        
        if bid is None or ask is None:
            warnings.append('no_spread_data')
            return 0.0, warnings
        
        if bid <= 0 or ask <= 0:
            warnings.append('invalid_spread_data')
            return 0.0, warnings
        
        spread = ask - bid
        
        # If we have underlying price, score relative to it
        if underlying_price is not None and underlying_price > 0:
            spread_pct = (spread / underlying_price) * 100
            
            if spread_pct < 0.5:
                score = 16.0
            elif spread_pct < 1.0:
                score = 12.0
            elif spread_pct < 2.0:
                score = 8.0
            elif spread_pct < 5.0:
                score = 4.0
                warnings.append('wide_spread')
            else:
                score = 1.0
                warnings.append('very_wide_spread')
        else:
            # Score based on absolute spread
            if spread < 0.05:
                score = 16.0
            elif spread < 0.10:
                score = 12.0
            elif spread < 0.25:
                score = 8.0
            elif spread < 0.50:
                score = 4.0
                warnings.append('wide_spread')
            else:
                score = 1.0
                warnings.append('very_wide_spread')
        
        return score, warnings
    
    def _score_moneyness(self, strike: Optional[float], underlying_price: Optional[float], contract_type: Optional[str]) -> Tuple[float, List[str]]:
        """
        Score moneyness (how close strike is to current price).
        
        Args:
            strike: Strike price
            underlying_price: Current underlying stock price
            contract_type: 'call' or 'put'
            
        Returns:
            Tuple of (score, warnings)
        """
        warnings = []
        
        if strike is None or underlying_price is None or underlying_price <= 0:
            warnings.append('no_moneyness_data')
            return 0.0, warnings
        
        moneyness = underlying_price / strike if strike > 0 else 0
        
        # Near-the-money (0.95-1.05) scores highest
        if 0.95 <= moneyness <= 1.05:
            score = 12.0
        # Slightly out-of-money or in-the-money (0.90-1.10)
        elif 0.90 <= moneyness <= 1.10:
            score = 10.0
        # Moderately out-of-money or in-the-money (0.80-1.20)
        elif 0.80 <= moneyness <= 1.20:
            score = 6.0
        # Far out-of-money or deep in-the-money
        else:
            score = 2.0
            warnings.append('far_from_money')
        
        return score, warnings
    
    def _score_expiration(self, days_to_expiration: Optional[int]) -> Tuple[float, List[str]]:
        """
        Score based on days to expiration.
        
        Prefers contracts with 20-60 days to expiration (sweet spot for theta decay).
        
        Args:
            days_to_expiration: Number of days until expiration
            
        Returns:
            Tuple of (score, warnings)
        """
        warnings = []
        
        if days_to_expiration is None or days_to_expiration <= 0:
            warnings.append('invalid_expiration')
            return 0.0, warnings
        
        # Sweet spot: 20-60 days
        if 20 <= days_to_expiration <= 60:
            score = 10.0
        # Acceptable: 10-20 or 60-90 days
        elif (10 <= days_to_expiration < 20) or (60 < days_to_expiration <= 90):
            score = 7.0
        # Less ideal: < 10 days (theta decay accelerates)
        elif days_to_expiration < 10:
            score = 3.0
            warnings.append('near_expiration')
        # Less ideal: > 90 days (high time decay cost)
        else:
            score = 4.0
            warnings.append('far_expiration')
        
        return score, warnings
    
    def _score_momentum(self, symbol: Optional[str], underlying_price: Optional[float]) -> Tuple[float, List[str]]:
        """
        Score recent underlying stock movement using technical indicators.
        
        Args:
            symbol: Stock symbol
            underlying_price: Current underlying stock price
            
        Returns:
            Tuple of (score, warnings)
        """
        warnings = []
        
        if symbol is None:
            warnings.append('no_symbol_for_momentum')
            return 0.0, warnings
        
        try:
            prediction = self.options_service.predict_price_movement(symbol)
            if prediction is None:
                warnings.append('insufficient_price_history')
                return 0.0, warnings
            
            rsi = prediction.get('rsi')
            bullish_signals = prediction.get('bullish_signals', 0)
            
            # Score based on RSI and bullish signals
            if bullish_signals >= 2:
                score = 9.0
            elif bullish_signals == 1:
                score = 5.0
            else:
                score = 2.0
            
            # Adjust for extreme RSI
            if rsi is not None:
                if rsi < 30 or rsi > 70:
                    score += 1.0  # Potential reversal
            
            return min(score, 10.0), warnings
        except Exception as e:
            logger.error(f"Error scoring momentum for {symbol}: {str(e)}")
            warnings.append('momentum_calculation_error')
            return 0.0, warnings
    
    def _score_implied_volatility(self, implied_volatility: Optional[float]) -> Tuple[float, List[str]]:
        """
        Score implied volatility.
        
        Moderate IV (0.20-0.50) is preferred; very low or very high IV increases risk.
        
        Args:
            implied_volatility: Implied volatility as decimal (e.g., 0.25 for 25%)
            
        Returns:
            Tuple of (score, warnings)
        """
        warnings = []
        
        if implied_volatility is None or implied_volatility < 0:
            warnings.append('no_iv_data')
            return 0.0, warnings
        
        # Moderate IV (0.20-0.50) is ideal
        if 0.20 <= implied_volatility <= 0.50:
            score = 9.5
        # Slightly low or high (0.15-0.20 or 0.50-0.70)
        elif (0.15 <= implied_volatility < 0.20) or (0.50 < implied_volatility <= 0.70):
            score = 6.0
        # Very low IV (< 0.15)
        elif implied_volatility < 0.15:
            score = 2.0
            warnings.append('very_low_iv')
        # Very high IV (> 0.70)
        else:
            score = 3.0
            warnings.append('very_high_iv')
        
        return score, warnings
    
    def _score_data_quality(self, missing_fields: List[str]) -> Tuple[float, List[str]]:
        """
        Score data quality based on missing fields.
        
        Args:
            missing_fields: List of field names that are missing or None
            
        Returns:
            Tuple of (score, warnings)
        """
        warnings = []
        
        if not missing_fields:
            return 10.0, warnings
        
        # Deduct points for each missing field
        score = 10.0 - (len(missing_fields) * 1.5)
        score = max(score, 0.0)
        
        if len(missing_fields) > 0:
            warnings.append('incomplete_data')
        
        return score, warnings
    
    def _derive_risk_label(self, score: float, warnings: List[str]) -> str:
        """
        Derive risk label from score and warnings.
        
        Args:
            score: Numeric score (0-100)
            warnings: List of warning flags
            
        Returns:
            Risk label: 'avoid', 'watchlist', 'interesting', or 'high_risk'
        """
        # Penalize for critical warnings
        critical_warnings = {
            'zero_volume', 'zero_open_interest', 'invalid_spread_data',
            'invalid_expiration', 'very_wide_spread'
        }
        
        if any(w in critical_warnings for w in warnings):
            return 'avoid'
        
        if score < self.SCORE_THRESHOLDS['avoid']:
            return 'avoid'
        elif score < self.SCORE_THRESHOLDS['watchlist']:
            return 'watchlist'
        elif score < self.SCORE_THRESHOLDS['interesting']:
            return 'interesting'
        else:
            return 'high_risk'
    
    def _generate_explanation(self, breakdown: Dict[str, float], warnings: List[str], grade: str) -> str:
        """
        Generate human-readable explanation of the score.
        
        Args:
            breakdown: Factor-level score breakdown
            warnings: List of warning flags
            grade: Risk label
            
        Returns:
            Human-readable explanation string
        """
        parts = []
        
        # Identify strongest factors
        sorted_factors = sorted(breakdown.items(), key=lambda x: x[1], reverse=True)
        top_factors = [f for f, s in sorted_factors[:2] if s > 0]
        
        if top_factors:
            parts.append(f"Strong factors: {', '.join(top_factors)}.")
        
        # Identify weak factors
        weak_factors = [f for f, s in sorted_factors if s < 3]
        if weak_factors:
            parts.append(f"Weak factors: {', '.join(weak_factors)}.")
        
        # Add warning context
        if warnings:
            warning_text = ', '.join(warnings.replace('_', ' ') for warnings in warnings[:2])
            parts.append(f"Cautions: {warning_text}.")
        
        # Add grade context
        grade_context = {
            'avoid': "This contract does not meet minimum quality thresholds.",
            'watchlist': "This contract has acceptable characteristics but warrants careful review.",
            'interesting': "This contract shows promising signal quality and may merit further analysis.",
            'high_risk': "This contract scores highly but carries elevated risk; use appropriate position sizing."
        }
        
        parts.append(grade_context.get(grade, "Review this contract carefully."))
        
        return ' '.join(parts)
    
    def score_option_contract(self, contract_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score an option contract using explainable factors.
        
        Args:
            contract_data: Dictionary with option contract information.
                Expected keys (all optional):
                - symbol: Stock symbol (str)
                - expiration: Expiration date (datetime or str)
                - strike: Strike price (float)
                - contract_type: 'call' or 'put' (str)
                - bid: Bid price (float)
                - ask: Ask price (float)
                - last: Last trade price (float)
                - volume: Trading volume (float)
                - open_interest: Open interest (float)
                - implied_volatility: IV as decimal (float)
                - underlying_price: Current stock price (float)
        
        Returns:
            Dictionary with scoring results:
            {
                'symbol': str,
                'strategy': str (e.g., 'call_candidate'),
                'score': float (0-100),
                'grade': str ('avoid', 'watchlist', 'interesting', 'high_risk'),
                'breakdown': dict of factor scores,
                'warnings': list of warning flags,
                'explanation': str
            }
        """
        try:
            # Extract data
            symbol = contract_data.get('symbol', 'UNKNOWN')
            expiration = contract_data.get('expiration')
            strike = contract_data.get('strike')
            contract_type = contract_data.get('contract_type', 'call')
            bid = contract_data.get('bid')
            ask = contract_data.get('ask')
            volume = contract_data.get('volume')
            open_interest = contract_data.get('open_interest')
            implied_volatility = contract_data.get('implied_volatility')
            underlying_price = contract_data.get('underlying_price')
            
            # Calculate days to expiration
            days_to_expiration = None
            if expiration:
                try:
                    if isinstance(expiration, str):
                        exp_date = datetime.fromisoformat(expiration.replace('Z', '+00:00'))
                    else:
                        exp_date = expiration
                    days_to_expiration = (exp_date - datetime.utcnow()).days
                except Exception as e:
                    logger.warning(f"Could not parse expiration date: {str(e)}")
            
            # Track missing fields for data quality score
            missing_fields = []
            if bid is None or ask is None:
                missing_fields.append('bid_ask')
            if volume is None:
                missing_fields.append('volume')
            if open_interest is None:
                missing_fields.append('open_interest')
            if implied_volatility is None:
                missing_fields.append('iv')
            if underlying_price is None:
                missing_fields.append('underlying_price')
            
            # Score each factor
            liquidity_score, liquidity_warnings = self._score_liquidity(volume, open_interest)
            spread_score, spread_warnings = self._score_spread(bid, ask, underlying_price)
            moneyness_score, moneyness_warnings = self._score_moneyness(strike, underlying_price, contract_type)
            expiration_score, expiration_warnings = self._score_expiration(days_to_expiration)
            momentum_score, momentum_warnings = self._score_momentum(symbol, underlying_price)
            iv_score, iv_warnings = self._score_implied_volatility(implied_volatility)
            quality_score, quality_warnings = self._score_data_quality(missing_fields)
            
            # Combine scores
            breakdown = {
                'liquidity': liquidity_score,
                'spread': spread_score,
                'moneyness': moneyness_score,
                'expiration': expiration_score,
                'momentum': momentum_score,
                'implied_volatility': iv_score,
                'data_quality': quality_score
            }
            
            total_score = sum(breakdown.values())
            # Normalize to 0-100 scale (max possible is 7 * 20 = 140, but realistically lower)
            normalized_score = min((total_score / 100.0) * 100, 100.0)
            
            # Combine all warnings
            all_warnings = (
                liquidity_warnings + spread_warnings + moneyness_warnings +
                expiration_warnings + momentum_warnings + iv_warnings + quality_warnings
            )
            # Remove duplicates while preserving order
            unique_warnings = list(dict.fromkeys(all_warnings))
            
            # Derive risk label
            grade = self._derive_risk_label(normalized_score, unique_warnings)
            
            # Generate explanation
            explanation = self._generate_explanation(breakdown, unique_warnings, grade)
            
            return {
                'symbol': symbol,
                'strategy': f"{contract_type}_candidate",
                'score': round(normalized_score, 1),
                'grade': grade,
                'breakdown': {k: round(v, 1) for k, v in breakdown.items()},
                'warnings': unique_warnings,
                'explanation': explanation
            }
        
        except Exception as e:
            logger.error(f"Error scoring option contract: {str(e)}")
            return {
                'symbol': contract_data.get('symbol', 'UNKNOWN'),
                'strategy': 'error',
                'score': 0.0,
                'grade': 'avoid',
                'breakdown': {},
                'warnings': ['scoring_error'],
                'explanation': f"Error during scoring: {str(e)}"
            }
    
    def score_option_chain(self, contracts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Score multiple option contracts and return ranked list.
        
        Args:
            contracts: List of contract data dictionaries
            
        Returns:
            List of scored contracts sorted by score (descending)
        """
        scored = [self.score_option_contract(c) for c in contracts]
        # Sort by score descending, then by grade
        grade_order = {'high_risk': 0, 'interesting': 1, 'watchlist': 2, 'avoid': 3}
        scored.sort(key=lambda x: (-x['score'], grade_order.get(x['grade'], 4)))
        return scored
