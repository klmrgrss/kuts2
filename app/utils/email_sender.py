# app/utils/email_sender.py
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def send_role_change_notification(user_email: str, user_name: str, new_role: str):
    """Sends an email notifying the user of their new role."""
    
    mail_server = os.getenv("MAIL_SERVER")
    mail_port = os.getenv("MAIL_PORT")
    mail_username = os.getenv("MAIL_USERNAME")
    mail_password = os.getenv("MAIL_PASSWORD")
    mail_from = os.getenv("MAIL_FROM")

    if not all([mail_server, mail_port, mail_username, mail_password, mail_from]):
        print("--- ERROR [Email Sender]: Email service is not configured. Please set MAIL_* variables in .env file. ---")
        return

    subject = "Teie Kuts2 platvormi kasutajaroll on uuendatud"
    body = f"""
    Lugupeetud {user_name},

    Anname teada, et teie kasutajakonto e-posti aadressiga {user_email} on Kuts2 platvormil saanud uue rolli: '{new_role.capitalize()}'.

    Järgmise sisselogimisega rakenduvad uued õigused.

    Lugupidamisega,
    Kuts2 Administratsioon
    """

    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = mail_from
    msg['To'] = user_email

    try:
        with smtplib.SMTP(mail_server, int(mail_port)) as server:
            server.starttls()
            server.login(mail_username, mail_password)
            server.sendmail(mail_from, [user_email], msg.as_string())
        print(f"--- SUCCESS [Email Sender]: Role change notification sent to {user_email}. ---")
    except Exception as e:
        print(f"--- ERROR [Email Sender]: Failed to send email to {user_email}. Error: {e} ---")