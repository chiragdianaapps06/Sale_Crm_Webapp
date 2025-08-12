from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from utils.logger import logging
from rest_framework.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password

User=get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password=serializers.CharField(max_length=255,min_length=6,write_only=True)
    confirm_password=serializers.CharField(max_length=255,min_length=6,write_only=True)


    class Meta:
        model=User
        fields=['email','password','confirm_password']


    def validate(self,attrs):
        try:
            print(attrs['password'])
            print(attrs['confirm_password'])
            validate_password(attrs['password'])
            print(validate_password(attrs['password']))
        except ValidationError as e:
            logging.error("Weak password: %s", e)
            raise ValidationError({"password": e.messages})
        if attrs['password']!=attrs['confirm_password']:
            print("===")
            logging.error("password fields didn't match")
            raise ValidationError({"password":"password fields didn't match"})

        return attrs
    

    

class CreateUserSerializer(serializers.ModelSerializer):
    password=serializers.CharField(write_only=True)

    class Meta:
        model=User
        fields=['email','password']

    def create(self,validated_data):
        user=User(
            email=validated_data['email'],
            username=validated_data['email'].split('@')[0],
            password=validated_data['password'],
            is_verified=True
        )

        user.save()
        return user



class ForgetPasswordOtpSerializer(serializers.ModelSerializer):
    password=serializers.CharField(max_length=255,min_length=6,write_only=True)
    confirm_password=serializers.CharField(max_length=255,min_length=6,write_only=True)


    class Meta:
        model=User
        fields=['password','confirm_password']


    def validate(self,attrs):
        try:
            print(attrs['password'])
            print(attrs['confirm_password'])
            validate_password(attrs['password'])
            print(validate_password(attrs['password']))
        except ValidationError as e:
            logging.error("Weak password: %s", e)
            raise ValidationError({"password": e.messages})
        if attrs['password']!=attrs['confirm_password']:
            print("===")
            logging.error("password fields didn't match")
            raise ValidationError({"password":"password fields didn't match"})

        return attrs