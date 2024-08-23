from django.contrib import admin
from .useradmin import UserAdmin
from .models import User

class  UserAdmin(admin.ModelAdmin):
    exclude = ('created_on',)

admin.site.register(User, UserAdmin)