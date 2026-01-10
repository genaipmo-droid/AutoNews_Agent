from agent import run_autonews_agent
from email_sender import send_email

if __name__ == "__main__":
    news = run_autonews_agent()
    send_email(news)
