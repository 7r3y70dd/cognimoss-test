from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from models import User, Post
from forms import UserForm, PostForm

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
