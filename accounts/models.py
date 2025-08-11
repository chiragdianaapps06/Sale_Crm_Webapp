from django.db import models
from .choices import UserType
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import datetime

class AbsModel(models.Model):
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

    class Meta:
        abstract=True

class CustomUser(AbsModel,AbstractUser):
    email=models.EmailField(unique=True)
    user_type=models.CharField(max_length=10,choices=UserType.choices,default=UserType.sale)
    business_info=models.TextField()
    location=models.TextField()
    is_verified=models.BooleanField(default=False)

    def __str__(self):
        return self.username or self.email

class OtpStore(AbsModel):
    mail=models.EmailField(unique=True)
    otp=models.CharField(max_length=6)
    data=models.JSONField()


    def is_valid(self):
        return self.updated_at>=timezone.now()-timezone.timedelta(minutes=15)