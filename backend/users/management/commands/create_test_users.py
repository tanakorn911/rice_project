# backend/users/management/commands/create_test_users.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'สร้าง User ทดสอบสำหรับทุก Role (FARMER, MILLER, GOVT)'

    def handle(self, *args, **options):
        # รายชื่อ User ที่ต้องการสร้าง
        users_data = [
            {
                'username': 'farmer1', 
                'password': '123', 
                'role': 'FARMER', 
                'email': 'farmer@example.com',
                'phone': '081-111-1111'
            },
            {
                'username': 'miller1', 
                'password': '123', 
                'role': 'MILLER', 
                'email': 'miller@example.com',
                'phone': '082-222-2222'
            },
            {
                'username': 'govt1', 
                'password': '123', 
                'role': 'GOVT', 
                'email': 'govt@example.com',
                'phone': '083-333-3333'
            },
        ]

        for data in users_data:
            if not User.objects.filter(username=data['username']).exists():
                User.objects.create_user(
                    username=data['username'],
                    password=data['password'],
                    email=data['email'],
                    role=data['role'],
                    phone=data['phone']
                )
                self.stdout.write(self.style.SUCCESS(f'✅ สร้างสำเร็จ: {data["username"]} ({data["role"]})'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠️ มีอยู่แล้ว: {data["username"]}'))

        self.stdout.write(self.style.SUCCESS('\n🎉 สร้างข้อมูลผู้ใช้ครบถ้วน พร้อมทดสอบ!'))