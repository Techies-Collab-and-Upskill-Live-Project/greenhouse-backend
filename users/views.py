from rest_framework import viewsets, status, generics, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import User 
from .serializers import *
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from products.models import *
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from rest_framework_simplejwt.tokens import RefreshToken
import random
from django.core.cache import cache
from django.contrib.auth import authenticate
from rest_framework.exceptions import MethodNotAllowed
from drf_yasg.utils import swagger_auto_schema


#verify mail otp
def verify_otp(email, otp):

        stored_otp = cache.get(f"otp_{email}")
        if stored_otp and stored_otp == otp:
            cache.delete(f"otp_{email}")
            return Response({"message": "OTP verified successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

#create and send otp to mail
def create_and_send_otp(user):
        # generate OTP
        try:
            user.generate_otp()
            context = {
            'otp': user.otp
        }
            #send the OTP
            html_content = render_to_string('products/otp_email_template.html', context)
            text_content = strip_tags(html_content)
            
            #Create the email
            email = EmailMultiAlternatives(
            subject='OTP Verification',
            body=text_content,
            from_email='youremail@example.com',
            to=[user.email]
        )
            email.attach_alternative(html_content, "text/html")
            email.send()
            return {"message": "OTP sent to your email"}, status.HTTP_201_CREATED
        except User.DoesNotExist:
            return {"invalid email"}, status.HTTP_400_BAD_REQUEST


#handle registration based on selected user_type
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.action == 'register':
            return RegisterSerializer
        elif self.action == 'send_otp':
            return RegisterSerializer
        elif self.action == 'login':
            return LoginSerializer
        elif self.action in ['resetrequest', 'reactivate']:
            return ResetRequestSerializer
        elif self.action == 'resetpassword':
            return ResetPasswordSerializer
        elif self.action == 'change_password':
            return ChangePasswordSerializer
        elif self.action == 'verify_otp':
            return ActivateSerializer
        elif self.action == 'complete_profile':
            return CompleteProfileSerializer
        elif self.action == 'set_password':
            return SetPasswordSerializer
        else:
            return UserSerializer

    def get_permissions(self):
        # Restrict 'list' (GET) to authenticated admin users
        if self.action == 'list':  # This is the GET method for all users
            permission_classes = [IsAuthenticated, IsAdminUser]
        else:
            # Allow other actions without these strict permissions
            permission_classes = []
        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        # Disable the create (POST) method for this viewset
        raise MethodNotAllowed("POST")

    # 1. Send OTP to email
    @action(detail=False, methods=['post'], url_path='send-otp')
    def send_otp(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        # Check if the email already exists
        if User.objects.filter(email=email).exists():
            return Response({'error': 'User with this email already exists'}, status=status.HTTP_409_CONFLICT)

        # Create a new user instance with inactive status and generate OTP
        user = User(email=email, is_active=False)
        user.save()
        response_data, status_code = create_and_send_otp(user)

        return Response(response_data, status=status_code)

    # 2. Verify OTP
    @action(detail=False, methods=['post'], url_path='verify-otp')
    def verify_otp(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']

        # Verify OTP
        if not User.objects.filter(email=email).exists():
            return Response({'error': 'Invalid email'}, status=status.HTTP_400_BAD_REQUEST)

        response = verify_otp(email, otp)
        user = User.objects.get(email=email)
        if otp == user.otp:
            user.is_active = True
            user.otp = ''
            user.save()
            return Response({'message': 'OTP verified. Proceed to password setup.'}, status=status.HTTP_200_OK)
        return response

    # 3. Set password
    @action(detail=False, methods=['post'], url_path='set-password')
    def set_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        password1 = serializer.validated_data['password1']

        if password != password1:
            return Response({"error": "Passwords do not match"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.get(email=email)
        user.set_password(password)
        user.save()

        return Response({"message": "Password set successfully"}, status=status.HTTP_200_OK)

    # 4. Complete profile
    @action(detail=False, methods=['post'], url_path='complete-profile')
    def complete_profile(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        user = User.objects.get(email=email)
        user.first_name = serializer.validated_data['first_name']
        user.last_name = serializer.validated_data['last_name']
        user.phone_number = serializer.validated_data['phone_number']
        user.save()

        return Response({"message": "Profile completed successfully{id}"}, status=status.HTTP_200_OK)

    
    @action(detail=False, methods=['post'], url_path='reactivate')
    def reactivate(self, request):
        queryset = User.objects.all()
        serializer = self.get_serializer(data = request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError
        response_data, status_code = create_and_send_otp(user)
        return Response(response_data, status=status_code)


#
#LOGIN/OUT ACTIONS
    @action(detail=False, methods=['post'], url_path='login')
    def login(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request, email=serializer.validated_data['email'], password=serializer.validated_data['password'])
        if user is None:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.is_active:
            return Response({'error': 'User account is not active'}, status=status.HTTP_401_UNAUTHORIZED)
        refresh = RefreshToken.for_user(user)
        user_data = UserSerializer(user).data
        profile_data = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone_number': user.phone_number,
        }
        
        # Construct the response
        response_data = {
            'status': 'success',
            'message': 'Login successful',
            'token': {
                'access': str(refresh.access_token),
            },
            'user': {
                'id': user_data['id'],
                'email': user_data['email'],
                'user_type': user_data['user_type'],
                'profile': {
                    'first_name': profile_data['first_name'],
                    'last_name': profile_data['last_name'],
                    'phone_number': profile_data['phone_number']
                }
            }
        }
    
        return Response(response_data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='logout', permission_classes=[IsAuthenticated])
    def logout(self, request):
        serializer = self.get_serializer(data=request.data)
        try:
            refresh_token = request.COOKIES['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': 'Failed to logout'}, status=status.HTTP_400_BAD_REQUEST)


#PASSWORDS ACTIONS
    @action(detail=False, methods=['put'], url_path='changepassword', permission_classes=[IsAuthenticated])
    def change_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        new_password = serializer.validated_data['new_password']
        user.set_password(new_password)
        user.save()

        return Response({"Password changed successfully!"}, status = status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='resetrequest')
    def resetrequest(self, request):
        queryset = User.objects.all()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            response_data, status_code = create_and_send_otp(user)
            return Response(response_data, status=status_code)
        except User.DoesNotExist:
            return Response({"user not registered"}, status = status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='resetpassword')
    def resetpassword(self, request):
        queryset = User.objects.all()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception = True)
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        otp = serializer.validated_data['otp']
        new_password=serializer.validated_data['new_password']
        password_again=serializer.validated_data['password_again']

        if user.otp != otp:
            raise serializers.ValidationError("invalid OTP")
        if user.email != email:
            raise serializers.ValidationError("email does not match")
        if new_password != password_again:
            raise serializers.ValidationError("Passwords do not match")
        user.otp = None
        user.set_password(new_password)
        user.save()
        return Response({"detail": "Password reset successfully."}, status=status.HTTP_200_OK)

 

class VendorViewSet(viewsets.ViewSet):
    queryset = Product.objects.all()

    # Set a default serializer to help with documentation generation
    serializer_class = VendorCountrySerializer

    def get_serializer_class(self):
        """
        Return different serializers based on the action.
        """
        if self.action == 'select_country':
            return VendorCountrySerializer
        elif self.action == 'submit_email':
            return VendorEmailSerializer
        elif self.action == 'verify_otp':
            return ActivationSerializer
        elif self.action == 'register_vendor':
            return VendorRegistrationSerializer
        elif self.action == 'register_vendor_shop':
            return FlexibleVendorShopSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=['post'], url_path='country', serializer_class=VendorCountrySerializer)
    def select_country(self, request, *args, **kwargs):
        """
        Step 1: Vendor selects their country.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.session['country'] = serializer.validated_data['country']
        return Response({'message': 'Country selected successfully'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='email', serializer_class=VendorEmailSerializer)
    def submit_email(self, request, *args, **kwargs):
        #Step 2: Vendor submits email to receive an OTP.
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        
        #Check if the user with this email exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            #If the user doesn’t exist, create one
            user = User.objects.create(email=email)
        #Generate OTP, store in cache, and send email
        response_data, status_code = create_and_send_otp(user)
        if status_code == status.HTTP_201_CREATED:
            cache.set(f"otp_{email}", user.otp, timeout=300)  # Cache OTP for verification
            return Response({"message": "OTP sent successfully. It expires in 5 minutes"}, status=status_code)
        else:
            return Response(response_data, status=status_code)
    @action(detail=False, methods=['post'], url_path='otp-verify', serializer_class=ActivationSerializer)
    def verify_otp(self, request, *args, **kwargs):
        """
        Step 3: Vendor verifies the OTP sent to the email.
        """
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

    @action(detail=False, methods=['post'], url_path='register', serializer_class=VendorRegistrationSerializer)
    def register_vendor(self, request, *args, **kwargs):
        """
        Step 4: Vendor registration (phone number, password, user type).
        """
        if not request.session.get('country') or not request.session.get('email_verified'):
            return Response({"error": "Please complete country selection and email verification first"}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        request.session['phone_number'] = serializer.validated_data['phone_number']
        request.session['password'] = serializer.validated_data['password']
        request.session['user_type'] = serializer.validated_data['user_type']
        
        return Response({
            "message": "Registration information stored successfully. Please complete vendor shop information.",
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='shop', serializer_class=FlexibleVendorShopSerializer)
    def register_vendor_shop(self, request, *args, **kwargs):
        """
        Step 5: Vendor completes shop registration.
        """
        required_keys = ['country', 'email_verified', 'phone_number', 'password', 'user_type']
        if not all(key in request.session for key in required_keys):
            return Response({"error": "Please complete all previous registration steps"}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = User.objects.create_user(
            email=request.session['email_verified'],
            phone_number=request.session['phone_number'],
            password=request.session['password'],
            user_type=request.session['user_type'],
            country=request.session['country']
        )
        user.is_active = True
        user.save()
        
        vendor = Vendor.objects.create(user=user, **serializer.validated_data)
        
        # Clear session data after successful registration
        for key in required_keys:
            if key in request.session:
                del request.session[key]
        
        return Response({
            "message": "Vendor registered successfully.",
            "vendor": FlexibleVendorShopSerializer(vendor).data,
        }, status=status.HTTP_201_CREATED)


 
#extend profile based on user_type

class VendorViewSet(viewsets.ViewSet):

    queryset = Product.objects.all()

    @swagger_auto_schema(
        method='post',
        request_body=VendorCountrySerializer,
        responses={200: 'Country selected successfully'}
    )
    @action(detail=False, methods=['post'], url_path='country')
    def select_country(self, request, *args, **kwargs):
        """
        Step 1: Vendor selects their country.
        """
        serializer = VendorCountrySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.session['country'] = serializer.validated_data['country']
        return Response({'message': 'Country selected successfully'}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        method='post',
        request_body=VendorEmailSerializer,
        responses={200: "OTP sent successfully, It expires in 5 minutes"}
    )
    @action(detail=False, methods=['post'], url_path='email')
    def submit_email(self, request, *args, **kwargs):
        """
        Step 2: Vendor submits email to receive an OTP.
        """
        serializer = VendorEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        
        #Check if the user with this email exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            #If the user doesn’t exist, create one
            user = User.objects.create(email=email)
        #Generate OTP, store in cache, and send email
        response_data, status_code = create_and_send_otp(user)
        if status_code == status.HTTP_201_CREATED:
            cache.set(f"otp_{email}", user.otp, timeout=300)
            return Response({"message": "OTP sent successfully. It expires in 5 minutes"}, status=status_code)
        else:
            return Response(response_data, status=status_code)
        
       
    @swagger_auto_schema(
        method='post',
        request_body=ActivationSerializer,
        responses={200: "OTP verified successfully", 400: "Invalid OTP"}
    )
    @action(detail=False, methods=['post'], url_path='otp-verify')
    def verify_otp(self, request, *args, **kwargs):
        """
        Step 3: Vendor verifies the OTP sent to the email.
        """
        serializer = ActivationSerializer(data=request.data)
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

    @swagger_auto_schema(
        method='post',
        request_body=VendorRegistrationSerializer,
        responses={200: "Registration information stored successfully. Please complete vendor shop information."}
    )
    @action(detail=False, methods=['post'], url_path='register')
    def register_vendor(self, request, *args, **kwargs):
        """
        Step 4: Vendor registration (phone number, password, user type).
        """
        if not request.session.get('country') or not request.session.get('email_verified'):
            return Response({"error": "Please complete country selection and email verification first"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = VendorRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.session['phone_number'] = serializer.validated_data['phone_number']
        request.session['password'] = serializer.validated_data['password']
        request.session['user_type'] = serializer.validated_data['user_type']
        return Response({
            "message": "Registration information stored successfully. Please complete vendor shop information.",
        }, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        method='post',
        request_body=FlexibleVendorShopSerializer,
        responses={201: "Vendor registered successfully."}
    )
    @action(detail=False, methods=['post'], url_path='shop')
    def register_vendor_shop(self, request, *args, **kwargs):
        """
        Step 5: Vendor completes shop registration.
        """
        required_keys = ['country', 'email_verified', 'phone_number', 'password', 'user_type']
        if not all(key in request.session for key in required_keys):
            return Response({"error": "Please complete all previous registration steps"}, status=status.HTTP_400_BAD_REQUEST)
         # Validate the shop data from the request
        serializer = FlexibleVendorShopSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

    # Extracting data from session
        email = request.session['email_verified']
        phone_number = request.session['phone_number']
        password = request.session['password']
        user_type = request.session['user_type']
        country = request.session['country']

    # Check if the User already exists
        user, created = User.objects.get_or_create(
        email=email,
        defaults={
            'phone_number': phone_number,
            'user_type': user_type,
            'country': country,
            'is_active': True
        }
        )
        if created:
            user.set_password(password) 
            user.save()
        else:
            if hasattr(user, 'vendor'):
                return Response({"error": "A vendor with this email already exists."}, status=status.HTTP_400_BAD_REQUEST)

    # Create the Vendor instance linked to the existing or new User
        vendor = Vendor.objects.create(user=user, **serializer.validated_data)
    
    # Clear the session data
        for key in required_keys:
            del request.session[key]
        
        
        return Response({
            "message": "Vendor registered successfully.",
            "vendor": FlexibleVendorShopSerializer(vendor).data,
        }, status=status.HTTP_201_CREATED)