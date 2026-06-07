"""Tests for application routes"""

import pytest
import json
from datetime import datetime
from models import User, Post, Stock, StockPrice


class TestBasicRoutes:
    """Tests for basic HTML routes"""
    
    def test_index_route(self, client):
        """Test home page route"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Golden Goose' in response.data
    
    def test_hello_route(self, client):
        """Test hello world route"""
        response = client.get('/hello')
        assert response.status_code == 200
        assert b'Hello World from Golden Goose!' in response.data
    
    def test_about_route(self, client):
        """Test about page route"""
        response = client.get('/about')
        assert response.status_code == 200
        assert b'About' in response.data or b'Golden Goose' in response.data


class TestUserRoutes:
    """Tests for user-related routes"""
    
    def test_users_list_empty(self, client, db):
        """Test users list with no users"""
        response = client.get('/users')
        assert response.status_code == 200
    
    def test_users_list_with_users(self, client, multiple_users):
        """Test users list with multiple users"""
        response = client.get('/users')
        assert response.status_code == 200
        assert b'user1' in response.data
        assert b'user2' in response.data
        assert b'user3' in response.data
    
    def test_create_user_get(self, client):
        """Test GET request to create user form"""
        response = client.get('/user/create')
        assert response.status_code == 200
        assert b'username' in response.data.lower() or b'Username' in response.data
    
    def test_create_user_post_valid(self, client, db):
        """Test POST request to create user with valid data"""
        response = client.post('/user/create', data={
            'username': 'newuser',
            'email': 'newuser@example.com'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        assert user.email == 'newuser@example.com'
    
    def test_create_user_post_invalid(self, client, db):
        """Test POST request to create user with invalid data"""
        response = client.post('/user/create', data={
            'username': 'ab',  # Too short
            'email': 'invalid-email'
        })
        
        assert response.status_code == 200
        user = User.query.filter_by(username='ab').first()
        assert user is None


class TestUserAPIRoutes:
    """Tests for user API endpoints"""
    
    def test_api_users_empty(self, client, db):
        """Test API users endpoint with no users"""
        response = client.get('/api/users')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_api_users_with_data(self, client, multiple_users):
        """Test API users endpoint with multiple users"""
        response = client.get('/api/users')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) == 3
        assert data[0]['username'] == 'user1'
        assert data[1]['username'] == 'user2'
        assert data[2]['username'] == 'user3'


class TestPostAPIRoutes:
    """Tests for post API endpoints"""
    
    def test_api_posts_empty(self, client, db):
        """Test API posts endpoint with no posts"""
        response = client.get('/api/posts')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_api_posts_with_data(self, client, sample_post):
        """Test API posts endpoint with posts"""
        response = client.get('/api/posts')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]['title'] == 'Test Post'
        assert data[0]['content'] == 'This is test content'


class TestStockAPIRoutes:
    """Tests for stock API endpoints"""
    
    def test_api_stocks_empty(self, client, db):
        """Test API stocks endpoint with no stocks"""
        response = client.get('/api/stocks')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['count'] == 0
        assert len(data['stocks']) == 0
    
    def test_api_stocks_with_data(self, client, multiple_stocks):
        """Test API stocks endpoint with multiple stocks"""
        response = client.get('/api/stocks')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['count'] == 3
        assert len(data['stocks']) == 3
    
    def test_api_stock_detail_found(self, client, sample_stock):
        """Test API stock detail endpoint for existing stock"""
        response = client.get('/api/stocks/AAPL')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['stock']['symbol'] == 'AAPL'
        assert data['stock']['name'] == 'Apple Inc.'
    
    def test_api_stock_detail_not_found(self, client, db):
        """Test API stock detail endpoint for non-existent stock"""
        response = client.get('/api/stocks/INVALID')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_api_add_stock_valid(self, client, db):
        """Test adding a new stock via API"""
        response = client.post('/api/stocks',
            data=json.dumps({
                'symbol': 'TSLA',
                'name': 'Tesla Inc.',
                'exchange': 'NASDAQ'
            }),
            content_type='application/json'
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['stock']['symbol'] == 'TSLA'
        
        stock = Stock.query.filter_by(symbol='TSLA').first()
        assert stock is not None
    
    def test_api_add_stock_duplicate(self, client, sample_stock):
        """Test adding a duplicate stock via API"""
        response = client.post('/api/stocks',
            data=json.dumps({
                'symbol': 'AAPL',
                'name': 'Apple Inc.'
            }),
            content_type='application/json'
        )
        assert response.status_code == 409
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_api_add_stock_missing_symbol(self, client, db):
        """Test adding stock without symbol"""
        response = client.post('/api/stocks',
            data=json.dumps({'name': 'Test Company'}),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_api_delete_stock(self, client, sample_stock):
        """Test deleting a stock via API"""
        response = client.delete('/api/stocks/AAPL')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        stock = Stock.query.filter_by(symbol='AAPL').first()
        assert stock is None
    
    def test_api_delete_stock_not_found(self, client, db):
        """Test deleting non-existent stock"""
        response = client.delete('/api/stocks/INVALID')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False


class TestStockPriceAPIRoutes:
    """Tests for stock price API endpoints"""
    
    def test_api_stock_prices(self, client, sample_stock, sample_stock_price):
        """Test API stock prices endpoint"""
        response = client.get('/api/stocks/AAPL/prices')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['symbol'] == 'AAPL'
        assert data['count'] == 1
        assert len(data['prices']) == 1
        assert data['prices'][0]['close'] == 153.0
    
    def test_api_stock_prices_with_limit(self, client, db, sample_stock):
        """Test API stock prices with limit parameter"""
        # Add multiple prices
        for i in range(5):
            price = StockPrice(
                stock_id=sample_stock.id,
                timestamp=datetime(2024, 1, i+1, 12, 0, 0),
                close_price=150.0 + i
            )
            db.session.add(price)
        db.session.commit()
        
        response = client.get('/api/stocks/AAPL/prices?limit=3')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] == 3
    
    def test_api_stock_prices_not_found(self, client, db):
        """Test API stock prices for non-existent stock"""
        response = client.get('/api/stocks/INVALID/prices')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_api_stock_latest(self, client, sample_stock, sample_stock_price):
        """Test API latest stock price endpoint"""
        response = client.get('/api/stocks/AAPL/latest')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['symbol'] == 'AAPL'
        assert data['latest_price']['close'] == 153.0
    
    def test_api_stock_latest_not_found(self, client, db):
        """Test API latest price for non-existent stock"""
        response = client.get('/api/stocks/INVALID/latest')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_api_stock_latest_no_prices(self, client, sample_stock):
        """Test API latest price when no prices exist"""
        response = client.get('/api/stocks/AAPL/latest')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
