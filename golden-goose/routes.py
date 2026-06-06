from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from models import User, Post, Stock, StockPrice
from forms import UserForm, PostForm
from services.stock_service import StockService
from config import Config
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Create blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Home page - Hello World"""
    return render_template('index.html', title='Golden Goose')

@main_bp.route('/users')
def users():
    """List all users"""
    all_users = User.query.all()
    return render_template('users.html', users=all_users)

@main_bp.route('/user/create', methods=['GET', 'POST'])
def create_user():
    """Create a new user"""
    form = UserForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data
        )
        db.session.add(user)
        db.session.commit()
        flash('User created successfully!', 'success')
        return redirect(url_for('main.users'))
    return render_template('create_user.html', form=form)

@main_bp.route('/api/users', methods=['GET'])
def api_users():
    """API endpoint - return users as JSON"""
    all_users = User.query.all()
    return jsonify([user.to_dict() for user in all_users])

@main_bp.route('/api/posts', methods=['GET'])
def api_posts():
    """API endpoint - return posts as JSON"""
    all_posts = Post.query.all()
    return jsonify([post.to_dict() for post in all_posts])

@main_bp.route('/about')
def about():
    """About page"""
    return render_template('about.html', title='About Golden Goose')

# Stock API endpoints

@main_bp.route('/api/stocks', methods=['GET'])
def api_stocks():
    """API endpoint - return all tracked stocks"""
    try:
        all_stocks = Stock.query.all()
        return jsonify({
            'success': True,
            'count': len(all_stocks),
            'stocks': [stock.to_dict() for stock in all_stocks]
        })
    except Exception as e:
        logger.error(f"Error fetching stocks: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/api/stocks/<symbol>', methods=['GET'])
def api_stock_detail(symbol):
    """API endpoint - return details for a specific stock"""
    try:
        stock = Stock.query.filter_by(symbol=symbol.upper()).first()
        if not stock:
            return jsonify({'success': False, 'error': 'Stock not found'}), 404
        
        return jsonify({
            'success': True,
            'stock': stock.to_dict()
        })
    except Exception as e:
        logger.error(f"Error fetching stock {symbol}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/api/stocks/<symbol>/prices', methods=['GET'])
def api_stock_prices(symbol):
    """API endpoint - return price history for a stock"""
    try:
        stock = Stock.query.filter_by(symbol=symbol.upper()).first()
        if not stock:
            return jsonify({'success': False, 'error': 'Stock not found'}), 404
        
        # Get query parameters
        limit = request.args.get('limit', 100, type=int)
        start_date = request.args.get('start_date', type=str)
        end_date = request.args.get('end_date', type=str)
        
        # Build query
        query = StockPrice.query.filter_by(stock_id=stock.id)
        
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date)
                query = query.filter(StockPrice.timestamp >= start_dt)
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid start_date format'}), 400
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date)
                query = query.filter(StockPrice.timestamp <= end_dt)
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid end_date format'}), 400
        
        # Order by timestamp descending and limit
        prices = query.order_by(StockPrice.timestamp.desc()).limit(limit).all()
        
        return jsonify({
            'success': True,
            'symbol': symbol.upper(),
            'count': len(prices),
            'prices': [price.to_dict() for price in prices]
        })
    except Exception as e:
        logger.error(f"Error fetching prices for {symbol}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/api/stocks/<symbol>/latest', methods=['GET'])
def api_stock_latest(symbol):
    """API endpoint - return latest price for a stock"""
    try:
        stock = Stock.query.filter_by(symbol=symbol.upper()).first()
        if not stock:
            return jsonify({'success': False, 'error': 'Stock not found'}), 404
        
        latest_price = StockPrice.query.filter_by(stock_id=stock.id).order_by(
            StockPrice.timestamp.desc()
        ).first()
        
        if not latest_price:
            return jsonify({'success': False, 'error': 'No price data available'}), 404
        
        return jsonify({
            'success': True,
            'symbol': symbol.upper(),
            'latest_price': latest_price.to_dict()
        })
    except Exception as e:
        logger.error(f"Error fetching latest price for {symbol}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/api/stocks', methods=['POST'])
def api_add_stock():
    """API endpoint - add a new stock to track"""
    try:
        data = request.get_json()
        if not data or 'symbol' not in data:
            return jsonify({'success': False, 'error': 'Symbol is required'}), 400
        
        symbol = data['symbol'].upper()
        name = data.get('name')
        exchange = data.get('exchange')
        
        # Check if stock already exists
        existing = Stock.query.filter_by(symbol=symbol).first()
        if existing:
            return jsonify({'success': False, 'error': 'Stock already exists'}), 409
        
        # Create new stock
        stock = Stock(
            symbol=symbol,
            name=name,
            exchange=exchange
        )
        db.session.add(stock)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Stock {symbol} added successfully',
            'stock': stock.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding stock: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/api/stocks/<symbol>/import', methods=['POST'])
def api_import_stock_data(symbol):
    """API endpoint - manually trigger stock data import"""
    try:
        from flask import current_app
        
        # Get API configuration
        api_key = current_app.config.get('STOCK_API_KEY')
        api_provider = current_app.config.get('STOCK_API_PROVIDER', 'alphavantage')
        
        if not api_key:
            return jsonify({'success': False, 'error': 'Stock API not configured'}), 500
        
        # Get data type from request
        data = request.get_json() or {}
        data_type = data.get('data_type', 'daily')
        
        if data_type not in ['quote', 'intraday', 'daily']:
            return jsonify({'success': False, 'error': 'Invalid data_type'}), 400
        
        # Initialize service and import data
        stock_service = StockService(api_key, api_provider)
        success = stock_service.import_stock_data(symbol.upper(), data_type)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Successfully imported {data_type} data for {symbol.upper()}'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to import data for {symbol.upper()}'
            }), 500
    except Exception as e:
        logger.error(f"Error importing stock data for {symbol}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/api/stocks/<symbol>', methods=['DELETE'])
def api_delete_stock(symbol):
    """API endpoint - remove a stock from tracking"""
    try:
        stock = Stock.query.filter_by(symbol=symbol.upper()).first()
        if not stock:
            return jsonify({'success': False, 'error': 'Stock not found'}), 404
        
        # Delete associated prices first
        StockPrice.query.filter_by(stock_id=stock.id).delete()
        
        # Delete stock
        db.session.delete(stock)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Stock {symbol.upper()} deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting stock {symbol}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
