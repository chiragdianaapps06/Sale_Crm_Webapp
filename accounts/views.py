from django.shortcuts import rende
from rest_framework.views import APIView
from rest_framework import permissions,status
from .serializers import RegisterSerializer
from rest_framework.response import Response
from utils.logger import logging
from django.contrib.auth.hashers import make_password
from .emails import send_otp_via_email
from .models import OtpStore

class UserRegister(APIView):
    def post(self,request):
        try:
            serializer=RegisterSerializer(data=request.data)
            logging.info(f"Serializer data : {serializer.data}")
            
            if serializer.is_valid():
                logging.info(f"data after validation {serializer.validated_data}")
                password=make_password(serializer.validated_data['password'])           #hashes the password for security
                otp=send_otp_via_email(serializer.data['email'])                    #generates an otp randomly
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
            pass
        except Exception as e:
            return Response({
                'data':str(e)
            },status=status.HTTP_400_BAD_REQUEST)