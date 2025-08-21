from django.shortcuts import render
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from rest_framework import permissions,status
from .serializers import RegisterSerializer,CreateUserSerializer,ForgetPasswordOtpSerializer,UserSerializer
from utils.logger import logging
from django.contrib.auth.hashers import make_password
from .emails import send_otp_via_email
from .models import OtpStore
from rest_framework import viewsets
from .models import CustomUser
from .serializers import ReferrerSerializer

User = get_user_model()

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

    def post(self, request):
        try:
            email = request.data['email']
            otp = request.data['otp']
            password = request.data.get('password', '')
            confirm_password = request.data.get('confirm_password', '')

            # Fetch the OTP record for the email
            otp_temp = OtpStore.objects.filter(mail=email).first()
            print("------")
            # Check if OTP record exists
            if not otp_temp:
                logging.warning(f"No OTP record found for {email}")
                return Response({
                    "message": "No OTP record found for this email.",
                    "data": None
                }, status=status.HTTP_404_NOT_FOUND)

            # Verify OTP
            if otp_temp.otp != otp:
                logging.warning("OTP didn't match.")
                return Response({
                    "message": "OTP didn't match.",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check if OTP has expired
            if not otp_temp.is_valid():
                logging.warning("OTP expired.")
                return Response({
                    "message": "OTP expired.",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)
            print("------")
            # Case 1: If password and confirm_password are provided, it's a password reset process
            if password and confirm_password:
                register_serializer = ForgetPasswordOtpSerializer(data={'password': password, 'confirm_password': confirm_password})

                if not register_serializer.is_valid():
                    logging.warning(f"Password validation failed: {register_serializer.errors}")
                    return Response({
                        "message": "Password and confirm password don't match.",
                        "data": register_serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Proceed with updating password
                try:
                    user = CustomUser.objects.get(email=email)
                    user.password = make_password(password)
                    user.save()

                    logging.info(f"Password updated for {email}")
                    otp_temp.delete()  # Delete OTP record after successful password reset

                    return Response({
                        "message": "Password updated successfully."
                    }, status=status.HTTP_200_OK)

                except CustomUser.DoesNotExist:
                    logging.warning(f"User {email} does not exist for password reset.")
                    return Response({
                        "message": "User does not exist to reset password.",
                        "data": None
                    }, status=status.HTTP_404_NOT_FOUND)

            else:
                # Case 2: If password and confirm_password are NOT provided, this is the initial OTP verification for user creation
                logging.info(f"OTP verified successfully for {email}")

                print("------")

                # If user doesn't exist, create a new one (without requiring a password here)
                try:
                    user = CustomUser.objects.get(email=email)
                    print("------")
                    return Response({
                        "message": "User already exists, you can now log in.",
                        "data": None
                    }, status=status.HTTP_200_OK)

                except CustomUser.DoesNotExist:
                    # User doesn't exist, create a new one
                    logging.info(f"Creating new user for {email}")
                    serializer = CreateUserSerializer(data=otp_temp.data)
                    print("------")

                    if serializer.is_valid():
                        new_user = serializer.save()
                        otp_temp.delete()  # Delete OTP record after successful user creation
                        logging.info(f"New user created: {new_user}")

                        refresh = RefreshToken.for_user(new_user)  # Generate token manually for new user
                        return Response({
                            'data': {
                                "access_token": str(refresh.access_token),
                                'refresh_token': str(refresh)
                            }
                        }, status=status.HTTP_201_CREATED)

                    return Response({
                        "data": serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logging.error(f"Error occurred: {str(e)}")
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

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
        logging.info(email)

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


class DeleteUser(APIView):
    permission_classes=[IsAuthenticated]
    def delete(self,request):
        try:
            user=User.objects.get(id=request.user.id)
            logging.info(f"User fetched successfully from db {user}")
            user.delete()
            logging.info("User deleted successfully.")
            return Response({
                "data":None
            },status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "data":str(e)
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR)


      


class SendOTPForgetPassword(APIView):
    
    def post(self, request):
        try:
            email = request.data.get('email')

            # Generate OTP and send it via email
            otp = send_otp_via_email(email)

            # Store OTP temporarily in OtpStore model
            OtpStore.objects.update_or_create(
                mail=email,
                defaults={
                        'otp': otp,
                        'data':{
                                'email':email
                    }        
                }
            )
            logging.info(f"OTP sent to {email}")

            return Response({
                'message': "OTP has been sent to your email."
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logging.error(f"Error occurred: {str(e)}")
            return Response({
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)



class ReferrerDetailView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,id):
        try:
            user=User.objects.get(id=id)
            serializer=UserSerializer(user)

            if user.user_type=='ref':
                return Response({
                    "data":serializer.data,
                    
                },status=status.HTTP_200_OK)
            return Response({
                "data":None,
                "message":"User is not type of referrer"
            },status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "message":"error",
                "data":str(e)
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        



# class ReferrerViewSet(viewsets.ModelViewSet):
#     permission_classes=[IsAuthenticated]
#     serializer_class=UserSerializer
#     queryset=User.objects.all()


class ReferrerViewSet(viewsets.ModelViewSet):
    serializer_class = ReferrerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Sales person sees only their own referrers
        return User.objects.filter(user_type="ref", created_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save()
