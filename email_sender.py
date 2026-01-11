import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os


def send_email(content):
    sender = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    receiver = "suvashis.padhi@gmail.com"

    if not sender or not password:
        raise ValueError("Missing EMAIL_USER or EMAIL_PASS")

    # Email container (supports HTML)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "🇮🇳 Daily AI News – India"
    msg["From"] = sender
    msg["To"] = receiver

    # Full HTML layout
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height:1.6;">
        <h2>🇮🇳 Daily AI News – India</h2>
        <p style="color: gray;">Curated AI developments from India (last 14 days)</p>
        <hr>
        {content}
        <hr>
        <p style="font-size:12px;color:gray;">
            Generated automatically by AutoNews Agent
        </p>
    </body>
    </html>
    """

    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, receiver, msg.as_string())

    print("✅ Beautiful HTML email sent successfully")
