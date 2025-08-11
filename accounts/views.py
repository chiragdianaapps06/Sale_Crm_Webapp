from django.shortcuts import render
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from rest_framework import permissions,status
from .serializers import RegisterSerializer,CreateUserSerializer
from utils.logger import logging
from django.contrib.auth.hashers import make_password
from .emails import send_otp_via_email
from .models import OtpStore


CustomUser = get_user_model()

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

class LoginView(APIView):

    '''
      View that handle user authentication using Jwt Authentication.
      User will send email and password
    '''

    def post(self,request):

        email = request.data.get('email')
        password =  request.data.get('password')

        if not  email or not password:
            return Response({"message":"Pass correct email and password.", 'data':None},status=status.HTTP_400_BAD_REQUEST)
        print(email)

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({"message":"User does not exist", 'data':None},status=status.HTTP_404_NOT_FOUND)


        user = authenticate(email =  email,password= password)

        if user  is None:
            return Response({"message":"Invalid User email or Password."},status=status.HTTP_401_UNAUTHORIZED)
        
        refresh_token = RefreshToken.for_user(user)

        return Response({
            'message': 'User logged in successfully.',
            'access_token': str(refresh_token.access_token),
            'refresh_token': str(refresh_token),
            'email':user.email
        }, status=status.HTTP_200_OK)




class ProtectedView(APIView):


    '''Protected View for testing'''
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"message": "You are authenticated"})



class LogoutView(APIView):

    '''
        View to handle logout by blacklisting the refresh token.
    '''
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            
            if not refresh_token:
                return Response({"message": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)

            # If blacklist is not yet set up or migrations are not done
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()  # Blacklisting the refresh token
            except Exception as e:
                return Response({"message": f"Error blacklisting token: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({"message": "User logged out successfully."}, status=status.HTTP_202_ACCEPTED)
        
        except Exception as e:
            # Catch any other exceptions not related to JWT/TokenError
            return Response({"message": f"An error occurred: {str(e)}", "data": None}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




