from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from utils.logger import logging
from rest_framework.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from utils.logger import logging
from utils.generate_password import random_password_generator
from .emails import send_account_credentials
import random
User=get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password=serializers.CharField(max_length=255,min_length=6,write_only=True)
    confirm_password=serializers.CharField(max_length=255,min_length=6,write_only=True)


    class Meta:
        model=User
        fields=['email','password','confirm_password']


    def validate(self,attrs):
        try:
            logging.info(attrs['password'])
            logging.info(attrs['confirm_password'])
            validate_password(attrs['password'])
            logging.info(validate_password(attrs['password']))
        except ValidationError as e:
            logging.error("Weak password: %s", e)
            raise ValidationError({"password": e.messages})
        if attrs['password']!=attrs['confirm_password']:
            logging.error("password fields didn't match")
            raise ValidationError({"password":"password fields didn't match"})

        return attrs
    

    # def create(self,validated_data):
    #     user=User(
    #         email=validated_data['email'],
    #         username=validated_data['email'].split('@')[0],
    #         password=validated_data['password'],
    #         is_verified=True
    #     )

    #     user.save()
    #     return user
    

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
            logging.info(attrs['password'])
            logging.info(attrs['confirm_password'])
            validate_password(attrs['password'])
            logging.info(validate_password(attrs['password']))
        except ValidationError as e:
            logging.error("Weak password: %s", e)
            raise ValidationError({"password": e.messages})
        if attrs['password']!=attrs['confirm_password']:

            logging.error("password fields didn't match")
            raise ValidationError({"password":"password fields didn't match"})

        return attrs
    

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields=["email","username","business_info","location","is_verified"]




class ReferrerSerializer(serializers.ModelSerializer):
    business_info = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    business_info = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "created_by","business_info","location"]
        read_only_fields = ["id", "username", "created_by"]

    def create(self, validated_data):
        request = self.context["request"]
        sales_person = request.user  

        # Generate random username + password
        username = validated_data["email"].split('@')[0]
        random_password = random_password_generator()
        logging.info(f'Random password for the user is {random_password}')
        referrer = User.objects.create_user(
            username=username,
            email=validated_data["email"],
            password=random_password,
            user_type="ref",
            created_by=sales_person
        )

        # Send credentials via email
        send_account_credentials(
            subject="Your Referrer Account Credentials",
            username=username,
            password=random_password,
            user_email=[validated_data["email"]],
        )

        return referrer