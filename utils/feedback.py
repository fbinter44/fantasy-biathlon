import smtplib
from email.mime.text import MIMEText
import streamlit as st

def send_feedback_email(user, feedback_type, subject, message):
    sender = st.secrets["gmail"]["email"]
    password = st.secrets["gmail"]["app_password"]
    recipient = st.secrets["gmail"]["recipient"]

    body = (
        f"Feedback de : {user}\n"
        f"Type : {feedback_type}\n"
        f"Sujet : {subject}\n\n"
        f"{message}"
    )

    msg = MIMEText(body)
    msg["Subject"] = f"[MPG Biathlon] Feedback – {subject}"
    msg["From"] = sender
    msg["To"] = recipient

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.send_message(msg)
