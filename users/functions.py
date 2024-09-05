 def get_serializer_class(self):
        user_type = self.request.data.get('user_type')
        if user_type == Vendor:
            return VendorRegistrationSerializer
        if user_type == Admin:
            return AdminRegistrationSerializer
        else:
            return CustomerRegistrationSerializer

