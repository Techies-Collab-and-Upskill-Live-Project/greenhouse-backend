from django.shortcuts import render
from rest_framework import generics, status
from .serializers import *
from rest_framework.response import Response
from django.core.mail import send_mail
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError


# Create your views here.


class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        # Check if the user already exists
        if User.objects.filter(email=email).exists():
            return Response({'error': 'User with this email already exists'}, status=status.HTTP_409_CONFLICT)

        # Create the new user
        user = serializer.save()
        user.generate_activation_pin()
        
        
        # Send the OTP via email
        send_mail(
            'OTP Verification',
            f'Your Activation PIN is {user.activation_pin}',
            'youremail@example.com',
            [user.email],
            fail_silently=False,
        )
        
        return Response({"message": "User registered successfully. OTP sent to your email",
            "refresh": str(refresh),
            "access": access_token},
            status=status.HTTP_201_CREATED)


class ActivationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = ActivationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        activation_pin = serializer.validated_data['activation_pin']
        
        try:
            user = User.objects.get(email=email)
            if user.activation_pin == activation_pin:
                user.is_active = True
                user.activation_pin = None  # Clear the activation pin after successful activation
                user.save()
                return Response({'message': 'Account activated successfully!'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid activation PIN.'}, status=status.HTTP_400_BAD_REQUEST)
        
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ResetrequestView(generics.GenericAPIView):
    queryset = User.objects.all()
    serializer_class = ResetrequestSerializer
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data = request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            otp = user.generate_otp()
             # Send the OTP via email
            send_mail(
                    'OTP Verification',
                    f'Your Password reset OTP is {otp}',
                    'youremail@example.com',
                    [user.email],
                    fail_silently=False,
                    )
            return Response({"Password reset OTP sent to your mail"}, status = status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"user not registered"}, status = status.HTTP_400_BAD_REQUEST)


class ResetpasswordView(generics.GenericAPIView):
    queryset = User.objects.all()
    serializer_class = ResetpasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception = True)
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        otp = serializer.validated_data['otp']
        if user.otp != otp:
            raise serializers.ValidationError("invalid OTP")
        if 
        serializer.save()
        return Response({"detail": "Password reset successfully."}, status=status.HTTP_200_OK)
