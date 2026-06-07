"""Tests for WTForms form classes"""

import pytest
from forms import UserForm, PostForm


class TestUserForm:
    """Tests for UserForm"""
    
    def test_user_form_valid(self, app):
        """Test UserForm with valid data"""
        with app.test_request_context():
            form = UserForm(data={
                'username': 'testuser',
                'email': 'test@example.com'
            })
            assert form.validate() is True
    
    def test_user_form_missing_username(self, app):
        """Test UserForm with missing username"""
        with app.test_request_context():
            form = UserForm(data={
                'email': 'test@example.com'
            })
            assert form.validate() is False
            assert 'username' in form.errors
    
    def test_user_form_missing_email(self, app):
        """Test UserForm with missing email"""
        with app.test_request_context():
            form = UserForm(data={
                'username': 'testuser'
            })
            assert form.validate() is False
            assert 'email' in form.errors
    
    def test_user_form_invalid_email(self, app):
        """Test UserForm with invalid email format"""
        with app.test_request_context():
            form = UserForm(data={
                'username': 'testuser',
                'email': 'invalid-email'
            })
            assert form.validate() is False
            assert 'email' in form.errors
    
    def test_user_form_username_too_short(self, app):
        """Test UserForm with username too short"""
        with app.test_request_context():
            form = UserForm(data={
                'username': 'ab',  # Less than 3 characters
                'email': 'test@example.com'
            })
            assert form.validate() is False
            assert 'username' in form.errors
    
    def test_user_form_username_too_long(self, app):
        """Test UserForm with username too long"""
        with app.test_request_context():
            form = UserForm(data={
                'username': 'a' * 81,  # More than 80 characters
                'email': 'test@example.com'
            })
            assert form.validate() is False
            assert 'username' in form.errors
    
    def test_user_form_empty_data(self, app):
        """Test UserForm with empty data"""
        with app.test_request_context():
            form = UserForm(data={})
            assert form.validate() is False
            assert 'username' in form.errors
            assert 'email' in form.errors


class TestPostForm:
    """Tests for PostForm"""
    
    def test_post_form_valid(self, app):
        """Test PostForm with valid data"""
        with app.test_request_context():
            form = PostForm(data={
                'title': 'Test Post',
                'content': 'This is test content'
            })
            assert form.validate() is True
    
    def test_post_form_missing_title(self, app):
        """Test PostForm with missing title"""
        with app.test_request_context():
            form = PostForm(data={
                'content': 'This is test content'
            })
            assert form.validate() is False
            assert 'title' in form.errors
    
    def test_post_form_missing_content(self, app):
        """Test PostForm with missing content"""
        with app.test_request_context():
            form = PostForm(data={
                'title': 'Test Post'
            })
            assert form.validate() is False
            assert 'content' in form.errors
    
    def test_post_form_title_too_long(self, app):
        """Test PostForm with title too long"""
        with app.test_request_context():
            form = PostForm(data={
                'title': 'a' * 201,  # More than 200 characters
                'content': 'This is test content'
            })
            assert form.validate() is False
            assert 'title' in form.errors
    
    def test_post_form_empty_content(self, app):
        """Test PostForm with empty content"""
        with app.test_request_context():
            form = PostForm(data={
                'title': 'Test Post',
                'content': ''
            })
            assert form.validate() is False
            assert 'content' in form.errors
    
    def test_post_form_whitespace_only_content(self, app):
        """Test PostForm with whitespace-only content"""
        with app.test_request_context():
            form = PostForm(data={
                'title': 'Test Post',
                'content': '   '
            })
            # WTForms DataRequired strips whitespace
            assert form.validate() is False
            assert 'content' in form.errors
    
    def test_post_form_empty_data(self, app):
        """Test PostForm with empty data"""
        with app.test_request_context():
            form = PostForm(data={})
            assert form.validate() is False
            assert 'title' in form.errors
            assert 'content' in form.errors
    
    def test_post_form_long_valid_content(self, app):
        """Test PostForm with long but valid content"""
        with app.test_request_context():
            form = PostForm(data={
                'title': 'Test Post',
                'content': 'a' * 5000  # Long content should be valid
            })
            assert form.validate() is True
