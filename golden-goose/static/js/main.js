// Golden Goose - Main JavaScript

// Simple console greeting
console.log('Golden Goose Flask Application Loaded!');

// Auto-hide flash messages after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.alert');
    
    flashMessages.forEach(function(message) {
        setTimeout(function() {
            message.style.transition = 'opacity 0.5s';
            message.style.opacity = '0';
            setTimeout(function() {
                message.remove();
            }, 500);
        }, 5000);
    });
});

// Form validation helper
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
        const inputs = form.querySelectorAll('input[required], textarea[required]');
        let isValid = true;
        
        inputs.forEach(function(input) {
            if (!input.value.trim()) {
                isValid = false;
                input.classList.add('error');
            } else {
                input.classList.remove('error');
            }
        });
        
        if (!isValid) {
            e.preventDefault();
            alert('Please fill in all required fields.');
        }
    });
}

// API fetch helper example
async function fetchUsers() {
    try {
        const response = await fetch('/api/users');
        const users = await response.json();
        console.log('Users:', users);
        return users;
    } catch (error) {
        console.error('Error fetching users:', error);
    }
}

// Example: Log API data on page load
if (window.location.pathname === '/users') {
    fetchUsers();
}
