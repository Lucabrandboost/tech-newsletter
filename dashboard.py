from flask import Flask, render_template, jsonify
from datetime import datetime
import os
from run_newsletter import health
import psutil
import requests

app = Flask(__name__)

def get_system_stats():
    """Get system statistics"""
    return {
        'cpu_percent': psutil.cpu_percent(),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_usage': psutil.disk_usage('/').percent
    }

def get_newsletter_stats():
    """Get newsletter service statistics"""
    return {
        'last_success': health.last_success,
        'failures': health.failures,
        'status': 'healthy' if health.failures < 3 else 'failing'
    }

@app.route('/')
def dashboard():
    return render_template('dashboard.html', 
                         system_stats=get_system_stats(),
                         newsletter_stats=get_newsletter_stats())

@app.route('/api/stats')
def stats():
    """API endpoint for real-time updates"""
    return jsonify({
        'system': get_system_stats(),
        'newsletter': get_newsletter_stats(),
        'timestamp': datetime.now().isoformat()
    })