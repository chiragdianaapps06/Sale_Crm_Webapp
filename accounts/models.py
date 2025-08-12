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
<<<<<<< HEAD
    user_type=models.CharField(max_length=10,choices=UserType.choices,default=UserType.ref)
    business_info=models.TextField(blank=True,null=True)
    location=models.TextField(blank=True,null=True)
=======
    user_type=models.CharField(max_length=10,choices=UserType.choices,default=UserType.sale)
    business_info=models.TextField(null=True, blank=True)
    location=models.TextField(null=True,blank=True)
>>>>>>> 6d5b41ede1aa5c23f66872cae3a874c338ca0d1a
    is_verified=models.BooleanField(default=False)

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