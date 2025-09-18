from .models import OtpStore
from rest_framework.response import Response
from rest_framework import status
from utils.logger import logging
from django.contrib.auth import get_user_model
import qrcode
from io import BytesIO
from django.core.files import File

User=get_user_model()


def validate_otp(email, otp):
    try:
        otp_obj = OtpStore.objects.get(mail=email)
    except OtpStore.DoesNotExist as e:
        return Response({
            "message":"OTP object not found for the given email",
            "data": None
        }, status=status.HTTP_404_NOT_FOUND)

    # Verify OTP
    if otp_obj.otp != otp:
        logging.warning("OTP didn't match.")
        return Response({
            "message": "OTP didn't match.",
            "data": None
        }, status=status.HTTP_400_BAD_REQUEST)

    # Check if OTP has expired
    if not otp_obj.is_valid():
        logging.warning("OTP expired.")
        return Response({
            "message": "OTP expired.",
            "data": None
        }, status=status.HTTP_400_BAD_REQUEST)

    return otp_obj

def generate_qr(obj):
    url = f"http://127.0.0.1:8000/admin/leads/leads/?assigned_to={obj.id}"
    qr_img=qrcode.make(url)
    buffer=BytesIO()
    qr_img.save(buffer,format="PNG")
    filename=f"qr_{obj.id}.png"
    obj.qr_code.save(filename,File(buffer),save=False)
    buffer.close()

