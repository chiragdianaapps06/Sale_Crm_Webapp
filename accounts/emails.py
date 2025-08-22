from django.core.mail import send_mail
from django.template.loader import render_to_string
from utils.logger import logging
from django.conf import settings
import random


def send_otp_via_email(email):
    subject="Mail for account verification"
    otp=random.randint(100000,999999)
    message=f"OTP for account verification {otp}"
    email_from=settings.EMAIL_HOST
    send_mail(subject,message,email_from,[email])
    return otp


def send_account_credentials(user_email, username, password,subject):
    subject = subject
    
    # Render plain text template
    message = render_to_string("emails/account_credentials.txt", {
        "user_name": username,
        "username": username,
        "password": password,
    })
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.EMAIL_HOST,
        recipient_list=user_email,
    )
    logging.info(f"Email sent successfully with message {message}")