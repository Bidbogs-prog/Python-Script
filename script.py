import os
import tweepy
import smtplib
import time
import logging
import schedule
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# X API v2 credentials
BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')

# Email credentials
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = int(os.getenv('SMTP_PORT'))

# Authenticate with X API v2
client = tweepy.Client(bearer_token=BEARER_TOKEN)

def get_tweets_with_keyword(username, keyword, max_retries=3):
    for retry in range(max_retries):
        try:
            query = f'from:{username} {keyword}'
            tweets = client.search_recent_tweets(query=query, max_results=10)
            return tweets.data if tweets.data else []
            
        except tweepy.errors.TooManyRequests as e:
            if retry == max_retries - 1:
                print("Max retries reached. Exiting.")
                raise
                
            reset_time = int(e.response.headers.get('x-rate-limit-reset', 0))
            current_time = int(time.time())
            wait_time = max(reset_time - current_time, 900)  # Minimum 15 minutes
            
            print(f"Rate limit exceeded. Waiting for {datetime.timedelta(seconds=wait_time)}")
            time.sleep(wait_time)
            
        except Exception as e:
            print(f"An error occurred: {e}")
            return []

    return []

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tweet_monitor.log'),
        logging.StreamHandler()
    ]
)

def send_email(subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = EMAIL_ADDRESS
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def main():
    username = "1337FIL"
    keyword = "check-in"
    
    logging.info(f"Starting tweet monitoring for user '{username}' with keyword '{keyword}'")
    
    try:
        matching_tweets = get_tweets_with_keyword(username, keyword)
        
        if matching_tweets:
            email_subject = f"New '{keyword}' post found on {username}'s profile"
            email_body = "\n\n".join([tweet.text for tweet in matching_tweets])
            
            if send_email(email_subject, email_body):
                logging.info("Email notification sent successfully!")
            else:
                logging.error("Failed to send email notification")
        else:
            logging.info(f"No '{keyword}' posts found.")
            
    except Exception as e:
        logging.error(f"An error occurred in main execution: {e}")

if __name__ == "__main__":
    logging.info("Starting scheduled tweet monitoring...")
    
    # Schedule the job every 15 minutes
    schedule.every(15).minutes.do(main)
    
    # Run the job right away instead of waiting for the first interval
    main()
    
    # Keep the script running
    try:
     while True:
        schedule.run_pending()
        time.sleep(1)

    except KeyboardInterrupt:
        logging.info("Stopping tweet monitoring...")        