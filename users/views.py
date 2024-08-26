from django.shortcuts import render
from rest_framework import generics, status
from .serializers import *
from rest_framework.response import Response
from django.core.mail import send_mail
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from .models import *
from django.contrib.auth import authenticate

class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = CustomerSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        if User.objects.filter(email=email).exists():
            return Response({'error': 'User with this email already exists'}, status=status.HTTP_409_CONFLICT)

        user = User(
            email=email,
        )
        
        user.set_password(serializer.validated_data['password'])
        user.generate_activation_pin()
        user.save()

        send_mail(
            'OTP Verification',
            f'Your Activation PIN is {user.activation_pin}',
            'youremail@example.com',
            [user.email],
            fail_silently=False,
        )

        return Response({"message": "User registered successfully. OTP sent to your email"}, status=status.HTTP_201_CREATED)


class ActivationView(generics.CreateAPIView):
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
                user.activation_pin = None
                user.save()
                return Response({'message': 'Account activated successfully!'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid activation PIN.'}, status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(email=serializer.validated_data['email'], password=serializer.validated_data['password'])
        
        if user is None:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return Response({'error': 'User account is not active'}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_200_OK)


class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswodSerializer
    
    def get_object(self):
        '''
        return the user making the requrst
        '''
        return self.request.user