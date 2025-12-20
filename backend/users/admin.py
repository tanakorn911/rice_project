from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# ลงทะเบียน User ให้หน้า Admin เห็น Role
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_staff')
    list_filter = ('role', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('ข้อมูลเพิ่มเติม', {'fields': ('role', 'phone')}),
    )