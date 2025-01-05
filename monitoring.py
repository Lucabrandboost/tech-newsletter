import requests
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('NewsletterMonitor')

def send_alert(message):
    # You can integrate with services like Slack, email, or SMS
    logger.error(message)

def check_heroku_status():
    app_name = "your-heroku-app-name"
    heroku_api_token = os.getenv('HEROKU_API_TOKEN')
    
    headers = {
        'Accept': 'application/vnd.heroku+json; version=3',
        'Authorization': f'Bearer {heroku_api_token}'
    }
    
    try:
        response = requests.get(
            f'https://api.heroku.com/apps/{app_name}/dynos',
            headers=headers
        )
        
        if response.status_code == 200:
            dynos = response.json()
            for dyno in dynos:
                if dyno['type'] == 'worker' and dyno['state'] != 'up':
                    send_alert(f"Worker dyno is {dyno['state']}!")
        else:
            send_alert("Failed to check Heroku status!")
            
    except Exception as e:
        send_alert(f"Error checking Heroku status: {str(e)}")

def verify_last_email():
    # Add logic to verify last email was sent
    pass 