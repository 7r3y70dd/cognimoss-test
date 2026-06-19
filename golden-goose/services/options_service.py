"""Stock options analysis and prediction service"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
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
            logger.error(f"Error getting price history for {symbol}: {e}")
            return None
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """
        Calculate Relative Strength Index
        
        Args:
            prices: Series of closing prices
            period: RSI period (default 14)
            
        Returns:
            RSI value (0-100)
        """
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return float(rsi.iloc[-1])
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
            return 50.0  # Neutral value
    
    def calculate_macd(self, prices: pd.Series) -> Tuple[float, float]:
        """
        Calculate MACD (Moving Average Convergence Divergence)
        
        Args:
            prices: Series of closing prices
            
        Returns:
            Tuple of (MACD value, signal line)
        """
        try:
            exp1 = prices.ewm(span=12, adjust=False).mean()
            exp2 = prices.ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()
            return float(macd.iloc[-1]), float(signal.iloc[-1])
        except Exception as e:
            logger.error(f"Error calculating MACD: {e}")
            return 0.0, 0.0
    
    def calculate_volatility(self, prices: pd.Series, period: int = 20) -> float:
        """
        Calculate historical volatility (annualized)
        
        Args:
            prices: Series of closing prices
            period: Period for calculation
            
        Returns:
            Annualized volatility as percentage
        """
        try:
            returns = prices.pct_change().dropna()
            volatility = returns.rolling(window=period).std().iloc[-1]
            # Annualize (assuming 252 trading days)
            annualized_vol = volatility * np.sqrt(252) * 100
            return float(annualized_vol)
        except Exception as e:
            logger.error(f"Error calculating volatility: {e}")
            return 0.0
    
    def predict_price_movement(self, df: pd.DataFrame) -> Dict:
        """
        Predict price movement based on technical indicators
        
        Args:
            df: DataFrame with price history
            
        Returns:
            Dictionary with prediction metrics
        """
        try:
            closes = df['close']
            current_price = float(closes.iloc[-1])
            
            # Calculate indicators
            rsi = self.calculate_rsi(closes)
            macd, signal = self.calculate_macd(closes)
            volatility = self.calculate_volatility(closes)
            ma_20 = float(closes.rolling(window=20).mean().iloc[-1])
            ma_50 = float(closes.rolling(window=50).mean().iloc[-1]) if len(closes) >= 50 else ma_20
            
            # Simple prediction logic based on indicators
            bullish_signals = 0
            bearish_signals = 0
            
            # RSI analysis
            if rsi < 30:
                bullish_signals += 2  # Oversold
            elif rsi > 70:
                bearish_signals += 2  # Overbought
            elif 40 <= rsi <= 60:
                bullish_signals += 1  # Neutral momentum
            
            # MACD analysis
            if macd > signal:
                bullish_signals += 1
            else:
                bearish_signals += 1
            
            # Moving average analysis
            if current_price > ma_20 > ma_50:
                bullish_signals += 2  # Strong uptrend
            elif current_price < ma_20 < ma_50:
                bearish_signals += 2  # Strong downtrend
            elif current_price > ma_20:
                bullish_signals += 1
            else:
                bearish_signals += 1
            
            # Calculate prediction
            total_signals = bullish_signals + bearish_signals
            bullish_probability = bullish_signals / total_signals if total_signals > 0 else 0.5
            
            # Predict price change (simple linear projection)
            recent_trend = (closes.iloc[-1] - closes.iloc[-5]) / closes.iloc[-5]
            predicted_change = recent_trend * 0.5  # Conservative estimate
            predicted_price = current_price * (1 + predicted_change)
            
            # Determine recommendation
            if bullish_probability > 0.65:
                recommendation = 'buy'
            elif bullish_probability < 0.35:
                recommendation = 'sell'
            else:
                recommendation = 'hold'
            
            return {
                'current_price': current_price,
                'predicted_price': predicted_price,
                'volatility': volatility,
                'rsi': rsi,
                'macd': macd,
                'ma_20': ma_20,
                'ma_50': ma_50,
                'bullish_probability': bullish_probability,
                'recommendation': recommendation,
                'confidence': min(abs(bullish_probability - 0.5) * 2, 1.0)  # 0-1 scale
            }
            
        except Exception as e:
            logger.error(f"Error predicting price movement: {e}")
            return None
    
    def analyze_option(self, symbol: str, option_type: str, strike_price: float, 
                      expiration_days: int = 30) -> Optional[Dict]:
        """
        Analyze a stock option and predict success probability
        
        Args:
            symbol: Stock symbol
            option_type: 'call' or 'put'
            strike_price: Option strike price
            expiration_days: Days until expiration
            
        Returns:
            Dictionary with analysis results or None if error
        """
        try:
            # Get price history
            df = self.get_price_history(symbol, days=60)
            if df is None:
                return None
            
            # Get prediction
            prediction = self.predict_price_movement(df)
            if prediction is None:
                return None
            
            current_price = prediction['current_price']
            predicted_price = prediction['predicted_price']
            
            # Calculate option success probability
            if option_type.lower() == 'call':
                # Call option profits if price goes above strike
                price_target = strike_price
                success_prob = prediction['bullish_probability']
                
                # Adjust based on how far strike is from current price
                distance_ratio = (strike_price - current_price) / current_price
                if distance_ratio > 0.1:  # Strike is >10% above current
                    success_prob *= 0.7
                elif distance_ratio < -0.05:  # Strike is already in the money
                    success_prob = min(success_prob * 1.2, 0.95)
                    
            else:  # put
                # Put option profits if price goes below strike
                price_target = strike_price
                success_prob = 1 - prediction['bullish_probability']
                
                # Adjust based on how far strike is from current price
                distance_ratio = (current_price - strike_price) / current_price
                if distance_ratio > 0.1:  # Strike is >10% below current
                    success_prob *= 0.7
                elif distance_ratio < -0.05:  # Strike is already in the money
                    success_prob = min(success_prob * 1.2, 0.95)
            
            # Adjust for time and volatility
            time_factor = min(expiration_days / 30, 1.0)  # Longer time = better
            volatility_factor = min(prediction['volatility'] / 30, 1.5)  # Higher vol = more movement
            
            adjusted_prob = success_prob * (0.7 + 0.3 * time_factor) * (0.8 + 0.2 * volatility_factor)
            adjusted_prob = min(max(adjusted_prob, 0.05), 0.95)  # Clamp between 5% and 95%
            
            # Generate notes
            notes = f"Analysis based on {len(df)} days of price data. "
            notes += f"RSI: {prediction['rsi']:.1f}, "
            notes += f"Volatility: {prediction['volatility']:.1f}%. "
            notes += f"Recommendation: {prediction['recommendation'].upper()}"
            
            return {
                'symbol': symbol.upper(),
                'option_type': option_type.lower(),
                'strike_price': strike_price,
                'expiration_days': expiration_days,
                'current_price': current_price,
                'predicted_price': predicted_price,
                'volatility': prediction['volatility'],
                'success_probability': adjusted_prob,
                'confidence_score': prediction['confidence'],
                'rsi': prediction['rsi'],
                'macd': prediction['macd'],
                'moving_avg_20': prediction['ma_20'],
                'moving_avg_50': prediction['ma_50'],
                'recommendation': prediction['recommendation'],
                'notes': notes
            }
            
        except Exception as e:
            logger.error(f"Error analyzing option for {symbol}: {e}")
            return None
    
    def generate_option_explanation(self, breakdown: Dict[str, float], warnings: List[str]) -> str:
        """
        Generate a plain-English explanation of an option score.
        
        Converts score breakdown and warnings into a short, understandable explanation
        that mentions major positives and negatives without sounding like financial advice.
        
        Args:
            breakdown: Dictionary with factor scores (e.g., {'liquidity': 15, 'spread': 10, ...})
            warnings: List of warning strings (e.g., ['low_volume', 'wide_spread', ...])
            
        Returns:
            Plain-English explanation string
        """
        try:
            if not breakdown:
                return "Unable to generate explanation due to missing score data."
            
            # Identify strong and weak factors
            strong_factors = []
            weak_factors = []
            
            factor_descriptions = {
                'liquidity': 'liquidity',
                'spread': 'bid-ask spread',
                'moneyness': 'strike positioning',
                'expiration': 'time to expiration',
                'momentum': 'recent momentum',
                'data_quality': 'data completeness'
            }
            
            max_score = 20.0  # Approximate max per factor
            
            for factor, score in breakdown.items():
                if score is None:
                    continue
                factor_name = factor_descriptions.get(factor, factor)
                if score >= max_score * 0.7:  # Strong (70%+)
                    strong_factors.append(factor_name)
                elif score <= max_score * 0.3:  # Weak (30%-)
                    weak_factors.append(factor_name)
            
            # Build explanation
            parts = []
            
            if strong_factors:
                parts.append(f"This contract has decent {' and '.join(strong_factors)}.")
            
            if weak_factors:
                if parts:
                    parts.append(f"However, {' and '.join(weak_factors)} are limited.")
                else:
                    parts.append(f"This contract has limited {' and '.join(weak_factors)}.")
            
            # Add warning-based context
            if warnings:
                warning_phrases = []
                for warning in warnings:
                    if 'low_volume' in warning or 'low_open_interest' in warning:
                        warning_phrases.append('low trading activity')
                    elif 'wide_spread' in warning:
                        warning_phrases.append('wide bid-ask spread')
                    elif 'missing_iv' in warning or 'missing_data' in warning:
                        warning_phrases.append('missing market data')
                    elif 'far_otm' in warning or 'far_itm' in warning:
                        warning_phrases.append('unfavorable strike positioning')
                    elif 'near_expiration' in warning:
                        warning_phrases.append('approaching expiration')
                
                if warning_phrases:
                    unique_warnings = list(set(warning_phrases))
                    if parts:
                        parts.append(f"Confidence is reduced by {' and '.join(unique_warnings)}.")
                    else:
                        parts.append(f"This contract has {' and '.join(unique_warnings)}.")
            
            # Fallback if no parts were added
            if not parts:
                parts.append("Analysis data is incomplete. Confidence in this assessment is limited.")
            
            explanation = ' '.join(parts)
            return explanation
            
        except Exception as e:
            logger.error(f"Error generating option explanation: {e}")
            return "Unable to generate explanation due to processing error."
    
    def save_option_analysis(self, analysis: Dict) -> Optional[StockOption]:
        """
        Save option analysis to database
        
        Args:
            analysis: Dictionary with analysis results
            
        Returns:
            StockOption object or None if error
        """
        try:
            stock = Stock.query.filter_