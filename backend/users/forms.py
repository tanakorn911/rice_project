from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'line_id', 'address', 'about_me']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'ชื่อจริง'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'นามสกุล'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'example@email.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '08x-xxx-xxxx'}),
            'line_id': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Line ID'}),
            'address': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'บ้านเลขที่ หมู่ที่ ตำบล...'}),
            'about_me': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'แนะนำตัวสั้นๆ หรือรายละเอียดเพิ่มเติม'}),
        }
        labels = {
            'first_name': 'ชื่อจริง',
            'last_name': 'นามสกุล',
            'email': 'อีเมล',
            'phone': 'เบอร์โทรศัพท์',
            'line_id': 'Line ID',
            'address': 'ที่อยู่ / ที่ตั้ง',
            'about_me': 'เกี่ยวกับฉัน',
        }