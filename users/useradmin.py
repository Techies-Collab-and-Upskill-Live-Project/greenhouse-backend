from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from .models import User  # Import your custom User model

class UserAdmin(BaseUserAdmin):
    ordering = ['email']
    list_display = ['email', 'is_staff']
    search_fields = ['email']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ( 'phone_number', 'street_address', 'city', 'country')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'user_type')}),
        ('Important dates', {'fields': ('last_login', 'created_on')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    filter_horizontal = ()
    list_filter = ('is_staff', 'is_superuser', 'is_active')

# Unregister the original Group model from admin as it may not be used
admin.site.unregister(Group)
