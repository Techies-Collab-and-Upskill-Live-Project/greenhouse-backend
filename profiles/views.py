from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework import permissions, status
from users.models import User
from users.serializers import UserSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import *
from .serializers import *
from rest_framework.decorators import action

class ProfileViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    def get_serializer_class(self):
        user = self.request.user
        if user.user_type == 'Vendor':
            return VendorSerializer
        else:
            return CustomerSerializer

#    serializer_class = UserSerializer
#    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        serializer = self.get_serializer_class()(instance=request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
