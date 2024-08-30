from django.shortcuts import render
from rest_framework import generics, status, permissions
from .serializers import *
from rest_framework.response import Response
from django.core.mail import send_mail
from rest_framework_simplejwt.tokens import RefreshToken
from .models import *
import random
from django.core.cache import cache
from django.contrib.auth import authenticate
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError

class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = CustomerSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        if User.objects.filter(email=email).exists():
            return Response({'error': 'User with this email already exists'}, status=status.HTTP_409_CONFLICT)

        user = User(email=email)
        
        
        # Send the OTP via email
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
            # 'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_200_OK)



class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswodSerializer
    
    def get_object(self):
        '''
        return the user making the request
        '''
        return self.request.user

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
        if user.email != email:
            raise serializers.ValidationError("email does not match")
        serializer.save()
        return Response({"detail": "Password reset successfully."}, status=status.HTTP_200_OK)
        #return Response(serializer.data, status=status.HTTP_200_OK)

    def perform_update(self, serializer):
        serializer.save()
        

class  LogoutView(generics.GenericAPIView):
    def post(self, request):
        try:
            refresh_token = request.COOKIES['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': 'Failed to logout'}, status=status.HTTP_400_BAD_REQUEST)
    
# Vendor Registratinon process, the views 
        
class VendorCountryView(generics.CreateAPIView):
    serializer_class = VendorCountrySerializer
    
    def create( self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.session['country'] = serializer.validated_data['country']
        return Response({'message': 'Country selected successfully'}, status=status.HTTP_200_OK)
    

class VendorEmailSubmissionView(generics.CreateAPIView):
    serializer_class = VendorEmailSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data = request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        
        otp = ''.join([str(random.randint(0, 9)) for _ in range(4)])
        
        # Store OTP in cache
        cache.set(f"otp_{email}", otp, timeout=300)  # OTP valid for 5 minutes
        
        # Send OTP via email
        send_mail(
            'Your OTP for registration',
            f'Your OTP is: {otp}',
            'from@fysi.com',
            [email],
            fail_silently=False,
        )
        
        return Response({"message": "OTP sent successfully, It expires in 5 minutes"}, status=status.HTTP_200_OK)
        
        
class VendorOTPVerificationView(generics.GenericAPIView):
    serializer_class = ActivationSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        otp = serializer.validated_data['activation_pin']
        
        stored_otp = cache.get(f"otp_{email}")
        if stored_otp and stored_otp == otp:
            cache.delete(f"otp_{email}")
            request.session['email_verified'] = email
            return Response({"message": "OTP verified successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

class VendorRegistrationView(generics.CreateAPIView):
    serializer_class = VendorRegistrationSerializer

    def create(self, request, *args, **kwargs):
        if not request.session.get('country') or not request.session.get('email_verified'):
            return Response({"error": "Please complete country selection and email verification first"}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Store the validated data in the session instead of creating a user
        request.session['phone_number'] = serializer.validated_data['phone_number']
        request.session['password'] = serializer.validated_data['password']
        request.session['user_type'] = serializer.validated_data['user_type']
        
        return Response({
            "message": "Registration information stored successfully. Please complete vendor shop information.",
        }, status=status.HTTP_200_OK)



class FlexibleVendorShopView(generics.CreateAPIView):
    serializer_class = FlexibleVendorShopSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        required_keys = ['country', 'email_verified', 'phone_number', 'password', 'user_type']
        if not all(key in request.session for key in required_keys):
            return Response({"error": "Please complete all previous registration steps"}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Check if user already exists
            user = User.objects.filter(email=request.session['email_verified']).first()
            
            if user:
                # If user exists, update fields
                user.is_active = True
                user.phone_number = request.session['phone_number']
                user.user_type = request.session['user_type']
                user.country = request.session['country']
                user.set_password(request.session['password'])
                user.save()
            else:
                # Create new user
                user = User.objects.create_user(
                    email=request.session['email_verified'],
                    password=request.session['password'],
                    is_active=True,
                    phone_number=request.session['phone_number'],
                    user_type=request.session['user_type'],
                    country=request.session['country']
                )

            # Get or create vendor
            vendor, created = Vendor.objects.get_or_create(
                user=user,
                defaults=serializer.validated_data
            )
            
            if not created:
                # If vendor exists, update fields
                for key, value in serializer.validated_data.items():
                    setattr(vendor, key, value)
                vendor.save()

            return Response({
                "message": "Vendor registered successfully.",
                # "user": UserSerializer(user).data,
                "vendor": serializer.data,
            }, status=status.HTTP_201_CREATED)
        
        except IntegrityError as e:
            transaction.set_rollback(True)
            return Response({"error": f"Database integrity error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            transaction.set_rollback(True)
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            # Clear the session data
            for key in required_keys:
                request.session.pop(key, None)



