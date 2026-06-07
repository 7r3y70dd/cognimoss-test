"""Pytest configuration and fixtures for Golden Goose tests"""

import pytest
import sys
import os
from datetime import datetime

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db as _db
from models import User, Post, Stock, StockPrice, StockOption, WatchlistItem
from config import TestingConfig


@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    app = create_app(TestingConfig)
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    
    with app.app_context():
        yield app


@pytest.fixture(scope='function')
def db(app):
    """Create database for testing"""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope='function')
def client(app, db):
    """Create test client"""
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """Create CLI test runner"""
    return app.test_cli_runner()


@pytest.fixture
def sample_user(db):
    """Create a sample user for testing"""
    user = User(
        username='testuser',
        email='test@example.com'
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def sample_post(db, sample_user):
    """Create a sample post for testing"""
    post = Post(
        title='Test Post',
        content='This is test content',
        user_id=sample_user.id
    )
    db.session.add(post)
    db.session.commit()
    return post


@pytest.fixture
def sample_stock(db):
    """Create a sample stock for testing"""
    stock = Stock(
        symbol='AAPL',
        name='Apple Inc.',
        exchange='NASDAQ',
        currency='USD'
    )
    db.session.add(stock)
    db.session.commit()
    return stock


@pytest.fixture
def sample_stock_price(db, sample_stock):
    """Create a sample stock price for testing"""
    price = StockPrice(
        stock_id=sample_stock.id,
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        open_price=150.0,
        high_price=155.0,
        low_price=149.0,
        close_price=153.0,
        volume=1000000
    )
    db.session.add(price)
    db.session.commit()
    return price


@pytest.fixture
def sample_stock_option(db, sample_stock):
    """Create a sample stock option for testing"""
    option = StockOption(
        stock_id=sample_stock.id,
        option_type='call',
        strike_price=160.0,
        expiration_date=datetime(2024, 2, 1),
        current_price=153.0,
        predicted_price=155.0,
        volatility=25.5,
        success_probability=0.72,
        confidence_score=0.65,
        rsi=55.0,
        macd=0.5,
        moving_avg_20=152.0,
        moving_avg_50=151.0,
        recommendation='buy',
        notes='Sample option analysis'
    )
    db.session.add(option)
    db.session.commit()
    return option


@pytest.fixture
def sample_watchlist_item(db, sample_user, sample_stock):
    """Create a sample watchlist item for testing"""
    watchlist_item = WatchlistItem(
        user_id=sample_user.id,
        stock_id=sample_stock.id,
        notes='Monitoring this stock'
    )
    db.session.add(watchlist_item)
    db.session.commit()
    return watchlist_item


@pytest.fixture
def multiple_users(db):
    """Create multiple users for testing"""
    users = [
        User(username='user1', email='user1@example.com'),
        User(username='user2', email='user2@example.com'),
        User(username='user3', email='user3@example.com')
    ]
    for user in users:
        db.session.add(user)
    db.session.commit()
    return users


@pytest.fixture
def multiple_stocks(db):
    """Create multiple stocks for testing"""
    stocks = [
        Stock(symbol='AAPL', name='Apple Inc.', exchange='NASDAQ'),
        Stock(symbol='GOOGL', name='Alphabet Inc.', exchange='NASDAQ'),
        Stock(symbol='MSFT', name='Microsoft Corporation', exchange='NASDAQ')
    ]
    for stock in stocks:
        db.session.add(stock)
    db.session.commit()
    return stocks
