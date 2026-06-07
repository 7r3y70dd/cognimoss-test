"""Tests for database models"""

import pytest
from datetime import datetime
from models import User, Post, Stock, StockPrice


class TestUserModel:
    """Tests for User model"""
    
    def test_create_user(self, db):
        """Test creating a user"""
        user = User(username='newuser', email='new@example.com')
        db.session.add(user)
        db.session.commit()
        
        assert user.id is not None
        assert user.username == 'newuser'
        assert user.email == 'new@example.com'
        assert user.created_at is not None
    
    def test_user_repr(self, sample_user):
        """Test user string representation"""
        assert repr(sample_user) == '<User testuser>'
    
    def test_user_to_dict(self, sample_user):
        """Test user serialization to dictionary"""
        user_dict = sample_user.to_dict()
        
        assert user_dict['id'] == sample_user.id
        assert user_dict['username'] == 'testuser'
        assert user_dict['email'] == 'test@example.com'
        assert 'created_at' in user_dict
    
    def test_user_unique_username(self, db, sample_user):
        """Test that username must be unique"""
        duplicate_user = User(username='testuser', email='other@example.com')
        db.session.add(duplicate_user)
        
        with pytest.raises(Exception):  # IntegrityError
            db.session.commit()
    
    def test_user_unique_email(self, db, sample_user):
        """Test that email must be unique"""
        duplicate_user = User(username='otheruser', email='test@example.com')
        db.session.add(duplicate_user)
        
        with pytest.raises(Exception):  # IntegrityError
            db.session.commit()
    
    def test_user_posts_relationship(self, db, sample_user, sample_post):
        """Test user-posts relationship"""
        assert len(sample_user.posts) == 1
        assert sample_user.posts[0].title == 'Test Post'


class TestPostModel:
    """Tests for Post model"""
    
    def test_create_post(self, db, sample_user):
        """Test creating a post"""
        post = Post(
            title='New Post',
            content='New content',
            user_id=sample_user.id
        )
        db.session.add(post)
        db.session.commit()
        
        assert post.id is not None
        assert post.title == 'New Post'
        assert post.content == 'New content'
        assert post.user_id == sample_user.id
        assert post.created_at is not None
    
    def test_post_repr(self, sample_post):
        """Test post string representation"""
        assert repr(sample_post) == '<Post Test Post>'
    
    def test_post_to_dict(self, sample_post):
        """Test post serialization to dictionary"""
        post_dict = sample_post.to_dict()
        
        assert post_dict['id'] == sample_post.id
        assert post_dict['title'] == 'Test Post'
        assert post_dict['content'] == 'This is test content'
        assert post_dict['user_id'] == sample_post.user_id
        assert 'created_at' in post_dict
    
    def test_post_user_relationship(self, sample_post, sample_user):
        """Test post-user relationship"""
        assert sample_post.user.id == sample_user.id
        assert sample_post.user.username == 'testuser'


class TestStockModel:
    """Tests for Stock model"""
    
    def test_create_stock(self, db):
        """Test creating a stock"""
        stock = Stock(
            symbol='TSLA',
            name='Tesla Inc.',
            exchange='NASDAQ',
            currency='USD'
        )
        db.session.add(stock)
        db.session.commit()
        
        assert stock.id is not None
        assert stock.symbol == 'TSLA'
        assert stock.name == 'Tesla Inc.'
        assert stock.exchange == 'NASDAQ'
        assert stock.currency == 'USD'
        assert stock.created_at is not None
        assert stock.updated_at is not None
    
    def test_stock_repr(self, sample_stock):
        """Test stock string representation"""
        assert repr(sample_stock) == '<Stock AAPL>'
    
    def test_stock_to_dict(self, sample_stock):
        """Test stock serialization to dictionary"""
        stock_dict = sample_stock.to_dict()
        
        assert stock_dict['id'] == sample_stock.id
        assert stock_dict['symbol'] == 'AAPL'
        assert stock_dict['name'] == 'Apple Inc.'
        assert stock_dict['exchange'] == 'NASDAQ'
        assert stock_dict['currency'] == 'USD'
        assert 'created_at' in stock_dict
        assert 'updated_at' in stock_dict
    
    def test_stock_unique_symbol(self, db, sample_stock):
        """Test that stock symbol must be unique"""
        duplicate_stock = Stock(symbol='AAPL', name='Duplicate')
        db.session.add(duplicate_stock)
        
        with pytest.raises(Exception):  # IntegrityError
            db.session.commit()
    
    def test_stock_prices_relationship(self, db, sample_stock, sample_stock_price):
        """Test stock-prices relationship"""
        assert len(sample_stock.prices) == 1
        assert sample_stock.prices[0].close_price == 153.0


class TestStockPriceModel:
    """Tests for StockPrice model"""
    
    def test_create_stock_price(self, db, sample_stock):
        """Test creating a stock price"""
        price = StockPrice(
            stock_id=sample_stock.id,
            timestamp=datetime(2024, 1, 2, 12, 0, 0),
            open_price=154.0,
            high_price=156.0,
            low_price=153.0,
            close_price=155.0,
            volume=1500000
        )
        db.session.add(price)
        db.session.commit()
        
        assert price.id is not None
        assert price.stock_id == sample_stock.id
        assert price.timestamp == datetime(2024, 1, 2, 12, 0, 0)
        assert price.open_price == 154.0
        assert price.high_price == 156.0
        assert price.low_price == 153.0
        assert price.close_price == 155.0
        assert price.volume == 1500000
        assert price.created_at is not None
    
    def test_stock_price_repr(self, sample_stock_price, sample_stock):
        """Test stock price string representation"""
        assert repr(sample_stock_price) == f'<StockPrice {sample_stock.id} @ 2024-01-01 12:00:00>'
    
    def test_stock_price_to_dict(self, sample_stock_price, sample_stock):
        """Test stock price serialization to dictionary"""
        price_dict = sample_stock_price.to_dict()
        
        assert price_dict['id'] == sample_stock_price.id
        assert price_dict['stock_id'] == sample_stock.id
        assert price_dict['symbol'] == 'AAPL'
        assert price_dict['open'] == 150.0
        assert price_dict['high'] == 155.0
        assert price_dict['low'] == 149.0
        assert price_dict['close'] == 153.0
        assert price_dict['volume'] == 1000000
        assert 'timestamp' in price_dict
        assert 'created_at' in price_dict
    
    def test_stock_price_stock_relationship(self, sample_stock_price, sample_stock):
        """Test stock price-stock relationship"""
        assert sample_stock_price.stock.id == sample_stock.id
        assert sample_stock_price.stock.symbol == 'AAPL'
    
    def test_stock_price_unique_constraint(self, db, sample_stock, sample_stock_price):
        """Test that stock_id + timestamp must be unique"""
        duplicate_price = StockPrice(
            stock_id=sample_stock.id,
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            close_price=160.0
        )
        db.session.add(duplicate_price)
        
        with pytest.raises(Exception):  # IntegrityError
            db.session.commit()
