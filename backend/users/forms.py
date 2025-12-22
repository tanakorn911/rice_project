# backend/users/forms.py
from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ชื่อจริง'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'นามสกุล'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'อีเมล'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'เบอร์โทรศัพท์'}),
        }
        labels = {
            'first_name': 'ชื่อจริง',
            'last_name': 'นามสกุล',
            'email': 'อีเมล',
            'phone': 'เบอร์โทรศัพท์',
        }