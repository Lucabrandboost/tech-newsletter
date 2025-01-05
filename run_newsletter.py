from newsletter_generator import NewsletterGenerator
import schedule
import time
import os
from datetime import datetime, timedelta
import logging
import requests

# Setup logging for Heroku
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('NewsletterService')

class HealthCheck:
    def __init__(self):
        self.last_success = None
        self.failures = 0
        
    def record_success(self):
        self.last_success = datetime.now()
        self.failures = 0
        
    def record_failure(self):
        self.failures += 1
        if self.failures >= 3:
            self.alert_admin()
    
    def alert_admin(self):
        # Send alert via email or other notification service
        pass

health = HealthCheck()

def send_daily_newsletter():
    try:
        logger.info("Starting daily newsletter generation")
        newsletter = NewsletterGenerator()
        newsletter.send_newsletter()
        logger.info("Newsletter sent successfully")
        health.record_success()
    except Exception as e:
        logger.error(f"Failed to send newsletter: {str(e)}")
        health.record_failure()

def main():
    # Schedule the newsletter (using UTC time - adjust as needed)
    schedule.every().day.at("22:00").do(send_daily_newsletter)  # 8 AM AEST = 10 PM UTC
    logger.info("Newsletter scheduled")
    
    # Run immediately on startup if within timeframe
    current_hour = datetime.utcnow().hour
    if current_hour >= 22:  # 10 PM UTC
        logger.info("Running initial newsletter send")
        send_daily_newsletter()
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)
        except Exception as e:
            logger.error(f"Scheduler error: {str(e)}")
            time.sleep(60)

if __name__ == "__main__":
    main() 