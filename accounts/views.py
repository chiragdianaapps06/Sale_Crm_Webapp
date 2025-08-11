from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import permissions,status
from .serializers import RegisterSerializer,CreateUserSerializer
from rest_framework.response import Response
from utils.logger import logging
from django.contrib.auth.hashers import make_password
from .emails import send_otp_via_email
from .models import OtpStore
from rest_framework_simplejwt.tokens import RefreshToken

class UserRegister(APIView):
    def post(self,request):
        try:
            serializer=RegisterSerializer(data=request.data)
            
            if serializer.is_valid():
                logging.info(f"Serializer data : {serializer.data}")
                logging.info(f"data after validation {serializer.validated_data}")
                password=make_password(serializer.validated_data['password'])           #hashes the password for security
                otp=send_otp_via_email(serializer.data['email'])                        #generates an otp randomly
                OtpStore.objects.update_or_create(mail=serializer.validated_data['email'],
                                                  defaults={
                                                      'otp':otp,
                                                      'data':{
                                                          'email':serializer.validated_data['email'],
                                                          'password':password
                                                      }
                                                  })
                logging.info(f"temporary data stored into otpstore model to use in otp verification api")
                return Response({
                    'message':"OTP sent successfully",
                    'data':serializer.data 
                },
                status=status.HTTP_200_OK)
            logging.warning(f"error is {serializer.errors}")
            return Response({
                'data':serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'data':str(e)
            },
            status=status.HTTP_400_BAD_REQUEST)
        

class VerifyOTP(APIView):
    def post(self,request):
        try:
            email=request.data['email']
            otp=request.data['otp']
            otp_temp=OtpStore.objects.get(mail=email)
            
            if not otp_temp.is_valid():
                logging.warning("OTP Expired.")
                return Response({
                    "message":"OTP expired.",
                    "data":None
                },   status=status.HTTP_400_BAD_REQUEST)
            
            if otp_temp.otp!=otp:
                logging.warning("OTP didn't match. try again")
                return Response({
                    "message":"OTP didn't match",
                    "data":None
                },
                status=status.HTTP_400_BAD_REQUEST)
            
            
            serializer=CreateUserSerializer(data=otp_temp.data)
            if serializer.is_valid():
                logging.info(f"serializer validated data: {serializer.validated_data}")
                user=serializer.save()
                logging.info(f"User created into database {user}")
                otp_temp.delete()
                logging.info("OTP entry deleted from the otpstore model")
                refresh=RefreshToken.for_user(user)             #generate token manually for user
                return Response({
                    'data':{
                        "access_token":str(refresh.access_token),
                        'refresh_token':str(refresh)
                    }
                },status=status.HTTP_201_CREATED)
            
            return Response({
                'data':serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'data':str(e)
            },status=status.HTTP_400_BAD_REQUEST)
