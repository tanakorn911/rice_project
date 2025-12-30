from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

# 1. บังคับต้องเป็น เกษตรกร (FARMER) เท่านั้น
def farmer_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'FARMER':
            return view_func(request, *args, **kwargs)
        
        messages.error(request, "คุณไม่มีสิทธิ์เข้าถึงหน้านี้ (เฉพาะเกษตรกร)")
        return redirect('dashboard') # เด้งกลับหน้าหลัก
    return _wrapped_view

# 2. บังคับต้องเป็น โรงสี (MILLER) เท่านั้น
def miller_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'MILLER':
            return view_func(request, *args, **kwargs)
        
        messages.error(request, "คุณไม่มีสิทธิ์เข้าถึงหน้านี้ (เฉพาะโรงสี)")
        return redirect('dashboard')
    return _wrapped_view

# 3. บังคับต้องเป็น เจ้าหน้าที่ (GOVT) เท่านั้น
def govt_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'GOVT':
            return view_func(request, *args, **kwargs)
        
        messages.error(request, "คุณไม่มีสิทธิ์เข้าถึงหน้านี้ (เฉพาะเจ้าหน้าที่)")
        return redirect('dashboard')
    return _wrapped_view

# 4. ห้ามเจ้าหน้าที่เข้า (เช่น หน้าแก้ไขโปรไฟล์)
def not_govt_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'GOVT':
            messages.warning(request, "เจ้าหน้าที่ไม่สามารถทำรายการนี้ได้")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view