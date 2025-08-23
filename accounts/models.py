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
    business_info=models.TextField(null=True, blank=True)
    location=models.TextField(null=True,blank=True)
    is_verified=models.BooleanField(default=False)
    created_by = models.ForeignKey("self",    null=True,    blank=True,    on_delete=models.SET_NULL,    related_name="referrers")
    
    USERNAME_FIELD = 'email' 
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username or self.email

class OtpStore(AbsModel):
    mail=models.EmailField(unique=True)
    otp=models.CharField(max_length=6)
    data=models.JSONField()


    def is_valid(self):
        return self.updated_at>=timezone.now()-timezone.timedelta(minutes=15)
    


class UserDevice(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    device_token = models.CharField(max_length=255)

    def __str__(self):
        return self.user.username