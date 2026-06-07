from datetime import datetime
from extensions import db

class User(db.Model):
    """Example User model - Hello World style"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    watchlist_items = db.relationship('WatchlistItem', backref=db.backref('user', lazy=True), cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Post(db.Model):
    """Example Post model - Hello World style"""
    __tablename__ = 'posts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('posts', lazy=True))
    
    def __repr__(self):
        return f'<Post {self.title}>'
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'user_id': self.user_id
        }

class Stock(db.Model):
    """Stock model for storing stock information"""
    __tablename__ = 'stocks'
    
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=True)
    exchange = db.Column(db.String(50), nullable=True)
    currency = db.Column(db.String(10), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    watchlist_items = db.relationship('WatchlistItem', backref=db.backref('stock', lazy=True), cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Stock {self.symbol}>'
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'name': self.name,
            'exchange': self.exchange,
            'currency': self.currency,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class StockPrice(db.Model):
    """Stock price model for storing historical price data"""
    __tablename__ = 'stock_prices'
    
    id = db.Column(db.Integer, primary_key=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, nullable=False, index=True)
    open_price = db.Column(db.Float, nullable=True)
    high_price = db.Column(db.Float, nullable=True)
    low_price = db.Column(db.Float, nullable=True)
    close_price = db.Column(db.Float, nullable=False)
    volume = db.Column(db.BigInteger, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    stock = db.relationship('Stock', backref=db.backref('prices', lazy=True, order_by='StockPrice.timestamp.desc()'))
    
    # Unique constraint to prevent duplicate entries
    __table_args__ = (
        db.UniqueConstraint('stock_id', 'timestamp', name='unique_stock_timestamp'),
    )
    
    def __repr__(self):
        return f'<StockPrice {self.stock_id} @ {self.timestamp}>'
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'stock_id': self.stock_id,
            'symbol': self.stock.symbol if self.stock else None,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'open': self.open_price,
            'high': self.high_price,
            'low': self.low_price,
            'close': self.close_price,
            'volume': self.volume,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class StockOption(db.Model):
    """Stock option prediction model for storing analysis results"""
    __tablename__ = 'stock_options'
    
    id = db.Column(db.Integer, primary_key=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'), nullable=False, index=True)
    option_type = db.Column(db.String(10), nullable=False)  # 'call' or 'put'
    strike_price = db.Column(db.Float, nullable=False)
    expiration_date = db.Column(db.DateTime, nullable=False)
    prediction_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Analysis metrics
    current_price = db.Column(db.Float, nullable=False)
    predicted_price = db.Column(db.Float, nullable=True)
    volatility = db.Column(db.Float, nullable=True)
    success_probability = db.Column(db.Float, nullable=True)  # 0-1 probability
    confidence_score = db.Column(db.Float, nullable=True)  # 0-1 confidence
    
    # Technical indicators
    rsi = db.Column(db.Float, nullable=True)  # Relative Strength Index
    macd = db.Column(db.Float, nullable=True)  # MACD indicator
    moving_avg_20 = db.Column(db.Float, nullable=True)
    moving_avg_50 = db.Column(db.Float, nullable=True)
    
    # Recommendation
    recommendation = db.Column(db.String(20), nullable=True)  # 'buy', 'sell', 'hold'
    notes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    stock = db.relationship('Stock', backref=db.backref('options', lazy=True, order_by='StockOption.prediction_date.desc()'))
    
    def __repr__(self):
        return f'<StockOption {self.stock_id} {self.option_type} ${self.strike_price}>'
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'stock_id': self.stock_id,
            'symbol': self.stock.symbol if self.stock else None,
            'option_type': self.option_type,
            'strike_price': self.strike_price,
            'expiration_date': self.expiration_date.isoformat() if self.expiration_date else None,
            'prediction_date': self.prediction_date.isoformat() if self.prediction_date else None,
            'current_price': self.current_price,
            'predicted_price': self.predicted_price,
            'volatility': self.volatility,
            'success_probability': self.success_probability,
            'confidence_score': self.confidence_score,
            'rsi': self.rsi,
            'macd': self.macd,
            'moving_avg_20': self.moving_avg_20,
            'moving_avg_50': self.moving_avg_50,
            'recommendation': self.recommendation,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class WatchlistItem(db.Model):
    """Watchlist item model for storing user's watched stocks"""
    __tablename__ = 'watchlist_items'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'), nullable=False, index=True)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)
    
    # Unique constraint to prevent duplicate watchlist entries
    __table_args__ = (
        db.UniqueConstraint('user_id', 'stock_id', name='unique_user_stock_watchlist'),
    )
    
    def __repr__(self):
        return f'<WatchlistItem user_id={self.user_id} stock_id={self.stock_id}>'
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'stock_id': self.stock_id,
            'symbol': self.stock.symbol if self.stock else None,
            'stock_name': self.stock.name if self.stock else None,
            'added_at': self.added_at.isoformat() if self.added_at else None,
            'notes': self.notes
        }
