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
                'first_name': 'สมชาย',
                'last_name': 'ใจดี',
                'email': 'farmer@example.com',
                'phone': '081-111-1111',
                'line_id': 'farmer_line',
                'address': '123 หมู่ 4 ตำบลนาเมืองเพชร อำเภอเมือง จังหวัดพะเยา',
                'about_me': 'สวัสดีครับ ผมเป็นเกษตรกรที่ปลูกข้าวในพื้นที่นี้'
            },
            {
                'username': 'miller1', 
                'password': '123', 
                'role': 'MILLER', 
                'first_name': 'สมศรี',
                'last_name': 'ใจดี',
                'email': 'miller@example.com',
                'phone': '082-222-2222',
                'line_id': 'miller_line',
                'address': '456 หมู่ 2 ตำบลเวียง อำเภอเชียงคำ จังหวัดพะเยา',
                'about_me': 'สวัสดีครับ ผมเป็นเจ้าของโรงสีข้าวในพื้นที่นี้'
            },
            {
                'username': 'govt1', 
                'password': '123', 
                'role': 'GOVT', 
                'first_name': 'สมปอง',
                'last_name': 'ใจดี',
                'email': 'govt@example.com',
                'phone': '083-333-3333',
                'line_id': 'govt_line',
                'address': '789 หมู่ 1 ตำบลท่าวังทอง อำเภอปง จังหวัดพะเยา',
                'about_me': 'สวัสดีครับ ผมเป็นเจ้าหน้าที่รัฐที่ดูแลด้านการเกษตร'
            },
        ]

        for data in users_data:
            # 1. ลองดึง User มาก่อน ถ้าไม่มีก็สร้างใหม่ (get_or_create)
            user, created = User.objects.get_or_create(username=data['username'])

            # 2. อัปเดตข้อมูลพื้นฐาน
            user.email = data['email']
            user.role = data['role']
            
            # --- เพิ่มส่วนบันทึกชื่อ-นามสกุล ---
            user.first_name = data.get('first_name', '')
            user.last_name = data.get('last_name', '')
            # --------------------------------

            # 3. ตรวจสอบและอัปเดตข้อมูลเพิ่มเติม
            if hasattr(user, 'phone'): 
                user.phone = data.get('phone', '')
            
            if hasattr(user, 'line_id'):
                user.line_id = data.get('line_id', '')

            if hasattr(user, 'address'):
                user.address = data.get('address', '')

            if hasattr(user, 'about_me'):
                user.about_me = data.get('about_me', '')

            # 4. ตั้งรหัสผ่าน (เฉพาะตอนสร้างใหม่)
            if created:
                user.set_password(data['password'])
            
            # บันทึกข้อมูลลงฐานข้อมูล
            user.save()

            # 5. แสดงผลลัพธ์
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ สร้างใหม่: {data["username"]}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'🔄 อัปเดตข้อมูล: {data["username"]}'))

        self.stdout.write(self.style.SUCCESS('\n🎉 ดำเนินการเรียบร้อย!'))