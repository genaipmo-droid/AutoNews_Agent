import smtplib
from email.mime.text import MIMEText
import os

def send_email(content):
    sender = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    receiver = "suvashis.padhi@gmail.com"

    if not sender or not password:
        raise ValueError("EMAIL_USER or EMAIL_PASS is missing from environment variables")

    msg = MIMEText(content, "plain", "utf-8")
    msg["Subject"] = "🇮🇳 Daily AI Advancements in India"
    msg["From"] = sender
    msg["To"] = receiver

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.ehlo()
            server.login(sender, password)
            server.sendmail(sender, receiver, msg.as_string())

        print("✅ Email sent successfully")

    except Exception as e:
        print("❌ Email failed:", repr(e))
        raise
