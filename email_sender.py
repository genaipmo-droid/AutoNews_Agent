import smtplib
from email.mime.text import MIMEText
import os

def send_email(content):
    sender = os.getenv("genai.pmo@gmail.com")
    password = os.getenv("SMTP_PASS")
    receiver = "suvashis.padhi@gmail.com"
    print("DEBUG EMAIL_USER:", sender)
    print("DEBUG EMAIL_PASS EXISTS:", password is not None)

    msg = MIMEText(content, "plain")
    msg["Subject"] = "🇮🇳 Daily AI Advancements in India"
    msg["From"] = sender
    msg["To"] = receiver

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.send_message(msg)
