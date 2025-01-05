from flask import Flask, jsonify
from datetime import datetime
import os
import psutil
from run_newsletter import health

app = Flask(__name__)

def get_uptime():
    """Get system uptime"""
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
        return str(datetime.timedelta(seconds=uptime_seconds))
    except:
        # Fallback for non-Linux systems
        return str(datetime.now() - datetime.fromtimestamp(psutil.boot_time()))

@app.route('/status')
def status():
    return jsonify({
        'status': 'healthy',
        'last_newsletter': health.last_success.isoformat() if health.last_success else None,
        'failures': health.failures,
        'uptime': get_uptime()
    })

@app.route('/health')
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    app.run(port=os.getenv('PORT', 5000))