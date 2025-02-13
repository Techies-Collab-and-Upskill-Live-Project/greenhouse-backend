from rest_framework import viewsets, status, generics, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import * 
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
        if stored_otp:
            if stored_otp["otp"] == otp and stored_otp["email"] == email:
                cache.delete(f"otp_{email}")
                return Response({"message": "OTP verified successfully"}, status=status.HTTP_200_OK)
            elif stored_otp["email"] != email:
                return Response({"message": "invalid email"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "Invalid OTP or OTP expired"}, status=status.HTTP_400_BAD_REQUEST)
        

#send mail
def send_email(email, template_name, context, subject):
    try:
        # Render the email content
        html_content = render_to_string(template_name, context)
        text_content = strip_tags(html_content)
            
        #Create the email
        email_obj= EmailMultiAlternatives(
        subject=subject,   
        body=text_content,
        from_email='youremail@example.com',
        to=[email]
        )
        email_obj.attach_alternative(html_content, "text/html")
        email_obj.send()
        return {
            "message": "Email sent successfully"}, status.HTTP_201_CREATED
    except Exception as e:
            return {"error": "Failed to send email",
            "details": str(e)}, status.HTTP_400_BAD_REQUEST


#handle registration based on selected user_type
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.action == 'register':
            return RegisterSerializer
        elif self.action in ['send_otp', 'resend_otp']:
            return RegisterSerializer
        elif self.action == 'login':
            return LoginSerializer
        elif self.action == 'resetrequest':
            return ResetRequestSerializer
        elif self.action == 'resetpassword':
            return ResetPasswordSerializer
        elif self.action == 'change_password':
            return ChangePasswordSerializer
        elif self.action == 'verify_otp':
            return ActivationSerializer
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
            return Response({'error': 'User with this email already exists, Kindly log in instead'}, status=status.HTTP_409_CONFLICT)

        # Create a new user instance with inactive status and generate OTP    
        
        otp = ''.join([str(random.randint(0, 9)) for _ in range(4)])
        template_name = 'products/otp_email_template.html'
        context= {"otp":otp}
        subject='OTP Verification'
        
        response_data, status_code = send_email(email,template_name, context, subject)
        if status_code == status.HTTP_201_CREATED:
            cache.set(f"otp_{email}", {"otp" : otp, "email" : email}, timeout=300)
            return Response({"message": "OTP sent successfully. It expires in 5 minutes"}, status=status_code)
        else:
            return Response(response_data, status=status_code)
        

    # 2. Verify OTP
    @action(detail=False, methods=['post'], url_path='verify-otp')
    def verify_otp(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']

        # Verify OTP
        response = verify_otp(email, otp)
        if response.status_code == status.HTTP_200_OK:
            user = User.objects.create(email=email)
            user.is_active = True
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

    
    @action(detail=False, methods=['post'], url_path='resend_otp')
    def resend_otp(self, request):
        serializer = self.get_serializer(data = request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        stored_otp = cache.get(f"otp_{email}")
        if not stored_otp:
            return Response({"error": "OTP not found or expired, please request a new OTP."}, status=status.HTTP_400_BAD_REQUEST)
        template_name = 'products/otp_email_template.html'
        context= {'otp': stored_otp["otp"]}
        subject='Resent OTP'
        send_email(email,template_name, context, subject)
        return Response({"message": "OTP resent successfully"}, status=status.HTTP_200_OK)



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
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"message": "if email exist, you should receive an OTP email"}, status=status.HTTP_200_OK)
        
        otp = ''.join([str(random.randint(0, 9)) for _ in range(4)])
        template_name = 'products/otp_email_template.html'
        context= {"otp":otp}
        subject="Request Password OTP"
        
        response_data, status_code = send_email(email,template_name, context, subject)
        if status_code == status.HTTP_201_CREATED:
            cache.set(f"otp_{email}", otp, timeout=300)
            return Response({"message": "OTP sent successfully. It expires in 5 minutes"}, status=status_code)
        else:
            return Response(response_data, status=status_code)


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
        response_data, status_code = send_email(user)
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
        user, created= User.objects.get_or_create(email=email, defaults={'is_active': False})
        if not created:
            return Response({'error': 'User with this email already exists'}, status=status.HTTP_409_CONFLICT)

        otp = ''.join([str(random.randint(0, 9)) for _ in range(4)])
        template_name = 'products/otp_email_template.html'
        context= {"otp":otp}
        subject='OTP Verification'
        email = serializer.validated_data['email']
        cache.set(f"otp_{email}", {"otp":otp, "email":email}, timeout=300)
        send_email(context,template_name, subject)
        response_data, status_code = send_email(email,template_name, context, subject)

        if status_code == status.HTTP_201_CREATED:
            cache.set(f"otp_{email}", otp, timeout=300)
            return Response({"message": "OTP sent successfully. It expires in 5 minutes"}, status=status_code)
        else:
            user.delete()
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
        # Required session keys for vendor registration
        required_keys = ['country', 'email_verified', 'phone_number', 'password', 'user_type']

        # Check if all required data exists in the session
        if not all(key in request.session for key in required_keys):
            return Response(
                {"error": "Please complete all previous registration steps"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate the shop data from the request
        serializer = FlexibleVendorShopSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Extracting data from session
        email = request.session['email_verified']
        raw_password = request.session['password'] 

        # Check if the User already exists
        user, created = User.objects.get_or_create(
            email=email, 
            phone_number = request.session['phone_number'],
            user_type = request.session['user_type'],
            country = request.session['country']
        )

        if created:
            # Hash and set the password if user is newly created
            user.set_password(raw_password)
            user.save()
        else:
            # If user exists and already a vendor, return an error

            if hasattr(user, 'vendor'):
                return Response(
                    {"error": "A vendor with this email already exists."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Create the Vendor instance linked to the User
        vendor = Vendor.objects.create(user=user, **serializer.validated_data)

        # Clear the session data
        for key in required_keys:
            request.session.pop(key, None)

        return Response(
            {
                "message": "Vendor registered successfully.",
                "vendor": FlexibleVendorShopSerializer(vendor).data,
            },
            status=status.HTTP_201_CREATED
        )
    
class NewsletterViewSet(viewsets.ModelViewSet):
    queryset=Newsletter.objects.all()
    serializer_class=NewsletterSerializer
    
    @swagger_auto_schema(
        method='post',
        request_body=NewsletterSerializer,
        responses={200: "OK"}
        )
    @action(detail=False, methods=['post'], url_path='Newsletter')
    def push_newsletter(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        newsletters, created = Newsletter.objects.get_or_create(email=email)
        if not created:
            return Response({"message": "Email already exists"}, status=status.HTTP_409_CONFLICT)

        template_name = 'products/newsletter_email_template.html'
        subject='Welcome to FYSI NewsLetter'
        context = {'email': email}
        send_email(email,template_name, context, subject)
        return Response({"message": "Thanks for Registering"}, status=status.HTTP_201_CREATED)