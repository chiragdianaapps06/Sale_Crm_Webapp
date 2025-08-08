from django.core.mail import send_mail

import random

from django.conf import settings


def send_otp_via_email(email):
    subject="Mail for account verification"
    otp=random.randint(100000,999999)
    message=f"OTP for account verification {otp}"
    email_from=settings.EMAIL_HOST
    send_mail(subject,message,email_from,[email])
    return otp