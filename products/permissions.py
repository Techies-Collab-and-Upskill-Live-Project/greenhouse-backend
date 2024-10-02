from rest_framework import permissions

class IsVendor(permissions.BasePermission):
    """
    Allows access only to vendor users.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.user_type == 'Vendor')

class IsCustomer(permissions.BasePermission):
    """
    Allows access only to customer users.
    """

    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.user_type == 'Customer')
