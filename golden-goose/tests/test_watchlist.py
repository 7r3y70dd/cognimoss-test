"""Tests for watchlist functionality"""

import pytest
from models import User, Stock, WatchlistItem
from extensions import db


class TestWatchlistModel:
    """Test WatchlistItem model"""
    
    def test_watchlist_item_creation(self, sample_user, sample_stock):
        """Test creating a watchlist item"""
        watchlist_item = WatchlistItem(
            user_id=sample_user.id,
            stock_id=sample_stock.id,
            notes='Test note'
        )
        db.session.add(watchlist_item)
        db.session.commit()
        
        assert watchlist_item.id is not None
        assert watchlist_item.user_id == sample_user.id
        assert watchlist_item.stock_id == sample_stock.id
        assert watchlist_item.notes == 'Test note'
    
    def test_watchlist_item_to_dict(self, sample_watchlist_item):
        """Test watchlist item to_dict method"""
        item_dict = sample_watchlist_item.to_dict()
        
        assert item_dict['id'] == sample_watchlist_item.id
        assert item_dict['user_id'] == sample_watchlist_item.user_id
        assert item_dict['stock_id'] == sample_watchlist_item.stock_id
        assert item_dict['symbol'] == 'AAPL'
        assert item_dict['notes'] == 'Monitoring this stock'
    
    def test_watchlist_item_unique_constraint(self, sample_user, sample_stock, db):
        """Test that duplicate watchlist entries are prevented"""
        # Create first watchlist item
        item1 = WatchlistItem(
            user_id=sample_user.id,
            stock_id=sample_stock.id
        )
        db.session.add(item1)
        db.session.commit()
        
        # Try to create duplicate
        item2 = WatchlistItem(
            user_id=sample_user.id,
            stock_id=sample_stock.id
        )
        db.session.add(item2)
        
        with pytest.raises(Exception):  # IntegrityError
            db.session.commit()
        db.session.rollback()
    
    def test_watchlist_item_repr(self, sample_watchlist_item):
        """Test watchlist item string representation"""
        repr_str = repr(sample_watchlist_item)
        assert 'WatchlistItem' in repr_str
        assert str(sample_watchlist_item.user_id) in repr_str
        assert str(sample_watchlist_item.stock_id) in repr_str


class TestWatchlistRelationships:
    """Test watchlist relationships"""
    
    def test_user_watchlist_relationship(self, sample_user, sample_stock, db):
        """Test user to watchlist relationship"""
        watchlist_item = WatchlistItem(
            user_id=sample_user.id,
            stock_id=sample_stock.id
        )
        db.session.add(watchlist_item)
        db.session.commit()
        
        # Refresh user to load relationship
        user = User.query.get(sample_user.id)
        assert len(user.watchlist_items) == 1
        assert user.watchlist_items[0].stock_id == sample_stock.id
    
    def test_stock_watchlist_relationship(self, sample_user, sample_stock, db):
        """Test stock to watchlist relationship"""
        watchlist_item = WatchlistItem(
            user_id=sample_user.id,
            stock_id=sample_stock.id
        )
        db.session.add(watchlist_item)
        db.session.commit()
        
        # Refresh stock to load relationship
        stock = Stock.query.get(sample_stock.id)
        assert len(stock.watchlist_items) == 1
        assert stock.watchlist_items[0].user_id == sample_user.id
    
    def test_multiple_users_same_stock(self, multiple_users, sample_stock, db):
        """Test multiple users can watch the same stock"""
        for user in multiple_users:
            watchlist_item = WatchlistItem(
                user_id=user.id,
                stock_id=sample_stock.id
            )
            db.session.add(watchlist_item)
        db.session.commit()
        
        stock = Stock.query.get(sample_stock.id)
        assert len(stock.watchlist_items) == len(multiple_users)
    
    def test_user_multiple_stocks(self, sample_user, multiple_stocks, db):
        """Test user can watch multiple stocks"""
        for stock in multiple_stocks:
            watchlist_item = WatchlistItem(
                user_id=sample_user.id,
                stock_id=stock.id
            )
            db.session.add(watchlist_item)
        db.session.commit()
        
        user = User.query.get(sample_user.id)
        assert len(user.watchlist_items) == len(multiple_stocks)


class TestWatchlistAPI:
    """Test watchlist API endpoints"""
    
    def test_get_empty_watchlist(self, client, sample_user):
        """Test getting empty watchlist"""
        response = client.get(f'/api/watchlist/{sample_user.id}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['count'] == 0
        assert data['watchlist'] == []
    
    def test_get_watchlist_with_items(self, client, sample_watchlist_item, sample_user):
        """Test getting watchlist with items"""
        response = client.get(f'/api/watchlist/{sample_user.id}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['count'] == 1
        assert len(data['watchlist']) == 1
        assert data['watchlist'][0]['symbol'] == 'AAPL'
    
    def test_get_nonexistent_user_watchlist(self, client):
        """Test getting watchlist for nonexistent user"""
        response = client.get('/api/watchlist/99999')
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False
        assert 'User not found' in data['error']
    
    def test_add_to_watchlist(self, client, sample_user, sample_stock):
        """Test adding stock to watchlist"""
        response = client.post(
            f'/api/watchlist/{sample_user.id}',
            json={
                'symbol': sample_stock.symbol,
                'notes': 'Test note'
            }
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert data['watchlist_item']['symbol'] == 'AAPL'
        assert data['watchlist_item']['notes'] == 'Test note'
    
    def test_add_to_watchlist_missing_symbol(self, client, sample_user):
        """Test adding to watchlist without symbol"""
        response = client.post(
            f'/api/watchlist/{sample_user.id}',
            json={}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'Symbol is required' in data['error']
    
    def test_add_nonexistent_stock_to_watchlist(self, client, sample_user):
        """Test adding nonexistent stock to watchlist"""
        response = client.post(
            f'/api/watchlist/{sample_user.id}',
            json={'symbol': 'NONEXISTENT'}
        )
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False
        assert 'Stock not found' in data['error']
    
    def test_add_duplicate_to_watchlist(self, client, sample_user, sample_watchlist_item):
        """Test adding duplicate stock to watchlist"""
        response = client.post(
            f'/api/watchlist/{sample_user.id}',
            json={'symbol': 'AAPL'}
        )
        
        assert response.status_code == 409
        data = response.get_json()
        assert data['success'] is False
        assert 'already in watchlist' in data['error']
    
    def test_remove_from_watchlist(self, client, sample_user, sample_watchlist_item, sample_stock):
        """Test removing stock from watchlist"""
        response = client.delete(
            f'/api/watchlist/{sample_user.id}/{sample_stock.id}'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'Removed' in data['message']
    
    def test_remove_nonexistent_from_watchlist(self, client, sample_user, sample_stock):
        """Test removing nonexistent item from watchlist"""
        response = client.delete(
            f'/api/watchlist/{sample_user.id}/{sample_stock.id}'
        )
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False
        assert 'not found' in data['error']
    
    def test_add_multiple_stocks_to_watchlist(self, client, sample_user, multiple_stocks):
        """Test adding multiple stocks to watchlist"""
        for stock in multiple_stocks:
            response = client.post(
                f'/api/watchlist/{sample_user.id}',
                json={'symbol': stock.symbol}
            )
            assert response.status_code == 201
        
        # Verify all stocks are in watchlist
        response = client.get(f'/api/watchlist/{sample_user.id}')
        data = response.get_json()
        assert data['count'] == len(multiple_stocks)
    
    def test_watchlist_case_insensitive(self, client, sample_user, sample_stock):
        """Test that watchlist handles case-insensitive symbols"""
        response = client.post(
            f'/api/watchlist/{sample_user.id}',
            json={'symbol': 'aapl'}  # lowercase
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['watchlist_item']['symbol'] == 'AAPL'


class TestWatchlistCascadeDelete:
    """Test watchlist cascade delete behavior"""
    
    def test_delete_user_removes_watchlist_items(self, sample_user, sample_watchlist_item, db):
        """Test that deleting user removes their watchlist items"""
        user_id = sample_user.id
        
        # Verify watchlist item exists
        item = WatchlistItem.query.filter_by(user_id=user_id).first()
        assert item is not None
        
        # Delete user
        db.session.delete(sample_user)
        db.session.commit()
        
        # Verify watchlist item is deleted
        item = WatchlistItem.query.filter_by(user_id=user_id).first()
        assert item is None
    
    def test_delete_stock_removes_watchlist_items(self, sample_user, sample_stock, sample_watchlist_item, db):
        """Test that deleting stock removes watchlist items"""
        stock_id = sample_stock.id
        
        # Verify watchlist item exists
        item = WatchlistItem.query.filter_by(stock_id=stock_id).first()
        assert item is not None
        
        # Delete stock
        db.session.delete(sample_stock)
        db.session.commit()
        
        # Verify watchlist item is deleted
        item = WatchlistItem.query.filter_by(stock_id=stock_id).first()
        assert item is None
