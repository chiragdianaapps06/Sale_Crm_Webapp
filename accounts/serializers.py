from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from utils.logger import logging
from rest_framework.exceptions import ValidationError

User=get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password=serializers.CharField(max_length=50,min_length=6,write_only=True)
    confirm_password=serializers.CharField(max_length=50,min_length=6,write_only=True)


    class Meta:
        model=User
        fields=['email','password','confirm_password']


    def validate(self,attrs):
        if attrs['password']!=attrs['confirm_password']:
            logging.error("password fields didn't match")
            raise ValidationError({"password":"password fields didn't match"})
        return attrs
    

    def create(self,validated_data):
        user=User(
            email=validated_data['email'],
            username=validated_data['email'].split('@')[0]
        )

        user.set_password(validated_data['password'])
        user.save()
        return user