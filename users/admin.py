from django.contrib import admin
from .useradmin import UserAdmin
from .models import User

admin.site.register(User, UserAdmin)